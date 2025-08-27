"""
FastAPI backend for Jira Status Automation
Provides REST API endpoints for retrieving Jira issue reports
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dateutil.parser import parse as parse_date
import logging
import traceback
from jira import JIRA
from jira.exceptions import JIRAError
import json
from config import Config

# Configure logging
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=Config.API_TITLE,
    description=Config.API_DESCRIPTION,
    version=Config.API_VERSION
)

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config().CORS_ORIGINS,  # Configurable frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def validate_date_format(date_string: str) -> datetime:
    """
    Validate and parse date string in YYYY-MM-DD format
    
    Args:
        date_string: Date string to validate
        
    Returns:
        Parsed datetime object
        
    Raises:
        ValueError: If date format is invalid
    """
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_string}. Expected YYYY-MM-DD format.")


def create_jira_client(jira_url: str, personal_access_token: str) -> JIRA:
    """
    Create authenticated Jira client using personal access token
    
    Args:
        jira_url: Base URL of the Jira instance
        personal_access_token: Personal access token for authentication
        
    Returns:
        Authenticated JIRA client instance
        
    Raises:
        JIRAError: If authentication fails or connection cannot be established
    """
    try:
        # Ensure URL has proper format
        if not jira_url.startswith(('http://', 'https://')):
            jira_url = f"https://{jira_url}"
        
        # Create Jira client with token-based authentication
        # Personal Access Token authentication uses the token as both username and password
        jira_client = JIRA(
            server=jira_url,
            token_auth=personal_access_token,
            options={
                'check_update': False,  # Skip version check for faster initialization
                'agile_rest_path': 'agile'
            }
        )
        
        # Test the connection by getting server info
        server_info = jira_client.server_info()
        logger.info(f"Successfully connected to Jira server: {server_info.get('serverTitle', 'Unknown')}")
        
        return jira_client
        
    except JIRAError as e:
        logger.error(f"Jira authentication/connection failed: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=f"Failed to authenticate with Jira: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating Jira client: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to Jira: {str(e)}"
        )


def build_jql_query(project_key: str, start_date: str, end_date: str) -> str:
    """
    Build JQL (Jira Query Language) query to find issues updated within date range
    
    JQL Query Components:
    - project = "{project_key}": Filter by specific project
    - updated >= "{start_date}": Include issues updated on or after start date
    - updated <= "{end_date} 23:59": Include issues updated before end of end date
    - ORDER BY updated DESC: Sort by most recently updated first
    
    Args:
        project_key: Jira project key (e.g., "PROJ", "DEV")
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        JQL query string
    """
    # Build comprehensive JQL query to find all issue types in the project
    # that have been updated within the specified date range
    jql_query = (
        f'project = "{project_key}" '
        f'AND updated >= "{start_date}" '
        f'AND updated <= "{end_date} 23:59" '
        f'ORDER BY updated DESC'
    )
    
    logger.info(f"Built JQL query: {jql_query}")
    return jql_query


def safe_get_attr(obj, attr_path, default=None):
    """Safely get nested attributes with fallback"""
    try:
        attrs = attr_path.split('.')
        current = obj
        for attr in attrs:
            if hasattr(current, attr):
                current = getattr(current, attr)
            else:
                return default
        return current
    except (AttributeError, TypeError):
        return default


def extract_issue_details(issue, jira_client: JIRA) -> Dict[str, Any]:
    """
    Extract comprehensive details from a Jira issue
    
    This function retrieves all available information about an issue including:
    - Basic issue information (key, summary, type, status, etc.)
    - All comments with full content
    - Complete changelog history
    - Custom fields and labels
    - Time tracking information
    
    Args:
        issue: Jira issue object
        jira_client: Authenticated Jira client for additional API calls
        
    Returns:
        Dictionary containing all issue details
    """
    try:
        logger.debug(f"Extracting details for issue {issue.key}")
        # Extract basic issue information with safe field access
        issue_data = {
            "key": safe_get_attr(issue, 'key', 'Unknown'),
            "id": safe_get_attr(issue, 'id', None),
            "summary": safe_get_attr(issue, 'fields.summary', 'No summary available'),
            "description": safe_get_attr(issue, 'fields.description', None),
            "issue_type": {
                "name": safe_get_attr(issue, 'fields.issuetype.name', 'Unknown'),
                "id": safe_get_attr(issue, 'fields.issuetype.id', None),
                "icon_url": safe_get_attr(issue, 'fields.issuetype.iconUrl', None)
            },
            "status": {
                "name": safe_get_attr(issue, 'fields.status.name', 'Unknown'),
                "id": safe_get_attr(issue, 'fields.status.id', None),
                "category": safe_get_attr(issue, 'fields.status.statusCategory.name', None)
            },
            "priority": {
                "name": safe_get_attr(issue, 'fields.priority.name', None),
                "id": safe_get_attr(issue, 'fields.priority.id', None)
            } if safe_get_attr(issue, 'fields.priority', None) else None,
            "reporter": {
                "display_name": safe_get_attr(issue, 'fields.reporter.displayName', None),
                "email": safe_get_attr(issue, 'fields.reporter.emailAddress', None),
                "account_id": safe_get_attr(issue, 'fields.reporter.accountId', None)
            } if safe_get_attr(issue, 'fields.reporter', None) else None,
            "assignee": {
                "display_name": safe_get_attr(issue, 'fields.assignee.displayName', None),
                "email": safe_get_attr(issue, 'fields.assignee.emailAddress', None),
                "account_id": safe_get_attr(issue, 'fields.assignee.accountId', None)
            } if safe_get_attr(issue, 'fields.assignee', None) else None,
            "created": safe_get_attr(issue, 'fields.created', None),
            "updated": safe_get_attr(issue, 'fields.updated', None),
            "resolved": safe_get_attr(issue, 'fields.resolutiondate', None),
            "resolution": {
                "name": safe_get_attr(issue, 'fields.resolution.name', None),
                "description": safe_get_attr(issue, 'fields.resolution.description', None)
            } if safe_get_attr(issue, 'fields.resolution', None) else None,
            "labels": safe_get_attr(issue, 'fields.labels', []),
            "components": [
                {"name": safe_get_attr(comp, 'name', 'Unknown'), "id": safe_get_attr(comp, 'id', None)} 
                for comp in safe_get_attr(issue, 'fields.components', [])
            ],
            "fix_versions": [
                {"name": safe_get_attr(version, 'name', 'Unknown'), "id": safe_get_attr(version, 'id', None), "released": safe_get_attr(version, 'released', None)}
                for version in safe_get_attr(issue, 'fields.fixVersions', [])
            ]
        }
        
        # Add time tracking information if available
        if hasattr(issue.fields, 'timetracking') and issue.fields.timetracking:
            issue_data["time_tracking"] = {
                "original_estimate": getattr(issue.fields.timetracking, 'originalEstimate', None),
                "remaining_estimate": getattr(issue.fields.timetracking, 'remainingEstimate', None),
                "time_spent": getattr(issue.fields.timetracking, 'timeSpent', None),
                "original_estimate_seconds": getattr(issue.fields.timetracking, 'originalEstimateSeconds', None),
                "remaining_estimate_seconds": getattr(issue.fields.timetracking, 'remainingEstimateSeconds', None),
                "time_spent_seconds": getattr(issue.fields.timetracking, 'timeSpentSeconds', None)
            }
        
        # Retrieve all comments with full content
        # Comments are paginated, so we need to fetch all of them
        try:
            comments = jira_client.comments(issue)
            issue_data["comments"] = []
            
            for comment in comments:
                comment_data = {
                    "id": comment.id,
                    "author": {
                        "display_name": getattr(comment.author, 'displayName', None),
                        "email": getattr(comment.author, 'emailAddress', None),
                        "account_id": getattr(comment.author, 'accountId', None)
                    } if comment.author else None,
                    "body": comment.body,  # Full, non-truncated comment content
                    "created": comment.created,
                    "updated": comment.updated,
                    "update_author": {
                        "display_name": getattr(comment.updateAuthor, 'displayName', None),
                        "email": getattr(comment.updateAuthor, 'emailAddress', None),
                        "account_id": getattr(comment.updateAuthor, 'accountId', None)
                    } if comment.updateAuthor else None
                }
                issue_data["comments"].append(comment_data)
                
            logger.info(f"Retrieved {len(issue_data['comments'])} comments for issue {issue.key}")
            
        except Exception as e:
            logger.warning(f"Failed to retrieve comments for issue {issue.key}: {str(e)}")
            issue_data["comments"] = []
        
        # Retrieve complete changelog to track all status changes and field updates
        try:
            issue_with_changelog = jira_client.issue(issue.key, expand='changelog')
            changelog = issue_with_changelog.changelog
            
            issue_data["changelog"] = []
            
            for history in changelog.histories:
                history_entry = {
                    "id": history.id,
                    "author": {
                        "display_name": getattr(history.author, 'displayName', None),
                        "email": getattr(history.author, 'emailAddress', None),
                        "account_id": getattr(history.author, 'accountId', None)
                    } if history.author else None,
                    "created": history.created,
                    "items": []
                }
                
                # Process each change item in the history entry
                for item in history.items:
                    change_item = {
                        "field": item.field,
                        "field_type": getattr(item, 'fieldtype', None),
                        "field_id": getattr(item, 'fieldId', None),
                        "from_value": getattr(item, 'fromString', None),
                        "to_value": getattr(item, 'toString', None),
                        "from_id": getattr(item, 'from', None),
                        "to_id": getattr(item, 'to', None)
                    }
                    history_entry["items"].append(change_item)
                
                issue_data["changelog"].append(history_entry)
            
            logger.info(f"Retrieved {len(issue_data['changelog'])} changelog entries for issue {issue.key}")
            
        except Exception as e:
            logger.warning(f"Failed to retrieve changelog for issue {issue.key}: {str(e)}")
            issue_data["changelog"] = []
        
        # Find the latest activity timestamp from comments and changelog
        latest_timestamps = []
        
        # Add basic timestamps
        if issue_data.get("updated"):
            latest_timestamps.append(issue_data["updated"])
        if issue_data.get("created"):
            latest_timestamps.append(issue_data["created"])
        
        # Add comment timestamps
        for comment in issue_data.get("comments", []):
            if comment.get("updated"):
                latest_timestamps.append(comment["updated"])
        
        # Add changelog timestamps
        for history in issue_data.get("changelog", []):
            if history.get("created"):
                latest_timestamps.append(history["created"])
        
        # Find the most recent timestamp, with fallback
        if latest_timestamps:
            issue_data["latest_activity"] = max(latest_timestamps)
        else:
            # Fallback to current timestamp if no activity found
            from datetime import datetime
            issue_data["latest_activity"] = datetime.now().isoformat()
        
        return issue_data
        
    except Exception as e:
        logger.error(f"Error extracting details for issue {getattr(issue, 'key', 'Unknown')}: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Return basic information even if detailed extraction fails
        return {
            "key": safe_get_attr(issue, 'key', 'Unknown'),
            "summary": safe_get_attr(issue, 'fields.summary', 'Unable to retrieve summary'),
            "issue_type": {
                "name": safe_get_attr(issue, 'fields.issuetype.name', 'Unknown'),
                "id": safe_get_attr(issue, 'fields.issuetype.id', None)
            },
            "status": {
                "name": safe_get_attr(issue, 'fields.status.name', 'Unknown'),
                "id": safe_get_attr(issue, 'fields.status.id', None)
            },
            "priority": {
                "name": safe_get_attr(issue, 'fields.priority.name', None),
                "id": safe_get_attr(issue, 'fields.priority.id', None)
            } if safe_get_attr(issue, 'fields.priority', None) else None,
            "assignee": {
                "display_name": safe_get_attr(issue, 'fields.assignee.displayName', None),
                "email": safe_get_attr(issue, 'fields.assignee.emailAddress', None)
            } if safe_get_attr(issue, 'fields.assignee', None) else None,
            "created": safe_get_attr(issue, 'fields.created', None),
            "updated": safe_get_attr(issue, 'fields.updated', None),
            "latest_activity": safe_get_attr(issue, 'fields.updated', None),
            "comments": [],
            "changelog": [],
            "labels": safe_get_attr(issue, 'fields.labels', []),
            "description": safe_get_attr(issue, 'fields.description', None),
            "error": f"Failed to extract full details: {str(e)}"
        }


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Jira Status Automation API is running"}


@app.get("/api/jira/report")
async def get_jira_report(
    jira_url: str = Query(..., description="Jira instance URL"),
    personal_access_token: str = Query(..., description="Jira personal access token"),
    project_key: str = Query(..., description="Jira project key"),
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format")
) -> List[Dict[str, Any]]:
    """
    Retrieve comprehensive Jira issue report for a project within a date range
    
    This endpoint:
    1. Authenticates to Jira using the provided personal access token
    2. Executes a JQL query to find all issues updated within the date range
    3. Retrieves complete details for each issue including comments and changelog
    4. Returns structured JSON data with all issue information
    
    Args:
        jira_url: Base URL of the Jira instance (e.g., "https://company.atlassian.net")
        personal_access_token: Personal access token for Jira authentication
        project_key: Project key to search within (e.g., "PROJ", "DEV")
        start_date: Start date for the search range (YYYY-MM-DD format)
        end_date: End date for the search range (YYYY-MM-DD format)
        
    Returns:
        List of dictionaries containing comprehensive issue details
        
    Raises:
        HTTPException: For authentication failures, invalid parameters, or API errors
    """
    try:
        logger.info(f"Starting Jira report generation for project {project_key} from {start_date} to {end_date}")
        
        # Validate date formats
        try:
            start_datetime = validate_date_format(start_date)
            end_datetime = validate_date_format(end_date)
            
            # Ensure start date is not after end date
            if start_datetime > end_datetime:
                raise HTTPException(
                    status_code=400,
                    detail="Start date cannot be after end date"
                )
                
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Validate required parameters
        if not all([jira_url, personal_access_token, project_key]):
            raise HTTPException(
                status_code=400,
                detail="Missing required parameters: jira_url, personal_access_token, and project_key are required"
            )
        
        # Create authenticated Jira client
        jira_client = create_jira_client(jira_url, personal_access_token)
        
        # Build JQL query to find issues in the specified date range
        jql_query = build_jql_query(project_key, start_date, end_date)
        
        # Execute JQL search to find all matching issues
        # Using maxResults=False to get all issues (removes default 50 limit)
        # expand parameter requests additional fields like changelog
        try:
            logger.info(f"Executing JQL search: {jql_query}")
            issues = jira_client.search_issues(
                jql_query,
                maxResults=False,  # Get all results, not just first 50
                expand='changelog'  # Include changelog data
            )
            logger.info(f"Found {len(issues)} issues matching the criteria")
            
        except JIRAError as e:
            logger.error(f"JQL search failed: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"JQL search failed: {str(e)}. Please check your project key and permissions."
            )
        
        # Process each issue to extract comprehensive details
        report_data = []
        
        for idx, issue in enumerate(issues, 1):
            try:
                logger.info(f"Processing issue {idx}/{len(issues)}: {issue.key}")
                issue_details = extract_issue_details(issue, jira_client)
                report_data.append(issue_details)
                
            except Exception as e:
                logger.error(f"Failed to process issue {issue.key}: {str(e)}")
                # Add fallback issue data with basic fields even if full processing fails
                report_data.append({
                    "key": issue.key,
                    "summary": getattr(issue.fields, 'summary', 'Unable to retrieve summary'),
                    "issue_type": {
                        "name": getattr(issue.fields.issuetype, 'name', 'Unknown') if hasattr(issue.fields, 'issuetype') else 'Unknown',
                        "id": getattr(issue.fields.issuetype, 'id', None) if hasattr(issue.fields, 'issuetype') else None
                    },
                    "status": {
                        "name": getattr(issue.fields.status, 'name', 'Unknown') if hasattr(issue.fields, 'status') else 'Unknown',
                        "id": getattr(issue.fields.status, 'id', None) if hasattr(issue.fields, 'status') else None
                    },
                    "priority": {
                        "name": getattr(issue.fields.priority, 'name', None) if hasattr(issue.fields, 'priority') and issue.fields.priority else None,
                        "id": getattr(issue.fields.priority, 'id', None) if hasattr(issue.fields, 'priority') and issue.fields.priority else None
                    },
                    "assignee": {
                        "display_name": getattr(issue.fields.assignee, 'displayName', None) if hasattr(issue.fields, 'assignee') and issue.fields.assignee else None,
                        "email": getattr(issue.fields.assignee, 'emailAddress', None) if hasattr(issue.fields, 'assignee') and issue.fields.assignee else None
                    },
                    "reporter": {
                        "display_name": getattr(issue.fields.reporter, 'displayName', None) if hasattr(issue.fields, 'reporter') and issue.fields.reporter else None,
                        "email": getattr(issue.fields.reporter, 'emailAddress', None) if hasattr(issue.fields, 'reporter') and issue.fields.reporter else None
                    },
                    "created": getattr(issue.fields, 'created', None),
                    "updated": getattr(issue.fields, 'updated', None),
                    "latest_activity": getattr(issue.fields, 'updated', None),
                    "comments": [],
                    "changelog": [],
                    "labels": getattr(issue.fields, 'labels', []),
                    "description": getattr(issue.fields, 'description', None),
                    "processing_error": f"Detailed processing failed: {str(e)}"
                })
        
        logger.info(f"Successfully generated report with {len(report_data)} issues")
        
        return report_data
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log unexpected errors and return generic error response
        logger.error(f"Unexpected error in get_jira_report: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    Config.print_config()
    uvicorn.run(app, host=Config.BACKEND_HOST, port=Config.BACKEND_PORT)
