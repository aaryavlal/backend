#!/usr/bin/env python3
"""
Quest User Deletion Script

This script allows you to delete users from the Quest database.
It handles cleanup of all related data (progress, room memberships, glossary entries).
"""

import os
import sys
from database import get_db

def list_users():
    """Display all users in the database"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, email, role, created_at
                FROM users
                ORDER BY created_at DESC
            """)
            users = cursor.fetchall()

            if not users:
                print("\n❌ No users found in the database.")
                return []

            print("\n" + "="*80)
            print("📋 Current Users in Database")
            print("="*80)
            print(f"{'ID':<6} {'Username':<20} {'Email':<30} {'Role':<10} {'Created'}")
            print("-"*80)

            for user in users:
                user_id = user['id']
                username = user['username']
                email = user['email']
                role = user['role']
                created = user['created_at']
                print(f"{user_id:<6} {username:<20} {email:<30} {role:<10} {created}")

            print("-"*80)
            print(f"Total users: {len(users)}\n")
            return users

    except Exception as e:
        print(f"❌ Error listing users: {e}")
        return []

def get_user_details(user_id):
    """Get detailed information about a user"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # Get user info
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()

            if not user:
                return None

            # Get user progress count
            cursor.execute("SELECT COUNT(*) as count FROM user_progress WHERE user_id = ?", (user_id,))
            progress_count = cursor.fetchone()['count']

            # Get room memberships
            cursor.execute("""
                SELECT r.name, r.room_code
                FROM room_members rm
                JOIN rooms r ON rm.room_id = r.id
                WHERE rm.user_id = ?
            """, (user_id,))
            rooms = cursor.fetchall()

            # Get glossary entries
            cursor.execute("SELECT COUNT(*) as count FROM glossary WHERE author_id = ?", (user_id,))
            glossary_count = cursor.fetchone()['count']

            return {
                'user': user,
                'progress_count': progress_count,
                'rooms': rooms,
                'glossary_count': glossary_count
            }

    except Exception as e:
        print(f"❌ Error getting user details: {e}")
        return None

def delete_user(user_id, force=False):
    """Delete a user and all related data"""
    details = get_user_details(user_id)

    if not details:
        print(f"❌ User with ID {user_id} not found.")
        return False

    user = details['user']
    username = user['username']
    email = user['email']

    print("\n" + "="*80)
    print(f"🗑️  User Deletion Summary")
    print("="*80)
    print(f"Username: {username}")
    print(f"Email: {email}")
    print(f"Role: {user['role']}")
    print(f"Created: {user['created_at']}")
    print("\n📊 Data to be deleted:")
    print(f"  - Progress entries: {details['progress_count']}")
    print(f"  - Room memberships: {len(details['rooms'])}")
    print(f"  - Glossary entries: {details['glossary_count']}")

    if details['rooms']:
        print("\n🏠 Rooms this user is a member of:")
        for room in details['rooms']:
            print(f"  - {room['name']} ({room['room_code']})")

    print("="*80)

    if not force:
        confirmation = input(f"\n⚠️  Are you sure you want to delete user '{username}'? This cannot be undone! (yes/no): ")
        if confirmation.lower() != 'yes':
            print("❌ Deletion cancelled.")
            return False

    try:
        with get_db() as conn:
            cursor = conn.cursor()

            print("\n🔄 Deleting user data...")

            # Delete user progress
            cursor.execute("DELETE FROM user_progress WHERE user_id = ?", (user_id,))
            print(f"  ✓ Deleted {cursor.rowcount} progress entries")

            # Delete room memberships
            cursor.execute("DELETE FROM room_members WHERE user_id = ?", (user_id,))
            print(f"  ✓ Deleted {cursor.rowcount} room memberships")

            # Delete glossary entries
            cursor.execute("DELETE FROM glossary WHERE author_id = ?", (user_id,))
            print(f"  ✓ Deleted {cursor.rowcount} glossary entries")

            # Delete the user
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            print(f"  ✓ Deleted user account")

            conn.commit()

        print(f"\n✅ User '{username}' (ID: {user_id}) has been successfully deleted!")
        return True

    except Exception as e:
        print(f"\n❌ Error deleting user: {e}")
        return False

def delete_user_by_username(username, force=False):
    """Delete a user by username"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

            if not user:
                print(f"❌ User '{username}' not found.")
                return False

            return delete_user(user['id'], force)

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def interactive_mode():
    """Interactive user deletion interface"""
    print("\n" + "="*80)
    print("🗑️  Quest User Deletion Tool")
    print("="*80)

    users = list_users()

    if not users:
        return

    print("\nOptions:")
    print("  1. Delete user by ID")
    print("  2. Delete user by username")
    print("  3. Exit")

    choice = input("\nEnter your choice (1-3): ").strip()

    if choice == '1':
        user_id = input("Enter user ID to delete: ").strip()
        try:
            user_id = int(user_id)
            delete_user(user_id)
        except ValueError:
            print("❌ Invalid user ID. Must be a number.")

    elif choice == '2':
        username = input("Enter username to delete: ").strip()
        delete_user_by_username(username)

    elif choice == '3':
        print("👋 Goodbye!")
        return

    else:
        print("❌ Invalid choice.")

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Delete users from the Quest database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python delete_user.py                    # Interactive mode
  python delete_user.py --list            # List all users
  python delete_user.py --id 5            # Delete user by ID
  python delete_user.py --username john   # Delete user by username
  python delete_user.py --id 5 --force    # Delete without confirmation
        """
    )

    parser.add_argument('--list', action='store_true', help='List all users')
    parser.add_argument('--id', type=int, help='Delete user by ID')
    parser.add_argument('--username', type=str, help='Delete user by username')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')

    args = parser.parse_args()

    # Check if database exists
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        print("Please run the application first to create the database.")
        sys.exit(1)

    # Handle command line arguments
    if args.list:
        list_users()
    elif args.id:
        delete_user(args.id, args.force)
    elif args.username:
        delete_user_by_username(args.username, args.force)
    else:
        # No arguments provided, run interactive mode
        interactive_mode()

if __name__ == '__main__':
    main()
