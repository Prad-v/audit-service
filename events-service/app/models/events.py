"""
Events Models for Cloud Provider Events and Monitoring

This module defines Pydantic models for cloud provider events, subscriptions, and alerting.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, validator, model_validator, field_validator
import re


class CloudProvider(str, Enum):
    """Supported cloud service providers"""
    GCP = "gcp"
    AWS = "aws"
    AZURE = "azure"
    OCI = "oci"


class EventType(str, Enum):
    """Types of events supported"""
    GRAFANA_ALERT = "grafana_alert"
    CLOUD_ALERT = "cloud_alert"
    OUTAGE_STATUS = "outage_status"
    CUSTOM_EVENT = "custom_event"


class EventSeverity(str, Enum):
    """Event severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class EventStatus(str, Enum):
    """Event status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertProviderType(str, Enum):
    """Supported alert providers"""
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"
    SLACK = "slack"
    EMAIL = "email"


class AlertStatus(str, Enum):
    """Alert status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"


class TimeWindow(BaseModel):
    """Time window for alert policies"""
    start_time: str = Field(..., description="Start time in HH:MM format")
    end_time: str = Field(..., description="End time in HH:MM format")
    days_of_week: List[int] = Field(default=[0, 1, 2, 3, 4, 5, 6], description="Days of week (0=Monday, 6=Sunday)")
    timezone: str = Field(default="UTC", description="Timezone for time calculations")

    @validator('start_time', 'end_time')
    def validate_time_format(cls, v):
        if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', v):
            raise ValueError('Time must be in HH:MM format')
        return v

    @validator('days_of_week')
    def validate_days_of_week(cls, v):
        if not all(0 <= day <= 6 for day in v):
            raise ValueError('Days must be between 0 and 6')
        return v


class AlertRuleConfig(BaseModel):
    """Alert rule configuration for policies"""
    field: str = Field(..., description="Field to match (e.g., event_type, severity, service_name)")
    operator: str = Field(..., description="Comparison operator (eq, ne, gt, lt, gte, lte, in, not_in, contains, regex)")
    value: Union[str, int, float, bool, List[Any]] = Field(..., description="Value to compare against")
    case_sensitive: bool = Field(default=True, description="Case sensitive matching")

    @validator('operator')
    def validate_operator(cls, v):
        valid_operators = ['eq', 'ne', 'gt', 'lt', 'gte', 'lte', 'in', 'not_in', 'contains', 'regex']
        if v not in valid_operators:
            raise ValueError(f'Operator must be one of: {valid_operators}')
        return v


class CloudProject(BaseModel):
    """Cloud project configuration"""
    project_id: str = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    cloud_provider: CloudProvider = Field(..., description="Cloud service provider")
    project_identifier: str = Field(..., description="Provider-specific project identifier")
    
    # Provider-specific configuration
    config: Dict[str, Any] = Field(..., description="Provider-specific configuration (API keys, regions, etc.)")
    
    # Subscription settings
    enabled: bool = Field(default=True, description="Whether project is enabled")
    auto_subscribe: bool = Field(default=True, description="Auto-subscribe to events")
    
    # Metadata
    tenant_id: str = Field(..., description="Tenant ID")
    created_by: str = Field(..., description="User who created the project")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "gcp-project-001",
                "name": "Production GCP Project",
                "description": "Main production environment",
                "cloud_provider": "gcp",
                "project_identifier": "my-gcp-project-123",
                "config": {
                    "api_key": "your-gcp-api-key",
                    "regions": ["us-central1", "us-east1"],
                    "services": ["compute", "storage", "database"]
                },
                "enabled": True,
                "auto_subscribe": True,
                "tenant_id": "default",
                "created_by": "admin"
            }
        }


