#!/usr/bin/env python3
"""
Simple script to run the FastAPI server
"""

import uvicorn
from main import app
from config import Config

if __name__ == "__main__":
    print("Starting Jira Status Automation API server...")
    Config.print_config()
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        app,
        host=Config.BACKEND_HOST,
        port=Config.BACKEND_PORT,
        reload=False,  # Disable auto-reload for stability
        log_level=Config.LOG_LEVEL.lower()
    )
