# JIRA Status Update Automation Tool

A comprehensive automation tool for generating bi-weekly status updates from JIRA projects. This tool fetches tasks, analyzes their status, and generates formatted reports automatically.

## 🚀 Features

- **JIRA Integration**: Connects to JIRA Cloud/Server using REST API
- **Smart Summarization**: Analyzes task status, assignees, priorities, and story points
- **Flexible Reporting**: Generates markdown reports with executive summaries
- **Automated Scheduling**: Supports bi-weekly or custom scheduling
- **Configurable**: Easy configuration via JSON file
- **Timeline Analysis**: Tracks recent updates and changes
- **Multiple Projects**: Supports multiple JIRA projects in one report
- **🐳 Containerized Deployment**: Run with Podman/Docker containers
- **🌐 Web Interface**: Browse and view reports through a modern web interface
- **📊 Real-time Monitoring**: Health checks and status monitoring

## 📋 Prerequisites

- Python 3.7 or higher
- JIRA account with API access
- API token for JIRA authentication

## 🔧 Installation

### Option 1: Containerized Deployment (Recommended)

For a quick, isolated deployment with web interface:

```bash
# Clone the repository
git clone <repository-url>
cd jira_status_automation

# Start with Podman (recommended)
./run-podman.sh start

# Or use Make
make start

# Access web interface at http://localhost:8080
```

**For detailed container setup, see [CONTAINER_DEPLOYMENT_GUIDE.md](CONTAINER_DEPLOYMENT_GUIDE.md)**

### Option 2: Local Installation

1. **Clone or download the project files**
   ```bash
   git clone <repository-url>
   # or download and extract the files
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-web.txt  # For web interface
   ```

3. **Set up configuration**
   ```bash
   cp config.example.json config.json
   ```

4. **Configure your JIRA settings** (see Configuration section below)

## ⚙️ Configuration

### Basic Setup

1. **Copy the example configuration:**
   ```bash
   cp config.example.json config.json
   ```

2. **Edit `config.json` with your details:**
   ```json
   {
     "jira": {
       "base_url": "https://your-company.atlassian.net",
       "username": "your-email@company.com",
       "api_token": "your-api-token"
     },
     "projects": ["PROJ1", "PROJ2", "TEAM"],
     "days_back": 14,
     "output_dir": "./reports"
   }
   ```

### Getting Your JIRA API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a label (e.g., "Status Update Tool")
4. Copy the generated token to your config file

### Advanced Configuration

The tool supports many customization options:

```json
{
  "schedule": {
    "enabled": true,
    "biweekly": true,
    "day_of_week": "monday",
    "hour": 9,
    "minute": 0
  },
  "report_settings": {
    "include_description": false,
    "max_recent_updates": 10,
    "max_previous_week_updates": 5,
    "story_points_field": "customfield_10016"
  },
  "status_mapping": {
    "completed": ["Done", "Closed", "Resolved"],
    "in_progress": ["In Progress", "In Development"],
    "blocked": ["Blocked", "Waiting", "On Hold"],
    "todo": ["To Do", "Open", "New", "Backlog"]
  }
}
```

## 🏃‍♂️ Usage

### Containerized Usage (Recommended)

```bash
# Start the web interface
./run-podman.sh start

# Access at http://localhost:8080
# Generate reports through the web interface or:

# Generate report manually
./run-podman.sh generate

# View logs
./run-podman.sh logs

# Shell access
./run-podman.sh shell
```

### Local Usage

#### Test Connection

Before running reports, test your JIRA connection:

```bash
python3 jira_status_automation.py --test-connection
```

#### Generate a Report Manually

```bash
# Basic usage
python3 jira_status_automation.py

# Specify projects and timeframe
python3 jira_status_automation.py --projects PROJ1 PROJ2 --days 7

# Custom output directory
python3 jira_status_automation.py --output /path/to/reports
```

#### Start Web Interface Locally

```bash
# Start web server
python3 web_server.py

# Access at http://localhost:8080
```

### Command Line Options

```bash
python3 jira_status_automation.py [OPTIONS]

Options:
  --config PATH         Config file path (default: config.json)
  --projects PROJECT... JIRA projects to include
  --days INTEGER        Days back to look for updates (default: 14)
  --output PATH         Output directory for reports (default: ./reports)
  --test-connection     Test JIRA connection only
  --help               Show help message
```

## ⏰ Automated Scheduling

### Using the Scheduler

The tool includes a scheduler for automated bi-weekly reports:

```bash
# Start scheduler with config file settings
python3 scheduler.py --from-config

# Custom schedule - every Monday at 9:00 AM
python3 scheduler.py --day monday --hour 9 --minute 0

# Bi-weekly schedule
python3 scheduler.py --day monday --hour 9 --biweekly

# Run report immediately
python3 scheduler.py --run-now
```

### Scheduler Options

