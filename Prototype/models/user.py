import bcrypt
from database import query_db, execute_db

class User:
    @staticmethod
    def create(username, email, password, role='student'):
        """Create a new user"""
        # Hash password
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user_id = execute_db(
            'INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
            (username, email, hashed.decode('utf-8'), role)
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
    def update_current_room(user_id, room_id):
        """Update user's current room"""
        execute_db('UPDATE users SET current_room_id = ? WHERE id = ?', (room_id, user_id))
    
    @staticmethod
    def get_all_users():
        """Get all users (excluding passwords)"""
        users = query_db('SELECT id, username, email, role, current_room_id, created_at FROM users')
        return [dict(user) for user in users]
    
    @staticmethod
    def delete_user(user_id):
        """Delete a user and all related data"""
        # Delete user progress
        execute_db('DELETE FROM user_progress WHERE user_id = ?', (user_id,))
        # Delete room memberships
        execute_db('DELETE FROM room_members WHERE user_id = ?', (user_id,))
        # Delete user
        execute_db('DELETE FROM users WHERE id = ?', (user_id,))
