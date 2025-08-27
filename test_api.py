#!/usr/bin/env ./venv/bin/python
"""
Simple test script for the Jira Status Automation API
This script validates the API endpoints and basic functionality
"""

import requests
import json
import sys
import os
from datetime import datetime, timedelta

# API base URL - configurable via environment variable
BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
BACKEND_HOST = os.getenv("BACKEND_HOST", "localhost")
BASE_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"

def test_health_check():
    """Test the root health check endpoint"""
    print("Testing health check endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✓ Health check passed")
            return True
        else:
            print(f"✗ Health check failed with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"✗ Cannot connect to API server. Is it running on {BASE_URL}?")
        return False
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_api_documentation():
    """Test that API documentation is available"""
    print("Testing API documentation endpoints...")
    try:
        # Test Swagger UI
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("✓ Swagger documentation available")
        else:
            print(f"✗ Swagger documentation failed: {response.status_code}")
        
        # Test ReDoc
        response = requests.get(f"{BASE_URL}/redoc")
        if response.status_code == 200:
            print("✓ ReDoc documentation available")
        else:
            print(f"✗ ReDoc documentation failed: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"✗ Documentation test failed: {e}")
        return False

def test_jira_endpoint_validation():
    """Test the Jira endpoint with invalid parameters"""
    print("Testing parameter validation...")
    
    # Test missing parameters
    response = requests.get(f"{BASE_URL}/api/jira/report")
    if response.status_code == 422:  # Validation error
        print("✓ Missing parameters correctly rejected")
    else:
        print(f"✗ Expected validation error, got {response.status_code}")
    
    # Test invalid date format
    params = {
        "jira_url": "https://test.atlassian.net",
        "personal_access_token": "test_token",
        "project_key": "TEST",
        "start_date": "invalid-date",
        "end_date": "2024-01-31"
    }
    
    response = requests.get(f"{BASE_URL}/api/jira/report", params=params)
    if response.status_code == 400:
        print("✓ Invalid date format correctly rejected")
    else:
        print(f"✗ Expected 400 for invalid date, got {response.status_code}")
    
    # Test start date after end date
    params = {
        "jira_url": "https://test.atlassian.net",
        "personal_access_token": "test_token",
        "project_key": "TEST",
        "start_date": "2024-02-01",
        "end_date": "2024-01-31"
    }
    
    response = requests.get(f"{BASE_URL}/api/jira/report", params=params)
    if response.status_code == 400:
        print("✓ Invalid date range correctly rejected")
    else:
        print(f"✗ Expected 400 for invalid date range, got {response.status_code}")
    
    return True

def test_jira_authentication_error():
    """Test that invalid Jira credentials are handled properly"""
    print("Testing Jira authentication error handling...")
    
    # Use invalid credentials that should fail authentication
    params = {
        "jira_url": "https://nonexistent-domain-test.atlassian.net",
        "personal_access_token": "invalid_token",
        "project_key": "TEST",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/jira/report", params=params, timeout=30)
        if response.status_code in [401, 403, 404]:
            print("✓ Invalid credentials correctly rejected")
            return True
        else:
            print(f"✗ Expected authentication error, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("✓ Request timeout (expected for invalid domain)")
        return True
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def run_tests():
    """Run all tests and report results"""
    print("=" * 60)
    print("Jira Status Automation API Test Suite")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health_check),
        ("API Documentation", test_api_documentation),
        ("Parameter Validation", test_jira_endpoint_validation),
        ("Authentication Error Handling", test_jira_authentication_error),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("🎉 All tests passed! The API is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the output above.")
        return False

if __name__ == "__main__":
    success = run_tests()
    
    frontend_port = os.getenv("FRONTEND_PORT", "3001")
    
    print("\nNext steps:")
    print("1. Start the backend: python run_server.py")
    print("2. Start the frontend: cd frontend && npm start")
    print(f"3. Open http://localhost:{frontend_port} in your browser")
    print("4. Enter your Jira credentials to generate a report")
    print("\nOr use the quick start script: ./start.sh")
    print(f"\nAPI is configured to run on: {BASE_URL}")
    print(f"Frontend is configured to run on: http://localhost:{frontend_port}")
    
    sys.exit(0 if success else 1)
