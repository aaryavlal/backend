#!/usr/bin/env python3
"""
Quick API test script to verify all endpoints are working
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def print_response(title, response):
    print(f"\n{'='*60}")
    print(f"📍 {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)

def test_api():
    print("🚀 Testing Parallel Computing Education API")
    
    # Test 1: Health check
    response = requests.get(f"{BASE_URL}/health")
    print_response("Health Check", response)
    
    # Test 2: Register student
    student_data = {
        "username": "teststudent",
        "email": "teststudent@example.com",
        "password": "testpass123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=student_data)
    print_response("Register Student", response)
    
    if response.status_code == 201:
        student_token = response.json()['access_token']
        
        # Test 3: Login
        login_data = {
            "username": "teststudent",
            "password": "testpass123"
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print_response("Login", response)
        
        # Test 4: Get current user
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        print_response("Get Current User", response)
        
        # Test 5: Complete a module
        module_data = {"module_number": 1}
        response = requests.post(f"{BASE_URL}/api/progress/complete", 
                               json=module_data, headers=headers)
        print_response("Complete Module 1", response)
        
        # Test 6: Get my progress
        response = requests.get(f"{BASE_URL}/api/progress/my-progress", headers=headers)
        print_response("Get My Progress", response)
        
        # Test 7: Get all rooms
        response = requests.get(f"{BASE_URL}/api/rooms", headers=headers)
        print_response("Get All Rooms", response)
    
    print("\n" + "="*60)
    print("✅ API Testing Complete!")
    print("="*60)

if __name__ == '__main__':
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to server. Make sure Flask app is running on port 5000")
    except Exception as e:
        print(f"❌ Error: {e}")
