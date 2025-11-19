from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from models.room import Room

progress_bp = Blueprint('progress', __name__, url_prefix='/api/progress')

@progress_bp.route('/complete', methods=['POST'])
@jwt_required()
def complete_module():
    """Mark a module as complete for the current user"""
    data = request.get_json()
    
    if not data.get('module_number'):
        return jsonify({'error': 'Module number required'}), 400
    
    module_number = data['module_number']
    
    # Validate module number
    if not isinstance(module_number, int) or module_number < 1 or module_number > 6:
        return jsonify({'error': 'Module number must be between 1 and 6'}), 400
    
    user_id = get_jwt_identity()
    
    # Mark module complete
    User.mark_module_complete(user_id, module_number)
    
    # Get user's current room
    user = User.find_by_id(user_id)
    room_id = user.get('current_room_id')
    
    response_data = {
        'message': f'Module {module_number} completed',
        'completed_modules': User.get_completed_modules(user_id)
    }
    
    # Check room progress if user is in a room
    if room_id:
        progress_result = Room.check_and_update_room_progress(room_id, module_number)
        response_data['room_progress'] = progress_result
        
        if progress_result['room_complete']:
            if progress_result.get('is_demo'):
                response_data['message'] = 'Congratulations! All modules complete. Demo room has been reset!'
            else:
                response_data['message'] = 'Congratulations! All modules complete. Room has been closed.'
        elif progress_result['module_complete']:
            response_data['message'] = f'Module {module_number} completed by entire room!'
    
    return jsonify(response_data), 200

@progress_bp.route('/my-progress', methods=['GET'])
@jwt_required()
def get_my_progress():
    """Get current user's progress"""
    user_id = get_jwt_identity()
    
    completed_modules = User.get_completed_modules(user_id)
    
    # Calculate progress percentage
    progress_percentage = (len(completed_modules) / 6) * 100
    
    return jsonify({
        'completed_modules': completed_modules,
        'total_modules': 6,
        'progress_percentage': round(progress_percentage, 2)
    }), 200

@progress_bp.route('/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_progress(user_id):
    """Get progress for a specific user"""
    user = User.find_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    completed_modules = User.get_completed_modules(user_id)
    
    return jsonify({
        'user_id': user_id,
        'username': user['username'],
        'completed_modules': completed_modules,
        'total_modules': 6,
        'progress_percentage': round((len(completed_modules) / 6) * 100, 2)
    }), 200