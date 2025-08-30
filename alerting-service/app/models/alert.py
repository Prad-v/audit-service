"""
Alert Models for Policy-Based Alerting System

This module defines Pydantic models for alert policies, rules, and providers.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, validator, model_validator
import re


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
    field: str = Field(..., description="Field to match (e.g., event_type, user_id, status)")
    operator: str = Field(..., description="Comparison operator (eq, ne, gt, lt, gte, lte, in, not_in, contains, regex)")
    value: Union[str, int, float, bool, List[Any]] = Field(..., description="Value to compare against")
    case_sensitive: bool = Field(default=True, description="Case sensitive matching")

    @validator('operator')
    def validate_operator(cls, v):
        valid_operators = ['eq', 'ne', 'gt', 'lt', 'gte', 'lte', 'in', 'not_in', 'contains', 'regex']
        if v not in valid_operators:
            raise ValueError(f'Operator must be one of: {valid_operators}')
        return v


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
                "name": "Failed Login Alerts",
                "description": "Alert on multiple failed login attempts",
                "enabled": True,
                "rules": [
                    {
                        "field": "event_type",
                        "operator": "eq",
                        "value": "user_login",
                        "case_sensitive": True
                    },
                    {
                        "field": "status",
                        "operator": "eq",
                        "value": "failed",
                        "case_sensitive": True
                    }
                ],
                "match_all": True,
                "severity": "high",
                "message_template": "Failed login attempt by user {user_id} from IP {ip_address}",
                "summary_template": "Failed login alert for {user_id}",
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
    severity: AlertSeverity = Field(..., description="Alert severity")
    status: AlertStatus = Field(default=AlertStatus.ACTIVE, description="Alert status")
    
    # Alert content
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    summary: str = Field(..., description="Alert summary")
    
    # Triggering event
    event_data: Dict[str, Any] = Field(..., description="Event data that triggered the alert")
    event_id: Optional[str] = Field(None, description="Original event ID")
    
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
                "severity": "high",
                "status": "active",
                "title": "Failed Login Alert",
                "message": "Failed login attempt by user john.doe from IP 192.168.1.100",
                "summary": "Failed login alert for john.doe",
                "event_data": {
                    "event_type": "user_login",
                    "user_id": "john.doe",
                    "ip_address": "192.168.1.100",
                    "status": "failed"
                },
                "event_id": "event-123",
                "delivery_status": {
                    "pagerduty-001": "sent",
                    "slack-001": "sent"
                },
                "tenant_id": "default"
            }
        }


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


class AlertResponse(BaseModel):
    """Response model for alerts"""
    alert_id: str
    policy_id: str
    severity: AlertSeverity
    status: AlertStatus
    title: str
    message: str
    summary: str
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


class AlertListResponse(BaseModel):
    """Response model for list of alerts"""
    alerts: List[AlertResponse]
    total: int
    page: int
    per_page: int


class AlertPolicyListResponse(BaseModel):
    """Response model for list of alert policies"""
    policies: List[AlertPolicyResponse]
    total: int
    page: int
    per_page: int


class AlertCondition(BaseModel):
    """Model for individual alert condition"""
    field: str
    operator: str
    value: Union[str, int, float, bool, List[Any]]
    case_sensitive: bool = True


class SimpleAlertRuleCreate(BaseModel):
    """Request model for creating simple alert rule"""
    name: str
    description: Optional[str] = None
    field: str
    operator: str
    value: Union[str, int, float, bool, List[Any]]
    case_sensitive: bool = True
    enabled: bool = True


class CompoundAlertRuleCreate(BaseModel):
    """Request model for creating compound alert rule"""
    name: str
    description: Optional[str] = None
    conditions: List[AlertCondition]
    group_operator: str  # "AND" or "OR"
    enabled: bool = True


class AlertRuleCreate(BaseModel):
    """Request model for creating alert rule"""
    name: str
    description: Optional[str] = None
    rule_type: str = "simple"  # "simple" or "compound"
    
    # For simple rules
    field: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[Union[str, int, float, bool, List[Any]]] = None
    case_sensitive: Optional[bool] = None
    
    # For compound rules
    conditions: Optional[List[AlertCondition]] = None
    group_operator: Optional[str] = None  # "AND" or "OR"
    
    enabled: bool = True

    @model_validator(mode='before')
    @classmethod
    def validate_rule_data(cls, data):
        """Validate rule data based on type"""
        if isinstance(data, dict):
            rule_type = data.get("rule_type", "simple")
            
            if rule_type == "simple":
                # For simple rules, ensure required fields are present
                if not data.get("field") or not data.get("operator") or data.get("value") is None:
                    raise ValueError("Simple rules require field, operator, and value")
            elif rule_type == "compound":
                # For compound rules, ensure conditions and group_operator are present
                if not data.get("conditions") or not data.get("group_operator"):
                    raise ValueError("Compound rules require conditions and group_operator")
                if data.get("group_operator") not in ["AND", "OR"]:
                    raise ValueError("Group operator must be 'AND' or 'OR'")
                # Validate each condition
                for i, condition in enumerate(data.get("conditions", [])):
                    if not condition.get("field") or not condition.get("operator") or condition.get("value") is None:
                        raise ValueError(f"Condition {i+1} requires field, operator, and value")
            else:
                # Auto-detect rule type
                if data.get("conditions") and data.get("group_operator"):
                    data["rule_type"] = "compound"
                else:
                    data["rule_type"] = "simple"
        
        return data


class AlertRuleUpdate(BaseModel):
    """Request model for updating alert rule"""
    name: Optional[str] = None
    description: Optional[str] = None
    rule_type: Optional[str] = None
    
    # For simple rules
    field: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[Union[str, int, float, bool, List[Any]]] = None
    case_sensitive: Optional[bool] = None
    
    # For compound rules
    conditions: Optional[List[AlertCondition]] = None
    group_operator: Optional[str] = None
    
    enabled: Optional[bool] = None


class AlertRuleResponse(BaseModel):
    """Response model for alert rules"""
    rule_id: str
    name: str
    description: Optional[str]
    rule_type: str
    
    # For simple rules
    field: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[Union[str, int, float, bool, List[Any]]] = None
    case_sensitive: Optional[bool] = None
    
    # For compound rules
    conditions: Optional[List[AlertCondition]] = None
    group_operator: Optional[str] = None
    
    enabled: bool
    tenant_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertRuleListResponse(BaseModel):
    """Response model for list of alert rules"""
    rules: List[AlertRuleResponse]
    total: int
    page: int
    per_page: int


class AlertProviderListResponse(BaseModel):
    """Response model for list of alert providers"""
    providers: List[AlertProviderResponse]
    total: int
    page: int
    per_page: int
