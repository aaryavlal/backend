from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.glossary import Glossary
from ..models.room import Room
from ..models.user import User

glossary_bp = Blueprint('glossary', __name__, url_prefix='/api/glossary')

def is_room_member(room_id, user_id):
    """Check if user is a member of the room"""
    members = Room.get_members(room_id)
    return any(member['id'] == user_id for member in members)

@glossary_bp.route('/room/<int:room_id>', methods=['GET'])
@jwt_required()
def get_room_glossary(room_id):
    """Get all glossary entries for a room with optional search"""
    user_id = int(get_jwt_identity())

    # Verify room exists
    room = Room.find_by_id(room_id)
    if not room:
        return jsonify({'error': 'Room not found'}), 404

    # Verify user is a member of the room
    if not is_room_member(room_id, user_id):
        return jsonify({'error': 'You must be a member of this room to view its glossary'}), 403

    # Get optional search parameter
    search_term = request.args.get('search', None)

    # Get glossary entries
    entries = Glossary.get_by_room(room_id, search_term)

    # Get stats
    stats = Glossary.get_stats(room_id)

    return jsonify({
        'entries': entries,
        'stats': stats,
        'search_term': search_term
    }), 200

@glossary_bp.route('/room/<int:room_id>', methods=['POST'])
@jwt_required()
def add_glossary_entry(room_id):
    """Add a new glossary entry to a room"""
    user_id = int(get_jwt_identity())
    data = request.get_json()

    # Validate input
    if not data.get('term'):
        return jsonify({'error': 'Term is required'}), 400

    if not data.get('definition'):
        return jsonify({'error': 'Definition is required'}), 400

    # Verify room exists
    room = Room.find_by_id(room_id)
    if not room:
        return jsonify({'error': 'Room not found'}), 404

    # Verify user is a member of the room
    if not is_room_member(room_id, user_id):
        return jsonify({'error': 'You must be a member of this room to add glossary entries'}), 403

    # Create glossary entry
    try:
        entry = Glossary.create(
            room_id=room_id,
            term=data['term'].strip(),
            definition=data['definition'].strip(),
            author_id=user_id
        )

        return jsonify({
            'message': 'Glossary entry added successfully',
            'entry': entry
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@glossary_bp.route('/<int:entry_id>', methods=['GET'])
@jwt_required()
def get_glossary_entry(entry_id):
    """Get a specific glossary entry"""
    user_id = int(get_jwt_identity())

    entry = Glossary.find_by_id(entry_id)

    if not entry:
        return jsonify({'error': 'Glossary entry not found'}), 404

    # Verify user is a member of the room
    if not is_room_member(entry['room_id'], user_id):
        return jsonify({'error': 'You must be a member of this room to view this entry'}), 403

    return jsonify({'entry': entry}), 200

@glossary_bp.route('/<int:entry_id>', methods=['PUT'])
@jwt_required()
def update_glossary_entry(entry_id):
    """Update a glossary entry (author or admin only)"""
    user_id = int(get_jwt_identity())
    data = request.get_json()

    # Find entry
    entry = Glossary.find_by_id(entry_id)
    if not entry:
        return jsonify({'error': 'Glossary entry not found'}), 404

    # Check if user is the author or admin
    user = User.find_by_id(user_id)
    if entry['author_id'] != user_id and user['role'] != 'admin':
        return jsonify({'error': 'Only the author or an admin can update this entry'}), 403

    # Verify user is a member of the room
    if not is_room_member(entry['room_id'], user_id):
        return jsonify({'error': 'You must be a member of this room to update this entry'}), 403

    # Update entry
    try:
        updated_entry = Glossary.update(
            glossary_id=entry_id,
            term=data.get('term', '').strip() if data.get('term') else None,
            definition=data.get('definition', '').strip() if data.get('definition') else None
        )

        return jsonify({
            'message': 'Glossary entry updated successfully',
            'entry': updated_entry
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@glossary_bp.route('/<int:entry_id>', methods=['DELETE'])
@jwt_required()
def delete_glossary_entry(entry_id):
    """Delete a glossary entry (author or admin only)"""
    user_id = int(get_jwt_identity())

    # Find entry
    entry = Glossary.find_by_id(entry_id)
    if not entry:
        return jsonify({'error': 'Glossary entry not found'}), 404

    # Check if user is the author or admin
    user = User.find_by_id(user_id)
    if entry['author_id'] != user_id and user['role'] != 'admin':
        return jsonify({'error': 'Only the author or an admin can delete this entry'}), 403

    # Delete entry
    try:
        Glossary.delete(entry_id)
        return jsonify({'message': 'Glossary entry deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@glossary_bp.route('/room/<int:room_id>/stats', methods=['GET'])
@jwt_required()
def get_glossary_stats(room_id):
    """Get statistics for a room's glossary"""
    user_id = int(get_jwt_identity())

    # Verify room exists
    room = Room.find_by_id(room_id)
    if not room:
        return jsonify({'error': 'Room not found'}), 404

    # Verify user is a member of the room
    if not is_room_member(room_id, user_id):
        return jsonify({'error': 'You must be a member of this room to view its glossary statistics'}), 403

    stats = Glossary.get_stats(room_id)

    return jsonify(stats), 200
