#!/usr/bin/env python3
"""
Test script to try bypassing CAPTCHA challenges
"""

import requests
import json
import time
from pathlib import Path

def load_config():
    """Load JIRA configuration"""
    config_file = Path("config.json")
    with open(config_file, 'r') as f:
        config = json.load(f)
    return config.get('jira', {})

def test_session_approach(config):
    """Try session-based authentication"""
    print("🧪 Testing Session-Based Approach...")
    
    session = requests.Session()
    
    # First, try to get login page to establish session
    try:
        login_response = session.get(f"{config['base_url']}/login.jsp", timeout=30)
        print(f"Login page status: {login_response.status_code}")
        
        # Try to find if there's an alternative endpoint
        # Some JIRA instances have /rest/auth/1/session for login
        auth_data = {
            'username': config['username'],
            'password': config['api_token']
        }
        
        session_response = session.post(
            f"{config['base_url']}/rest/auth/1/session",
            json=auth_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Session auth status: {session_response.status_code}")
        if session_response.status_code == 200:
            # Now try API call with session
            api_response = session.get(f"{config['base_url']}/rest/api/2/myself")
            print(f"API call status: {api_response.status_code}")
            if api_response.status_code == 200:
                print("✅ Session approach worked!")
                return True
                
    except Exception as e:
        print(f"❌ Session approach failed: {e}")
    
    return False

def test_different_endpoints(config):
    """Try different API endpoints that might not require CAPTCHA"""
    print("🧪 Testing Different Endpoints...")
    
    endpoints_to_try = [
        "/rest/api/2/serverInfo",  # Server info (sometimes less restricted)
        "/rest/api/2/configuration",  # Configuration
        "/rest/api/2/myself",  # Current user
        "/rest/api/3/myself",  # API v3
        "/rest/auth/1/session",  # Session endpoint
    ]
    
    session = requests.Session()
    session.auth = (config['username'], config['api_token'])
    session.headers.update({
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'curl/7.68.0'  # Try mimicking curl
    })
    
    for endpoint in endpoints_to_try:
        try:
            response = session.get(f"{config['base_url']}{endpoint}", timeout=30)
            print(f"  {endpoint}: {response.status_code}")
            
            if response.status_code == 200:
                print(f"    ✅ Success! Try using this endpoint")
                return True
            elif response.status_code != 403:
                print(f"    ⚠️ Different response than 403")
                
        except Exception as e:
            print(f"  {endpoint}: Error - {e}")
    
    return False

def test_oauth_discovery(config):
    """Try to discover OAuth endpoints"""
    print("🧪 Testing OAuth Discovery...")
    
    oauth_endpoints = [
        "/.well-known/oauth_authorization_server",
        "/plugins/servlet/oauth/authorize",
        "/rest/oauth/request-token",
    ]
    
    for endpoint in oauth_endpoints:
        try:
            response = requests.get(f"{config['base_url']}{endpoint}", timeout=10)
            print(f"  {endpoint}: {response.status_code}")
            if response.status_code == 200:
                print(f"    ✅ OAuth endpoint found: {endpoint}")
        except Exception as e:
            print(f"  {endpoint}: {e}")

def main():
    """Main testing function"""
    print("🔍 CAPTCHA Bypass Testing")
    print("=" * 50)
    
    config = load_config()
    if not config:
        print("❌ No config found")
        return 1
    
    print(f"Target: {config['base_url']}")
    print(f"Username: {config['username']}")
    print()
    
    # Try different approaches
    approaches = [
        ("Session-Based Authentication", test_session_approach),
        ("Different API Endpoints", test_different_endpoints),
        ("OAuth Discovery", test_oauth_discovery),
    ]
    
    for name, test_func in approaches:
        print(f"\n{name}")
        print("-" * len(name))
        try:
            if test_func(config):
                print(f"✅ {name} might work!")
                break
        except Exception as e:
            print(f"❌ {name} failed: {e}")
    
    print(f"\n{'='*50}")
    print("💡 RECOMMENDATIONS")
    print(f"{'='*50}")
    print("1. Check what authentication method your working test.py uses")
    print("2. Red Hat JIRA likely requires OAuth or session-based auth")
    print("3. You might need to authenticate through a web browser first")
    print("4. Consider using VPN if you're accessing from outside Red Hat network")
    print("5. Check if your working script uses different endpoints")

if __name__ == '__main__':
    exit(main())