```bash
python3 scheduler.py [OPTIONS]

Options:
  --script PATH         Path to main script (default: jira_status_automation.py)
  --config PATH         Path to config file (default: config.json)
  --day TEXT           Day of week for updates (default: monday)
  --hour INTEGER       Hour for updates in 24-hour format (default: 9)
  --minute INTEGER     Minute for updates (default: 0)
  --biweekly          Run bi-weekly instead of weekly
  --run-now           Run status update immediately
  --list-jobs         List scheduled jobs
  --from-config       Load schedule from config file
```

### System Service Setup (Linux)

To run the scheduler as a system service, create a systemd service file:

```bash
sudo nano /etc/systemd/system/jira-status-updates.service
```

```ini
[Unit]
Description=JIRA Status Update Automation
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/jira_status_automation
ExecStart=/usr/bin/python3 scheduler.py --from-config
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable jira-status-updates.service
sudo systemctl start jira-status-updates.service
```

## 🌐 Web Interface

The containerized deployment includes a modern web interface that provides:

- **Report Dashboard**: Browse all generated reports with metadata
- **Report Viewer**: Read reports with formatted markdown rendering
- **Download Feature**: Download reports as markdown files
- **Manual Generation**: Trigger report generation on-demand
- **Health Monitoring**: Check system status and configuration
- **Responsive Design**: Works on desktop and mobile devices

### Web Interface Features

- **Real-time Updates**: Automatically refreshes when new reports are available
- **Search and Filter**: Find specific reports quickly
- **Raw View Toggle**: Switch between formatted and raw markdown
- **API Endpoints**: RESTful API for integration with other tools

## 🐳 Container Deployment

### Benefits of Containerized Deployment

- **Isolation**: No conflicts with system Python packages
- **Portability**: Runs consistently across different environments
- **Security**: Runs as non-root user with minimal privileges
- **Scalability**: Easy to deploy multiple instances
- **Maintenance**: Simple updates and rollbacks

### Container Management Commands

```bash
# Quick start
./run-podman.sh start

# View all available commands
./run-podman.sh help
make help

# Management operations
./run-podman.sh status    # Check container status
./run-podman.sh logs      # View real-time logs
./run-podman.sh generate  # Generate report manually
./run-podman.sh shell     # Open container shell
```

## 📊 Report Format

The tool generates markdown reports with the following sections:

### Executive Summary
- Total tasks reviewed
- Story points progress
- Active projects count

### Status Breakdown
- Tasks categorized by status (completed, in-progress, blocked, todo)
- Percentage breakdown

### Project Breakdown
- Task count per project

### Team Activity
- Task count per assignee

### This Week's Highlights
- Recent updates with details
- Status changes
- Assignment information

### Previous Week's Activity
- Summary of last week's activity

## 🔍 Troubleshooting

### Common Issues

1. **Connection Failed**
   ```
   Error: JIRA connection failed!
   ```
   - Verify your base URL, username, and API token
   - Check if your JIRA instance is accessible
   - Ensure API token has necessary permissions

2. **No Tasks Found**
   ```
   Warning: No tasks found for the specified criteria
   ```
   - Check project keys are correct
   - Verify tasks exist in the specified timeframe
   - Ensure you have permission to view the projects

3. **Permission Denied**
   ```
   Error: API request failed: 403
   ```
   - Verify your API token has read access to projects
   - Check if projects exist and are accessible

### Debugging

Enable debug logging by modifying the script:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

### Testing Specific Projects

Test with a single project first:

```bash
python3 jira_status_automation.py --projects YOUR_PROJECT --days 7
```

## 🎛️ Customization

### Custom Status Mapping

Modify the `status_mapping` in your config file to match your JIRA workflow:

```json
{
  "status_mapping": {
    "completed": ["Done", "Closed", "Resolved", "Deployed"],
    "in_progress": ["In Progress", "In Development", "Code Review"],
    "blocked": ["Blocked", "Waiting for Approval", "On Hold"],
    "todo": ["To Do", "Open", "New", "Backlog", "Ready for Dev"]
  }
}
```

### Story Points Field

If your JIRA uses a different field for story points, update the configuration:

```json
{
  "report_settings": {
    "story_points_field": "customfield_10026"
  }
}
```

To find your story points field ID:
1. Go to JIRA Settings → Issues → Custom Fields
2. Find your story points field
3. Note the field ID (customfield_XXXXX)

### Custom Report Templates

You can modify the `_build_markdown_content` method in `jira_status_automation.py` to customize the report format.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source. Feel free to modify and distribute as needed.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the configuration examples
3. Test with minimal configuration first
4. Check JIRA permissions and API access

## 📝 Changelog

### v1.0.0
- Initial release
- JIRA API integration
- Markdown report generation
- Bi-weekly scheduling
- Configurable status mapping
- Story points tracking
