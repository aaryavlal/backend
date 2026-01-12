import sqlite3
import os
import bcrypt
from contextlib import contextmanager

# Get absolute path for database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'database.db'))

def get_db_connection():
    """Create a database connection with optimized settings"""
    conn = sqlite3.connect(DATABASE_PATH, timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    # Enable foreign key constraints
    conn.execute('PRAGMA foreign_keys = ON')
    # Enable write-ahead logging for better concurrency
    conn.execute('PRAGMA journal_mode = WAL')
    return conn

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """Initialize the database with all necessary tables"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'student' CHECK(role IN ('student', 'admin')),
                current_room_id INTEGER,
                student_id TEXT,
                github_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (current_room_id) REFERENCES rooms(id)
            )
        ''')

        # Migration: Add student_id and github_id columns if they don't exist
        try:
            cursor.execute("SELECT student_id FROM users LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE users ADD COLUMN student_id TEXT")
            print("✅ Added student_id column to users table")

        try:
            cursor.execute("SELECT github_id FROM users LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE users ADD COLUMN github_id TEXT")
            print("✅ Added github_id column to users table")
        
        # Rooms table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')
        
        # User progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                module_number INTEGER NOT NULL CHECK(module_number >= 1 AND module_number <= 6),
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, module_number),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Room members table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS room_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(room_id, user_id),
                FOREIGN KEY (room_id) REFERENCES rooms(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Room progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS room_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                module_number INTEGER NOT NULL CHECK(module_number >= 1 AND module_number <= 6),
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(room_id, module_number),
                FOREIGN KEY (room_id) REFERENCES rooms(id)
            )
        ''')

        # Glossary table for collaborative knowledge base
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS glossary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                term TEXT NOT NULL,
                definition TEXT NOT NULL,
                author_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(id),
                FOREIGN KEY (author_id) REFERENCES users(id)
            )
        ''')

        # Create index for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_glossary_room_id
            ON glossary(room_id)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_glossary_term
            ON glossary(term)
        ''')

        # Create default admin account if it doesn't exist
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if cursor.fetchone() is None:
            hashed_password = bcrypt.hashpw('Tr12Qu3st@Adm1n!2026'.encode('utf-8'), bcrypt.gensalt())
            cursor.execute(
                'INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
                ('admin', 'admin@tri2quest.local', hashed_password.decode('utf-8'), 'admin')
            )
            print('✅ Default admin account created (username: admin)')

        # Create test users if they don't exist
        test_users = [
            ('testuser1', 'testuser1@tri2quest.local', 'TestUser1@2026'),
            ('testuser2', 'testuser2@tri2quest.local', 'TestUser2@2026'),
            ('testuser3', 'testuser3@tri2quest.local', 'TestUser3@2026'),
            ('testuser4', 'testuser4@tri2quest.local', 'TestUser4@2026'),
            ('testuser5', 'testuser5@tri2quest.local', 'TestUser5@2026'),
            ('testuser6', 'testuser6@tri2quest.local', 'TestUser6@2026'),
            ('testuser7', 'testuser7@tri2quest.local', 'TestUser7@2026'),
            ('testuser8', 'testuser8@tri2quest.local', 'TestUser8@2026'),
            ('testuser9', 'testuser9@tri2quest.local', 'TestUser9@2026'),
        ]
        for username, email, password in test_users:
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone() is None:
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                cursor.execute(
                    'INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
                    (username, email, hashed_password.decode('utf-8'), 'student')
                )
        print('✅ Test users created (testuser1-9)')

        conn.commit()
        print('✅ Database initialized successfully')

def query_db(query, args=(), one=False):
    """Execute a query and return results"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(query, args)
            rv = cursor.fetchall()
            return (rv[0] if rv else None) if one else rv
    except sqlite3.Error as e:
        raise DatabaseError(f"Database query failed: {str(e)}")

def execute_db(query, args=()):
    """Execute a query without returning results (INSERT, UPDATE, DELETE)"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(query, args)
            return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        raise DatabaseError(f"Database integrity error: {str(e)}")
    except sqlite3.Error as e:
        raise DatabaseError(f"Database execution failed: {str(e)}")

class DatabaseError(Exception):
    """Custom exception for database errors"""
    pass

if __name__ == '__main__':
    init_db()
