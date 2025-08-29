"""
Metrics models for the audit log framework.

This module defines Pydantic models for various metrics and analytics data
used in the audit log framework dashboard and monitoring.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class MetricsData(BaseModel):
    """Model for overall metrics data."""
    
    total_events: int = Field(..., description="Total number of events in the system")
    events_today: int = Field(..., description="Number of events created today")
    events_this_hour: int = Field(..., description="Number of events created in the last hour")
    ingestion_rate: float = Field(..., description="Events per minute ingestion rate")
    query_rate: float = Field(..., description="Queries per minute rate")
    avg_response_time: float = Field(..., description="Average API response time in milliseconds")
    error_rate: float = Field(..., description="Error rate percentage")


class IngestionRateData(BaseModel):
    """Model for ingestion rate data points."""
    
    timestamp: datetime = Field(..., description="Timestamp for the data point")
    rate: float = Field(..., description="Events per minute rate")
    events_count: int = Field(..., description="Number of events in this time period")


class QueryRateData(BaseModel):
    """Model for query rate data points."""
    
    timestamp: datetime = Field(..., description="Timestamp for the data point")
    rate: float = Field(..., description="Queries per minute rate")
    queries_count: int = Field(..., description="Number of queries in this time period")


class TopEventType(BaseModel):
    """Model for top event types statistics."""
    
    event_type: str = Field(..., description="Event type name")
    count: int = Field(..., description="Number of events of this type")
    percentage: float = Field(..., description="Percentage of total events")


class SystemMetrics(BaseModel):
    """Model for system performance metrics."""
    
    cpu_usage: float = Field(..., description="CPU usage percentage")
    memory_usage: float = Field(..., description="Memory usage percentage")
    disk_usage: float = Field(..., description="Disk usage percentage")
    active_connections: int = Field(..., description="Number of active database connections")
    database_size: int = Field(..., description="Database size in bytes")


class MetricsResponse(BaseModel):
    """Model for metrics API response."""
    
    metrics: MetricsData
    ingestion_rate_data: List[IngestionRateData]
    query_rate_data: List[QueryRateData]
    top_event_types: List[TopEventType]
    system_metrics: SystemMetrics
    timestamp: datetime = Field(default_factory=datetime.utcnow)
