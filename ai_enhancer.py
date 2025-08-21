#!/usr/bin/env python3
"""
AI Enhancement Module for JIRA Status Reports

This module adds AI-powered insights and summaries to status reports using:
1. Cursor IDE AI Agent integration
2. Google Gemini via Selenium automation
3. Structured data export for other AI tools
"""

import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import asdict
from datetime import datetime

# Selenium imports (optional)
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

logger = logging.getLogger(__name__)

class AIEnhancer:
    """AI enhancement for JIRA status reports"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.ai_enabled = self.config.get('ai_enhancement', {}).get('enabled', False)
        self.cursor_integration = self.config.get('ai_enhancement', {}).get('cursor_integration', True)
        self.gemini_integration = self.config.get('ai_enhancement', {}).get('gemini_selenium', False)
        
    def enhance_report(self, tasks: List, summary: Dict, output_dir: str = "./reports") -> Dict:
        """Enhance the status report with AI insights"""
        if not self.ai_enabled:
            logger.info("AI enhancement disabled, skipping...")
            return {"ai_summary": "AI enhancement disabled"}
        
        logger.info("🤖 Enhancing report with AI insights...")
        
        # Prepare structured data for AI processing
        ai_data = self._prepare_ai_data(tasks, summary)
        
        # Save structured data for Cursor integration
        if self.cursor_integration:
            cursor_file = self._save_cursor_data(ai_data, output_dir)
            logger.info(f"📋 Cursor AI data saved to: {cursor_file}")
        
        # Generate Gemini insights if enabled
        gemini_insights = {}
        if self.gemini_integration and SELENIUM_AVAILABLE:
            try:
                gemini_insights = self._get_gemini_insights(ai_data)
            except Exception as e:
                logger.error(f"Gemini integration failed: {e}")
        
        return {
            "ai_summary": gemini_insights.get("summary", "AI processing completed"),
            "cursor_data_file": cursor_file if self.cursor_integration else None,
            "insights": gemini_insights.get("insights", []),
            "recommendations": gemini_insights.get("recommendations", [])
        }
    
    def _prepare_ai_data(self, tasks: List, summary: Dict) -> Dict:
        """Prepare structured data for AI analysis"""
        
        # Convert tasks to serializable format
        tasks_data = []
        for task in tasks:
            task_dict = asdict(task) if hasattr(task, '__dict__') else {
                'key': getattr(task, 'key', ''),
                'summary': getattr(task, 'summary', ''),
                'status': getattr(task, 'status', ''),
                'assignee': getattr(task, 'assignee', ''),
                'priority': getattr(task, 'priority', ''),
                'updated': getattr(task, 'updated', datetime.now()).isoformat(),
                'project': getattr(task, 'project', ''),
                'issue_type': getattr(task, 'issue_type', ''),
                'description': getattr(task, 'description', '')[:200]  # Truncate for AI
            }
            tasks_data.append(task_dict)
        
        return {
            "report_date": datetime.now().isoformat(),
            "summary": summary,
            "tasks": tasks_data,
            "ai_prompt": self._generate_ai_prompt(summary, tasks_data)
        }
    
    def _generate_ai_prompt(self, summary: Dict, tasks: List[Dict]) -> str:
        """Generate a comprehensive prompt for AI analysis"""
        
        prompt = f"""# JIRA Status Report Analysis Request

## Overview
Please analyze this bi-weekly JIRA status report and provide insights:

## Summary Statistics
- Total Tasks: {summary.get('total_tasks', 0)}
- Status Distribution: {summary.get('by_status', {})}
- Active Projects: {len(summary.get('by_project', {}))}
- Team Members: {len(summary.get('by_assignee', {}))}

## Recent Tasks
"""
        
        # Add recent tasks for context
        for i, task in enumerate(tasks[:10], 1):  # Limit to top 10 for prompt size
            prompt += f"""
{i}. **{task['key']}** - {task['summary']}
   - Status: {task['status']}
   - Assignee: {task['assignee']}
   - Priority: {task['priority']}
   - Description: {task['description'][:100]}...
"""
        
        prompt += """

## Analysis Request
Please provide:

1. **Executive Summary** (2-3 sentences about overall team progress)

2. **Key Insights** (3-5 bullet points about trends, blockers, or notable patterns)

3. **Team Performance** (observations about workload distribution and productivity)

4. **Recommendations** (3-5 actionable suggestions for improving team efficiency)

5. **Risk Assessment** (any potential blockers or concerns to escalate)

