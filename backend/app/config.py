"""
Configuration management for the audit log framework.

This module handles all configuration settings using Pydantic Settings
with support for environment variables and .env files.
"""

import os
from typing import Any, Dict, List, Optional, Union

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    url: str = Field(
        default="postgresql+asyncpg://audit_user:audit_password@localhost:5432/audit_logs",
        description="Database connection URL"
    )
    pool_size: int = Field(default=20, description="Connection pool size")
    max_overflow: int = Field(default=30, description="Maximum pool overflow")
    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    pool_recycle: int = Field(default=3600, description="Pool recycle time in seconds")
    echo: bool = Field(default=False, description="Enable SQL query logging")
    
    class Config:
        env_prefix = "DATABASE_"


class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    
    url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    pool_size: int = Field(default=10, description="Connection pool size")
    cache_ttl: int = Field(default=3600, description="Default cache TTL in seconds")
    max_connections: int = Field(default=50, description="Maximum connections")
    
    class Config:
        env_prefix = "REDIS_"


class NATSSettings(BaseSettings):
    """NATS configuration settings."""
    
    url: str = Field(
        default="nats://localhost:4222",
        description="NATS server URL"
    )
    cluster_id: str = Field(default="audit-cluster", description="NATS cluster ID")
    client_id: str = Field(default="audit-api", description="NATS client ID")
    max_reconnect: int = Field(default=10, description="Maximum reconnection attempts")
    reconnect_wait: int = Field(default=2, description="Reconnection wait time in seconds")
    
    class Config:
        env_prefix = "NATS_"


class SecuritySettings(BaseSettings):
    """Security and authentication settings."""
    
    secret_key: str = Field(
        default="your-super-secret-key-change-this-in-production",
        description="Secret key for JWT signing"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7, description="Refresh token expiration in days"
    )
    bcrypt_rounds: int = Field(default=12, description="Bcrypt hashing rounds")
    
    class Config:
        env_prefix = "SECURITY_"


class APISettings(BaseSettings):
    """API server configuration settings."""
    
    host: str = Field(default="0.0.0.0", description="API server host")
    port: int = Field(default=8000, description="API server port")
    workers: int = Field(default=4, description="Number of worker processes")
    reload: bool = Field(default=False, description="Enable auto-reload")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # CORS settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(
        default=True, description="Allow CORS credentials"
    )
    
    class Config:
        env_prefix = "API_"


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="json", description="Log format (json or text)")
    file: Optional[str] = Field(default=None, description="Log file path")
    rotation: str = Field(default="1 day", description="Log rotation interval")
    retention: str = Field(default="30 days", description="Log retention period")
    
    class Config:
        env_prefix = "LOG_"


class MonitoringSettings(BaseSettings):
    """Monitoring and metrics settings."""
    
    prometheus_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    prometheus_port: int = Field(default=9090, description="Prometheus metrics port")
    metrics_enabled: bool = Field(default=True, description="Enable custom metrics")
    health_check_interval: int = Field(
        default=30, description="Health check interval in seconds"
    )
    health_check_timeout: int = Field(
        default=10, description="Health check timeout in seconds"
    )
    
    class Config:
        env_prefix = "MONITORING_"


class RateLimitSettings(BaseSettings):
    """Rate limiting configuration."""
    
    enabled: bool = Field(default=True, description="Enable rate limiting")
    requests: int = Field(default=1000, description="Requests per window")
    window: int = Field(default=3600, description="Rate limit window in seconds")
    
    class Config:
        env_prefix = "RATE_LIMIT_"


class PaginationSettings(BaseSettings):
    """Pagination configuration."""
    
    default_page_size: int = Field(default=50, description="Default page size")
    max_page_size: int = Field(default=1000, description="Maximum page size")
    
    class Config:
        env_prefix = "PAGINATION_"


class ExportSettings(BaseSettings):
    """Export functionality settings."""
    
    max_records: int = Field(default=100000, description="Maximum records per export")
    timeout_seconds: int = Field(default=300, description="Export timeout in seconds")
    
    class Config:
        env_prefix = "EXPORT_"


class WorkerSettings(BaseSettings):
    """Background worker settings."""
    
    concurrency: int = Field(default=4, description="Worker concurrency")
    prefetch_count: int = Field(default=10, description="Message prefetch count")
    batch_size: int = Field(default=1000, description="Batch processing size")
    batch_timeout_seconds: int = Field(
        default=5, description="Batch timeout in seconds"
    )
    
    class Config:
        env_prefix = "WORKER_"


class RetentionSettings(BaseSettings):
    """Data retention settings."""
    
    default_retention_days: int = Field(
        default=90, description="Default retention period in days"
    )
    max_retention_days: int = Field(
        default=2555, description="Maximum retention period in days (7 years)"
    )
    cleanup_interval_hours: int = Field(
        default=24, description="Cleanup job interval in hours"
    )
    
    class Config:
        env_prefix = "RETENTION_"


class BigQuerySettings(BaseSettings):
    """BigQuery configuration for production."""
    
    project_id: Optional[str] = Field(default=None, description="GCP project ID")
    dataset: str = Field(default="audit_logs", description="BigQuery dataset")
    table: str = Field(default="events", description="BigQuery table")
    location: str = Field(default="US", description="BigQuery location")
    
    class Config:
        env_prefix = "BIGQUERY_"


class PubSubSettings(BaseSettings):
    """Pub/Sub configuration for production."""
    
    project_id: Optional[str] = Field(default=None, description="GCP project ID")
    topic: str = Field(default="audit-events", description="Pub/Sub topic")
    subscription: str = Field(default="audit-processor", description="Pub/Sub subscription")
    
    class Config:
        env_prefix = "PUBSUB_"


class FeatureFlags(BaseSettings):
    """Feature flags configuration."""
    
    export_enabled: bool = Field(default=True, description="Enable export functionality")
    batch_processing: bool = Field(default=True, description="Enable batch processing")
    real_time_updates: bool = Field(default=True, description="Enable real-time updates")
    advanced_search: bool = Field(default=True, description="Enable advanced search")
    
    class Config:
        env_prefix = "FEATURE_"


class Settings(BaseSettings):
    """Main application settings."""
    
    # Environment
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Component settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    nats: NATSSettings = Field(default_factory=NATSSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    api: APISettings = Field(default_factory=APISettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    pagination: PaginationSettings = Field(default_factory=PaginationSettings)
    export: ExportSettings = Field(default_factory=ExportSettings)
    worker: WorkerSettings = Field(default_factory=WorkerSettings)
    retention: RetentionSettings = Field(default_factory=RetentionSettings)
    bigquery: BigQuerySettings = Field(default_factory=BigQuerySettings)
    pubsub: PubSubSettings = Field(default_factory=PubSubSettings)
    features: FeatureFlags = Field(default_factory=FeatureFlags)
    
    @validator("environment")
    def validate_environment(cls, v: str) -> str:
        """Validate environment setting."""
        allowed = ["development", "staging", "production", "testing"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.environment == "testing"
    
    def get_database_url(self, async_driver: bool = True) -> str:
        """Get database URL with appropriate driver."""
        url = self.database.url
        if async_driver and "postgresql://" in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://")
        elif not async_driver and "postgresql+asyncpg://" in url:
            url = url.replace("postgresql+asyncpg://", "postgresql://")
        return url
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global settings
    settings = Settings()
    return settings