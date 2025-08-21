#!/usr/bin/env python3
"""
Debug script to capture and compare HTTP requests
This helps identify differences between working and non-working JIRA requests
"""

import requests
import json
import base64
from pathlib import Path
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

class RequestCapture:
    """Capture details about HTTP requests for comparison"""
    
    def __init__(self):
        self.requests_log = []
    
    def log_request(self, name, method, url, headers, auth_info, response):
        """Log request details"""
        log_entry = {
            'name': name,
            'method': method,
            'url': url,
            'headers': dict(headers),
            'auth_info': auth_info,
            'status_code': response.status_code,
            'response_headers': dict(response.headers),
            'response_size': len(response.content) if response.content else 0
        }
        
        # Try to get response body if it's JSON
        try:
            if response.headers.get('content-type', '').startswith('application/json'):
                log_entry['response_json'] = response.json()
        except:
            log_entry['response_text'] = response.text[:500]
        
        self.requests_log.append(log_entry)
        return log_entry
    
    def print_comparison(self):
        """Print detailed comparison of requests"""
        print("🔍 REQUEST COMPARISON")
        print("=" * 60)
        
        for i, entry in enumerate(self.requests_log, 1):
            print(f"\n{i}. {entry['name']}")
            print("-" * 40)
            print(f"URL: {entry['url']}")
            print(f"Status: {entry['status_code']}")
            print(f"Response Size: {entry['response_size']} bytes")
            
            print(f"\nRequest Headers:")
            for key, value in entry['headers'].items():
                if 'authorization' in key.lower():
                    print(f"  {key}: [REDACTED]")
                else:
                    print(f"  {key}: {value}")
            
            print(f"\nAuth Info: {entry['auth_info']}")
            
            if entry['status_code'] != 200:
                print(f"\nError Response:")
                if 'response_json' in entry:
                    print(f"  JSON: {json.dumps(entry['response_json'], indent=2)}")
                elif 'response_text' in entry:
                    print(f"  Text: {entry['response_text']}")

def load_config():
    """Load JIRA configuration"""
    config_file = Path("config.json")
    if not config_file.exists():
        print("❌ config.json not found")
        return None
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    return config.get('jira', {})

def test_python_jira_style(config, capture):
    """Test using python-jira library style with detailed logging"""
    print("🧪 Testing Python-JIRA Library Style...")
    
    try:
        from jira import JIRA
        
        # Create JIRA instance with detailed logging
        options = {
            'server': config['base_url'],
            'verify': True,
            'headers': {
                'User-Agent': 'python-jira/3.4.1 (requests/2.28.1)',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        }
        
        # Enable request logging
        import logging
        import http.client
        http.client.HTTPConnection.debuglevel = 1
        logging.basicConfig(level=logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True
        
        jira = JIRA(
            basic_auth=(config['username'], config['api_token']),
            options=options
        )
        
        # Test myself endpoint
        user = jira.myself()
        print(f"✅ SUCCESS: {user['displayName']}")
        return True
        
    except ImportError:
        print("⚠️ python-jira not installed, trying manual approach...")
        return test_manual_session_style(config, capture)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_manual_session_style(config, capture):
    """Test manual session-based approach like python-jira"""
    print("🧪 Testing Manual Session Style...")
    
    # Create session like python-jira does
    session = requests.Session()
    
    # Set up retries
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Set authentication
    session.auth = (config['username'], config['api_token'])
    
    # Set headers like python-jira
    session.headers.update({
        'User-Agent': 'python-jira/3.4.1 (requests/2.28.1)',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache'
    })
    
    try:
        # Test API v2 first (python-jira default)
        response = session.get(f"{config['base_url']}/rest/api/2/myself", timeout=30)
        
        entry = capture.log_request(
            "Python-JIRA Session Style",
            "GET",
            f"{config['base_url']}/rest/api/2/myself",
            session.headers,
            "Session basic auth",
            response
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ SUCCESS: {user_data.get('displayName', 'Unknown')}")
            return True
        else:
            print(f"❌ FAILED: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_our_current_method(config, capture):
    """Test our current authentication method"""
    print("🧪 Testing Our Current Method...")
    
    # Replicate our current approach
    auth = (config['username'], config['api_token'])
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'JIRA-Status-Automation/1.0'
    }
    
    try:
        response = requests.get(
            f"{config['base_url']}/rest/api/2/myself",
            auth=auth,
            headers=headers,
            timeout=30
        )
        
        entry = capture.log_request(
            "Our Current Method",
            "GET",
            f"{config['base_url']}/rest/api/2/myself",
            headers,
            "Basic auth tuple",
            response
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ SUCCESS: {user_data.get('displayName', 'Unknown')}")
            return True
        else:
            print(f"❌ FAILED: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_redhat_specific_headers(config, capture):
    """Test with Red Hat specific headers that might be required"""
    print("🧪 Testing Red Hat Specific Headers...")
    
    # Red Hat might require specific headers
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'X-Atlassian-Token': 'no-check',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    auth = (config['username'], config['api_token'])
    
    try:
        response = requests.get(
            f"{config['base_url']}/rest/api/2/myself",
            auth=auth,
            headers=headers,
            timeout=30
        )
        
        entry = capture.log_request(
            "Red Hat Specific Headers",
            "GET",
            f"{config['base_url']}/rest/api/2/myself",
            headers,
            "Basic auth with RH headers",
            response
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ SUCCESS: {user_data.get('displayName', 'Unknown')}")
            return True
        else:
            print(f"❌ FAILED: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Main debugging function"""
    print("🔍 JIRA Request Debugging Tool")
    print("=" * 50)
    
    config = load_config()
    if not config:
        return 1
    
    print(f"Target: {config['base_url']}")
    print(f"Username: {config['username']}")
    print()
    
    capture = RequestCapture()
    
    # Test different approaches
    methods = [
        ("Python-JIRA Library", test_python_jira_style),
        ("Manual Session Style", test_manual_session_style),
        ("Our Current Method", test_our_current_method),
        ("Red Hat Specific", test_redhat_specific_headers)
    ]
    
    successful_methods = []
    
    for name, test_func in methods:
        print(f"\n{name}")
        print("-" * len(name))
        try:
            if test_func(config, capture):
                successful_methods.append(name)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    # Print detailed comparison
    print("\n")
    capture.print_comparison()
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")
    
    if successful_methods:
        print("✅ Successful methods:")
        for method in successful_methods:
            print(f"   - {method}")
        
        print(f"\n💡 Use the working method's headers/approach in the main tool")
    else:
        print("❌ No methods worked")
        print("\n🔧 Red Hat JIRA might require:")
        print("   1. VPN connection")
        print("   2. Specific IP allowlist")
        print("   3. Session-based authentication")
        print("   4. Account with API access permissions")
        print("   5. Two-factor authentication handling")
    
    return 0 if successful_methods else 1

if __name__ == '__main__':
    exit(main())