Please format your response in clear, business-appropriate language suitable for management presentations.
"""
        
        return prompt
    
    def _save_cursor_data(self, ai_data: Dict, output_dir: str) -> str:
        """Save structured data for Cursor AI integration"""
        
        cursor_dir = Path(output_dir) / "cursor_ai"
        cursor_dir.mkdir(exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cursor_file = cursor_dir / f"jira_analysis_{timestamp}.json"
        
        # Save the AI data
        with open(cursor_file, 'w', encoding='utf-8') as f:
            json.dump(ai_data, f, indent=2, default=str)
        
        # Also create a .md file with the prompt for easy copy-paste
        prompt_file = cursor_dir / f"cursor_prompt_{timestamp}.md"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(ai_data['ai_prompt'])
        
        # Create instructions file
        instructions_file = cursor_dir / "CURSOR_INSTRUCTIONS.md"
        if not instructions_file.exists():
            with open(instructions_file, 'w', encoding='utf-8') as f:
                f.write("""# Cursor AI Integration Instructions

## How to Use with Cursor IDE

1. **Open the latest prompt file** in Cursor IDE:
   ```
   cursor_prompt_YYYYMMDD_HHMMSS.md
   ```

2. **Select all content** (Ctrl+A / Cmd+A)

3. **Send to Cursor AI** using one of these methods:
   - Press `Ctrl+K` (Cmd+K on Mac) to open Cursor AI
   - Use the "Ask Cursor" command in the command palette
   - Right-click and select "Ask Cursor"

4. **Ask Cursor to analyze** with a prompt like:
   ```
   Please analyze this JIRA status report data and provide insights as requested in the prompt.
   ```

5. **Save the Cursor AI response** for automatic integration:
   - Copy the complete Cursor AI response
   - Create a new file named `cursor_response_YYYYMMDD_HHMMSS.md` in this directory
   - Paste the response content into the file
   - Re-run the JIRA automation tool - it will automatically detect and integrate the response!

## Alternative: Manual Integration

If you don't save the response file, you can still:
- Copy the AI response and paste it into your status report or presentation manually

## Alternative: Use JSON Data

You can also use the JSON file (`jira_analysis_*.json`) for:
- Custom analysis scripts
- Integration with other AI tools
- Data visualization tools
- Further processing