class EventSubscription(BaseModel):
    """Event subscription configuration"""
    subscription_id: str = Field(..., description="Unique subscription identifier")
    name: str = Field(..., description="Subscription name")
    description: Optional[str] = Field(None, description="Subscription description")
    
    # Project association
    project_id: str = Field(..., description="Associated cloud project ID")
    
    # Event type and service filtering
    event_types: List[str] = Field(..., description="List of event types to subscribe to")
    services: List[str] = Field(..., description="List of services to monitor")
    regions: Optional[List[str]] = Field(None, description="Specific regions to monitor")
    
    # Filtering criteria
    severity_levels: List[str] = Field(..., description="List of severity levels to include")
    custom_filters: Optional[Dict[str, Any]] = Field(None, description="Custom filtering criteria")
    
    # Subscription settings
    enabled: bool = Field(default=True, description="Whether subscription is enabled")
    auto_resolve: bool = Field(default=True, description="Auto-resolve events")
    resolve_after_hours: int = Field(default=24, description="Hours after which to auto-resolve")
    
    # Metadata
    tenant_id: str = Field(..., description="Tenant ID")
    created_by: str = Field(..., description="User who created the subscription")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "subscription_id": "sub-001",
                "name": "Critical Alerts Subscription",
                "description": "Subscribe to critical alerts from GCP",
                "project_id": "gcp-project-001",
                "event_types": ["cloud_alert", "outage_status"],
                "services": ["compute", "storage"],
                "regions": ["us-central1"],
                "severity_levels": ["critical", "high"],
                "custom_filters": {
                    "resource_type": ["instance", "disk"]
                },
                "enabled": True,
                "auto_resolve": True,
                "resolve_after_hours": 24,
                "tenant_id": "default",
                "created_by": "admin"
            }
        }


class CloudEvent(BaseModel):
    """Cloud provider event"""
    event_id: str = Field(..., description="Unique event identifier")
    external_id: Optional[str] = Field(None, description="External event ID from provider")
    
    # Event classification
    event_type: EventType = Field(..., description="Type of event")
    severity: EventSeverity = Field(..., description="Event severity")
    status: EventStatus = Field(default=EventStatus.ACTIVE, description="Event status")
    
    # Source information
    cloud_provider: CloudProvider = Field(..., description="Cloud service provider")
    project_id: Optional[str] = Field(None, description="Associated cloud project ID")
    subscription_id: Optional[str] = Field(None, description="Associated subscription ID")
    
    # Event details
    title: str = Field(..., description="Event title")
    description: str = Field(..., description="Event description")
    summary: str = Field(..., description="Event summary")
    
    # Service and resource information
    service_name: Optional[str] = Field(None, description="Service name")
    resource_type: Optional[str] = Field(None, description="Resource type")
    resource_id: Optional[str] = Field(None, description="Resource identifier")
    region: Optional[str] = Field(None, description="Region")
    
    # Timing
    event_time: datetime = Field(default_factory=datetime.utcnow, description="When event occurred")
    resolved_at: Optional[datetime] = Field(None, description="When event was resolved")
    acknowledged_at: Optional[datetime] = Field(None, description="When event was acknowledged")
    acknowledged_by: Optional[str] = Field(None, description="Who acknowledged the event")
    
    # Raw event data
    raw_data: Dict[str, Any] = Field(..., description="Original event data from provider")
    
    # Alerting
    alert_id: Optional[str] = Field(None, description="Associated alert if any")
    
    # Metadata
    tenant_id: str = Field(..., description="Tenant ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "event-001",
                "external_id": "gcp-event-123",
                "event_type": "cloud_alert",
                "severity": "high",
                "status": "active",
                "cloud_provider": "gcp",
                "project_id": "gcp-project-001",
                "title": "High CPU Usage Alert",
                "description": "Instance cpu-usage-001 is experiencing high CPU usage",
                "summary": "High CPU usage detected on instance",
                "service_name": "compute",
                "resource_type": "instance",
                "resource_id": "cpu-usage-001",
                "region": "us-central1",
                "raw_data": {
                    "metric": "cpu_usage",
                    "value": 95.5,
                    "threshold": 80.0
                },
                "tenant_id": "default"
            }
        }


