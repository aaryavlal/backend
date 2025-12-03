from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from models.room import Room

rooms_bp = Blueprint('rooms', __name__, url_prefix='/api/rooms')

def require_admin():
    """Check if current user is admin"""
    user_id = int(get_jwt_identity())
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
    
    user_id = int(get_jwt_identity())
    
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

@rooms_bp.route('/active', methods=['GET'])
@jwt_required()
def get_active_rooms():
    """Get all active rooms with member information (admin only)"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403

    all_rooms = Room.get_all_rooms()

    # Enhance each room with additional info
    active_rooms = []
    for room in all_rooms:
        room_info = {
            'id': room['id'],
            'room_code': room['room_code'],
            'name': room['name'],
            'created_by': room['created_by'],
            'creator_name': room.get('creator_name', 'System'),
            'created_at': room['created_at'],
            'member_count': room.get('member_count', 0),
            'is_demo': room['room_code'] == Room.DEMO_ROOM_CODE,
            'can_delete': room['room_code'] != Room.DEMO_ROOM_CODE
        }

        # Get progress stats
        stats = Room.get_room_stats(room['id'])
        room_info['completed_modules'] = stats['completed_modules']
        room_info['total_modules'] = 6
        room_info['progress_percentage'] = (len(stats['completed_modules']) / 6) * 100

        active_rooms.append(room_info)

    return jsonify({'rooms': active_rooms}), 200

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
    user_id = int(get_jwt_identity())
    
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
    user_id = int(get_jwt_identity())
    
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
    user_id = int(get_jwt_identity())
    room = Room.find_by_id(room_id)

    if not room:
        return jsonify({'error': 'Room not found'}), 404

    # Get room stats without aggressive membership checking
    # The user's current_room_id is sufficient authorization
    stats = Room.get_room_stats(room_id)

    return jsonify(stats), 200

@rooms_bp.route('/<int:room_id>/reset-progress', methods=['POST'])
@jwt_required()
def reset_room_progress(room_id):
    """Reset all progress for a room (admin only or demo room)"""
    room = Room.find_by_id(room_id)
    
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    
    # Allow reset for demo room or if user is admin
    is_demo = Room.is_demo_room(room_id)
    is_admin = require_admin()
    
    if not is_demo and not is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    Room.reset_room_progress(room_id)
    
    return jsonify({
        'message': 'Room progress reset successfully',
        'room_id': room_id
    }), 200

@rooms_bp.route('/bulk-delete', methods=['POST'])
@jwt_required()
def bulk_delete_rooms():
    """Delete multiple rooms at once (admin only, cannot delete demo room)"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    room_ids = data.get('room_ids', [])

    if not room_ids or not isinstance(room_ids, list):
        return jsonify({'error': 'room_ids array is required'}), 400

    deleted = []
    failed = []
    protected = []

    for room_id in room_ids:
        room = Room.find_by_id(room_id)

        if not room:
            failed.append({'id': room_id, 'reason': 'Room not found'})
            continue

        # Check if it's the demo room
        if Room.is_demo_room(room_id):
            protected.append({
                'id': room_id,
                'room_code': room['room_code'],
                'name': room['name'],
                'reason': 'Demo room is protected'
            })
            continue

        try:
            # Delete the room
            Room.delete_room(room_id)
            deleted.append({
                'id': room_id,
                'room_code': room['room_code'],
                'name': room['name']
            })
        except Exception as e:
            failed.append({'id': room_id, 'reason': str(e)})

    return jsonify({
        'message': f'Deleted {len(deleted)} room(s)',
        'deleted': deleted,
        'protected': protected,
        'failed': failed,
        'summary': {
            'deleted_count': len(deleted),
            'protected_count': len(protected),
            'failed_count': len(failed)
        }
    }), 200

@rooms_bp.route('/<int:room_id>', methods=['DELETE'])
@jwt_required()
def delete_room(room_id):
    """Delete a room (admin only, cannot delete demo room)"""
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403

    room = Room.find_by_id(room_id)

    if not room:
        return jsonify({'error': 'Room not found'}), 404

    # Check if it's the demo room
    if Room.is_demo_room(room_id):
        return jsonify({
            'error': 'Cannot delete the demo room',
            'message': 'The demo room is protected and cannot be deleted. You can reset its progress instead.'
        }), 403

    # Get room info before deletion for response
    room_code = room['room_code']
    room_name = room['name']

    # Delete the room
    Room.delete_room(room_id)

    return jsonify({
        'message': 'Room deleted successfully',
        'deleted_room': {
            'id': room_id,
            'room_code': room_code,
            'name': room_name
        }
    }), 200