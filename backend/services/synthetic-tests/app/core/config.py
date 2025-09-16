"""
Configuration for Synthetic Test Framework
"""

import os
from typing import Optional


class Settings:
    """Application settings for synthetic test framework"""
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/synthetic_tests")
    
    # Pub/Sub Configuration
    GOOGLE_CLOUD_PROJECT: Optional[str] = os.getenv("GOOGLE_CLOUD_PROJECT")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # Test Execution
    MAX_CONCURRENT_TESTS: int = int(os.getenv("MAX_CONCURRENT_TESTS", "10"))
    DEFAULT_TEST_TIMEOUT: int = int(os.getenv("DEFAULT_TEST_TIMEOUT", "300"))  # 5 minutes
    MAX_TEST_DURATION: int = int(os.getenv("MAX_TEST_DURATION", "1800"))  # 30 minutes
    
    # Webhook Configuration
    WEBHOOK_BASE_URL: str = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000/webhooks")
    WEBHOOK_SECRET: Optional[str] = os.getenv("WEBHOOK_SECRET")
    
    # Incident Management
    INCIDENT_API_URL: str = os.getenv("INCIDENT_API_URL", "http://localhost:8000/api/v1/incidents")
    
    # Redis for message caching
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


settings = Settings()