class AlertPolicy(BaseModel):
    """Alert policy configuration"""
    policy_id: str = Field(..., description="Unique policy identifier")
    name: str = Field(..., description="Policy name")
    description: Optional[str] = Field(None, description="Policy description")
    enabled: bool = Field(default=True, description="Whether policy is enabled")
    
    # Matching criteria
    rules: List[AlertRuleConfig] = Field(..., description="Alert rules to match")
    match_all: bool = Field(default=True, description="Whether all rules must match (AND) or any rule (OR)")
    
    # Alert configuration
    severity: AlertSeverity = Field(default=AlertSeverity.MEDIUM, description="Alert severity")
    message_template: str = Field(..., description="Alert message template with placeholders")
    summary_template: str = Field(..., description="Alert summary template")
    
    # Timing and throttling
    time_window: Optional[TimeWindow] = Field(None, description="Time window for policy activation")
    throttle_minutes: int = Field(default=0, description="Throttle alerts (minutes between alerts)")
    max_alerts_per_hour: int = Field(default=10, description="Maximum alerts per hour")
    
    # Provider configuration
    providers: List[str] = Field(..., description="List of provider IDs to send alerts to")
    
    # Metadata
    tenant_id: str = Field(..., description="Tenant ID")
    created_by: str = Field(..., description="User who created the policy")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "policy_id": "policy-001",
                "name": "Critical Events Alert Policy",
                "description": "Alert on critical cloud events",
                "enabled": True,
                "rules": [
                    {
                        "field": "severity",
                        "operator": "eq",
                        "value": "critical",
                        "case_sensitive": True
                    },
                    {
                        "field": "cloud_provider",
                        "operator": "in",
                        "value": ["gcp", "aws"],
                        "case_sensitive": True
                    }
                ],
                "match_all": True,
                "severity": "high",
                "message_template": "Critical event: {title} in {cloud_provider}",
                "summary_template": "Critical event alert for {cloud_provider}",
                "throttle_minutes": 5,
                "max_alerts_per_hour": 10,
                "providers": ["pagerduty-001", "slack-001"],
                "tenant_id": "default",
                "created_by": "admin"
            }
        }


class AlertProvider(BaseModel):
    """Alert provider configuration"""
    provider_id: str = Field(..., description="Unique provider identifier")
    name: str = Field(..., description="Provider name")
    provider_type: AlertProviderType = Field(..., description="Provider type")
    enabled: bool = Field(default=True, description="Whether provider is enabled")
    
    # Provider-specific configuration
    config: Dict[str, Any] = Field(..., description="Provider-specific configuration")
    
    # Metadata
    tenant_id: str = Field(..., description="Tenant ID")
    created_by: str = Field(..., description="User who created the provider")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "provider_id": "pagerduty-001",
                "name": "Production PagerDuty",
                "provider_type": "pagerduty",
                "enabled": True,
                "config": {
                    "api_key": "your-pagerduty-api-key",
                    "service_id": "your-service-id",
                    "urgency": "high"
                },
                "tenant_id": "default",
                "created_by": "admin"
            }
        }


class Alert(BaseModel):
    """Alert instance"""
    alert_id: str = Field(..., description="Unique alert identifier")
    policy_id: str = Field(..., description="Policy that triggered the alert")
    event_id: Optional[str] = Field(None, description="Event that triggered the alert")
    severity: AlertSeverity = Field(..., description="Alert severity")
    status: AlertStatus = Field(default=AlertStatus.ACTIVE, description="Alert status")
    
    # Alert content
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    summary: str = Field(..., description="Alert summary")
    
    # Triggering event
    event_data: Dict[str, Any] = Field(..., description="Event data that triggered the alert")
    
    # Timing
    triggered_at: datetime = Field(default_factory=datetime.utcnow, description="When alert was triggered")
    resolved_at: Optional[datetime] = Field(None, description="When alert was resolved")
    acknowledged_at: Optional[datetime] = Field(None, description="When alert was acknowledged")
    acknowledged_by: Optional[str] = Field(None, description="Who acknowledged the alert")
    
    # Provider delivery status
    delivery_status: Dict[str, str] = Field(default_factory=dict, description="Delivery status per provider")
    
    # Metadata
    tenant_id: str = Field(..., description="Tenant ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "alert_id": "alert-001",
                "policy_id": "policy-001",
                "event_id": "event-001",
                "severity": "high",
                "status": "active",
                "title": "Critical Event Alert",
                "message": "Critical event: High CPU Usage Alert in gcp",
                "summary": "Critical event alert for gcp",
                "event_data": {
                    "event_id": "event-001",
                    "title": "High CPU Usage Alert",
                    "cloud_provider": "gcp"
                },
                "delivery_status": {
                    "pagerduty-001": "sent",
                    "slack-001": "sent"
                },
                "tenant_id": "default"
            }
        }


# Request/Response Models
class CloudProjectCreate(BaseModel):
    """Request model for creating cloud project"""
    name: str
    description: Optional[str] = None
    cloud_provider: CloudProvider
    project_identifier: str
    config: Dict[str, Any]
    enabled: bool = True
    auto_subscribe: bool = True


class CloudProjectUpdate(BaseModel):
    """Request model for updating cloud project"""
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None
    auto_subscribe: Optional[bool] = None


class EventSubscriptionCreate(BaseModel):
    """Request model for creating event subscription"""
    name: str
    description: Optional[str] = None
    project_id: str
    event_types: List[str]
    services: List[str]
    regions: Optional[List[str]] = None
    severity_levels: List[str]
    custom_filters: Optional[Dict[str, Any]] = None
    enabled: bool = True
    auto_resolve: bool = True
    resolve_after_hours: int = 24


