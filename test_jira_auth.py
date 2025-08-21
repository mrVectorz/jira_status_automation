#!/usr/bin/env python3
"""
Test script to compare different JIRA authentication methods
This script helps debug authentication issues by testing various approaches
"""

import requests
import base64
import json
import sys
from pathlib import Path

def test_python_jira_style(base_url, username, api_token):
    """Test authentication using python-jira library style"""
    print("🔍 Testing python-jira library style authentication...")
    
    try:
        # This mimics how python-jira typically does authentication
        from requests.auth import HTTPBasicAuth
        
        # Create session (like python-jira does)
        session = requests.Session()
        session.auth = HTTPBasicAuth(username, api_token)
        session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'python-jira/3.4.1 (requests/2.28.1)'
        })
        
        # Test with API v2 (python-jira default)
        response = session.get(f"{base_url}/rest/api/2/myself", timeout=10)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ SUCCESS - Connected as: {user_data.get('displayName', 'Unknown')}")
            print(f"Email: {user_data.get('emailAddress', 'Unknown')}")
            return True
        else:
            print(f"❌ FAILED - {response.status_code}: {response.text}")
            return False
            
    except ImportError:
        print("⚠️ requests library not available, testing manual approach...")
        return test_manual_basic_auth(base_url, username, api_token)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_manual_basic_auth(base_url, username, api_token):
    """Test manual basic authentication"""
    print("🔍 Testing manual basic authentication...")
    
    try:
        # Manual basic auth
        response = requests.get(
            f"{base_url}/rest/api/2/myself",
            auth=(username, api_token),
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ SUCCESS - Connected as: {user_data.get('displayName', 'Unknown')}")
            return True
        else:
            print(f"❌ FAILED - {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_authorization_header(base_url, username, api_token):
    """Test with Authorization header"""
    print("🔍 Testing Authorization header authentication...")
    
    try:
        # Encode credentials
        credentials = f"{username}:{api_token}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        response = requests.get(
            f"{base_url}/rest/api/2/myself",
            headers={
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ SUCCESS - Connected as: {user_data.get('displayName', 'Unknown')}")
            return True
        else:
            print(f"❌ FAILED - {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_with_python_jira_library(base_url, username, api_token):
    """Test with actual python-jira library if available"""
    print("🔍 Testing with actual python-jira library...")
    
    try:
        from jira import JIRA
        
        # Create JIRA connection
        jira = JIRA(
            server=base_url,
            basic_auth=(username, api_token),
            options={'verify': True}
        )
        
        # Test connection
        user = jira.myself()
        print(f"✅ SUCCESS with python-jira - Connected as: {user['displayName']}")
        print(f"Email: {user.get('emailAddress', 'Unknown')}")
        
        # Test search
        issues = jira.search_issues('assignee = currentUser()', maxResults=1)
        print(f"Found {len(issues)} issue(s) assigned to you")
        
        return True
        
    except ImportError:
        print("⚠️ python-jira library not installed")
        print("Install with: pip install jira")
        return False
    except Exception as e:
        print(f"❌ ERROR with python-jira: {e}")
        return False

def load_config():
    """Load configuration from config.json"""
    config_file = Path("config.json")
    if not config_file.exists():
        print("❌ config.json not found. Please run setup first.")
        return None
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return None

def main():
    """Main test function"""
    print("🧪 JIRA Authentication Test Suite")
    print("=" * 50)
    
    # Load configuration
    config = load_config()
    if not config:
        return 1
    
    jira_config = config.get('jira', {})
    base_url = jira_config.get('base_url')
    username = jira_config.get('username')
    api_token = jira_config.get('api_token')
    
    if not all([base_url, username, api_token]):
        print("❌ Incomplete JIRA configuration in config.json")
        return 1
    
    print(f"Base URL: {base_url}")
    print(f"Username: {username}")
    print(f"API Token: {'*' * len(api_token)}")
    print()
    
    # Test different methods
    methods = [
        ("Python-JIRA Library Style", test_python_jira_style),
        ("Manual Basic Auth", test_manual_basic_auth),
        ("Authorization Header", test_authorization_header),
        ("Actual Python-JIRA Library", test_with_python_jira_library),
    ]
    
    successful_methods = []
    
    for name, test_func in methods:
        print(f"\n{name}")
        print("-" * len(name))
        try:
            if test_func(base_url, username, api_token):
                successful_methods.append(name)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    if successful_methods:
        print("✅ Successful authentication methods:")
        for method in successful_methods:
            print(f"   - {method}")
    else:
        print("❌ No authentication methods worked")
        print("\n🔧 Troubleshooting tips:")
        print("1. Verify your JIRA base URL")
        print("2. Check your username (usually email address)")
        print("3. Verify your API token is correct and not expired")
        print("4. Ensure your account has API access permissions")
        print("5. Check if your JIRA instance has specific authentication requirements")
    
    return 0 if successful_methods else 1

if __name__ == '__main__':
    exit(main())
