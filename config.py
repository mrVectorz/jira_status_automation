"""
Configuration module for Jira Status Automation
Handles environment variables and default settings
"""

import os
from typing import List

class Config:
    """Application configuration class"""
    
    # Backend server configuration
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    
    # Frontend configuration
    FRONTEND_HOST: str = os.getenv("FRONTEND_HOST", "localhost")
    FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "3001"))  # Changed default to 3001
    
    # CORS origins - automatically configured based on frontend settings
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Get CORS origins based on frontend configuration"""
        origins = [
            f"http://{self.FRONTEND_HOST}:{self.FRONTEND_PORT}",
            f"http://127.0.0.1:{self.FRONTEND_PORT}",
            f"http://localhost:{self.FRONTEND_PORT}"
        ]
        
        # Add additional origins from environment variable
        additional_origins = os.getenv("CORS_ORIGINS", "")
        if additional_origins:
            origins.extend([origin.strip() for origin in additional_origins.split(",")])
        
        return list(set(origins))  # Remove duplicates
    
    # API configuration
    API_TITLE: str = os.getenv("API_TITLE", "Jira Status Automation API")
    API_DESCRIPTION: str = os.getenv("API_DESCRIPTION", "REST API for retrieving comprehensive Jira issue reports")
    API_VERSION: str = os.getenv("API_VERSION", "1.0.0")
    
    # Request timeout settings
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "120"))  # 2 minutes default
    
    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def get_backend_url(cls) -> str:
        """Get the full backend URL"""
        return f"http://{cls.BACKEND_HOST}:{cls.BACKEND_PORT}"
    
    @classmethod
    def get_frontend_url(cls) -> str:
        """Get the full frontend URL"""
        return f"http://{cls.FRONTEND_HOST}:{cls.FRONTEND_PORT}"
    
    @classmethod
    def print_config(cls) -> None:
        """Print current configuration"""
        print("=" * 50)
        print("Jira Status Automation - Configuration")
        print("=" * 50)
        print(f"Backend URL:  {cls.get_backend_url()}")
        print(f"Frontend URL: {cls.get_frontend_url()}")
        print(f"CORS Origins: {', '.join(cls().CORS_ORIGINS)}")
        print(f"Log Level:    {cls.LOG_LEVEL}")
        print("=" * 50)

