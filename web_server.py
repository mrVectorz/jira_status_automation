#!/usr/bin/env python3
"""
Web Server for JIRA Status Automation Reports

This module provides a web interface to view and browse through
generated JIRA status reports with configurable port settings.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import argparse
import subprocess
import threading
import time

from flask import Flask, render_template, jsonify, request, send_file, abort
from werkzeug.serving import WSGIRequestHandler
import schedule

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress Flask's default logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class ReportServer:
    """Web server for serving JIRA status reports"""
    
    def __init__(self, config_file: str = "config.json", reports_dir: str = "./reports"):
        self.config_file = Path(config_file)
        self.reports_dir = Path(reports_dir)
        self.app = Flask(__name__, template_folder='templates', static_folder='static')
        
        # Ensure reports directory exists
        self.reports_dir.mkdir(exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Setup routes
        self._setup_routes()
        
        # Setup background scheduler for automated reports
        self.scheduler_thread = None
        self.is_running = False
        
    def _load_config(self) -> Dict:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                return {}
        return {}
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main page showing list of reports"""
            try:
                reports = self._get_report_list()
                return render_template('index.html', reports=reports)
            except Exception as e:
                logger.error(f"Error in index route: {e}")
                return f"Error loading reports: {e}", 500
        
        @self.app.route('/api/reports')
        def api_reports():
            """API endpoint to get list of reports"""
            try:
                reports = self._get_report_list()
                return jsonify(reports)
            except Exception as e:
                logger.error(f"Error in API reports: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/report/<filename>')
        def view_report(filename):
            """View a specific report"""
            try:
                report_path = self.reports_dir / filename
                if not report_path.exists() or not report_path.suffix.lower() == '.md':
                    abort(404)
                
                with open(report_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return render_template('report.html', 
                                     filename=filename, 
                                     content=content,
                                     raw_content=content)
            except Exception as e:
                logger.error(f"Error viewing report {filename}: {e}")
                return f"Error loading report: {e}", 500
        
        @self.app.route('/download/<filename>')
        def download_report(filename):
            """Download a specific report"""
            try:
                report_path = self.reports_dir / filename
                if not report_path.exists():
                    abort(404)
                
                return send_file(report_path, as_attachment=True)
            except Exception as e:
                logger.error(f"Error downloading report {filename}: {e}")
                abort(500)
        
        @self.app.route('/api/generate')
        def api_generate():
            """API endpoint to trigger report generation"""
            try:
                success, error_details = self._generate_report()
                if success:
                    return jsonify({"status": "success", "message": "Report generated successfully"})
                else:
                    return jsonify({"status": "error", "message": error_details}), 500
            except Exception as e:
                logger.error(f"Error generating report: {e}")
                return jsonify({"status": "error", "message": f"Unexpected error: {str(e)}"}), 500
        
        @self.app.route('/health')
        def health():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "reports_count": len(self._get_report_list())
            })
        
        @self.app.route('/config')
        def config_info():
            """Configuration information (non-sensitive data only)"""
            safe_config = {
                "projects": self.config.get('projects', []),
                "days_back": self.config.get('days_back', 14),
                "schedule": self.config.get('schedule', {}),
                "web_server": self.config.get('web_server', {})
            }
            return jsonify(safe_config)
        
        @self.app.route('/api/config')
        def api_get_config():
            """Get configuration (with sensitive data masked)"""
            try:
                config_copy = self.config.copy()
                
                # Mask sensitive data
                if 'jira' in config_copy:
                    jira_config = config_copy['jira'].copy()
                    if 'api_token' in jira_config and jira_config['api_token']:
                        # Show only first 4 and last 4 characters
                        token = jira_config['api_token']
                        if len(token) > 8:
                            jira_config['api_token'] = token[:4] + '*' * (len(token) - 8) + token[-4:]
                        else:
                            jira_config['api_token'] = '*' * len(token)
                    config_copy['jira'] = jira_config
                
                if 'jira_oauth' in config_copy:
                    oauth_config = config_copy['jira_oauth'].copy()
                    # Mask OAuth secrets
                    for key in ['consumer_secret', 'access_token', 'access_token_secret']:
                        if key in oauth_config and oauth_config[key]:
                            oauth_config[key] = '*' * 8
                    config_copy['jira_oauth'] = oauth_config
                
                return jsonify({"status": "success", "config": config_copy})
            except Exception as e:
                logger.error(f"Error getting config: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/config', methods=['POST'])
        def api_update_config():
            """Update configuration"""
            try:
                new_config = request.get_json()
                if not new_config:
                    return jsonify({"status": "error", "message": "No configuration data provided"}), 400
                
                # Validate required fields
                if 'jira' in new_config:
                    jira_config = new_config['jira']
                    required_fields = ['base_url', 'username']
                    for field in required_fields:
                        if field not in jira_config or not jira_config[field]:
                            return jsonify({"status": "error", "message": f"Missing required JIRA field: {field}"}), 400
                
                # If API token is masked, preserve the original value
                if 'jira' in new_config and 'jira' in self.config:
                    new_token = new_config['jira'].get('api_token', '')
                    if '*' in new_token and self.config['jira'].get('api_token'):
                        new_config['jira']['api_token'] = self.config['jira']['api_token']
                
                # Update configuration
                self.config.update(new_config)
                
                # Save to file
                with open(self.config_file, 'w') as f:
                    json.dump(self.config, f, indent=2)
                
                logger.info("Configuration updated successfully")
                return jsonify({"status": "success", "message": "Configuration updated successfully"})
                
            except Exception as e:
                logger.error(f"Error updating config: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/config/test')
        def api_test_config():
            """Test JIRA connection with current configuration"""
            try:
                # Import here to avoid circular imports
                import subprocess
                
                # Use the same method that works - call main script with --test-connection
                # This uses the sophisticated authentication logic from JiraClient
                main_script = Path(__file__).parent / "jira_status_automation.py"
                cmd = ["python3", str(main_script), "--test-connection"]
                
                if self.config_file.exists():
                    cmd.extend(["--config", str(self.config_file)])
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30  # 30 second timeout for testing
                )
                
                if result.returncode == 0:
                    return jsonify({"status": "success", "message": "JIRA connection test successful"})
                else:
                    error_msg = self._parse_error_message(result.stderr)
                    return jsonify({"status": "error", "message": error_msg}), 400
                    
            except subprocess.TimeoutExpired:
                return jsonify({"status": "error", "message": "Connection test timed out"}), 408
            except Exception as e:
                logger.error(f"Error testing config: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/config-ui')
        def config_ui():
            """Configuration management page"""
            try:
                return render_template('config.html')
            except Exception as e:
                logger.error(f"Error in config UI route: {e}")
                return f"Error loading configuration page: {e}", 500
    
    def _get_report_list(self) -> List[Dict]:
        """Get list of available reports"""
        reports = []
        
        try:
            # Get all markdown files in reports directory
            for file_path in self.reports_dir.glob('*.md'):
                if file_path.is_file():
                    stat = file_path.stat()
                    report_info = {
                        'filename': file_path.name,
                        'title': self._extract_title_from_file(file_path),
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'url': f'/report/{file_path.name}',
                        'download_url': f'/download/{file_path.name}'
                    }
                    reports.append(report_info)
            
            # Sort by modification time (newest first)
            reports.sort(key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting report list: {e}")
        
        return reports
    
    def _extract_title_from_file(self, file_path: Path) -> str:
        """Extract title from markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for first # heading
            lines = content.split('\n')
            for line in lines[:10]:  # Check first 10 lines
                line = line.strip()
                if line.startswith('# '):
                    return line[2:].strip()
            
            # Fallback to filename without extension
            return file_path.stem.replace('_', ' ').title()
            
        except Exception as e:
            logger.debug(f"Error extracting title from {file_path}: {e}")
            return file_path.stem.replace('_', ' ').title()
    
    def _generate_report(self) -> tuple[bool, str]:
        """Generate a new report using the main automation script"""
        try:
            logger.info("Generating new JIRA status report...")
            
            # Run the main automation script
            script_path = Path(__file__).parent / "jira_status_automation.py"
            cmd = ["python3", str(script_path)]
            
            # Add config if it exists
            if self.config_file.exists():
                cmd.extend(["--config", str(self.config_file)])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info("✅ Report generated successfully")
                logger.debug(f"Output: {result.stdout}")
                return True, "Report generated successfully"
            else:
                logger.error(f"❌ Report generation failed with exit code {result.returncode}")
                logger.error(f"Error output: {result.stderr}")
                # Extract meaningful error message from stderr
                error_msg = self._parse_error_message(result.stderr)
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = "Report generation timed out after 5 minutes. This may indicate a network connectivity issue or JIRA server problems."
            logger.error(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Error generating report: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def _parse_error_message(self, stderr: str) -> str:
        """Parse error message from stderr and extract meaningful information"""
        if not stderr:
            return "Report generation failed with no error details"
        
        # Common error patterns and their user-friendly messages
        if "JiraError HTTP 401" in stderr or "401 Unauthorized" in stderr:
            return "JIRA Authentication Failed: Invalid username, password, or API token. Please check your credentials in the configuration."
        elif "JiraError HTTP 403" in stderr or "Failed to parse Connect Session Auth Token" in stderr:
            return "JIRA Authentication Error: API token is invalid or has insufficient permissions. Please generate a new API token."
        elif "JiraError HTTP 404" in stderr:
            return "JIRA Server Not Found: The JIRA base URL is incorrect. Please verify your JIRA server URL in the configuration."
        elif "ConnectionError" in stderr or "requests.exceptions.ConnectionError" in stderr:
            return "Network Connection Error: Cannot connect to JIRA server. Please check your internet connection and JIRA server URL."
        elif "TimeoutError" in stderr or "timeout" in stderr.lower():
            return "Connection Timeout: JIRA server is not responding. Please try again later or check if the server is accessible."
        elif "No module named" in stderr:
            return "Missing Dependencies: Required Python modules are not installed."
        elif "❌ JIRA connection failed" in stderr:
            return "JIRA Connection Failed: Unable to connect to JIRA. Please verify your configuration settings (URL, username, API token)."
        else:
            # Try to extract the last meaningful error line
            lines = stderr.strip().split('\n')
            for line in reversed(lines):
                if line.strip() and not line.startswith('2025-') and 'ERROR' in line:
                    return line.strip()
            
            # If no specific error found, return a cleaned up version of the first few lines
            relevant_lines = [line for line in lines[:10] if line.strip() and not line.startswith('2025-')]
            if relevant_lines:
                return '. '.join(relevant_lines[:2])
            
            return "Report generation failed. Please check the server logs for more details."
    
    def _setup_scheduler(self):
        """Setup automated report generation scheduler"""
        schedule_config = self.config.get('schedule', {})
        if not schedule_config.get('enabled', False):
            logger.info("Automated scheduling is disabled")
            return
        
        try:
            # Clear any existing schedules
            schedule.clear()
            
            day_of_week = schedule_config.get('day_of_week', 'monday')
            hour = schedule_config.get('hour', 9)
            minute = schedule_config.get('minute', 0)
            biweekly = schedule_config.get('biweekly', True)
            
            # Convert day number to day name if needed
            if isinstance(day_of_week, int):
                day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                day_of_week = day_names[day_of_week % 7]
            
            if biweekly:
                # For bi-weekly, check daily and run if it's the right day
                schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self._biweekly_check, day_of_week)
                logger.info(f"Scheduled bi-weekly reports for {day_of_week} at {hour:02d}:{minute:02d}")
            else:
                # Weekly schedule
                getattr(schedule.every(), day_of_week.lower()).at(f"{hour:02d}:{minute:02d}").do(self._generate_report)
                logger.info(f"Scheduled weekly reports for {day_of_week} at {hour:02d}:{minute:02d}")
                
        except Exception as e:
            logger.error(f"Error setting up scheduler: {e}")
    
    def _biweekly_check(self, target_day: str):
        """Check if today is the bi-weekly target day"""
        today = datetime.now()
        
        # Map day names to weekday numbers (0=Monday, 6=Sunday)
        day_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        target_weekday = day_map.get(target_day.lower())
        if target_weekday is None or today.weekday() != target_weekday:
            return
        
        # Check if it's been 2 weeks since last run
        last_run_file = Path("last_run.txt")
        if last_run_file.exists():
            try:
                with open(last_run_file, 'r') as f:
                    last_run_str = f.read().strip()
                    last_run = datetime.fromisoformat(last_run_str)
                    
                    # If less than 13 days since last run, skip
                    if (today - last_run).days < 13:
                        logger.info(f"Skipping report - last run was {(today - last_run).days} days ago")
                        return
            except Exception as e:
                logger.warning(f"Could not read last run file: {e}")
        
        # Generate report and record the date
        success, _ = self._generate_report()
        if success:
            with open(last_run_file, 'w') as f:
                f.write(today.isoformat())
    
    def _run_scheduler(self):
        """Background scheduler thread"""
        logger.info("Starting background scheduler...")
        self._setup_scheduler()
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                time.sleep(60)
        
        logger.info("Background scheduler stopped")
    
    def start_scheduler(self):
        """Start the background scheduler"""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            logger.warning("Scheduler already running")
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
    
    def run(self, host: str = '0.0.0.0', port: int = 8080, debug: bool = False):
        """Run the web server"""
        logger.info(f"Starting JIRA Status Reports Web Server on {host}:{port}")
        logger.info(f"Reports directory: {self.reports_dir.absolute()}")
        
        # Start scheduler if enabled
        if self.config.get('schedule', {}).get('enabled', False):
            self.start_scheduler()
        
        try:
            # Use Waitress for production deployment
            from waitress import serve
            logger.info("Using Waitress WSGI server for production")
            serve(self.app, host=host, port=port, threads=4)
        except ImportError:
            # Fallback to Flask's development server
            logger.warning("Waitress not available, using Flask development server")
            self.app.run(host=host, port=port, debug=debug, threaded=True)
        except KeyboardInterrupt:
            logger.info("Shutting down server...")
        finally:
            self.stop_scheduler()

def create_templates():
    """Create HTML templates for the web interface"""
    templates_dir = Path(__file__).parent / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    # Create base template
    base_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}JIRA Status Reports{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .navbar-brand { font-weight: bold; }
        .report-card { transition: transform 0.2s; }
        .report-card:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .markdown-content { line-height: 1.6; }
        .markdown-content h1, .markdown-content h2, .markdown-content h3 { color: #343a40; margin-top: 1.5rem; }
        .markdown-content pre { background-color: #f8f9fa; padding: 1rem; border-radius: 0.375rem; }
        .markdown-content code { background-color: #f8f9fa; padding: 0.2rem 0.4rem; border-radius: 0.25rem; }
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .status-healthy { background-color: #28a745; }
        .status-warning { background-color: #ffc107; }
        .status-error { background-color: #dc3545; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-chart-line me-2"></i>
                JIRA Status Reports
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">
                    <i class="fas fa-home me-1"></i>
                    Reports
                </a>
                <a class="nav-link" href="/config-ui">
                    <i class="fas fa-cog me-1"></i>
                    Configuration
                </a>
                <a class="nav-link" href="#" onclick="generateReport()">
                    <i class="fas fa-sync-alt me-1"></i>
                    Generate New
                </a>
            </div>
        </div>
    </nav>

    <main class="container my-4">
        {% block content %}{% endblock %}
    </main>

    <footer class="bg-light py-3 mt-5">
        <div class="container text-center text-muted">
            <small>JIRA Status Automation - Containerized Web Interface</small>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function generateReport() {
            const btn = event.target.closest('a') || event.target.closest('button');
            const originalContent = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Generating...';
            btn.classList.add('disabled');
            
            fetch('/api/generate')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        alert('Report generated successfully! Refreshing page...');
                        window.location.reload();
                    } else {
                        alert('Error generating report: ' + data.message);
                    }
                })
                .catch(error => {
                    alert('Error generating report: ' + error.message);
                })
                .finally(() => {
                    btn.innerHTML = originalContent;
                    btn.classList.remove('disabled');
                });
        }
        
        function formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        function formatDateTime(isoString) {
            return new Date(isoString).toLocaleString();
        }
    </script>
    {% block scripts %}{% endblock %}
</body>
</html>'''
    
    # Create index template
    index_template = '''{% extends "base.html" %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1>
                <i class="fas fa-file-alt me-2"></i>
                Status Reports
            </h1>
            <div>
                <span class="status-indicator status-healthy"></span>
                <span class="text-muted">{{ reports|length }} reports available</span>
            </div>
        </div>
        
        {% if reports %}
            <div class="row">
                {% for report in reports %}
                <div class="col-md-6 col-lg-4 mb-4">
                    <div class="card report-card h-100">
                        <div class="card-body">
                            <h5 class="card-title">
                                <i class="fas fa-file-alt me-2 text-primary"></i>
                                {{ report.title }}
                            </h5>
                            <p class="card-text">
                                <small class="text-muted">
                                    <i class="fas fa-clock me-1"></i>
                                    Modified: <span class="formatted-date">{{ report.modified }}</span><br>
                                    <i class="fas fa-hdd me-1"></i>
                                    Size: <span class="formatted-size">{{ report.size }}</span>
                                </small>
                            </p>
                            <div class="d-flex gap-2">
                                <a href="{{ report.url }}" class="btn btn-primary btn-sm flex-fill">
                                    <i class="fas fa-eye me-1"></i>View
                                </a>
                                <a href="{{ report.download_url }}" class="btn btn-outline-secondary btn-sm">
                                    <i class="fas fa-download me-1"></i>Download
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        {% else %}
            <div class="text-center py-5">
                <i class="fas fa-file-alt fa-4x text-muted mb-3"></i>
                <h3 class="text-muted">No Reports Available</h3>
                <p class="text-muted mb-4">Generate your first report to get started.</p>
                <button class="btn btn-primary" onclick="generateReport()">
                    <i class="fas fa-plus me-1"></i>
                    Generate First Report
                </button>
            </div>
        {% endif %}
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    // Format file sizes
    document.querySelectorAll('.formatted-size').forEach(el => {
        el.textContent = formatFileSize(parseInt(el.textContent));
    });
    
    // Format dates
    document.querySelectorAll('.formatted-date').forEach(el => {
        el.textContent = formatDateTime(el.textContent);
    });
});
</script>
{% endblock %}'''
    
    # Create report template
    report_template = '''{% extends "base.html" %}

{% block title %}{{ filename }} - JIRA Status Reports{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <nav aria-label="breadcrumb">
                    <ol class="breadcrumb">
                        <li class="breadcrumb-item"><a href="/">Reports</a></li>
                        <li class="breadcrumb-item active">{{ filename }}</li>
                    </ol>
                </nav>
            </div>
            <div>
                <a href="/download/{{ filename }}" class="btn btn-outline-primary me-2">
                    <i class="fas fa-download me-1"></i>Download
                </a>
                <button class="btn btn-secondary" onclick="toggleRawView()">
                    <i class="fas fa-code me-1"></i>Raw View
                </button>
            </div>
        </div>
        
        <div class="card">
            <div class="card-body">
                <!-- Rendered markdown content -->
                <div id="rendered-content" class="markdown-content">
                    {{ content | markdown | safe }}
                </div>
                
                <!-- Raw markdown content (hidden by default) -->
                <div id="raw-content" style="display: none;">
                    <pre><code>{{ raw_content }}</code></pre>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
function toggleRawView() {
    const rendered = document.getElementById('rendered-content');
    const raw = document.getElementById('raw-content');
    const btn = event.target.closest('button');
    
    if (raw.style.display === 'none') {
        raw.style.display = 'block';
        rendered.style.display = 'none';
        btn.innerHTML = '<i class="fas fa-eye me-1"></i>Rendered View';
    } else {
        raw.style.display = 'none';
        rendered.style.display = 'block';
        btn.innerHTML = '<i class="fas fa-code me-1"></i>Raw View';
    }
}
</script>
{% endblock %}'''
    
    # Write templates
    with open(templates_dir / "base.html", 'w') as f:
        f.write(base_template)
    
    with open(templates_dir / "index.html", 'w') as f:
        f.write(index_template)
    
    with open(templates_dir / "report.html", 'w') as f:
        f.write(report_template)
    
    # Create configuration template
    config_template = '''{% extends "base.html" %}

{% block title %}Configuration - JIRA Status Reports{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1>
                <i class="fas fa-cog me-2"></i>
                Configuration
            </h1>
            <div>
                <button class="btn btn-success me-2" onclick="testConnection()">
                    <i class="fas fa-link me-1"></i>Test Connection
                </button>
                <button class="btn btn-primary" onclick="saveConfiguration()">
                    <i class="fas fa-save me-1"></i>Save Changes
                </button>
            </div>
        </div>
        
        <!-- Alert area for messages -->
        <div id="alertArea"></div>
        
        <!-- Loading indicator -->
        <div id="loadingIndicator" class="text-center mb-4" style="display: none;">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading configuration...</p>
        </div>
        
        <!-- Configuration Form -->
        <div id="configForm" style="display: none;">
            <div class="row">
                <!-- JIRA Configuration -->
                <div class="col-md-6">
                    <div class="card mb-4">
                        <div class="card-header">
                            <h5><i class="fas fa-server me-2"></i>JIRA Connection</h5>
                        </div>
                        <div class="card-body">
                            <div class="mb-3">
                                <label for="jiraBaseUrl" class="form-label">Base URL *</label>
                                <input type="url" class="form-control" id="jiraBaseUrl" 
                                       placeholder="https://your-company.atlassian.net"
                                       required>
                                <div class="form-text">Your JIRA server URL</div>
                            </div>
                            
                            <div class="mb-3">
                                <label for="jiraUsername" class="form-label">Username *</label>
                                <input type="email" class="form-control" id="jiraUsername" 
                                       placeholder="your-email@company.com"
                                       required>
                                <div class="form-text">Your JIRA username (usually email)</div>
                            </div>
                            
                            <div class="mb-3">
                                <label for="jiraApiToken" class="form-label">API Token *</label>
                                <div class="input-group">
                                    <input type="password" class="form-control" id="jiraApiToken" 
                                           placeholder="Enter your API token">
                                    <button class="btn btn-outline-secondary" type="button" onclick="togglePasswordVisibility('jiraApiToken')">
                                        <i class="fas fa-eye"></i>
                                    </button>
                                </div>
                                <div class="form-text">
                                    <a href="https://id.atlassian.com/manage-profile/security/api-tokens" target="_blank">
                                        Generate API Token <i class="fas fa-external-link-alt"></i>
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Projects Configuration -->
                <div class="col-md-6">
                    <div class="card mb-4">
                        <div class="card-header">
                            <h5><i class="fas fa-project-diagram me-2"></i>Projects</h5>
                        </div>
                        <div class="card-body">
                            <div class="mb-3">
                                <label for="projectsInput" class="form-label">Project Keys</label>
                                <textarea class="form-control" id="projectsInput" rows="4" 
                                         placeholder="Enter project keys, one per line:&#10;PROJ1&#10;TEAM&#10;MYPROJECT"></textarea>
                                <div class="form-text">JIRA project keys to include in reports</div>
                            </div>
                            
                            <div class="mb-3">
                                <label for="daysBack" class="form-label">Days Back</label>
                                <input type="number" class="form-control" id="daysBack" 
                                       min="1" max="90" value="14">
                                <div class="form-text">Number of days to look back for recent updates</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Report Settings -->
            <div class="row">
                <div class="col-md-12">
                    <div class="card mb-4">
                        <div class="card-header">
                            <h5><i class="fas fa-chart-bar me-2"></i>Report Settings</h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label for="includeDescription" class="form-label">Include Descriptions</label>
                                        <select class="form-control" id="includeDescription">
                                            <option value="false">No</option>
                                            <option value="true">Yes</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label for="maxRecentUpdates" class="form-label">Max Recent Updates</label>
                                        <input type="number" class="form-control" id="maxRecentUpdates" 
                                               min="1" max="50" value="10">
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label for="maxPreviousWeekUpdates" class="form-label">Max Previous Week Updates</label>
                                        <input type="number" class="form-control" id="maxPreviousWeekUpdates" 
                                               min="1" max="20" value="5">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Schedule Settings -->
            <div class="row">
                <div class="col-md-12">
                    <div class="card mb-4">
                        <div class="card-header">
                            <h5><i class="fas fa-clock me-2"></i>Automated Scheduling</h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-3">
                                    <div class="mb-3">
                                        <label for="scheduleEnabled" class="form-label">Enable Scheduling</label>
                                        <select class="form-control" id="scheduleEnabled">
                                            <option value="false">Disabled</option>
                                            <option value="true">Enabled</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="mb-3">
                                        <label for="scheduleBiweekly" class="form-label">Frequency</label>
                                        <select class="form-control" id="scheduleBiweekly">
                                            <option value="false">Weekly</option>
                                            <option value="true">Bi-weekly</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="mb-3">
                                        <label for="scheduleDayOfWeek" class="form-label">Day of Week</label>
                                        <select class="form-control" id="scheduleDayOfWeek">
                                            <option value="monday">Monday</option>
                                            <option value="tuesday">Tuesday</option>
                                            <option value="wednesday">Wednesday</option>
                                            <option value="thursday">Thursday</option>
                                            <option value="friday">Friday</option>
                                            <option value="saturday">Saturday</option>
                                            <option value="sunday">Sunday</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="mb-3">
                                        <label for="scheduleTime" class="form-label">Time</label>
                                        <input type="time" class="form-control" id="scheduleTime" value="09:00">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
let currentConfig = {};

document.addEventListener('DOMContentLoaded', function() {
    loadConfiguration();
});

function showAlert(message, type = 'info') {
    const alertArea = document.getElementById('alertArea');
    alertArea.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = alertArea.querySelector('.alert');
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

function showLoading(show = true) {
    document.getElementById('loadingIndicator').style.display = show ? 'block' : 'none';
    document.getElementById('configForm').style.display = show ? 'none' : 'block';
}

function loadConfiguration() {
    showLoading(true);
    
    fetch('/api/config')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                currentConfig = data.config;
                populateForm(data.config);
                showLoading(false);
            } else {
                throw new Error(data.message || 'Failed to load configuration');
            }
        })
        .catch(error => {
            showAlert('Error loading configuration: ' + error.message, 'danger');
            showLoading(false);
        });
}

function populateForm(config) {
    // JIRA settings
    if (config.jira) {
        document.getElementById('jiraBaseUrl').value = config.jira.base_url || '';
        document.getElementById('jiraUsername').value = config.jira.username || '';
        document.getElementById('jiraApiToken').value = config.jira.api_token || '';
    }
    
    // Projects
    if (config.projects) {
        document.getElementById('projectsInput').value = config.projects.join('\\n');
    }
    
    // General settings
    document.getElementById('daysBack').value = config.days_back || 14;
    
    // Report settings
    if (config.report_settings) {
        document.getElementById('includeDescription').value = String(config.report_settings.include_description || false);
        document.getElementById('maxRecentUpdates').value = config.report_settings.max_recent_updates || 10;
        document.getElementById('maxPreviousWeekUpdates').value = config.report_settings.max_previous_week_updates || 5;
    }
    
    // Schedule settings
    if (config.schedule) {
        document.getElementById('scheduleEnabled').value = String(config.schedule.enabled || false);
        document.getElementById('scheduleBiweekly').value = String(config.schedule.biweekly || true);
        document.getElementById('scheduleDayOfWeek').value = config.schedule.day_of_week || 'monday';
        
        const hour = config.schedule.hour || 9;
        const minute = config.schedule.minute || 0;
        document.getElementById('scheduleTime').value = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
    }
}

function getFormData() {
    const timeValue = document.getElementById('scheduleTime').value;
    const [hour, minute] = timeValue.split(':').map(Number);
    
    return {
        jira: {
            base_url: document.getElementById('jiraBaseUrl').value.trim(),
            username: document.getElementById('jiraUsername').value.trim(),
            api_token: document.getElementById('jiraApiToken').value
        },
        projects: document.getElementById('projectsInput').value
            .split('\\n')
            .map(p => p.trim())
            .filter(p => p.length > 0),
        days_back: parseInt(document.getElementById('daysBack').value),
        report_settings: {
            include_description: document.getElementById('includeDescription').value === 'true',
            max_recent_updates: parseInt(document.getElementById('maxRecentUpdates').value),
            max_previous_week_updates: parseInt(document.getElementById('maxPreviousWeekUpdates').value),
            story_points_field: currentConfig.report_settings?.story_points_field || "customfield_10016"
        },
        schedule: {
            enabled: document.getElementById('scheduleEnabled').value === 'true',
            biweekly: document.getElementById('scheduleBiweekly').value === 'true',
            day_of_week: document.getElementById('scheduleDayOfWeek').value,
            hour: hour,
            minute: minute
        },
        // Preserve other settings
        jira_oauth: currentConfig.jira_oauth || {},
        status_mapping: currentConfig.status_mapping || {},
        ai_enhancement: currentConfig.ai_enhancement || {},
        web_server: currentConfig.web_server || {},
        container: currentConfig.container || {}
    };
}

function saveConfiguration() {
    const formData = getFormData();
    
    // Validate required fields
    if (!formData.jira.base_url || !formData.jira.username) {
        showAlert('Please fill in all required JIRA fields (Base URL and Username)', 'warning');
        return;
    }
    
    const saveButton = document.querySelector('button[onclick="saveConfiguration()"]');
    const originalText = saveButton.innerHTML;
    saveButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Saving...';
    saveButton.disabled = true;
    
    fetch('/api/config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showAlert('Configuration saved successfully!', 'success');
            currentConfig = formData;
        } else {
            throw new Error(data.message || 'Failed to save configuration');
        }
    })
    .catch(error => {
        showAlert('Error saving configuration: ' + error.message, 'danger');
    })
    .finally(() => {
        saveButton.innerHTML = originalText;
        saveButton.disabled = false;
    });
}

function testConnection() {
    const testButton = document.querySelector('button[onclick="testConnection()"]');
    const originalText = testButton.innerHTML;
    testButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Testing...';
    testButton.disabled = true;
    
    fetch('/api/config/test')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showAlert('✅ ' + data.message, 'success');
            } else {
                showAlert('❌ Connection test failed: ' + data.message, 'warning');
            }
        })
        .catch(error => {
            showAlert('❌ Connection test error: ' + error.message, 'danger');
        })
        .finally(() => {
            testButton.innerHTML = originalText;
            testButton.disabled = false;
        });
}

function togglePasswordVisibility(inputId) {
    const input = document.getElementById(inputId);
    const button = input.nextElementSibling;
    const icon = button.querySelector('i');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'fas fa-eye-slash';
    } else {
        input.type = 'password';
        icon.className = 'fas fa-eye';
    }
}
</script>
{% endblock %}'''
    
    with open(templates_dir / "config.html", 'w') as f:
        f.write(config_template)

def setup_markdown_filter(app):
    """Setup markdown filter for Jinja2"""
    try:
        import markdown
        
        @app.template_filter('markdown')
        def markdown_filter(text):
            return markdown.markdown(text, extensions=['tables', 'fenced_code', 'toc'])
    except ImportError:
        @app.template_filter('markdown')
        def markdown_filter(text):
            # Simple fallback - just convert line breaks to <br> and wrap in <pre>
            return f'<pre>{text}</pre>'

def main():
    """Main function for the web server"""
    parser = argparse.ArgumentParser(description='JIRA Status Reports Web Server')
    parser.add_argument('--config', default='config.json', help='Config file path')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, help='Port to bind to (overrides config)')
    parser.add_argument('--reports-dir', default='./reports', help='Reports directory')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--setup-templates', action='store_true', help='Create template files and exit')
    
    args = parser.parse_args()
    
    # Create templates if requested
    if args.setup_templates:
        create_templates()
        logger.info("Templates created successfully")
        return 0
    
    # Load web server config
    config_file = Path(args.config)
    web_config = {}
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                web_config = config.get('web_server', {})
        except Exception as e:
            logger.warning(f"Could not load config: {e}")
    
    # Determine port (command line overrides config)
    port = args.port or web_config.get('port', int(os.environ.get('WEB_PORT', 8080)))
    host = web_config.get('host', args.host)
    
    # Create templates
    create_templates()
    
    # Create and run server
    server = ReportServer(args.config, args.reports_dir)
    
    # Setup markdown filter
    setup_markdown_filter(server.app)
    
    server.run(host=host, port=port, debug=args.debug)
    
    return 0

if __name__ == '__main__':
    exit(main())
