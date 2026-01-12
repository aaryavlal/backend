3#!/usr/bin/env python3
"""
Script to create an admin user
Usage: python -m Quest.create_admin (from backend directory)
   or: python create_admin.py (from Quest directory)
   or: python create_admin.py --default (to create default admin account)
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

# Default admin credentials
DEFAULT_ADMIN_USERNAME = 'admin'
DEFAULT_ADMIN_EMAIL = 'admin@tri2quest.local'
DEFAULT_ADMIN_PASSWORD = 'Tr12Qu3st@Adm1n!2026'


def create_default_admin():
    """Create a default admin account with preset credentials"""
    init_db()

    print("=" * 50)
    print("Creating Default Admin User")
    print("=" * 50)

    # Check if admin already exists
    if User.find_by_username(DEFAULT_ADMIN_USERNAME):
        print(f"Admin user '{DEFAULT_ADMIN_USERNAME}' already exists.")
        return False

    if User.find_by_email(DEFAULT_ADMIN_EMAIL):
        print(f"Email '{DEFAULT_ADMIN_EMAIL}' already exists.")
        return False

    try:
        user = User.create(
            username=DEFAULT_ADMIN_USERNAME,
            email=DEFAULT_ADMIN_EMAIL,
            password=DEFAULT_ADMIN_PASSWORD,
            role='admin'
        )
        print(f"\nDefault admin user created successfully!")
        print(f"   Username: {DEFAULT_ADMIN_USERNAME}")
        print(f"   Email: {DEFAULT_ADMIN_EMAIL}")
        print(f"   Password: {DEFAULT_ADMIN_PASSWORD}")
        print(f"\n   IMPORTANT: Change this password after first login!")
        return True
    except Exception as e:
        print(f"Error creating default admin: {e}")
        return False


def create_admin():
    # Initialize database
    init_db()
    
    print("=" * 50)
    print("Create Admin User")
    print("=" * 50)
    
    # Get user input
    username = input("Enter admin username: ").strip()
    email = input("Enter admin email: ").strip()
    password = getpass.getpass("Enter admin password: ")
    password_confirm = getpass.getpass("Confirm password: ")

    # Optional fields
    student_id = input("Enter student ID (optional, press Enter to skip): ").strip() or None
    github_id = input("Enter GitHub ID (optional, press Enter to skip): ").strip() or None
    
    # Validate inputs
    if not username or not email or not password:
        print("❌ Error: All fields are required")
        return
    
    if password != password_confirm:
        print("❌ Error: Passwords do not match")
        return
    
    # Check if user already exists
    if User.find_by_username(username):
        print(f"❌ Error: Username '{username}' already exists")
        return
    
    if User.find_by_email(email):
        print(f"❌ Error: Email '{email}' already exists")
        return
    
    # Create admin user
    try:
        user = User.create(username, email, password, role='admin', student_id=student_id, github_id=github_id)
        print(f"\n✅ Admin user '{username}' created successfully!")
        print(f"   ID: {user['id']}")
        print(f"   Email: {user['email']}")
        print(f"   Role: {user['role']}")
        if student_id:
            print(f"   Student ID: {user['student_id']}")
        if github_id:
            print(f"   GitHub ID: {user['github_id']}")
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")

if __name__ == '__main__':
    create_admin()
