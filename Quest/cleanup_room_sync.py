#!/usr/bin/env python3
"""
Clean up room membership inconsistencies
This script ensures current_room_id matches actual room_members table
"""

import sys
import os

# Handle relative imports when run as a script
if __name__ == '__main__' and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from database import init_db, query_db, execute_db
else:
    from .database import init_db, query_db, execute_db

def cleanup_room_sync():
    """Fix any users with current_room_id set but not in room_members"""
    init_db()

    # Get all users with a current_room_id
    users = query_db('SELECT id, username, current_room_id FROM users WHERE current_room_id IS NOT NULL')

    fixed_count = 0

    for user in users:
        user_id = user['id']
        room_id = user['current_room_id']
        username = user['username']

        # Check if they're actually in the room_members table
        membership = query_db(
            'SELECT * FROM room_members WHERE user_id = ? AND room_id = ?',
            (user_id, room_id),
            one=True
        )

        if not membership:
            print(f"❌ {username} (ID: {user_id}) has current_room_id={room_id} but is NOT in room_members")
            print(f"   Fixing: Setting current_room_id to NULL")
            execute_db('UPDATE users SET current_room_id = NULL WHERE id = ?', (user_id,))
            fixed_count += 1
        else:
            print(f"✅ {username} (ID: {user_id}) is correctly in room {room_id}")

    print(f"\n{'='*60}")
    print(f"Fixed {fixed_count} inconsistencies")
    print(f"{'='*60}")

if __name__ == '__main__':
    cleanup_room_sync()