## Tips
- Review AI insights before including in official reports
- Combine AI insights with your domain knowledge
- Use AI suggestions as starting points for deeper analysis
- The tool automatically finds the latest response file based on timestamp
- Response files should contain the full Cursor AI analysis including all requested sections
""")
        
        logger.info(f"📋 Cursor integration files created:")
        logger.info(f"   Prompt: {prompt_file}")
        logger.info(f"   Data: {cursor_file}")
        logger.info(f"   Instructions: {instructions_file}")
        
        return str(prompt_file)
    
    def _get_gemini_insights(self, ai_data: Dict) -> Dict:
        """Get insights from Google Gemini using Selenium automation"""
        
        if not SELENIUM_AVAILABLE:
            logger.error("Selenium not available for Gemini integration")
            return {}
        
        logger.info("🚀 Starting Gemini Selenium automation...")
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        # chrome_options.add_argument("--headless")  # Comment out to see browser
        
        try:
            # Set up the driver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Navigate to Gemini
            logger.info("Opening Gemini web interface...")
            driver.get("https://gemini.google.com")
            
            # Wait for page to load
            time.sleep(3)
            
            # You might need to handle login here
            logger.info("⚠️  Please ensure you're logged into Gemini in this browser window")
            logger.info("Press Enter when ready to continue...")
            input()  # Wait for user confirmation
            
            # Find the text input area
            wait = WebDriverWait(driver, 20)
            
            # Look for common Gemini input selectors
            input_selectors = [
                "textarea[aria-label*='message']",
                "textarea[placeholder*='message']",
                "div[contenteditable='true']",
                ".input-area textarea",
                "[data-testid='input-area']"
            ]
            
            text_input = None
            for selector in input_selectors:
                try:
                    text_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except:
                    continue
            
            if not text_input:
                logger.error("Could not find Gemini input area")
                return {}
            
            # Clear any existing text and input our prompt
            logger.info("Sending prompt to Gemini...")
            text_input.clear()
            text_input.send_keys(ai_data['ai_prompt'])
            
            # Find and click submit button
            submit_selectors = [
                "button[aria-label*='send']",
                "button[type='submit']",
                ".send-button",
                "[data-testid='send-button']"
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if submit_button:
                submit_button.click()
            else:
                logger.warning("Could not find submit button, please submit manually")
                input("Press Enter after submitting the prompt...")
            
            # Wait for response
            logger.info("Waiting for Gemini response...")
            time.sleep(10)  # Give Gemini time to process
            
            # Try to extract the response
            response_selectors = [
                ".response-content",
                ".message-content",
                "[data-testid='response']",
                ".assistant-message"
            ]
            
            response_text = ""
            for selector in response_selectors:
                try:
                    response_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if response_elements:
                        response_text = response_elements[-1].text  # Get the latest response
                        break
                except:
                    continue
            
            if not response_text:
                logger.warning("Could not automatically extract response")
                logger.info("Please copy the Gemini response manually")
                response_text = input("Paste Gemini response here: ")
            
            # Parse the response
            insights = self._parse_gemini_response(response_text)
            
            logger.info("✅ Gemini analysis completed")
            return insights
            
        except Exception as e:
            logger.error(f"Gemini automation error: {e}")
            return {}
        finally:
            try:
                driver.quit()
            except:
                pass
    
    def _parse_gemini_response(self, response_text: str) -> Dict:
        """Parse Gemini response into structured insights"""
        
        try:
            # Simple parsing - you might want to make this more sophisticated
            lines = response_text.split('\n')
            
            insights = {
                "summary": "",
                "insights": [],
                "recommendations": [],
                "full_response": response_text
            }
            
            current_section = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detect sections
                if "executive summary" in line.lower():
                    current_section = "summary"
                elif "insights" in line.lower() or "key findings" in line.lower():
                    current_section = "insights"
                elif "recommendations" in line.lower():
                    current_section = "recommendations"
                elif line.startswith(('•', '-', '*')) or line.startswith(tuple('123456789')):
                    # This is a bullet point
                    if current_section == "insights":
                        insights["insights"].append(line.lstrip('•-* ').lstrip('123456789. '))
                    elif current_section == "recommendations":
                        insights["recommendations"].append(line.lstrip('•-* ').lstrip('123456789. '))
                elif current_section == "summary" and len(line) > 20:
                    # Likely part of the summary
                    insights["summary"] += line + " "
            
            # Clean up summary
            insights["summary"] = insights["summary"].strip()
            
            return insights
            
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            return {"full_response": response_text, "parsing_error": str(e)}

def load_cursor_ai_response(output_dir: str = "./reports") -> Optional[Dict]:
    """Load the latest Cursor AI response file if it exists"""
    cursor_dir = Path(output_dir) / "cursor_ai"
    
    # Look for response files
    response_files = list(cursor_dir.glob("cursor_response_*.md"))
    if not response_files:
        return None
    
    # Get the latest response file
    latest_response = max(response_files, key=lambda f: f.stat().st_mtime)
    
    logger.info(f"📖 Loading Cursor AI response from: {latest_response}")
    
    try:
        with open(latest_response, 'r', encoding='utf-8') as f:
            cursor_response = f.read()
        
        return integrate_cursor_ai_response(cursor_response, output_dir)
    except Exception as e:
        logger.error(f"Error loading Cursor AI response: {e}")
        return None

def integrate_cursor_ai_response(cursor_response: str, output_dir: str = "./reports") -> Dict:
    """Parse and structure Cursor AI response"""
    
    logger.info("🤖 Processing Cursor AI response...")
    
    # Parse the response into structured sections
    sections = {
        "executive_summary": "",
        "key_insights": [],
        "team_performance": "",
        "recommendations": [],
        "risk_assessment": "",
        "full_response": cursor_response
    }
    
    lines = cursor_response.split('\n')
    current_section = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Detect section headers (must start with ## to be a header)
        lower_line = line.lower()
        is_header = line.startswith('##')
        
        if is_header and any(phrase in lower_line for phrase in ["executive summary", "summary"]):
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content)
            current_section = "executive_summary"
            current_content = []
        elif is_header and any(phrase in lower_line for phrase in ["key insights", "insights", "findings"]):
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content)
            current_section = "key_insights"
            current_content = []
        elif is_header and any(phrase in lower_line for phrase in ["team performance", "performance"]):
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content)
            current_section = "team_performance"
            current_content = []
        elif is_header and any(phrase in lower_line for phrase in ["recommendations", "suggestions"]):
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content)
            current_section = "recommendations"
            current_content = []
        elif is_header and any(phrase in lower_line for phrase in ["risk assessment", "risks", "concerns"]):
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content)
            current_section = "risk_assessment"
            current_content = []
        else:
            # This is content for the current section (skip empty lines and non-header lines starting with #)
            if current_section and line and not line.startswith('#'):
                current_content.append(line)
    
    # Don't forget the last section
    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content)
    
    # Debug logging (can be uncommented for troubleshooting)
    # logger.debug(f"Parsed sections: {list(sections.keys())}")
    # for section, content in sections.items():
    #     logger.debug(f"Section {section}: {repr(content[:200])}")
    
    # Extract bullet points from insights and recommendations
    for section in ["key_insights", "recommendations"]:
        content = sections.get(section, "")
        if isinstance(content, str):
            bullet_points = []
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith(('•', '-', '*')) or any(line.startswith(f'{i}.') for i in range(1, 20)):
                    # Clean bullet point
                    clean_point = line.lstrip('•-*0123456789. ').strip()
                    if clean_point:
                        bullet_points.append(clean_point)
                elif line and not any(phrase in line.lower() for phrase in ["insights", "recommendations", "key", "assessment"]):
                    # Regular line that might be a bullet point without formatting
                    bullet_points.append(line)
            # logger.debug(f"Parsed {section}: {bullet_points}")  # Debug logging
            sections[section] = bullet_points
    
    return sections

def create_ai_enhanced_report(tasks: List, summary: Dict, ai_insights: Dict, output_dir: str) -> str:
    """Create an enhanced report with AI insights"""
    
    report_date = datetime.now().strftime("%Y-%m-%d")
    filename = f"ai_enhanced_status_update_{report_date}.md"
    filepath = Path(output_dir) / filename
    
    # Handle different types of AI insights
    executive_summary = ""
    ai_insights_section = ""
    ai_recommendations = ""
    team_performance = ""
    risk_assessment = ""
    
    if ai_insights:
        # Handle structured AI response (from Cursor AI integration)
        if 'executive_summary' in ai_insights:
            executive_summary = ai_insights.get('executive_summary', '')
        elif 'ai_summary' in ai_insights:
            executive_summary = ai_insights.get('ai_summary', '')
        else:
            executive_summary = "AI analysis completed - see detailed sections below"
        
        # Handle insights
        insights = ai_insights.get('key_insights', ai_insights.get('insights', []))
        if insights:
            if isinstance(insights, list):
                ai_insights_section = "\n".join([f"- {insight}" for insight in insights])
            else:
                ai_insights_section = str(insights)
        
        # Handle recommendations
        recommendations = ai_insights.get('recommendations', [])
        if recommendations:
            if isinstance(recommendations, list):
                ai_recommendations = "\n".join([f"- {rec}" for rec in recommendations])
            else:
                ai_recommendations = str(recommendations)
        
        # Handle team performance
        team_performance = ai_insights.get('team_performance', '')
        
        # Handle risk assessment
        risk_assessment = ai_insights.get('risk_assessment', '')

    content = f"""# AI-Enhanced Bi-Weekly Status Update - {report_date}

