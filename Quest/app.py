from flask import Blueprint, jsonify, request
import os
import json
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Create Blueprint
quest_bp = Blueprint('quest', __name__)

# Configure data folder for jokes/scenarios (will be set in main app)
DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_FOLDER, exist_ok=True)

# Configure logs folder for game logging (will be set in main app)
LOGS_FOLDER = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOGS_FOLDER, exist_ok=True)


GEMINI_API_KEY = "" #insert api key here if you want to use the Gemini grading feature
#gemini_client = genai.Client(api_key=GEMINI_API_KEY)

QUESTION = (
    "Mission debrief: Module 4 explained that every algorithm mixes sequential setup/combining steps with parallel chunks. "
    "In 2 short sentences, describe why the sequential portion eventually limits speedup even if you keep adding processors, "
    "and mention one practical tweak from the module (shrink the sequential slice, expose more parallel work, reduce overhead/balance issues) "
    "that keeps improvements coming a little longer."
)

RUBRIC = """
Score from 0 to 3. Keep grading gentle and focus on Module 4 concepts.

3 points:
- States that the sequential portion (setup/combining/critical section) becomes the bottleneck so extra processors have diminishing returns.
- Names one concrete Module 4 tactic (reduce sequential work, expose more parallelism, trim overhead/balance costs).

2 points:
- Provides either the bottleneck explanation or the adjustment idea clearly, but not both.

1 point:
- Only says “more cores make it faster” or similar with no reference to sequential limits or improvements.

0 points:
- Off-topic or empty response.
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
@quest_bp.route("/api/quiz/grade", methods=["POST"])
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


# Root endpoint
@quest_bp.route('/quest')
def quest_index():
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
@quest_bp.route('/quest/health')
def quest_health():
    return jsonify({'status': 'healthy'}), 200
