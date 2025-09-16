"""
Configuration for StackStorm Synthetic Test Framework
"""

import os
from typing import Optional


class Settings:
    """Application settings for StackStorm synthetic test framework"""
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/stackstorm_tests")
    
    # StackStorm Configuration
    STACKSTORM_API_URL: str = os.getenv("STACKSTORM_API_URL", "http://stackstorm:9101")
    STACKSTORM_AUTH_URL: str = os.getenv("STACKSTORM_AUTH_URL", "http://stackstorm:9100")
    STACKSTORM_USERNAME: str = os.getenv("STACKSTORM_USERNAME", "st2admin")
    STACKSTORM_PASSWORD: str = os.getenv("STACKSTORM_PASSWORD", "st2admin")
    STACKSTORM_API_KEY: Optional[str] = os.getenv("STACKSTORM_API_KEY")
    STACKSTORM_VERIFY_SSL: bool = os.getenv("STACKSTORM_VERIFY_SSL", "false").lower() == "true"
    STACKSTORM_TIMEOUT: int = int(os.getenv("STACKSTORM_TIMEOUT", "30"))
    
    # Test Execution
    MAX_CONCURRENT_TESTS: int = int(os.getenv("MAX_CONCURRENT_TESTS", "10"))
    DEFAULT_TEST_TIMEOUT: int = int(os.getenv("DEFAULT_TEST_TIMEOUT", "300"))  # 5 minutes
    MAX_TEST_DURATION: int = int(os.getenv("MAX_TEST_DURATION", "1800"))  # 30 minutes
    
    # Incident Management
    INCIDENT_API_URL: str = os.getenv("INCIDENT_API_URL", "http://localhost:8000/api/v1/incidents")
    
    # Redis for caching
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


settings = Settings()
