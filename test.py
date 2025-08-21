import os
from jira import JIRA

# --- Configuration ---
# Set these environment variables before running the script
# export JIRA_SERVER="https://your-jira-domain.atlassian.net"
# export JIRA_TOKEN="your-personal-access-token"
# export JIRA_USER="your-email@example.com"
jira_server = os.environ.get("JIRA_SERVER")
jira_token = os.environ.get("JIRA_TOKEN")
jira_user = os.environ.get("JIRA_USER")

if not all([jira_server, jira_token, jira_user]):
    print("Error: Please set the JIRA_SERVER, JIRA_TOKEN, and JIRA_USER environment variables.")
    print("Example (for a bash terminal):")
    print("export JIRA_SERVER=\"https://your-jira-domain.atlassian.net\"")
    print("export JIRA_TOKEN=\"your-personal-access-token\"")
    print("export JIRA_USER=\"your-email@example.com\"")
    exit()

# --- Connection Test ---
try:
    print(f"Connecting to Jira server at: {jira_server}...")
    jira = JIRA(server=jira_server, token_auth=(jira_token))

    # Test the connection by getting the current user's details
    myself = jira.myself()
    print("Connection successful!")
    print(f"You are logged in as: {myself['displayName']} ({myself['emailAddress']})")

except Exception as e:
    print("Connection failed.")
    print(f"Error: {e}")
