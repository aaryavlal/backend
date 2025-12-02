import sqlite3
import os
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (current_room_id) REFERENCES rooms(id)
            )
        ''')
        
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
