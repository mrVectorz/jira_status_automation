#!/usr/bin/env python3
"""
JIRA Status Update Automation Tool

This tool automates bi-weekly status updates by:
1. Fetching JIRA tasks from specified projects
2. Summarizing current status and recent updates
3. Generating formatted status reports
4. Supporting scheduled execution
"""

import os
import json
import requests
import base64
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional
import argparse
from pathlib import Path
import logging
from urllib.parse import urljoin, parse_qs, urlparse
import webbrowser
import hashlib
import hmac
import secrets
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import AI enhancer
try:
    from ai_enhancer import AIEnhancer, create_ai_enhanced_report, load_cursor_ai_response, integrate_cursor_ai_response
    AI_ENHANCER_AVAILABLE = True
except ImportError:
    AI_ENHANCER_AVAILABLE = False
    # Note: logger warning will be shown when AI features are requested

@dataclass
class JiraTask:
    """Represents a JIRA task with relevant information"""
    key: str
    summary: str
    status: str
    assignee: Optional[str]
    priority: str
    created: datetime
    updated: datetime
    project: str
    issue_type: str
    story_points: Optional[int] = None
    components: List[str] = None
    labels: List[str] = None
    description: str = ""

class JiraClient:
    """JIRA API client for fetching tasks and updates"""
    
    def __init__(self, base_url: str, username: str = None, api_token: str = None, oauth_config: Dict = None):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.oauth_config = oauth_config or {}
        
        # Authentication methods
        self.auth = None
        self.oauth_token = None
        self.oauth_token_secret = None
        
        # Set up authentication based on available credentials
        if oauth_config:
            self._setup_oauth()
        elif username and api_token:
            self._setup_basic_auth()
        else:
            raise ValueError("Either username/api_token or oauth_config must be provided")
        
        # Headers for API requests
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'JIRA-Status-Automation/1.0'
        }
        
        # Determine API version to use
        self.api_version = None
        self.api_endpoint = None
    
    def _setup_basic_auth(self):
        """Set up basic authentication"""
        self.auth = (self.username, self.api_token)
        
        # Prepare base64 encoded credentials (some JIRA instances prefer this)
        credentials = f"{self.username}:{self.api_token}"
        self.encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    def _setup_oauth(self):
        """Set up OAuth authentication"""
        required_fields = ['consumer_key', 'consumer_secret']
        if not all(field in self.oauth_config for field in required_fields):
            raise ValueError(f"OAuth config must contain: {required_fields}")
        
        self.consumer_key = self.oauth_config['consumer_key']
        self.consumer_secret = self.oauth_config['consumer_secret']
        self.oauth_token = self.oauth_config.get('access_token')
        self.oauth_token_secret = self.oauth_config.get('access_token_secret')
    
    def oauth_flow(self):
        """Complete OAuth authentication flow"""
        if not self.oauth_config:
            raise ValueError("OAuth configuration not provided")
        
        logger.info("Starting OAuth authentication flow...")
        
        try:
            # Step 1: Get request token
            request_token_url = f"{self.base_url}/plugins/servlet/oauth/request-token"
            
            # Generate OAuth 1.0a signature
            oauth_params = {
                'oauth_callback': 'oob',  # Out of band
                'oauth_consumer_key': self.consumer_key,
                'oauth_nonce': secrets.token_hex(16),
                'oauth_signature_method': 'RSA-SHA1',
                'oauth_timestamp': str(int(time.time())),
                'oauth_version': '1.0'
            }
            
            # For Red Hat JIRA, you'll need to configure OAuth application first
            logger.warning("⚠️  OAuth requires setup in JIRA admin panel first")
            logger.info("📋 To set up OAuth:")
            logger.info("   1. Go to JIRA Admin → Applications → Application links")
            logger.info("   2. Create a new Application Link")
            logger.info("   3. Get Consumer Key and Consumer Secret")
            logger.info("   4. Update your config with OAuth credentials")
            
            return False
            
        except Exception as e:
            logger.error(f"OAuth flow failed: {e}")
            return False
    
    def _test_token_auth(self) -> bool:
        """Test token authentication using python-jira library (like your working test.py)"""
        logger.info("Testing token authentication with python-jira library...")
        
        try:
            from jira import JIRA
            
            # Use the same method as your working test.py
            logger.info("Creating JIRA connection with token_auth...")
            jira = JIRA(server=self.base_url, token_auth=self.api_token)
            
            # Test the connection by getting current user details
            logger.info("Testing connection by getting user details...")
            myself = jira.myself()
            
            logger.info(f"✅ Token authentication successful!")
            logger.info(f"Connected as: {myself['displayName']} ({myself['emailAddress']})")
            
            # Store the working JIRA instance for future use
            self.jira_instance = jira
            self.successful_auth_method = 'token_auth'
            self.api_version = 2  # python-jira typically uses API v2
            self.api_endpoint = f"{self.base_url}/rest/api/2"
            
            return True
            
        except ImportError:
            logger.error("❌ python-jira library not installed")
            logger.info("💡 Install with: pip install jira")
            return False
        except Exception as e:
            logger.error(f"❌ Token authentication failed: {e}")
            return False
    
    def _test_oauth_connection(self) -> bool:
        """Test OAuth connection"""
        logger.info("Testing OAuth connection...")
        try:
            # This would require implementing full OAuth 1.0a signatures
            # For now, just indicate OAuth is configured but not implemented
            logger.warning("⚠️  OAuth connection testing not fully implemented yet")
            logger.info("💡 OAuth support requires additional setup - check your working test.py method")
            return False
        except Exception as e:
            logger.error(f"OAuth test failed: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test the JIRA connection with comprehensive diagnostics"""
        logger.info(f"Testing connection to: {self.base_url}")
        if self.username:
            logger.info(f"Username: {self.username}")
        if self.oauth_config:
            logger.info(f"OAuth Consumer Key: {self.oauth_config.get('consumer_key', 'Not set')}")
        
        # Check if this looks like Red Hat JIRA
        if 'redhat.com' in self.base_url:
            logger.warning("🔴 Red Hat JIRA detected - trying token_auth method")
            logger.info("💡 Using same method as your working test.py")
        
        # First try python-jira token_auth method (like your working test.py)
        if self.api_token and self._test_token_auth():
            return True
        
        # Try OAuth if configured
        if self.oauth_config and self.oauth_token:
            if self._test_oauth_connection():
                return True
        
        # If no OAuth or OAuth failed, try basic auth methods
        if not self.auth:
            logger.error("No valid authentication method available")
            return False
        
        # Test different authentication methods and API versions
        test_methods = [
            # Method 1: Basic auth with API v3
            {
                'name': 'Basic Auth + API v3',
                'url': f"{self.base_url}/rest/api/3/myself",
                'headers': self.headers.copy(),
                'auth_method': 'basic'
            },
            # Method 2: Basic auth with API v2
            {
                'name': 'Basic Auth + API v2',
                'url': f"{self.base_url}/rest/api/2/myself",
                'headers': self.headers.copy(),
                'auth_method': 'basic'
            },
            # Method 3: Authorization header with API v3
            {
                'name': 'Authorization Header + API v3',
                'url': f"{self.base_url}/rest/api/3/myself",
                'headers': {**self.headers, 'Authorization': f'Basic {self.encoded_credentials}'},
                'auth_method': 'header'
            },
            # Method 4: Authorization header with API v2
            {
                'name': 'Authorization Header + API v2',
                'url': f"{self.base_url}/rest/api/2/myself",
                'headers': {**self.headers, 'Authorization': f'Basic {self.encoded_credentials}'},
                'auth_method': 'header'
            }
        ]
        
        for method in test_methods:
            try:
                logger.info(f"Trying: {method['name']}")
                
                kwargs = {
                    'headers': method['headers'],
                    'timeout': 15,
                    'verify': True  # SSL verification
                }
                
                if method['auth_method'] == 'basic':
                    kwargs['auth'] = self.auth
                
                response = requests.get(method['url'], **kwargs)
                
                logger.info(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    logger.info(f"✅ Authentication successful with {method['name']}")
                    
                    # Store successful method for future use
                    if 'api/3' in method['url']:
                        self.api_version = 3
                        self.api_endpoint = f"{self.base_url}/rest/api/3"
                    else:
                        self.api_version = 2
                        self.api_endpoint = f"{self.base_url}/rest/api/2"
                    
                    self.successful_auth_method = method['auth_method']
                    if method['auth_method'] == 'header':
                        self.headers['Authorization'] = f'Basic {self.encoded_credentials}'
                    
                    # Get user info for confirmation
                    try:
                        user_data = response.json()
                        logger.info(f"Connected as: {user_data.get('displayName', 'Unknown')} ({user_data.get('emailAddress', 'No email')})")
                    except:
                        pass
                    
                    return True
                elif response.status_code == 401:
                    logger.warning(f"❌ Authentication failed (401 Unauthorized) with {method['name']}")
                    try:
                        error_data = response.json()
                        logger.warning(f"Error details: {error_data}")
                    except:
                        logger.warning(f"Response text: {response.text[:200]}")
                elif response.status_code == 403:
                    logger.warning(f"❌ Access forbidden (403) with {method['name']} - check permissions")
                elif response.status_code == 404:
                    logger.warning(f"❌ Endpoint not found (404) with {method['name']}")
                else:
                    logger.warning(f"❌ Unexpected status {response.status_code} with {method['name']}")
                    logger.warning(f"Response: {response.text[:200]}")
                    
            except requests.exceptions.ConnectTimeout:
                logger.error(f"❌ Connection timeout with {method['name']}")
            except requests.exceptions.SSLError as e:
                logger.error(f"❌ SSL error with {method['name']}: {e}")
                logger.info("💡 Try adding 'verify=False' if using self-signed certificates")
            except requests.exceptions.ConnectionError as e:
                logger.error(f"❌ Connection error with {method['name']}: {e}")
            except Exception as e:
                logger.error(f"❌ Unexpected error with {method['name']}: {e}")
        
        # Additional diagnostics
        logger.error("🔍 Connection test failed with all methods")
        
        if 'redhat.com' in self.base_url:
            logger.error("🔴 RED HAT JIRA SPECIFIC GUIDANCE:")
            logger.info("   ⚠️  Red Hat JIRA likely requires OAuth authentication (not API tokens)")
            logger.info("   🔍 Check what authentication method your working test.py uses:")
            logger.info("      • Does it use OAuth tokens?")
            logger.info("      • Does it use session-based authentication?")
            logger.info("      • Does it use different credentials?")
            logger.info("   📝 Run: grep -i 'oauth\\|session\\|auth' your_test.py")
            logger.info("   🌐 You may need VPN access to Red Hat internal JIRA")
        else:
            logger.info("🔧 Troubleshooting tips:")
            logger.info("   1. Verify your JIRA base URL (should be https://company.atlassian.net)")
            logger.info("   2. Check your username (usually your email address)")
            logger.info("   3. Verify your API token is correct and not expired")
            logger.info("   4. Ensure your account has appropriate permissions")
            logger.info("   5. Check if your JIRA instance requires specific authentication")
        
        return False
    
    def fetch_tasks(self, projects: List[str], days_back: int = 14) -> List[JiraTask]:
        """Fetch tasks from specified projects updated in the last N days"""
        tasks = []
        
        # Calculate date range for recent updates
        since_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # Use python-jira library if available (token_auth method)
        if hasattr(self, 'jira_instance') and self.jira_instance:
            return self._fetch_tasks_with_jira_library(projects, since_date)
        
        # Fallback to custom requests method
        for project in projects:
            logger.info(f"Fetching tasks from project: {project}")
            
            # JQL query to get tasks updated in the last N days
            jql = f'project = "{project}" AND updated >= "{since_date}" ORDER BY updated DESC'
            
            try:
                tasks.extend(self._execute_search(jql, project))
            except Exception as e:
                logger.error(f"Error fetching tasks from {project}: {e}")
                continue
                
        return tasks
    
    def _fetch_tasks_with_jira_library(self, projects: List[str], since_date: str) -> List[JiraTask]:
        """Fetch tasks using python-jira library (for token_auth)"""
        tasks = []
        
        for project in projects:
            logger.info(f"Fetching tasks from project: {project} using python-jira library")
            
            # JQL query to get tasks updated in the last N days
            jql = f'project = "{project}" AND updated >= "{since_date}" ORDER BY updated DESC'
            
            try:
                # Use python-jira library to search
                logger.debug(f"Executing JQL: {jql}")
                issues = self.jira_instance.search_issues(
                    jql_str=jql,
                    maxResults=1000,  # Adjust as needed
                    fields='key,summary,status,assignee,priority,created,updated,issuetype,project,description,components,labels,customfield_10016'
                )
                
                logger.info(f"Retrieved {len(issues)} issues from {project}")
                
                # Convert JIRA issues to our JiraTask objects
                for issue in issues:
                    task = self._parse_jira_library_issue(issue)
                    if task:
                        tasks.append(task)
                        
            except Exception as e:
                logger.error(f"Error fetching tasks from {project} using python-jira: {e}")
                continue
        
        logger.info(f"Total tasks retrieved: {len(tasks)}")
        return tasks
    
    def _parse_jira_library_issue(self, issue) -> Optional[JiraTask]:
        """Parse python-jira library issue into JiraTask object"""
        try:
            # Parse assignee
            assignee = None
            if hasattr(issue.fields, 'assignee') and issue.fields.assignee:
                assignee = issue.fields.assignee.displayName
            
            # Parse components
            components = []
            if hasattr(issue.fields, 'components'):
                components = [comp.name for comp in issue.fields.components]
            
            # Parse labels
            labels = []
            if hasattr(issue.fields, 'labels'):
                labels = issue.fields.labels
            
            # Parse story points (might be in different custom fields)
            story_points = None
            if hasattr(issue.fields, 'customfield_10016'):
                story_points = issue.fields.customfield_10016
            
            # Parse description
            description = ""
            if hasattr(issue.fields, 'description') and issue.fields.description:
                description = str(issue.fields.description)[:500]  # Limit length
            
            # Parse datetime strings - handle different formats
            def parse_datetime(dt_str):
                """Parse datetime string from JIRA API"""
                if hasattr(dt_str, 'strftime'):  # Already a datetime object
                    return dt_str.replace(tzinfo=None) if dt_str.tzinfo else dt_str
                
                # Handle string format
                dt_str = str(dt_str)
                if 'T' in dt_str:
                    if dt_str.endswith('Z'):
                        dt_str = dt_str.replace('Z', '+00:00')
                    elif '+' in dt_str[-6:] or '-' in dt_str[-6:]:
                        pass  # Already has timezone
                    else:
                        dt_str += '+00:00'  # Add UTC timezone
                    
                    return datetime.fromisoformat(dt_str).replace(tzinfo=None)
                return datetime.now()  # Fallback
            
            return JiraTask(
                key=issue.key,
                summary=issue.fields.summary,
                status=issue.fields.status.name,
                assignee=assignee,
                priority=issue.fields.priority.name,
                created=parse_datetime(issue.fields.created),
                updated=parse_datetime(issue.fields.updated),
                project=issue.fields.project.key,
                issue_type=issue.fields.issuetype.name,
                story_points=story_points,
                components=components,
                labels=labels,
                description=description
            )
        except Exception as e:
            logger.error(f"Error parsing issue {getattr(issue, 'key', 'unknown')}: {e}")
            return None
    
    def _execute_search(self, jql: str, project: str) -> List[JiraTask]:
        """Execute JQL search and return tasks"""
        if not self.api_endpoint:
            logger.error("No working API endpoint found. Please run test_connection() first.")
            return []
        
        tasks = []
        start_at = 0
        max_results = 50
        
        logger.debug(f"Executing JQL: {jql}")
        
        while True:
            params = {
                'jql': jql,
                'startAt': start_at,
                'maxResults': max_results,
                'fields': 'key,summary,status,assignee,priority,created,updated,issuetype,project,description,components,labels,customfield_10016'  # customfield_10016 is typically story points
            }
            
            # Build request arguments
            kwargs = {
                'headers': self.headers,
                'params': params,
                'timeout': 30
            }
            
            # Use the authentication method that worked during connection test
            if hasattr(self, 'successful_auth_method') and self.successful_auth_method == 'basic':
                kwargs['auth'] = self.auth
            # Authorization header is already in self.headers if needed
            
            try:
                response = requests.get(f"{self.api_endpoint}/search", **kwargs)
                
                logger.debug(f"Search API response: {response.status_code}")
                
                if response.status_code != 200:
                    logger.error(f"API request failed: {response.status_code}")
                    try:
                        error_data = response.json()
                        logger.error(f"Error details: {error_data}")
                        
                        # Handle specific error cases
                        if response.status_code == 400:
                            logger.error("Bad request - check your JQL syntax")
                        elif response.status_code == 401:
                            logger.error("Authentication failed - token may have expired")
                        elif response.status_code == 403:
                            logger.error("Access forbidden - check project permissions")
                        
                    except:
                        logger.error(f"Response text: {response.text}")
                    break
                
                data = response.json()
                issues = data.get('issues', [])
                total = data.get('total', 0)
                
                logger.debug(f"Retrieved {len(issues)} issues in this batch (total: {total})")
                
                for issue in issues:
                    task = self._parse_issue(issue)
                    if task:
                        tasks.append(task)
                
                # Check if we've retrieved all results
                if start_at + max_results >= total:
                    break
                
                start_at += max_results
                
            except requests.exceptions.Timeout:
                logger.error(f"Request timeout while fetching from {project}")
                break
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error while fetching from {project}: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error while fetching from {project}: {e}")
                break
        
        logger.info(f"Retrieved {len(tasks)} tasks from {project}")
        return tasks
    
    def _parse_issue(self, issue: dict) -> Optional[JiraTask]:
        """Parse JIRA issue JSON into JiraTask object"""
        try:
            fields = issue['fields']
            
            # Parse assignee
            assignee = None
            if fields.get('assignee'):
                assignee = fields['assignee'].get('displayName', 'Unknown')
            
            # Parse components
            components = [comp['name'] for comp in fields.get('components', [])]
            
            # Parse labels
            labels = fields.get('labels', [])
            
            # Parse story points (might be in different custom fields)
            story_points = fields.get('customfield_10016')  # Common story points field
            
            return JiraTask(
                key=issue['key'],
                summary=fields['summary'],
                status=fields['status']['name'],
                assignee=assignee,
                priority=fields['priority']['name'],
                created=datetime.fromisoformat(fields['created'].replace('Z', '+00:00')),
                updated=datetime.fromisoformat(fields['updated'].replace('Z', '+00:00')),
                project=fields['project']['key'],
                issue_type=fields['issuetype']['name'],
                story_points=story_points,
                components=components,
                labels=labels,
                description=fields.get('description', {}).get('content', [{}])[0].get('content', [{}])[0].get('text', '') if fields.get('description') else ''
            )
        except Exception as e:
            logger.error(f"Error parsing issue {issue.get('key', 'unknown')}: {e}")
            return None

class StatusSummarizer:
    """Analyzes and summarizes task statuses"""
    
    def __init__(self):
        self.status_groups = {
            'completed': ['Done', 'Closed', 'Resolved', 'Complete'],
            'in_progress': ['In Progress', 'In Development', 'In Review', 'Testing'],
            'blocked': ['Blocked', 'Waiting', 'On Hold'],
            'todo': ['To Do', 'Open', 'New', 'Backlog']
        }
    
    def summarize_tasks(self, tasks: List[JiraTask]) -> Dict:
        """Generate comprehensive summary of tasks"""
        if not tasks:
            return {"error": "No tasks found"}
        
        summary = {
            'total_tasks': len(tasks),
            'by_status': {},
            'by_project': {},
            'by_assignee': {},
            'by_priority': {},
            'recent_updates': [],
            'story_points': {'total': 0, 'completed': 0},
            'timeline': {
                'this_week': [],
                'last_week': []
            }
        }
        
        # Calculate time boundaries
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)
        
        for task in tasks:
            # Status summary
            status_group = self._categorize_status(task.status)
            summary['by_status'][status_group] = summary['by_status'].get(status_group, 0) + 1
            
            # Project summary
            summary['by_project'][task.project] = summary['by_project'].get(task.project, 0) + 1
            
            # Assignee summary
            assignee = task.assignee or 'Unassigned'
            summary['by_assignee'][assignee] = summary['by_assignee'].get(assignee, 0) + 1
            
            # Priority summary
            summary['by_priority'][task.priority] = summary['by_priority'].get(task.priority, 0) + 1
            
            # Story points
            if task.story_points:
                summary['story_points']['total'] += task.story_points
                if status_group == 'completed':
                    summary['story_points']['completed'] += task.story_points
            
            # Recent updates timeline
            if task.updated >= week_ago:
                summary['timeline']['this_week'].append(task)
            elif task.updated >= two_weeks_ago:
                summary['timeline']['last_week'].append(task)
        
        # Sort recent updates by date
        summary['timeline']['this_week'].sort(key=lambda x: x.updated, reverse=True)
        summary['timeline']['last_week'].sort(key=lambda x: x.updated, reverse=True)
        
        return summary
    
    def _categorize_status(self, status: str) -> str:
        """Categorize status into high-level groups"""
        for group, statuses in self.status_groups.items():
            if status in statuses:
                return group
        return 'other'

class DocumentGenerator:
    """Generates formatted status update documents"""
    
    def __init__(self, output_dir: str = "./reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_markdown_report(self, summary: Dict, tasks: List[JiraTask]) -> str:
        """Generate a markdown status report"""
        report_date = datetime.now().strftime("%Y-%m-%d")
        filename = f"status_update_{report_date}.md"
        filepath = self.output_dir / filename
        
        content = self._build_markdown_content(summary, tasks, report_date)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Generated report: {filepath}")
        return str(filepath)
    
    def _build_markdown_content(self, summary: Dict, tasks: List[JiraTask], report_date: str) -> str:
        """Build the markdown content for the report"""
        content = f"""# Bi-Weekly Status Update - {report_date}

## 📊 Executive Summary

- **Total Tasks Reviewed:** {summary['total_tasks']}
- **Story Points Progress:** {summary['story_points']['completed']}/{summary['story_points']['total']} completed
- **Active Projects:** {len(summary['by_project'])}

## 🎯 Status Breakdown

"""
        
        # Status breakdown
        for status, count in summary['by_status'].items():
            percentage = (count / summary['total_tasks'] * 100) if summary['total_tasks'] > 0 else 0
            emoji = self._get_status_emoji(status)
            content += f"- {emoji} **{status.title()}:** {count} tasks ({percentage:.1f}%)\n"
        
        content += "\n## 📈 Project Breakdown\n\n"
        
        # Project breakdown
        for project, count in sorted(summary['by_project'].items()):
            content += f"- **{project}:** {count} tasks\n"
        
        content += "\n## 👥 Team Activity\n\n"
        
        # Assignee breakdown
        for assignee, count in sorted(summary['by_assignee'].items(), key=lambda x: x[1], reverse=True):
            content += f"- **{assignee}:** {count} tasks\n"
        
        content += "\n## 🔥 This Week's Highlights\n\n"
        
        # This week's updates
        if summary['timeline']['this_week']:
            for task in summary['timeline']['this_week'][:10]:  # Top 10 recent updates
                content += f"- **[{task.key}]** {task.summary}\n"
                content += f"  - Status: {task.status}\n"
                content += f"  - Assignee: {task.assignee or 'Unassigned'}\n"
                content += f"  - Updated: {task.updated.strftime('%Y-%m-%d %H:%M')}\n\n"
        else:
            content += "No significant updates this week.\n\n"
        
        content += "## 📋 Previous Week's Activity\n\n"
        
        # Last week's updates
        if summary['timeline']['last_week']:
            for task in summary['timeline']['last_week'][:5]:  # Top 5 from last week
                content += f"- **[{task.key}]** {task.summary} - {task.status}\n"
        else:
            content += "No significant updates from previous week.\n\n"
        
        content += f"\n---\n*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return content
    
    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for status"""
        emoji_map = {
            'completed': '✅',
            'in_progress': '🚧',
            'blocked': '🚫',
            'todo': '📝',
            'other': '❓'
        }
        return emoji_map.get(status, '❓')

class ConfigManager:
    """Manages configuration for the automation tool"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from file or create default"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            # Create default config
            default_config = {
                "jira": {
                    "base_url": "https://your-domain.atlassian.net",
                    "username": "your-email@company.com",
                    "api_token": "your-api-token"
                },
                "projects": ["PROJ1", "PROJ2"],
                "days_back": 14,
                "output_dir": "./reports",
                "schedule": {
                    "enabled": False,
                    "day_of_week": 1,  # Monday
                    "hour": 9
                }
            }
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: Dict):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        self.config = config
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            value = value.get(k, default)
            if value is None:
                return default
        return value

def main():
    """Main function to run the status update automation"""
    parser = argparse.ArgumentParser(description='JIRA Status Update Automation')
    parser.add_argument('--config', default='config.json', help='Config file path')
    parser.add_argument('--projects', nargs='+', help='JIRA projects to include')
    parser.add_argument('--days', type=int, default=14, help='Days back to look for updates')
    parser.add_argument('--output', default='./reports', help='Output directory for reports')
    parser.add_argument('--test-connection', action='store_true', help='Test JIRA connection only')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--force-api', choices=['2', '3'], help='Force specific JIRA API version')
    parser.add_argument('--ai-enhance', action='store_true', help='Enable AI-powered insights and summaries')
    parser.add_argument('--cursor-only', action='store_true', help='Generate Cursor AI data only (no Gemini automation)')
    parser.add_argument('--gemini-selenium', action='store_true', help='Use Selenium automation for Gemini insights')
    parser.add_argument('--process-cursor-response', action='store_true', help='Process existing Cursor AI response files and regenerate enhanced report')
    parser.add_argument('--cursor-response-file', help='Specify a specific Cursor AI response file to process')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Load configuration
    config_manager = ConfigManager(args.config)
    
    # Override config with command line args
    projects = args.projects or config_manager.get('projects', [])
    days_back = args.days
    output_dir = args.output
    
    if not projects:
        logger.error("No projects specified. Please configure projects in config.json or use --projects")
        return 1
    
    # Initialize JIRA client
    jira_config = config_manager.get('jira', {})
    if not all(jira_config.get(k) for k in ['base_url', 'username', 'api_token']):
        logger.error("JIRA configuration incomplete. Please update config.json with your JIRA details.")
        return 1
    
    jira_client = JiraClient(
        base_url=jira_config['base_url'],
        username=jira_config['username'],
        api_token=jira_config['api_token']
    )
    
    # Force specific API version if requested
    if args.force_api:
        logger.info(f"Forcing JIRA API version {args.force_api}")
        jira_client.api_version = int(args.force_api)
        jira_client.api_endpoint = f"{jira_client.base_url}/rest/api/{args.force_api}"
        jira_client.successful_auth_method = 'basic'  # Default to basic auth
    
    # Always test connection first to determine working method
    logger.info("Testing JIRA connection...")
    if not jira_client.test_connection():
        logger.error("❌ JIRA connection failed!")
        logger.error("Please check your configuration and network connectivity")
        return 1
    
    # Test connection if that's all that was requested
    if args.test_connection:
        logger.info("✅ JIRA connection test completed successfully!")
        return 0
    
    # Handle Cursor AI response processing if requested
    if args.process_cursor_response or args.cursor_response_file:
        if not AI_ENHANCER_AVAILABLE:
            logger.error("❌ AI enhancement not available for response processing")
            return 1
        
        logger.info("🤖 Processing Cursor AI response...")
        
        # Load cursor AI response
        if args.cursor_response_file:
            # Process specific file
            response_file = Path(args.cursor_response_file)
            if not response_file.exists():
                logger.error(f"❌ Cursor response file not found: {response_file}")
                return 1
            
            logger.info(f"📖 Loading specific Cursor AI response: {response_file}")
            try:
                with open(response_file, 'r', encoding='utf-8') as f:
                    cursor_response = f.read()
                
                cursor_insights = integrate_cursor_ai_response(cursor_response, output_dir)
            except Exception as e:
                logger.error(f"Error processing cursor response file: {e}")
                return 1
        else:
            # Process latest response file
            cursor_insights = load_cursor_ai_response(output_dir)
            if not cursor_insights:
                logger.warning("⚠️ No Cursor AI response files found in ./reports/cursor_ai/")
                logger.info("💡 Save your Cursor AI response as 'cursor_response_YYYYMMDD_HHMMSS.md'")
                return 0
        
        # We need task data to generate a report, so let's fetch it
        logger.info(f"Fetching tasks for enhanced report generation...")
        tasks = jira_client.fetch_tasks(projects, days_back)
        
        if not tasks:
            logger.warning("No tasks found - cannot generate enhanced report")
            return 0
        
        # Summarize tasks
        summarizer = StatusSummarizer()
        summary = summarizer.summarize_tasks(tasks)
        
        # Generate AI-enhanced report with cursor insights
        ai_report_path = create_ai_enhanced_report(tasks, summary, cursor_insights, output_dir)
        logger.info(f"✅ AI-enhanced report with Cursor insights saved to: {ai_report_path}")
        return 0
    
    try:
        # Fetch tasks
        logger.info(f"Fetching tasks from projects: {projects}")
        tasks = jira_client.fetch_tasks(projects, days_back)
        
        if not tasks:
            logger.warning("No tasks found for the specified criteria")
            return 0
        
        # Summarize tasks
        logger.info("Analyzing and summarizing tasks...")
        summarizer = StatusSummarizer()
        summary = summarizer.summarize_tasks(tasks)
        
        # Generate report
        logger.info("Generating status report...")
        doc_generator = DocumentGenerator(output_dir)
        report_path = doc_generator.generate_markdown_report(summary, tasks)
        
        # AI Enhancement
        ai_insights = {}
        if args.ai_enhance or args.cursor_only or args.gemini_selenium:
            if not AI_ENHANCER_AVAILABLE:
                logger.error("❌ AI enhancement requested but not available")
                logger.info("💡 Install selenium: pip install selenium webdriver-manager")
                return 1
            
            # Configure AI enhancer
            ai_config = {
                'ai_enhancement': {
                    'enabled': True,
                    'cursor_integration': True,
                    'gemini_selenium': args.gemini_selenium
                }
            }
            
            # Override if cursor-only is specified
            if args.cursor_only:
                ai_config['ai_enhancement']['gemini_selenium'] = False
            
            ai_enhancer = AIEnhancer(ai_config)
            ai_insights = ai_enhancer.enhance_report(tasks, summary, output_dir)
            
            # Check for existing Cursor AI response and integrate it
            cursor_insights = load_cursor_ai_response(output_dir)
            if cursor_insights:
                logger.info("✅ Found and integrated Cursor AI response!")
                # Merge cursor insights with existing ai_insights
                if ai_insights:
                    # Update with cursor insights - cursor takes precedence
                    ai_insights.update(cursor_insights)
                else:
                    ai_insights = cursor_insights
            
            # Generate AI-enhanced report if we have insights
            if ai_insights and not args.cursor_only:
                ai_report_path = create_ai_enhanced_report(tasks, summary, ai_insights, output_dir)
                logger.info(f"🤖 AI-enhanced report saved to: {ai_report_path}")
            elif ai_insights and args.cursor_only:
                # Even with cursor_only, generate enhanced report if we have cursor insights
                ai_report_path = create_ai_enhanced_report(tasks, summary, ai_insights, output_dir)
                logger.info(f"🤖 AI-enhanced report with Cursor insights saved to: {ai_report_path}")
        
        logger.info(f"✅ Status update completed! Report saved to: {report_path}")
        
        if ai_insights and args.cursor_only:
            logger.info("📋 Cursor AI integration files created - check ./reports/cursor_ai/")
            logger.info("💡 Open the prompt file in Cursor IDE and send to Cursor AI for analysis")
        elif args.cursor_only:
            logger.info("📋 Cursor AI integration files created - check ./reports/cursor_ai/")
            logger.info("💡 To auto-integrate your Cursor AI response:")
            logger.info("   1. Send the prompt to Cursor AI")
            logger.info("   2. Save the response as 'cursor_response_YYYYMMDD_HHMMSS.md' in ./reports/cursor_ai/")
            logger.info("   3. Re-run the tool - it will automatically integrate the response!")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during execution: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
