from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from datetime import timedelta
from dotenv import load_dotenv

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

# Create Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_super_secret_key_change_in_production')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your_jwt_secret_key_change_in_production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

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

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(rooms_bp)
app.register_blueprint(progress_bp)
app.register_blueprint(glossary_bp)

# Security headers middleware
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
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
            'glossary': '/api/glossary'
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

# Initialize database on startup
with app.app_context():
    init_db()
    # Ensure demo room exists
    demo_room = Room.ensure_demo_room_exists()
    print(f'✅ Flask app initialized')
    print(f'✅ Demo room available: {Room.DEMO_ROOM_CODE}')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
