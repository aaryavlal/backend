from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.user import User
from utils.validators import validate_email, validate_password, validate_username, validate_required_fields

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Import limiter from app (will be set by app.py)
from flask import current_app

def get_limiter():
    """Get limiter from current app"""
    return current_app.extensions.get('limiter')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    # Validate required fields
    is_valid, missing = validate_required_fields(data, ['username', 'email', 'password'])
    if not is_valid:
        return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400

    # Validate and sanitize username
    is_valid, result = validate_username(data['username'])
    if not is_valid:
        return jsonify({'error': result}), 400
    username = result

    # Validate email (allow simple formats or placeholders)
    email = data['email'].strip()
    # Allow '?' as a placeholder email for compatibility with main system
    if email != '?' and not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400

    # Validate password
    is_valid, message = validate_password(data['password'])
    if not is_valid:
        return jsonify({'error': message}), 400
    password = data['password']

    # Optional fields
    student_id = data.get('student_id')
    github_id = data.get('github_id')

    # Check if user already exists
    if User.find_by_username(username):
        return jsonify({'error': 'Username already exists'}), 400

    if email != '?' and User.find_by_email(email):
        return jsonify({'error': 'Email already exists'}), 400

    # Create user
    try:
        user = User.create(username, email, password, student_id=student_id, github_id=github_id)

        # Remove password from response
        user.pop('password', None)

        # Create access token (convert ID to string for JWT)
        access_token = create_access_token(identity=str(user['id']))

        return jsonify({
            'message': 'User created successfully',
            'user': user,
            'access_token': access_token
        }), 201
    except Exception as e:
        return jsonify({'error': 'Failed to create user'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()
    
    if not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    username = data['username']
    password = data['password']
    
    # Find user
    user = User.find_by_username(username)
    
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Validate password
    if not User.validate_password(password, user['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Remove password from response
    user.pop('password', None)
    
    # Create access token (convert ID to string for JWT)
    access_token = create_access_token(identity=str(user['id']))
    
    return jsonify({
        'message': 'Login successful',
        'user': user,
        'access_token': access_token
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info"""
    user_id = int(get_jwt_identity())  # Convert back to int
    user = User.find_by_id(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Remove password
    user.pop('password', None)

    # Get completed modules
    user['completed_modules'] = User.get_completed_modules(user_id)

    # Get full room information if user is in a room
    if user.get('current_room_id'):
        from models.room import Room
        room = Room.find_by_id(user['current_room_id'])
        user['current_room'] = room
    else:
        user['current_room'] = None

    return jsonify({'user': user}), 200

@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_current_user():
    """Update current user profile"""
    user_id = int(get_jwt_identity())
    user = User.find_by_id(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    # Update optional fields
    update_fields = {}
    if 'student_id' in data:
        update_fields['student_id'] = data['student_id']
    if 'github_id' in data:
        update_fields['github_id'] = data['github_id']
    if 'email' in data:
        email = data['email'].strip()
        if email != '?' and not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        update_fields['email'] = email

    if update_fields:
        User.update_user(user_id, **update_fields)

    # Get updated user
    updated_user = User.find_by_id(user_id)
    updated_user.pop('password', None)

    return jsonify({
        'message': 'Profile updated successfully',
        'user': updated_user
    }), 200
