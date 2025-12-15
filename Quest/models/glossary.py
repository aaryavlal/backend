import sys
import os

# Support both module imports and direct script imports
try:
    from ..database import query_db, execute_db
except (ImportError, ValueError):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database import query_db, execute_db

class Glossary:
    @staticmethod
    def create(room_id, term, definition, author_id):
        """Create a new glossary entry"""
        glossary_id = execute_db(
            'INSERT INTO glossary (room_id, term, definition, author_id) VALUES (?, ?, ?, ?)',
            (room_id, term, definition, author_id)
        )
        return Glossary.find_by_id(glossary_id)

    @staticmethod
    def find_by_id(glossary_id):
        """Find glossary entry by ID"""
        entry = query_db('''
            SELECT g.*, u.username as author_name
            FROM glossary g
            JOIN users u ON g.author_id = u.id
            WHERE g.id = ?
        ''', (glossary_id,), one=True)
        return dict(entry) if entry else None

    @staticmethod
    def get_by_room(room_id, search_term=None):
        """Get all glossary entries for a room with optional search"""
        if search_term:
            # Search in both term and definition (case-insensitive)
            entries = query_db('''
                SELECT g.*, u.username as author_name
                FROM glossary g
                JOIN users u ON g.author_id = u.id
                WHERE g.room_id = ?
                AND (LOWER(g.term) LIKE ? OR LOWER(g.definition) LIKE ?)
                ORDER BY g.term ASC
            ''', (room_id, f'%{search_term.lower()}%', f'%{search_term.lower()}%'))
        else:
            entries = query_db('''
                SELECT g.*, u.username as author_name
                FROM glossary g
                JOIN users u ON g.author_id = u.id
                WHERE g.room_id = ?
                ORDER BY g.term ASC
            ''', (room_id,))

        return [dict(entry) for entry in entries]

    @staticmethod
    def update(glossary_id, term=None, definition=None):
        """Update a glossary entry"""
        entry = Glossary.find_by_id(glossary_id)
        if not entry:
            return None

        # Build dynamic update query
        updates = []
        params = []

        if term is not None:
            updates.append('term = ?')
            params.append(term)

        if definition is not None:
            updates.append('definition = ?')
            params.append(definition)

        if not updates:
            return entry

        params.append(glossary_id)
        query = f"UPDATE glossary SET {', '.join(updates)} WHERE id = ?"

        execute_db(query, tuple(params))
        return Glossary.find_by_id(glossary_id)

    @staticmethod
    def delete(glossary_id):
        """Delete a glossary entry"""
        execute_db('DELETE FROM glossary WHERE id = ?', (glossary_id,))

    @staticmethod
    def delete_by_room(room_id):
        """Delete all glossary entries for a room"""
        execute_db('DELETE FROM glossary WHERE room_id = ?', (room_id,))

    @staticmethod
    def get_stats(room_id):
        """Get statistics for a room's glossary"""
        result = query_db('''
            SELECT
                COUNT(*) as total_entries,
                COUNT(DISTINCT author_id) as contributors
            FROM glossary
            WHERE room_id = ?
        ''', (room_id,), one=True)

        return dict(result) if result else {'total_entries': 0, 'contributors': 0}
