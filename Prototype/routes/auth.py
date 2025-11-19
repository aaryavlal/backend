from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['username', 'email', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    username = data['username']
    email = data['email']
    password = data['password']
    
    # Check if user already exists
    if User.find_by_username(username):
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.find_by_email(email):
        return jsonify({'error': 'Email already exists'}), 400
    
    # Create user
    try:
        user = User.create(username, email, password)
        
        # Remove password from response
        user.pop('password', None)
        
        # Create access token
        access_token = create_access_token(identity=user['id'])
        
        return jsonify({
            'message': 'User created successfully',
            'user': user,
            'access_token': access_token
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    
    # Create access token
    access_token = create_access_token(identity=user['id'])
    
    return jsonify({
        'message': 'Login successful',
        'user': user,
        'access_token': access_token
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info"""
    user_id = get_jwt_identity()
    user = User.find_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Remove password
    user.pop('password', None)
    
    # Get completed modules
    user['completed_modules'] = User.get_completed_modules(user_id)
    
    return jsonify({'user': user}), 200
