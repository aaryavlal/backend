#!/usr/bin/env python3
"""
Script to edit user information
Usage: python -m Quest.edit_user (from backend directory)
   or: python edit_user.py (from Quest directory)
"""

import sys
import os

# Handle relative imports when run as a script
if __name__ == '__main__' and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from database import init_db
    from models.user import User
else:
    from .database import init_db
    from .models.user import User

import getpass
import bcrypt

def list_users():
    """Display all users in the system"""
    users = User.get_all_users()
    if not users:
        print("❌ No users found in the database")
        return []

    print("\n" + "=" * 80)
    print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Role':<10}")
    print("=" * 80)
    for user in users:
        print(f"{user['id']:<5} {user['username']:<20} {user['email']:<30} {user['role']:<10}")
    print("=" * 80 + "\n")
    return users

def edit_user():
    # Initialize database
    init_db()

    print("=" * 50)
    print("Edit User Information")
    print("=" * 50)

    # List all users
    users = list_users()
    if not users:
        return

    # Get user to edit
    try:
        user_id = int(input("Enter user ID to edit: ").strip())
    except ValueError:
        print("❌ Error: Invalid user ID")
        return

    # Find the user
    user = User.find_by_id(user_id)
    if not user:
        print(f"❌ Error: User with ID {user_id} not found")
        return

    print(f"\n📝 Editing user: {user['username']}")
    print("=" * 50)
    print("Leave fields blank to keep current values")
    print("=" * 50 + "\n")

    # Display current values and get new ones
    print(f"Current email: {user['email']}")
    new_email = input("New email (or press Enter to keep current): ").strip()

    print(f"\nCurrent student ID: {user.get('student_id', 'Not set')}")
    new_student_id = input("New student ID (or press Enter to keep current): ").strip()

    print(f"\nCurrent GitHub ID: {user.get('github_id', 'Not set')}")
    new_github_id = input("New GitHub ID (or press Enter to keep current): ").strip()

    # Ask if they want to change password
    change_password = input("\nDo you want to change the password? (y/n): ").strip().lower()
    new_password = None
    if change_password == 'y':
        new_password = getpass.getpass("Enter new password: ")
        password_confirm = getpass.getpass("Confirm new password: ")

        if new_password != password_confirm:
            print("❌ Error: Passwords do not match")
            return

    # Prepare update fields
    update_fields = {}

    if new_email:
        update_fields['email'] = new_email

    if new_student_id:
        update_fields['student_id'] = new_student_id
    elif new_student_id == '' and user.get('student_id'):
        # Allow clearing the field if user enters empty string
        update_fields['student_id'] = None

    if new_github_id:
        update_fields['github_id'] = new_github_id
    elif new_github_id == '' and user.get('github_id'):
        # Allow clearing the field if user enters empty string
        update_fields['github_id'] = None

    # Update user
    try:
        # Update password separately if needed
        if new_password:
            from database import execute_db
            hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            execute_db('UPDATE users SET password = ? WHERE id = ?',
                      (hashed.decode('utf-8'), user_id))
            print("✅ Password updated successfully")

        # Update other fields
        if update_fields:
            User.update_user(user_id, **update_fields)
            print("✅ User information updated successfully")

        # Get and display updated user
        updated_user = User.find_by_id(user_id)
        print(f"\n{'='*50}")
        print("Updated User Information:")
        print(f"{'='*50}")
        print(f"   ID: {updated_user['id']}")
        print(f"   Username: {updated_user['username']}")
        print(f"   Email: {updated_user['email']}")
        print(f"   Role: {updated_user['role']}")
        if updated_user.get('student_id'):
            print(f"   Student ID: {updated_user['student_id']}")
        if updated_user.get('github_id'):
            print(f"   GitHub ID: {updated_user['github_id']}")
        print(f"{'='*50}\n")

    except Exception as e:
        print(f"❌ Error updating user: {e}")

if __name__ == '__main__':
    edit_user()
