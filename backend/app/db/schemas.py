"""
SQLAlchemy database schemas for the audit log framework.

This module contains SQLAlchemy ORM models that define the database schema
with BigQuery-compatible design for easy migration.
"""

import uuid
from datetime import datetime, date
from typing import List

from sqlalchemy import (
    Column, String, DateTime, Date, Integer, Boolean, Text, JSON,
    ForeignKey, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, INET, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class TimestampMixin:
    """Mixin for timestamp fields."""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class AuditLog(Base, TimestampMixin):
    """
    Audit log table with partitioning support.
    
    This table is designed to be compatible with BigQuery schema
    and supports partitioning by date for performance.
    """
    __tablename__ = "audit_logs"
    
    # Primary key
    audit_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event metadata
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    event_type = Column(String(100), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False, default='success', index=True)
    
    # User and session information
    user_id = Column(String(255), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Resource information
    resource_type = Column(String(100), nullable=True, index=True)
    resource_id = Column(String(255), nullable=True, index=True)
    
    # Request/Response data (JSON fields for BigQuery compatibility)
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Multi-tenancy and service identification
    tenant_id = Column(String(255), nullable=False, index=True)
    service_name = Column(String(100), nullable=False, index=True)
    correlation_id = Column(String(255), nullable=True, index=True)
    
    # Data retention
    retention_period_days = Column(Integer, nullable=False, default=90)
    
    # Partitioning field (for BigQuery compatibility)
    partition_date = Column(Date, nullable=False, default=func.current_date(), index=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('retention_period_days > 0 AND retention_period_days <= 2555', 
                       name='ck_audit_logs_retention_period'),
        CheckConstraint("status IN ('success', 'error', 'warning', 'info')", 
                       name='ck_audit_logs_status'),
        Index('idx_audit_logs_tenant_timestamp', 'tenant_id', 'timestamp'),
        Index('idx_audit_logs_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_logs_event_timestamp', 'event_type', 'timestamp'),
        Index('idx_audit_logs_partition_tenant', 'partition_date', 'tenant_id'),
        Index('idx_audit_logs_correlation', 'correlation_id'),
        Index('idx_audit_logs_resource', 'resource_type', 'resource_id'),
        # GIN indexes for JSON fields (PostgreSQL specific)
        Index('idx_audit_logs_metadata_gin', 'metadata', postgresql_using='gin'),
        Index('idx_audit_logs_request_data_gin', 'request_data', postgresql_using='gin'),
    )


class Tenant(Base, TimestampMixin):
    """Tenant table for multi-tenancy support."""
    __tablename__ = "tenants"
    
    id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    settings = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="tenant", cascade="all, delete-orphan")
    retention_policies = relationship("RetentionPolicy", back_populates="tenant", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_tenants_active', 'is_active'),
    )


class User(Base, TimestampMixin):
    """User table for authentication."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    tenant_id = Column(String(255), ForeignKey('tenants.id'), nullable=False, index=True)
    roles = Column(ARRAY(String), nullable=False, default=list)
    is_active = Column(Boolean, nullable=False, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_users_tenant_active', 'tenant_id', 'is_active'),
        Index('idx_users_roles_gin', 'roles', postgresql_using='gin'),
    )


class APIKey(Base, TimestampMixin):
    """API key table for service authentication."""
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    tenant_id = Column(String(255), ForeignKey('tenants.id'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    permissions = Column(ARRAY(String), nullable=False, default=list)
    is_active = Column(Boolean, nullable=False, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="api_keys")
    user = relationship("User", back_populates="api_keys")
    
    __table_args__ = (
        Index('idx_api_keys_tenant_active', 'tenant_id', 'is_active'),
        Index('idx_api_keys_expires', 'expires_at'),
        Index('idx_api_keys_permissions_gin', 'permissions', postgresql_using='gin'),
    )


class RetentionPolicy(Base, TimestampMixin):
    """Retention policy table for data lifecycle management."""
    __tablename__ = "retention_policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), ForeignKey('tenants.id'), nullable=False, index=True)
    event_type = Column(String(100), nullable=True, index=True)
    resource_type = Column(String(100), nullable=True, index=True)
    retention_days = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="retention_policies")
    
    __table_args__ = (
        CheckConstraint('retention_days > 0 AND retention_days <= 2555', 
                       name='ck_retention_policies_days'),
        Index('idx_retention_policies_tenant_active', 'tenant_id', 'is_active'),
        Index('idx_retention_policies_event_type', 'event_type'),
        Index('idx_retention_policies_resource_type', 'resource_type'),
        # Unique constraint for tenant + event_type + resource_type combination
        UniqueConstraint('tenant_id', 'event_type', 'resource_type', 
                        name='uq_retention_policies_tenant_event_resource'),
    )


class ExportJob(Base, TimestampMixin):
    """Export job table for tracking data exports."""
    __tablename__ = "export_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    status = Column(String(50), nullable=False, default='pending', index=True)
    format = Column(String(20), nullable=False)
    query_params = Column(JSON, nullable=False)
    total_records = Column(Integer, nullable=True)
    processed_records = Column(Integer, nullable=True, default=0)
    file_path = Column(String(500), nullable=True)
    download_url = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed', 'expired')", 
                       name='ck_export_jobs_status'),
        CheckConstraint("format IN ('csv', 'json', 'xlsx')", 
                       name='ck_export_jobs_format'),
        Index('idx_export_jobs_tenant_status', 'tenant_id', 'status'),
        Index('idx_export_jobs_user_created', 'user_id', 'created_at'),
        Index('idx_export_jobs_expires', 'expires_at'),
    )


class AuditLogPartition(Base):
    """
    Table for managing audit log partitions.
    
    This table tracks partition information for maintenance operations.
    """
    __tablename__ = "audit_log_partitions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partition_name = Column(String(100), nullable=False, unique=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    record_count = Column(Integer, nullable=False, default=0)
    size_bytes = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_maintenance = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index('idx_audit_log_partitions_dates', 'start_date', 'end_date'),
        Index('idx_audit_log_partitions_active', 'is_active'),
    )


# Materialized view for daily audit statistics (PostgreSQL specific)
class DailyAuditSummary(Base):
    """
    Materialized view for daily audit statistics.
    
    This provides pre-aggregated statistics for performance.
    """
    __tablename__ = "daily_audit_summary"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False, index=True)
    service_name = Column(String(100), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    total_events = Column(Integer, nullable=False, default=0)
    unique_users = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    error_count = Column(Integer, nullable=False, default=0)
    warning_count = Column(Integer, nullable=False, default=0)
    avg_response_time_ms = Column(Integer, nullable=True)
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'service_name', 'event_type', 'date',
                        name='uq_daily_audit_summary'),
        Index('idx_daily_audit_summary_tenant_date', 'tenant_id', 'date'),
        Index('idx_daily_audit_summary_service_date', 'service_name', 'date'),
    )