## 🤖 AI Executive Summary

{executive_summary if executive_summary else 'AI analysis not available'}

## 📊 Key Statistics

- **Total Tasks Reviewed:** {summary['total_tasks']}
- **Story Points Progress:** {summary['story_points']['completed']}/{summary['story_points']['total']} completed
- **Active Projects:** {len(summary['by_project'])}
- **Team Members Active:** {len(summary['by_assignee'])}

## 🎯 Status Breakdown

"""
    
    # Add status breakdown with emojis
    for status, count in summary['by_status'].items():
        percentage = (count / summary['total_tasks'] * 100) if summary['total_tasks'] > 0 else 0
        emoji_map = {
            'completed': '✅',
            'in_progress': '🚧',
            'blocked': '🚫',
            'todo': '📝',
            'other': '❓'
        }
        emoji = emoji_map.get(status.lower(), '❓')
        content += f"- {emoji} **{status.title()}:** {count} tasks ({percentage:.1f}%)\n"
    
    # Add AI insights if available
    if ai_insights_section:
        content += "\n## 🔍 AI-Generated Insights\n\n"
        content += ai_insights_section + "\n"
    
    # Add team performance analysis if available
    if team_performance:
        content += "\n## 👥 AI Team Performance Analysis\n\n"
        content += team_performance + "\n"
    
    # Add AI recommendations if available
    if ai_recommendations:
        content += "\n## 💡 AI Recommendations\n\n"
        content += ai_recommendations + "\n"
    
    # Add risk assessment if available
    if risk_assessment:
        content += "\n## ⚠️ AI Risk Assessment\n\n"
        content += risk_assessment + "\n"
    
    # Add rest of the standard report content...
    content += f"\n## 📈 Project Breakdown\n\n"
    for project, count in sorted(summary['by_project'].items()):
        content += f"- **{project}:** {count} tasks\n"
    
    content += f"\n## 👥 Team Activity\n\n"
    for assignee, count in sorted(summary['by_assignee'].items(), key=lambda x: x[1], reverse=True):
        content += f"- **{assignee}:** {count} tasks\n"
    
    # Add recent highlights
    content += f"\n## 🔥 Recent Highlights\n\n"
    if summary['timeline']['this_week']:
        for task in summary['timeline']['this_week'][:10]:
            content += f"- **[{task.key}]** {task.summary}\n"
            content += f"  - Status: {task.status}\n"
            content += f"  - Assignee: {task.assignee or 'Unassigned'}\n"
            content += f"  - Updated: {task.updated.strftime('%Y-%m-%d %H:%M')}\n\n"
    
    content += f"\n---\n*AI-Enhanced report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return str(filepath)
