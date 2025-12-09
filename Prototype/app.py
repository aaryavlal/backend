from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import json
from datetime import timedelta
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Import database initialization
from database import init_db

# Import models
from models.room import Room

# Import blueprints
from routes.auth import auth_bp
from routes.rooms import rooms_bp
from routes.progress import progress_bp
from routes.glossary import glossary_bp
from routes.game_logs import game_logs_bp
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from hacks.joke import scenario_api

# Create Flask app
app = Flask(__name__)
app.url_map.strict_slashes = False

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_super_secret_key_change_in_production')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your_jwt_secret_key_change_in_production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

# Configure data folder for jokes/scenarios
app.config['DATA_FOLDER'] = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)

# Configure logs folder for game logging
app.config['LOGS_FOLDER'] = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(app.config['LOGS_FOLDER'], exist_ok=True)

# Security headers
app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max request size

# Configure CORS with security settings
cors_config = {
    "origins": os.environ.get('CORS_ORIGINS', '*').split(','),
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"],
    "expose_headers": ["Content-Type", "Authorization"],
    "supports_credentials": True,
    "max_age": 3600
}
CORS(app, resources={r"/api/*": cors_config})

# Initialize JWT
jwt = JWTManager(app)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per hour", "50 per minute"],
    storage_uri="memory://",
    strategy="fixed-window"
)


GEMINI_API_KEY = "" #insert api key here if you want to use the Gemini grading feature
#gemini_client = genai.Client(api_key=GEMINI_API_KEY)

QUESTION = (
    "In your own words, explain what parallel computing is and give one real-world "
    "example where it would be beneficial. Answer in 3–5 sentences."
)

RUBRIC = """
Score from 0 to 3.

3 points:
- Clearly defines parallel computing (multiple tasks executed at the same time).
- Gives at least one realistic, correct real-world example (e.g., image processing, simulations, AI training).
- Explanation is coherent and 3–5 sentences long.

2 points:
- Mostly correct definition but missing some detail or weak example.

1 point:
- Very vague or partially incorrect understanding.

0 points:
- Totally off-topic or no meaningful answer.
"""

GRADING_INSTRUCTIONS = """
You are an automated grading assistant for a CS quiz.
Use ONLY the rubric below to score.

Return ONLY valid JSON in exactly this format:

{
  "score": <integer 0-3>,
  "max_score": 3,
  "feedback": "<short explanation>"
}
"""

# ----------------------------------------------------
# LIST USED TO MANAGE PROGRAM COMPLEXITY (BACKEND)
# ----------------------------------------------------
# This list stores a history of recent quiz attempts.
# It is used by summarize_attempts to build feedback
# about the user's overall performance.
RECENT_ATTEMPTS = []


# ----------------------------------------------------------------
# STUDENT-DEVELOPED PROCEDURE WITH LIST + SEQUENCING/SELECTION/LOOP
# ----------------------------------------------------------------
def summarize_attempts(attempts, max_items=5):
    """
    Build a short summary of recent quiz attempts.

    Parameters:
        attempts: list of attempt dictionaries (each has 'score' and 'max_score')
        max_items: maximum number of recent attempts to include

    Returns:
        Multi-line string describing performance history.
    """

    # --- SEQUENCING: set up early-return and data structures in order ---
    if not attempts:
        return "No attempts have been recorded yet."

    summary_lines = []

    # --- ITERATION: loop through the last max_items attempts (from newest to oldest) ---
    start_index = len(attempts) - 1
    end_index = max(-1, len(attempts) - 1 - max_items)

    for index in range(start_index, end_index, -1):
        attempt = attempts[index]
        score = attempt["score"]
        max_score = attempt["max_score"]

        # --- SELECTION: choose a label based on score ---
        if score == max_score:
            label = "Perfect"
        elif score > 0:
            label = "Partial"
        else:
            label = "No credit"

        summary_lines.append(
            f"Attempt {index + 1}: {label} ({score}/{max_score})"
        )

    # --- SEQUENCING: combine the lines into a single summary string ---
    summary_text = "\n".join(summary_lines)
    return summary_text


