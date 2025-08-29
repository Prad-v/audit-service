"""
Database Schema for Alerting Service

This module defines SQLAlchemy models for alert policies, providers, and alerts.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List

from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, Text, JSON, 
    ForeignKey, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class AlertPolicy(Base, TimestampMixin):
    """Alert policy table"""
    __tablename__ = "alert_policies"
    
    policy_id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    
    # Matching criteria
    rules = Column(JSON, nullable=False)
    match_all = Column(Boolean, nullable=False, default=True)
    
    # Alert configuration
    severity = Column(String(20), nullable=False, index=True)
    message_template = Column(Text, nullable=False)
    summary_template = Column(Text, nullable=False)
    
    # Timing and throttling
    time_window = Column(JSON, nullable=True)
    throttle_minutes = Column(Integer, nullable=False, default=0)
    max_alerts_per_hour = Column(Integer, nullable=False, default=10)
    
    # Provider configuration
    providers = Column(JSON, nullable=False)  # List of provider IDs
    
    # Metadata
    tenant_id = Column(String(255), nullable=False, index=True)
    created_by = Column(String(255), nullable=False, index=True)
    
    # Relationships
    alerts = relationship("Alert", back_populates="policy")
    
    __table_args__ = (
        CheckConstraint("severity IN ('critical', 'high', 'medium', 'low', 'info')", 
                       name='ck_alert_policies_severity'),
        Index('idx_alert_policies_tenant_enabled', 'tenant_id', 'enabled'),
        Index('idx_alert_policies_created_by', 'created_by'),
    )


class AlertProvider(Base, TimestampMixin):
    """Alert provider table"""
    __tablename__ = "alert_providers"
    
    provider_id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    provider_type = Column(String(50), nullable=False, index=True)
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    
    # Provider-specific configuration
    config = Column(JSON, nullable=False)
    
    # Metadata
    tenant_id = Column(String(255), nullable=False, index=True)
    created_by = Column(String(255), nullable=False, index=True)
    
    __table_args__ = (
        CheckConstraint("provider_type IN ('pagerduty', 'webhook', 'slack', 'email')", 
                       name='ck_alert_providers_type'),
        Index('idx_alert_providers_tenant_enabled', 'tenant_id', 'enabled'),
        Index('idx_alert_providers_type_enabled', 'provider_type', 'enabled'),
        Index('idx_alert_providers_created_by', 'created_by'),
    )


class Alert(Base, TimestampMixin):
    """Alert table"""
    __tablename__ = "alerts"
    
    alert_id = Column(String(255), primary_key=True)
    policy_id = Column(String(255), ForeignKey('alert_policies.policy_id'), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    status = Column(String(20), nullable=False, default='active', index=True)
    
    # Alert content
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    
    # Triggering event
    event_data = Column(JSON, nullable=False)
    event_id = Column(String(255), nullable=True, index=True)
    
    # Timing
    triggered_at = Column(DateTime(timezone=True), nullable=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(255), nullable=True, index=True)
    
    # Provider delivery status
    delivery_status = Column(JSON, nullable=False, default=dict)
    
    # Metadata
    tenant_id = Column(String(255), nullable=False, index=True)
    
    # Relationships
    policy = relationship("AlertPolicy", back_populates="alerts")
    
    __table_args__ = (
        CheckConstraint("severity IN ('critical', 'high', 'medium', 'low', 'info')", 
                       name='ck_alerts_severity'),
        CheckConstraint("status IN ('active', 'resolved', 'acknowledged', 'suppressed')", 
                       name='ck_alerts_status'),
        Index('idx_alerts_tenant_status', 'tenant_id', 'status'),
        Index('idx_alerts_tenant_severity', 'tenant_id', 'severity'),
        Index('idx_alerts_triggered_at', 'triggered_at'),
        Index('idx_alerts_policy_triggered', 'policy_id', 'triggered_at'),
    )


class AlertThrottle(Base, TimestampMixin):
    """Alert throttling table for rate limiting"""
    __tablename__ = "alert_throttles"
    
    throttle_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(String(255), ForeignKey('alert_policies.policy_id'), nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    
    # Throttling data
    last_alert_at = Column(DateTime(timezone=True), nullable=False)
    alert_count = Column(Integer, nullable=False, default=1)
    hour_start = Column(DateTime(timezone=True), nullable=False, index=True)  # Start of current hour
    
    __table_args__ = (
        Index('idx_alert_throttles_policy_hour', 'policy_id', 'hour_start'),
        Index('idx_alert_throttles_tenant_hour', 'tenant_id', 'hour_start'),
        UniqueConstraint('policy_id', 'hour_start', name='uq_alert_throttles_policy_hour'),
    )


class AlertSuppression(Base, TimestampMixin):
    """Alert suppression table for managing alert suppressions"""
    __tablename__ = "alert_suppressions"
    
    suppression_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(String(255), ForeignKey('alert_policies.policy_id'), nullable=False, index=True)
    tenant_id = Column(String(255), nullable=False, index=True)
    
    # Suppression criteria
    suppression_key = Column(String(500), nullable=False, index=True)  # Unique key for suppression
    reason = Column(Text, nullable=True)
    
    # Timing
    suppressed_until = Column(DateTime(timezone=True), nullable=False, index=True)
    created_by = Column(String(255), nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_alert_suppressions_policy_key', 'policy_id', 'suppression_key'),
        Index('idx_alert_suppressions_tenant_until', 'tenant_id', 'suppressed_until'),
        UniqueConstraint('policy_id', 'suppression_key', name='uq_alert_suppressions_policy_key'),
    )
