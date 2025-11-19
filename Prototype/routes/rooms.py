from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from models.room import Room

rooms_bp = Blueprint('rooms', __name__, url_prefix='/api/rooms')

def require_admin():
    """Check if current user is admin"""
    user_id = get_jwt_identity()
    user = User.find_by_id(user_id)
    return user and user['role'] == 'admin'

@rooms_bp.route('/', methods=['POST'])
@jwt_required()
def create_room():
    """Create a new room (admin only)"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': 'Room name required'}), 400
    
    user_id = get_jwt_identity()
    
    try:
        room = Room.create(data['name'], user_id)
        return jsonify({
            'message': 'Room created successfully',
            'room': room
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@rooms_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_rooms():
    """Get all rooms"""
    rooms = Room.get_all_rooms()
    return jsonify({'rooms': rooms}), 200

@rooms_bp.route('/<int:room_id>', methods=['GET'])
@jwt_required()
def get_room(room_id):
    """Get room details"""
    room = Room.find_by_id(room_id)
    
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    
    # Get room stats
    stats = Room.get_room_stats(room_id)
    room['stats'] = stats
    
    return jsonify({'room': room}), 200

@rooms_bp.route('/join', methods=['POST'])
@jwt_required()
def join_room():
    """Join a room by room code"""
    data = request.get_json()
    
    if not data.get('room_code'):
        return jsonify({'error': 'Room code required'}), 400
    
    room_code = data['room_code'].upper()
    user_id = get_jwt_identity()
    
    # Find room
    room = Room.find_by_code(room_code)
    
    if not room:
        return jsonify({'error': 'Invalid room code'}), 404
    
    # Add user to room
    success = Room.add_member(room['id'], user_id)
    
    if not success:
        return jsonify({'error': 'Already a member of this room'}), 400
    
    return jsonify({
        'message': 'Joined room successfully',
        'room': room
    }), 200

@rooms_bp.route('/<int:room_id>/leave', methods=['POST'])
@jwt_required()
def leave_room(room_id):
    """Leave a room"""
    user_id = get_jwt_identity()
    
    room = Room.find_by_id(room_id)
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    
    Room.remove_member(room_id, user_id)
    
    return jsonify({'message': 'Left room successfully'}), 200

@rooms_bp.route('/<int:room_id>/members', methods=['GET'])
@jwt_required()
def get_room_members(room_id):
    """Get all members of a room"""
    room = Room.find_by_id(room_id)
    
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    
    members = Room.get_members(room_id)
    
    return jsonify({'members': members}), 200

@rooms_bp.route('/<int:room_id>/progress', methods=['GET'])
@jwt_required()
def get_room_progress(room_id):
    """Get progress for a room"""
    room = Room.find_by_id(room_id)
    
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    
    stats = Room.get_room_stats(room_id)
    
    return jsonify(stats), 200

@rooms_bp.route('/<int:room_id>', methods=['DELETE'])
@jwt_required()
def delete_room(room_id):
    """Delete a room (admin only)"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    room = Room.find_by_id(room_id)
    
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    
    Room.delete_room(room_id)
    
    return jsonify({'message': 'Room deleted successfully'}), 200
