#!/usr/bin/env python3
"""
Debug script to test JWT token generation and validation
Run this to see if JWT is working correctly
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create test app
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your_jwt_secret_key_change_in_production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

jwt = JWTManager(app)

print("=" * 60)
print("JWT DEBUG TEST")
print("=" * 60)
print(f"JWT_SECRET_KEY: {app.config['JWT_SECRET_KEY']}")
print()

# Test creating a token
with app.app_context():
    test_user_id = "123"  # Must be string!
    token = create_access_token(identity=test_user_id)
    print(f"✅ Created token for user_id={test_user_id}")
    print(f"Token: {token[:50]}...")
    print()

# Test endpoint with token
@app.route('/test')
@jwt_required()
def test():
    user_id = get_jwt_identity()
    return {'user_id': user_id, 'message': 'Success!'}

# Test the token
with app.test_client() as client:
    # Test without token
    print("Testing endpoint WITHOUT token...")
    response = client.get('/test')
    print(f"Status: {response.status_code}")
    print(f"Response: {response.get_json()}")
    print()
    
    # Test with token
    print("Testing endpoint WITH token...")
    response = client.get('/test', headers={'Authorization': f'Bearer {token}'})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.get_json()}")
    print()

if response.status_code == 200:
    print("✅ JWT is working correctly!")
else:
    print("❌ JWT is NOT working!")
    print("\nTroubleshooting:")
    print("1. Make sure .env file exists with JWT_SECRET_KEY")
    print("2. Make sure python-dotenv is installed: pip install python-dotenv")
    print("3. Check that the same JWT_SECRET_KEY is used in app.py")
