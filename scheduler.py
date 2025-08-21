#!/usr/bin/env python3
"""
Scheduler module for automating JIRA status updates

This module provides scheduling capabilities to run status updates automatically
on a bi-weekly basis or at custom intervals.
"""

import schedule
import time
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import json

logger = logging.getLogger(__name__)

class StatusUpdateScheduler:
    """Scheduler for automated status updates"""
    
    def __init__(self, script_path: str = "jira_status_automation.py", config_path: str = "config.json"):
        self.script_path = Path(script_path)
        self.config_path = Path(config_path)
        self.is_running = False
        
        if not self.script_path.exists():
            raise FileNotFoundError(f"Script not found: {self.script_path}")
    
    def setup_schedule(self, day_of_week: str = "monday", hour: int = 9, minute: int = 0):
        """Set up the bi-weekly schedule"""
        # Clear any existing schedules
        schedule.clear()
        
        # Schedule the job
        if day_of_week.lower() == "monday":
            schedule.every().monday.at(f"{hour:02d}:{minute:02d}").do(self._run_status_update)
        elif day_of_week.lower() == "tuesday":
            schedule.every().tuesday.at(f"{hour:02d}:{minute:02d}").do(self._run_status_update)
        elif day_of_week.lower() == "wednesday":
            schedule.every().wednesday.at(f"{hour:02d}:{minute:02d}").do(self._run_status_update)
        elif day_of_week.lower() == "thursday":
            schedule.every().thursday.at(f"{hour:02d}:{minute:02d}").do(self._run_status_update)
        elif day_of_week.lower() == "friday":
            schedule.every().friday.at(f"{hour:02d}:{minute:02d}").do(self._run_status_update)
        elif day_of_week.lower() == "saturday":
            schedule.every().saturday.at(f"{hour:02d}:{minute:02d}").do(self._run_status_update)
        elif day_of_week.lower() == "sunday":
            schedule.every().sunday.at(f"{hour:02d}:{minute:02d}").do(self._run_status_update)
        else:
            raise ValueError(f"Invalid day of week: {day_of_week}")
        
        logger.info(f"Scheduled status updates for {day_of_week} at {hour:02d}:{minute:02d}")
    
    def setup_biweekly_schedule(self, day_of_week: str = "monday", hour: int = 9, minute: int = 0):
        """Set up a bi-weekly schedule (every 2 weeks)"""
        # For bi-weekly, we'll use a custom approach since schedule doesn't support it directly
        schedule.clear()
        
        # Use a wrapper function to handle bi-weekly logic
        def biweekly_wrapper():
            return self._run_biweekly_check(day_of_week, hour, minute)
        
        # Check daily at the specified time if it's the right bi-weekly day
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(biweekly_wrapper)
        
        logger.info(f"Scheduled bi-weekly status updates for {day_of_week} at {hour:02d}:{minute:02d}")
    
    def _run_biweekly_check(self, target_day: str, hour: int, minute: int):
        """Check if today is the bi-weekly target day"""
        today = datetime.now()
        
        # Map day names to weekday numbers (0=Monday, 6=Sunday)
        day_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        target_weekday = day_map.get(target_day.lower())
        if target_weekday is None:
            logger.error(f"Invalid day: {target_day}")
            return
        
        # Check if today is the target weekday
        if today.weekday() != target_weekday:
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
                        logger.info(f"Skipping run - last run was {(today - last_run).days} days ago")
                        return
            except Exception as e:
                logger.warning(f"Could not read last run file: {e}")
        
        # Run the update and record the date
        self._run_status_update()
        
        with open(last_run_file, 'w') as f:
            f.write(today.isoformat())
    
    def _run_status_update(self):
        """Execute the status update script"""
        try:
            logger.info("Starting scheduled status update...")
            
            # Build command
            cmd = ["python3", str(self.script_path)]
            
            # Add config if it exists
            if self.config_path.exists():
                cmd.extend(["--config", str(self.config_path)])
            
            # Run the script
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info("✅ Status update completed successfully")
                logger.info(f"Output: {result.stdout}")
            else:
                logger.error(f"❌ Status update failed with exit code {result.returncode}")
                logger.error(f"Error output: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Status update timed out after 5 minutes")
        except Exception as e:
            logger.error(f"❌ Error running status update: {e}")
    
    def run_now(self):
        """Run status update immediately"""
        logger.info("Running status update immediately...")
        self._run_status_update()
    
    def start_scheduler(self):
        """Start the scheduler loop"""
        self.is_running = True
        logger.info("🚀 Scheduler started. Waiting for scheduled times...")
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("📛 Scheduler stopped by user")
        finally:
            self.is_running = False
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        logger.info("⏹️ Scheduler stopped")
    
    def list_jobs(self):
        """List all scheduled jobs"""
        jobs = schedule.get_jobs()
        if not jobs:
            logger.info("No jobs scheduled")
            return
        
        logger.info("Scheduled jobs:")
        for i, job in enumerate(jobs, 1):
            logger.info(f"  {i}. {job}")
    
    def load_config_schedule(self):
        """Load schedule configuration from config file"""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            return False
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            schedule_config = config.get('schedule', {})
            if not schedule_config.get('enabled', False):
                logger.info("Scheduling is disabled in config")
                return False
            
            day_of_week = schedule_config.get('day_of_week', 'monday')
            hour = schedule_config.get('hour', 9)
            minute = schedule_config.get('minute', 0)
            biweekly = schedule_config.get('biweekly', True)
            
            # Convert day number to day name if needed
            if isinstance(day_of_week, int):
                day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                day_of_week = day_names[day_of_week % 7]
            
            if biweekly:
                self.setup_biweekly_schedule(day_of_week, hour, minute)
            else:
                self.setup_schedule(day_of_week, hour, minute)
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading schedule config: {e}")
            return False

def main():
    """Main function for the scheduler"""
    parser = argparse.ArgumentParser(description='JIRA Status Update Scheduler')
    parser.add_argument('--script', default='jira_status_automation.py', help='Path to main script')
    parser.add_argument('--config', default='config.json', help='Path to config file')
    parser.add_argument('--day', default='monday', help='Day of week for updates')
    parser.add_argument('--hour', type=int, default=9, help='Hour for updates (24-hour format)')
    parser.add_argument('--minute', type=int, default=0, help='Minute for updates')
    parser.add_argument('--biweekly', action='store_true', help='Run bi-weekly instead of weekly')
    parser.add_argument('--run-now', action='store_true', help='Run status update immediately')
    parser.add_argument('--list-jobs', action='store_true', help='List scheduled jobs')
    parser.add_argument('--from-config', action='store_true', help='Load schedule from config file')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        scheduler = StatusUpdateScheduler(args.script, args.config)
        
        if args.run_now:
            scheduler.run_now()
            return 0
        
        if args.list_jobs:
            scheduler.list_jobs()
            return 0
        
        # Set up schedule
        if args.from_config:
            if not scheduler.load_config_schedule():
                logger.error("Failed to load schedule from config")
                return 1
        else:
            if args.biweekly:
                scheduler.setup_biweekly_schedule(args.day, args.hour, args.minute)
            else:
                scheduler.setup_schedule(args.day, args.hour, args.minute)
        
        # Start the scheduler
        scheduler.start_scheduler()
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
