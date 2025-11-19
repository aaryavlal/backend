import secrets
from database import query_db, execute_db

class Room:
    # Static demo room code that's always available
    DEMO_ROOM_CODE = "DEMO01"
    DEMO_ROOM_NAME = "Demo Room - Always Available"
    @staticmethod
    def generate_room_code():
        """Generate a random 6-character room code"""
        return secrets.token_hex(3).upper()
    
    @staticmethod
    def ensure_demo_room_exists():
        """Ensure the demo room exists, create it if it doesn't"""
        demo_room = Room.find_by_code(Room.DEMO_ROOM_CODE)
        
        if not demo_room:
            # Create demo room with a system user (id=0, we'll handle this specially)
            try:
                room_id = execute_db(
                    'INSERT INTO rooms (room_code, name, created_by) VALUES (?, ?, ?)',
                    (Room.DEMO_ROOM_CODE, Room.DEMO_ROOM_NAME, 0)
                )
                return Room.find_by_id(room_id)
            except:
                # If it fails, try to find it again (race condition)
                return Room.find_by_code(Room.DEMO_ROOM_CODE)
        
        return demo_room
    
    @staticmethod
    def is_demo_room(room_id):
        """Check if a room is the demo room"""
        room = Room.find_by_id(room_id)
        return room and room['room_code'] == Room.DEMO_ROOM_CODE
    
    @staticmethod
    def create(name, created_by):
        """Create a new room with a unique room code"""
        max_attempts = 10
        
        for _ in range(max_attempts):
            room_code = Room.generate_room_code()
            
            # Check if code already exists
            if not Room.find_by_code(room_code):
                room_id = execute_db(
                    'INSERT INTO rooms (room_code, name, created_by) VALUES (?, ?, ?)',
                    (room_code, name, created_by)
                )
                return Room.find_by_id(room_id)
        
        raise Exception('Failed to generate unique room code')
    
    @staticmethod
    def find_by_id(room_id):
        """Find room by ID"""
        room = query_db('SELECT * FROM rooms WHERE id = ?', (room_id,), one=True)
        return dict(room) if room else None
    
    @staticmethod
    def find_by_code(room_code):
        """Find room by code"""
        room = query_db('SELECT * FROM rooms WHERE room_code = ?', (room_code,), one=True)
        return dict(room) if room else None
    
    @staticmethod
    def get_all_rooms():
        """Get all rooms with additional info"""
        rooms = query_db('''
            SELECT r.*, u.username as creator_name,
                   (SELECT COUNT(*) FROM room_members WHERE room_id = r.id) as member_count
            FROM rooms r
            LEFT JOIN users u ON r.created_by = u.id
            ORDER BY r.created_at DESC
        ''')
        return [dict(room) for room in rooms]
    
    @staticmethod
    def add_member(room_id, user_id):
        """Add a user to a room"""
        try:
            execute_db(
                'INSERT INTO room_members (room_id, user_id) VALUES (?, ?)',
                (room_id, user_id)
            )
            # Update user's current room
            execute_db('UPDATE users SET current_room_id = ? WHERE id = ?', (room_id, user_id))
            return True
        except:
            # User already in room
            return False
    
    @staticmethod
    def remove_member(room_id, user_id):
        """Remove a user from a room"""
        execute_db('DELETE FROM room_members WHERE room_id = ? AND user_id = ?', (room_id, user_id))
        execute_db('UPDATE users SET current_room_id = NULL WHERE id = ?', (user_id,))
    
    @staticmethod
    def get_members(room_id):
        """Get all members of a room"""
        members = query_db('''
            SELECT u.id, u.username, u.email, u.role, rm.joined_at
            FROM room_members rm
            JOIN users u ON rm.user_id = u.id
            WHERE rm.room_id = ?
            ORDER BY rm.joined_at
        ''', (room_id,))
        return [dict(member) for member in members]
    
    @staticmethod
    def get_member_progress(room_id):
        """Get progress of all members in a room"""
        members = query_db('''
            SELECT u.id, u.username,
                   GROUP_CONCAT(up.module_number) as completed_modules
            FROM room_members rm
            JOIN users u ON rm.user_id = u.id
            LEFT JOIN user_progress up ON u.id = up.user_id
            WHERE rm.room_id = ?
            GROUP BY u.id, u.username
            ORDER BY u.username
        ''', (room_id,))
        
        result = []
        for member in members:
            member_dict = dict(member)
            if member_dict['completed_modules']:
                member_dict['completed_modules'] = [int(m) for m in member_dict['completed_modules'].split(',')]
            else:
                member_dict['completed_modules'] = []
            result.append(member_dict)
        
        return result
    
    @staticmethod
    def get_room_progress(room_id):
        """Get modules completed by the entire room"""
        progress = query_db('''
            SELECT module_number, completed_at
            FROM room_progress
            WHERE room_id = ?
            ORDER BY module_number
        ''', (room_id,))
        return [dict(p) for p in progress]
    
    @staticmethod
    def check_and_update_room_progress(room_id, module_number):
        """Check if all members completed a module and update room progress"""
        members = Room.get_members(room_id)
        
        if not members:
            return {'module_complete': False, 'room_complete': False}
        
        # Count how many members completed this module
        result = query_db('''
            SELECT COUNT(DISTINCT user_id) as completed_count
            FROM user_progress up
            JOIN room_members rm ON up.user_id = rm.user_id
            WHERE rm.room_id = ? AND up.module_number = ?
        ''', (room_id, module_number), one=True)
        
        completed_count = result['completed_count']
        all_completed = completed_count == len(members)
        
        if all_completed:
            # Mark module as complete for the room
            try:
                execute_db(
                    'INSERT INTO room_progress (room_id, module_number) VALUES (?, ?)',
                    (room_id, module_number)
                )
            except:
                # Already marked
                pass
            
            # Check if all 6 modules are complete
            completed_modules = Room.get_room_progress(room_id)
            
            if len(completed_modules) == 6:
                # Check if this is the demo room
                if Room.is_demo_room(room_id):
                    # Reset demo room progress instead of deleting
                    Room.reset_demo_room(room_id)
                    return {'module_complete': True, 'room_complete': True, 'is_demo': True}
                else:
                    # Regular room - delete it
                    Room.delete_room(room_id)
                    return {'module_complete': True, 'room_complete': True}
            
            return {'module_complete': True, 'room_complete': False}
        
        return {'module_complete': False, 'room_complete': False}
    
    @staticmethod
    def reset_demo_room(room_id):
        """Reset the demo room's progress but keep members"""
        if not Room.is_demo_room(room_id):
            return
        
        # Delete all room progress
        execute_db('DELETE FROM room_progress WHERE room_id = ?', (room_id,))
        
        # Delete all user progress for members in this room
        members = Room.get_members(room_id)
        for member in members:
            execute_db('DELETE FROM user_progress WHERE user_id = ?', (member['id'],))
    
    @staticmethod
    def delete_room(room_id):
        """Delete a room and all associated data (protects demo room)"""
        # Don't allow deleting the demo room
        if Room.is_demo_room(room_id):
            return
        
        # Update all members' current_room_id to NULL
        members = Room.get_members(room_id)
        for member in members:
            execute_db('UPDATE users SET current_room_id = NULL WHERE id = ?', (member['id'],))
        
        # Delete room progress
        execute_db('DELETE FROM room_progress WHERE room_id = ?', (room_id,))
        # Delete room members
        execute_db('DELETE FROM room_members WHERE room_id = ?', (room_id,))
        # Delete room
        execute_db('DELETE FROM rooms WHERE id = ?', (room_id,))
    
    @staticmethod
    def get_room_stats(room_id):
        """Get comprehensive stats for a room"""
        members = Room.get_members(room_id)
        room_progress = Room.get_room_progress(room_id)
        member_progress = Room.get_member_progress(room_id)
        
        return {
            'total_members': len(members),
            'completed_modules': [p['module_number'] for p in room_progress],
            'member_progress': member_progress
        }