import bcrypt
import sys
import os

# Support both module imports and direct script imports
try:
    from ..database import query_db, execute_db
except (ImportError, ValueError):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database import query_db, execute_db

class User:
    @staticmethod
    def create(username, email, password, role='student', student_id=None, github_id=None):
        """Create a new user"""
        # Hash password
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        user_id = execute_db(
            'INSERT INTO users (username, email, password, role, student_id, github_id) VALUES (?, ?, ?, ?, ?, ?)',
            (username, email, hashed.decode('utf-8'), role, student_id, github_id)
        )

        return User.find_by_id(user_id)
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        user = query_db('SELECT * FROM users WHERE id = ?', (user_id,), one=True)
        return dict(user) if user else None
    
    @staticmethod
    def find_by_username(username):
        """Find user by username"""
        user = query_db('SELECT * FROM users WHERE username = ?', (username,), one=True)
        return dict(user) if user else None
    
    @staticmethod
    def find_by_email(email):
        """Find user by email"""
        user = query_db('SELECT * FROM users WHERE email = ?', (email,), one=True)
        return dict(user) if user else None
    
    @staticmethod
    def validate_password(plain_password, hashed_password):
        """Validate password"""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    @staticmethod
    def get_completed_modules(user_id):
        """Get list of completed modules for a user"""
        results = query_db(
            'SELECT module_number FROM user_progress WHERE user_id = ? ORDER BY module_number',
            (user_id,)
        )
        return [row['module_number'] for row in results]
    
    @staticmethod
    def mark_module_complete(user_id, module_number):
        """Mark a module as complete for a user"""
        try:
            execute_db(
                'INSERT INTO user_progress (user_id, module_number) VALUES (?, ?)',
                (user_id, module_number)
            )
            return True
        except:
            # Module already completed (UNIQUE constraint)
            return False

    @staticmethod
    def remove_module_complete(user_id, module_number):
        """Remove a module completion for a user"""
        try:
            execute_db(
                'DELETE FROM user_progress WHERE user_id = ? AND module_number = ?',
                (user_id, module_number)
            )
            return True
        except:
            return False

    @staticmethod
    def update_current_room(user_id, room_id):
        """Update user's current room"""
        execute_db('UPDATE users SET current_room_id = ? WHERE id = ?', (room_id, user_id))

    @staticmethod
    def update_user(user_id, **kwargs):
        """Update user details"""
        allowed_fields = ['student_id', 'github_id', 'email']
        updates = []
        values = []

        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                updates.append(f"{field} = ?")
                values.append(value)

        if updates:
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            execute_db(query, tuple(values))
            return True
        return False

    @staticmethod
    def get_all_users():
        """Get all users (excluding passwords)"""
        users = query_db('SELECT id, username, email, role, current_room_id, student_id, github_id, created_at FROM users')
        return [dict(user) for user in users]
    
    @staticmethod
    def delete_user(user_id):
        """Delete a user and all related data"""
        # Delete user progress
        execute_db('DELETE FROM user_progress WHERE user_id = ?', (user_id,))
        # Delete room memberships
        execute_db('DELETE FROM room_members WHERE user_id = ?', (user_id,))
        # Delete glossary entries authored by user
        execute_db('DELETE FROM glossary WHERE author_id = ?', (user_id,))
        # Update current_room_id for this user to NULL (in case of foreign key constraints)
        execute_db('UPDATE users SET current_room_id = NULL WHERE id = ?', (user_id,))
        # Delete user
        execute_db('DELETE FROM users WHERE id = ?', (user_id,))
