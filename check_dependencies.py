#!/usr/bin/env ./venv/bin/python
"""
Dependency check script for Jira Status Automation
Verifies that all required Python modules are available
"""

import sys
import importlib

def check_module(module_name, description=""):
    """Check if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name:<20} - {description}")
        return True
    except ImportError as e:
        print(f"❌ {module_name:<20} - {description}")
        print(f"   Error: {e}")
        return False

def main():
    """Check all required dependencies"""
    print("=" * 60)
    print("Jira Status Automation - Dependency Check")
    print("=" * 60)
    
    dependencies = [
        ("fastapi", "Web framework for the backend API"),
        ("uvicorn", "ASGI server for running FastAPI"),
        ("jira", "Jira Python library for API interactions"),
        ("requests", "HTTP library for API calls"),
        ("dateutil", "Date parsing utilities"),
        ("pydantic", "Data validation and settings management"),
    ]
    
    all_good = True
    
    for module_name, description in dependencies:
        if not check_module(module_name, description):
            all_good = False
    
    print("\n" + "=" * 60)
    
    if all_good:
        print("🎉 All dependencies are installed correctly!")
        print("✅ The application should run without dependency issues.")
        return 0
    else:
        print("❌ Some dependencies are missing or broken.")
        print("🔧 Run the following to fix dependency issues:")
        print("   ./venv/bin/pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