class EventSubscriptionUpdate(BaseModel):
    """Request model for updating event subscription"""
    name: Optional[str] = None
    description: Optional[str] = None
    event_types: Optional[List[str]] = None
    services: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    severity_levels: Optional[List[str]] = None
    custom_filters: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None
    auto_resolve: Optional[bool] = None
    resolve_after_hours: Optional[int] = None


class CloudEventCreate(BaseModel):
    """Request model for creating cloud event"""
    external_id: Optional[str] = None
    event_type: EventType
    severity: EventSeverity
    cloud_provider: CloudProvider
    project_id: Optional[str] = None
    subscription_id: Optional[str] = None
    title: str
    description: str
    summary: str
    service_name: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    region: Optional[str] = None
    event_time: Optional[datetime] = None
    raw_data: Dict[str, Any]


class AlertPolicyCreate(BaseModel):
    """Request model for creating alert policy"""
    name: str
    description: Optional[str] = None
    enabled: bool = True
    rules: List[AlertRuleConfig]
    match_all: bool = True
    severity: AlertSeverity = AlertSeverity.MEDIUM
    message_template: str
    summary_template: str
    time_window: Optional[TimeWindow] = None
    throttle_minutes: int = 0
    max_alerts_per_hour: int = 10
    providers: List[str]


class AlertPolicyUpdate(BaseModel):
    """Request model for updating alert policy"""
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    rules: Optional[List[AlertRuleConfig]] = None
    match_all: Optional[bool] = None
    severity: Optional[AlertSeverity] = None
    message_template: Optional[str] = None
    summary_template: Optional[str] = None
    time_window: Optional[TimeWindow] = None
    throttle_minutes: Optional[int] = None
    max_alerts_per_hour: Optional[int] = None
    providers: Optional[List[str]] = None


class AlertProviderCreate(BaseModel):
    """Request model for creating alert provider"""
    name: str
    provider_type: AlertProviderType
    enabled: bool = True
    config: Dict[str, Any]


class AlertProviderUpdate(BaseModel):
    """Request model for updating alert provider"""
    name: Optional[str] = None
    enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


# Response Models
class CloudProjectResponse(BaseModel):
    """Response model for cloud projects"""
    project_id: str
    name: str
    description: Optional[str]
    cloud_provider: CloudProvider
    project_identifier: str
    config: Dict[str, Any]
    enabled: bool
    auto_subscribe: bool
    tenant_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventSubscriptionResponse(BaseModel):
    """Response model for event subscriptions"""
    subscription_id: str
    name: str
    description: Optional[str]
    project_id: str
    event_types: List[str]
    services: List[str]
    regions: Optional[List[str]]
    severity_levels: List[str]
    custom_filters: Optional[Dict[str, Any]]
    enabled: bool
    auto_resolve: bool
    resolve_after_hours: int
    tenant_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CloudEventResponse(BaseModel):
    """Response model for cloud events"""
    event_id: str
    external_id: Optional[str]
    event_type: EventType
    severity: EventSeverity
    status: EventStatus
    cloud_provider: CloudProvider
    project_id: Optional[str]
    subscription_id: Optional[str]
    title: str
    description: str
    summary: str
    service_name: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    region: Optional[str]
    event_time: datetime
    resolved_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]
    raw_data: Dict[str, Any]
    alert_id: Optional[str]
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertPolicyResponse(BaseModel):
    """Response model for alert policies"""
    policy_id: str
    name: str
    description: Optional[str]
    enabled: bool
    rules: List[AlertRuleConfig]
    match_all: bool
    severity: AlertSeverity
    message_template: str
    summary_template: str
    time_window: Optional[TimeWindow]
    throttle_minutes: int
    max_alerts_per_hour: int
    providers: List[str]
    tenant_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertProviderResponse(BaseModel):
    """Response model for alert providers"""
    provider_id: str
    name: str
    provider_type: AlertProviderType
    enabled: bool
    config: Dict[str, Any]
    tenant_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    """Response model for alerts"""
    alert_id: str
    policy_id: str
    event_id: Optional[str]
    severity: AlertSeverity
    status: AlertStatus
    title: str
    message: str
    summary: str
    event_data: Dict[str, Any]
    triggered_at: datetime
    resolved_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]
    delivery_status: Dict[str, str]
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# List Response Models
class CloudProjectListResponse(BaseModel):
    """Response model for list of cloud projects"""
    projects: List[CloudProjectResponse]
    total: int
    page: int
    per_page: int


