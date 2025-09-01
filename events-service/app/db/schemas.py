"""
Database Schema for Events Service

This module defines SQLAlchemy models for cloud provider events, subscriptions, and alerting.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List

from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, Text, JSON, 
    ForeignKey, Index, CheckConstraint, UniqueConstraint, Enum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class CloudProvider(str, enum.Enum):
    """Supported cloud service providers"""
    GCP = "gcp"
    AWS = "aws"
    AZURE = "azure"
    OCI = "oci"


class EventType(str, enum.Enum):
    """Types of events supported"""
    GRAFANA_ALERT = "grafana_alert"
    CLOUD_ALERT = "cloud_alert"
    OUTAGE_STATUS = "outage_status"
    CUSTOM_EVENT = "custom_event"


class EventSeverity(str, enum.Enum):
    """Event severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class EventStatus(str, enum.Enum):
    """Event status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"


class CloudProject(Base, TimestampMixin):
    """Cloud project configuration"""
    __tablename__ = "cloud_projects"
    
    project_id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    cloud_provider = Column(Enum(CloudProvider), nullable=False, index=True)
    project_identifier = Column(String(255), nullable=False)  # GCP project ID, AWS account ID, etc.
    
    # Provider-specific configuration
    config = Column(JSON, nullable=False)  # API keys, regions, etc.
    
    # Subscription settings
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    auto_subscribe = Column(Boolean, nullable=False, default=True)
    
    # Metadata
    tenant_id = Column(String(255), nullable=False, index=True)
    created_by = Column(String(255), nullable=False, index=True)
    
    # Relationships
    subscriptions = relationship("EventSubscription", back_populates="project")
    events = relationship("CloudEvent", back_populates="project")
    
    __table_args__ = (
        Index('idx_cloud_projects_tenant_enabled', 'tenant_id', 'enabled'),
        Index('idx_cloud_projects_provider', 'cloud_provider'),
        Index('idx_cloud_projects_created_by', 'created_by'),
    )


class EventSubscription(Base, TimestampMixin):
    """Event subscription configuration"""
    __tablename__ = "event_subscriptions"
    
    subscription_id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Project association
    project_id = Column(String(255), ForeignKey('cloud_projects.project_id'), nullable=False, index=True)
    
    # Event type and service filtering
    event_types = Column(JSON, nullable=False)  # List of event types to subscribe to
    services = Column(JSON, nullable=False)  # List of services to monitor
    regions = Column(JSON, nullable=True)  # Specific regions to monitor
    
    # Filtering criteria
    severity_levels = Column(JSON, nullable=False)  # List of severity levels to include
    custom_filters = Column(JSON, nullable=True)  # Custom filtering criteria
    
    # Subscription settings
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    auto_resolve = Column(Boolean, nullable=False, default=True)
    resolve_after_hours = Column(Integer, nullable=False, default=24)
    
    # Metadata
    tenant_id = Column(String(255), nullable=False, index=True)
    created_by = Column(String(255), nullable=False, index=True)
    
    # Relationships
    project = relationship("CloudProject", back_populates="subscriptions")
    events = relationship("CloudEvent", back_populates="subscription")
    
    __table_args__ = (
        Index('idx_event_subscriptions_tenant_enabled', 'tenant_id', 'enabled'),
        Index('idx_event_subscriptions_project', 'project_id'),
        Index('idx_event_subscriptions_created_by', 'created_by'),
    )


class CloudEvent(Base, TimestampMixin):
    """Cloud provider event"""
    __tablename__ = "cloud_events"
    
    event_id = Column(String(255), primary_key=True)
    external_id = Column(String(255), nullable=True, index=True)  # External event ID from provider
    
    # Event classification
    event_type = Column(Enum(EventType), nullable=False, index=True)
    severity = Column(Enum(EventSeverity), nullable=False, index=True)
    status = Column(Enum(EventStatus), nullable=False, default=EventStatus.ACTIVE, index=True)
    
    # Source information
    cloud_provider = Column(Enum(CloudProvider), nullable=False, index=True)
    project_id = Column(String(255), ForeignKey('cloud_projects.project_id'), nullable=True, index=True)
    subscription_id = Column(String(255), ForeignKey('event_subscriptions.subscription_id'), nullable=True, index=True)
    
    # Event details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    
    # Service and resource information
    service_name = Column(String(255), nullable=True, index=True)
    resource_type = Column(String(255), nullable=True, index=True)
    resource_id = Column(String(255), nullable=True, index=True)
    region = Column(String(100), nullable=True, index=True)
    
    # Timing
    event_time = Column(DateTime(timezone=True), nullable=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(255), nullable=True, index=True)
    
    # Raw event data
    raw_data = Column(JSON, nullable=False)  # Original event data from provider
    
    # Alerting
    alert_id = Column(String(255), nullable=True, index=True)  # Associated alert if any
    
    # Metadata
    tenant_id = Column(String(255), nullable=False, index=True)
    
    # Relationships
    project = relationship("CloudProject", back_populates="events")
    subscription = relationship("EventSubscription", back_populates="events")
    
    __table_args__ = (
        Index('idx_cloud_events_tenant_status', 'tenant_id', 'status'),
        Index('idx_cloud_events_tenant_severity', 'tenant_id', 'severity'),
        Index('idx_cloud_events_event_time', 'event_time'),
        Index('idx_cloud_events_provider_type', 'cloud_provider', 'event_type'),
        Index('idx_cloud_events_service_region', 'service_name', 'region'),
    )


class AlertPolicy(Base, TimestampMixin):
    """Alert policy for events"""
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
    """Alert provider configuration"""
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
    """Alert instance"""
    __tablename__ = "alerts"
    
    alert_id = Column(String(255), primary_key=True)
    policy_id = Column(String(255), ForeignKey('alert_policies.policy_id'), nullable=False, index=True)
    event_id = Column(String(255), ForeignKey('cloud_events.event_id'), nullable=True, index=True)
    severity = Column(String(20), nullable=False, index=True)
    status = Column(String(20), nullable=False, default='active', index=True)
    
    # Alert content
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    
    # Triggering event
    event_data = Column(JSON, nullable=False)
    
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


class EventProcessor(Base, TimestampMixin):
    """Event processor configuration for transforming and enriching events"""
    __tablename__ = "event_processors"
    
    processor_id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Processor type and configuration
    processor_type = Column(String(50), nullable=False, index=True)  # transformer, enricher, filter, router
    config = Column(JSON, nullable=False)  # Processor-specific configuration
    
    # Processing order and dependencies
    order = Column(Integer, nullable=False, default=0, index=True)
    depends_on = Column(JSON, nullable=True)  # List of processor IDs this depends on
    
    # Event filtering criteria
    event_types = Column(JSON, nullable=True)  # List of event types to process
    severity_levels = Column(JSON, nullable=True)  # List of severity levels to process
    cloud_providers = Column(JSON, nullable=True)  # List of cloud providers to process
    
    # Processing rules and conditions
    conditions = Column(JSON, nullable=True)  # Conditional logic for when to apply processor
    transformations = Column(JSON, nullable=False)  # Transformation rules and mappings
    
    # Status and monitoring
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    last_processed = Column(DateTime(timezone=True), nullable=True)
    processed_count = Column(Integer, nullable=False, default=0)
    error_count = Column(Integer, nullable=False, default=0)
    
    # Metadata
    tenant_id = Column(String(255), nullable=False, index=True)
    created_by = Column(String(255), nullable=False, index=True)
    
    __table_args__ = (
        CheckConstraint("processor_type IN ('transformer', 'enricher', 'filter', 'router')", 
                       name='ck_event_processors_type'),
        Index('idx_event_processors_tenant_enabled', 'tenant_id', 'enabled'),
        Index('idx_event_processors_type_enabled', 'processor_type', 'enabled'),
        Index('idx_event_processors_order', 'order'),
        Index('idx_event_processors_created_by', 'created_by'),
    )