# -----------------------------
# QUIZ GRADING ENDPOINT
# -----------------------------
@app.route("/api/quiz/grade", methods=["POST"])
def grade_quiz():
    print(">>> grade_quiz endpoint hit")

    if gemini_client is None:
        return jsonify({
            "error": "Gemini API is not configured on the server (GEMINI_API_KEY missing)."
        }), 500

    # ---- INPUT FROM USER (body JSON field 'answer') ----
    data = request.get_json(silent=True) or {}
    student_answer = (data.get("answer") or "").strip()

    if not student_answer:
        return jsonify({"error": "Field 'answer' is required."}), 400

    prompt = f"""{GRADING_INSTRUCTIONS}

Question:
{QUESTION}

Rubric:
{RUBRIC}

Student answer:
\"\"\"{student_answer}\"\"\""""

    try:
        # Ask Gemini for a JSON response
        gemini_response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )

        result = getattr(gemini_response, "parsed", None)
        raw_text = getattr(gemini_response, "text", "")

        if isinstance(result, dict):
            graded = result
        else:
            try:
                graded = json.loads(raw_text)
            except Exception:
                graded = {
                    "score": 0,
                    "max_score": 3,
                    "feedback": raw_text or "Model returned an unexpected response."
                }

        graded_score = graded.get("score", 0)
        graded_max = graded.get("max_score", 3)
        graded_feedback = graded.get("feedback", "No feedback provided.")

        safe_payload = {
            "score": int(graded_score) if isinstance(graded_score, (int, float, str)) else 0,
            "max_score": int(graded_max) if isinstance(graded_max, (int, float, str)) else 3,
            "feedback": str(graded_feedback),
        }

        # ---------------------------------------------------------
        # USE THE LIST + PROCEDURE TO GENERATE ATTEMPT HISTORY
        # ---------------------------------------------------------
        RECENT_ATTEMPTS.append({
            "score": safe_payload["score"],
            "max_score": safe_payload["max_score"],
        })

        attempt_summary = summarize_attempts(RECENT_ATTEMPTS)
        safe_payload["attempt_summary"] = attempt_summary

        print(">>> Gemini graded:", safe_payload)

        # ---- OUTPUT: JSON based on input and program functionality ----
        return jsonify(safe_payload), 200

    except Exception as e:
        print(">>> Gemini error:", e)
        return jsonify({
            "error": "Gemini API call failed.",
            "details": str(e)
        }), 500


# -----------------------------
# Existing routes
# -----------------------------
app.register_blueprint(auth_bp)
app.register_blueprint(rooms_bp)
app.register_blueprint(progress_bp)
app.register_blueprint(glossary_bp)
app.register_blueprint(scenario_api)
app.register_blueprint(game_logs_bp)

# Security headers middleware
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Root endpoint
@app.route('/')
def index():
    return jsonify({
        'message': 'Parallel Computing Education Platform API',
        'version': '1.0.0',
        'endpoints': {
            'auth': '/api/auth',
            'rooms': '/api/rooms',
            'progress': '/api/progress',
            'glossary': '/api/glossary',
            'scenarios': '/api/scenarios',
            'game_logs': '/api/game-logs'
        }
    })

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

# Test JWT endpoint
@app.route('/api/test-auth')
@jwt_required()
def test_auth():
    from flask_jwt_extended import get_jwt_identity
    user_id = get_jwt_identity()
    return jsonify({
        'message': 'Token is valid!',
        'user_id': user_id
    }), 200

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'Invalid token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'Authorization token required'}), 401

# Initialize DB on startup
with app.app_context():
    init_db()
    demo_room = Room.ensure_demo_room_exists()
    # Initialize scenarios
    from hacks.jokes import initScenarios
    initScenarios()
    print("✅ Flask app initialized")
    print(f"✅ Demo room available: {Room.DEMO_ROOM_CODE}")

if __name__ == '__main__':
    print(">>> STARTING FLASK ON PORT 5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
