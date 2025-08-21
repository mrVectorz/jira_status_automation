#!/usr/bin/env python3
"""
Setup script for JIRA Status Update Automation Tool

This script helps users set up the tool by:
1. Installing dependencies
2. Creating configuration files
3. Testing JIRA connection
4. Setting up scheduling (optional)
"""

import subprocess
import sys
import json
import getpass
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def install_dependencies():
    """Install required Python packages"""
    logger.info("Installing required dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        logger.info("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        return False

def create_config():
    """Create configuration file interactively"""
    logger.info("Setting up JIRA configuration...")
    
    config = {
        "jira": {},
        "projects": [],
        "days_back": 14,
        "output_dir": "./reports",
        "schedule": {
            "enabled": False,
            "biweekly": True,
            "day_of_week": "monday",
            "hour": 9,
            "minute": 0
        }
    }
    
    # Get JIRA details
    print("\n🔧 JIRA Configuration")
    print("-" * 50)
    
    base_url = input("JIRA Base URL (e.g., https://company.atlassian.net): ").strip()
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'https://' + base_url
    config["jira"]["base_url"] = base_url
    
    username = input("JIRA Username/Email: ").strip()
    config["jira"]["username"] = username
    
    print("\n📋 To get your API token:")
    print("1. Go to https://id.atlassian.com/manage-profile/security/api-tokens")
    print("2. Click 'Create API token'")
    print("3. Give it a name and copy the token")
    api_token = getpass.getpass("JIRA API Token: ").strip()
    config["jira"]["api_token"] = api_token
    
    # Get projects
    print("\n📊 Project Configuration")
    print("-" * 50)
    projects_input = input("JIRA Project Keys (comma-separated, e.g., PROJ1,PROJ2,TEAM): ").strip()
    if projects_input:
        config["projects"] = [p.strip().upper() for p in projects_input.split(',')]
    
    # Days back
    days_back = input("Days back to look for updates (default: 14): ").strip()
    if days_back.isdigit():
        config["days_back"] = int(days_back)
    
    # Output directory
    output_dir = input("Output directory for reports (default: ./reports): ").strip()
    if output_dir:
        config["output_dir"] = output_dir
    
    # Scheduling
    print("\n⏰ Scheduling Configuration")
    print("-" * 50)
    enable_schedule = input("Enable automatic scheduling? (y/N): ").strip().lower()
    if enable_schedule in ['y', 'yes']:
        config["schedule"]["enabled"] = True
        
        biweekly = input("Run bi-weekly (every 2 weeks)? (Y/n): ").strip().lower()
        if biweekly not in ['n', 'no']:
            config["schedule"]["biweekly"] = True
        else:
            config["schedule"]["biweekly"] = False
        
        day = input("Day of week (monday/tuesday/.../sunday, default: monday): ").strip().lower()
        if day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            config["schedule"]["day_of_week"] = day
        
        hour = input("Hour (0-23, default: 9): ").strip()
        if hour.isdigit() and 0 <= int(hour) <= 23:
            config["schedule"]["hour"] = int(hour)
        
        minute = input("Minute (0-59, default: 0): ").strip()
        if minute.isdigit() and 0 <= int(minute) <= 59:
            config["schedule"]["minute"] = int(minute)
    
    # Save configuration
    config_path = Path("config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"✅ Configuration saved to {config_path}")
    return config

def test_connection(config):
    """Test JIRA connection"""
    logger.info("Testing JIRA connection...")
    
    try:
        # Import our main script
        sys.path.insert(0, str(Path(__file__).parent))
        from jira_status_automation import JiraClient
        
        jira_client = JiraClient(
            base_url=config["jira"]["base_url"],
            username=config["jira"]["username"],
            api_token=config["jira"]["api_token"]
        )
        
        if jira_client.test_connection():
            logger.info("✅ JIRA connection successful!")
            return True
        else:
            logger.error("❌ JIRA connection failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing connection: {e}")
        return False

def setup_scheduler(config):
    """Set up scheduler if enabled"""
    if not config["schedule"]["enabled"]:
        return True
    
    logger.info("Setting up scheduler...")
    
    try:
        # Create a simple systemd service file template
        service_content = f"""[Unit]
Description=JIRA Status Update Automation
After=network.target

[Service]
Type=simple
User={getpass.getuser()}
WorkingDirectory={Path(__file__).parent.absolute()}
ExecStart=/usr/bin/python3 scheduler.py --from-config
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
"""
        
        service_file = Path("jira-status-updates.service")
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        logger.info(f"✅ Service file created: {service_file}")
        logger.info("To install as a system service, run:")
        logger.info(f"  sudo cp {service_file} /etc/systemd/system/")
        logger.info("  sudo systemctl enable jira-status-updates.service")
        logger.info("  sudo systemctl start jira-status-updates.service")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error setting up scheduler: {e}")
        return False

def run_test_report(config):
    """Run a test report"""
    if not config.get("projects"):
        logger.warning("No projects configured, skipping test report")
        return True
    
    logger.info("Running test report...")
    
    try:
        subprocess.check_call([
            sys.executable, "jira_status_automation.py",
            "--projects"] + config["projects"] + [
            "--days", "7",  # Last week only for test
            "--output", "./test_reports"
        ])
        logger.info("✅ Test report generated successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Test report failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 JIRA Status Update Automation - Setup")
    print("=" * 50)
    
    # Check if config already exists
    config_path = Path("config.json")
    if config_path.exists():
        overwrite = input("Configuration file already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite not in ['y', 'yes']:
            logger.info("Setup cancelled")
            return 1
    
    # Step 1: Install dependencies
    if not install_dependencies():
        return 1
    
    # Step 2: Create configuration
    config = create_config()
    if not config:
        return 1
    
    # Step 3: Test connection
    if not test_connection(config):
        logger.error("Please check your JIRA configuration and try again")
        return 1
    
    # Step 4: Set up scheduler (if enabled)
    if not setup_scheduler(config):
        logger.warning("Scheduler setup failed, but you can still run reports manually")
    
    # Step 5: Run test report
    run_test = input("\nRun a test report now? (Y/n): ").strip().lower()
    if run_test not in ['n', 'no']:
        run_test_report(config)
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Run manual report: python3 jira_status_automation.py")
    print("2. Start scheduler: python3 scheduler.py --from-config")
    print("3. Check README.md for advanced configuration options")
    
    return 0

if __name__ == '__main__':
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        exit(1)