class EventSubscriptionListResponse(BaseModel):
    """Response model for list of event subscriptions"""
    subscriptions: List[EventSubscriptionResponse]
    total: int
    page: int
    per_page: int


class CloudEventListResponse(BaseModel):
    """Response model for list of cloud events"""
    events: List[CloudEventResponse]
    total: int
    page: int
    per_page: int


class AlertPolicyListResponse(BaseModel):
    """Response model for list of alert policies"""
    policies: List[AlertPolicyResponse]
    total: int
    page: int
    per_page: int


class AlertProviderListResponse(BaseModel):
    """Response model for list of alert providers"""
    providers: List[AlertProviderResponse]
    total: int
    page: int
    per_page: int


class AlertListResponse(BaseModel):
    """Response model for list of alerts"""
    alerts: List[AlertResponse]
    total: int
    page: int
    per_page: int


# Event Processor Models
class EventProcessorType(str, Enum):
    """Types of event processors"""
    TRANSFORMER = "transformer"
    ENRICHER = "enricher"
    FILTER = "filter"
    ROUTER = "router"


class EventProcessorCreate(BaseModel):
    """Create event processor request model"""
    name: str = Field(..., min_length=1, max_length=255, description="Processor name")
    description: Optional[str] = Field(None, max_length=1000, description="Processor description")
    processor_type: EventProcessorType = Field(..., description="Type of processor")
    config: Dict[str, Any] = Field(..., description="Processor-specific configuration")
    order: int = Field(0, ge=0, description="Processing order (lower numbers first)")
    depends_on: Optional[List[str]] = Field(None, description="List of processor IDs this depends on")
    event_types: Optional[List[str]] = Field(None, description="List of event types to process")
    severity_levels: Optional[List[str]] = Field(None, description="List of severity levels to process")
    cloud_providers: Optional[List[str]] = Field(None, description="List of cloud providers to process")
    conditions: Optional[Dict[str, Any]] = Field(None, description="Conditional logic for when to apply processor")
    transformations: Dict[str, Any] = Field(..., description="Transformation rules and mappings")
    enabled: bool = Field(True, description="Whether the processor is enabled")
    tenant_id: str = Field(..., description="Tenant ID")
    created_by: str = Field(..., description="User who created the processor")


class EventProcessorUpdate(BaseModel):
    """Update event processor request model"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Processor name")
    description: Optional[str] = Field(None, max_length=1000, description="Processor description")
    processor_type: Optional[EventProcessorType] = Field(None, description="Type of processor")
    config: Optional[Dict[str, Any]] = Field(None, description="Processor-specific configuration")
    order: Optional[int] = Field(None, ge=0, description="Processing order (lower numbers first)")
    depends_on: Optional[List[str]] = Field(None, description="List of processor IDs this depends on")
    event_types: Optional[List[str]] = Field(None, description="List of event types to process")
    severity_levels: Optional[List[str]] = Field(None, description="List of severity levels to process")
    cloud_providers: Optional[List[str]] = Field(None, description="List of cloud providers to process")
    conditions: Optional[Dict[str, Any]] = Field(None, description="Conditional logic for when to apply processor")
    transformations: Optional[Dict[str, Any]] = Field(None, description="Transformation rules and mappings")
    enabled: Optional[bool] = Field(None, description="Whether the processor is enabled")


class EventProcessorResponse(BaseModel):
    """Response model for event processor"""
    processor_id: str
    name: str
    description: Optional[str]
    processor_type: EventProcessorType
    config: Dict[str, Any]
    order: int
    depends_on: Optional[List[str]]
    event_types: Optional[List[str]]
    severity_levels: Optional[List[str]]
    cloud_providers: Optional[List[str]]
    conditions: Optional[Dict[str, Any]]
    transformations: Dict[str, Any]
    enabled: bool
    last_processed: Optional[datetime]
    processed_count: int
    error_count: int
    tenant_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventProcessorListResponse(BaseModel):
    """Response model for list of event processors"""
    processors: List[EventProcessorResponse]
    total: int
    page: int
    per_page: int


class EventProcessorStats(BaseModel):
    """Statistics for event processor"""
    processor_id: str
    name: str
    processor_type: EventProcessorType
    processed_count: int
    error_count: int
    last_processed: Optional[datetime]
    avg_processing_time: Optional[float]
    success_rate: float
    enabled: bool
