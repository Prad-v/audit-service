"""
FastMCP Service for Natural Language Audit Event Queries

This service provides a FastMCP server that allows users to query audit events
using natural language. It integrates with the audit service to provide
intelligent search and analysis capabilities.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import text, and_, or_, func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.schemas import AuditLog
from app.models.audit import EventType, Severity
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of natural language queries supported"""
    SEARCH = "search"
    ANALYTICS = "analytics"
    SUMMARY = "summary"
    TREND = "trend"
    ALERT = "alert"


@dataclass
class QueryIntent:
    """Represents the intent extracted from a natural language query"""
    query_type: QueryType
    filters: Dict[str, Any]
    time_range: Optional[Dict[str, datetime]]
    limit: Optional[int]
    aggregation: Optional[str]
    keywords: List[str]


class MCPAuditService:
    """FastMCP service for audit event queries"""
    
    def __init__(self):
        self.audit_service = AuditService()
    
    def _parse_query_intent(self, query: str) -> QueryIntent:
        """Parse natural language query to extract intent and filters"""
        query_lower = query.lower()
        keywords = []
        filters = {}
        time_range = None
        limit = None
        aggregation = None
        
        # Extract time range
        if "today" in query_lower:
            time_range = {
                "start": datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                "end": datetime.now()
            }
        elif "yesterday" in query_lower:
            yesterday = datetime.now() - timedelta(days=1)
            time_range = {
                "start": yesterday.replace(hour=0, minute=0, second=0, microsecond=0),
                "end": yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
            }
        elif "last week" in query_lower or "past week" in query_lower:
            time_range = {
                "start": datetime.now() - timedelta(days=7),
                "end": datetime.now()
            }
        elif "last month" in query_lower or "past month" in query_lower:
            time_range = {
                "start": datetime.now() - timedelta(days=30),
                "end": datetime.now()
            }
        elif "last hour" in query_lower:
            time_range = {
                "start": datetime.now() - timedelta(hours=1),
                "end": datetime.now()
            }
        
        # Extract event types
        event_type_mapping = {
            "login": EventType.LOGIN,
            "logout": EventType.LOGOUT,
            "create": EventType.CREATE,
            "update": EventType.UPDATE,
            "delete": EventType.DELETE,
            "read": EventType.READ,
            "access": EventType.ACCESS,
            "permission": EventType.PERMISSION_CHANGE,
            "security": EventType.SECURITY_EVENT,
            "error": EventType.ERROR,
            "warning": EventType.WARNING,
            "info": EventType.INFO
        }
        
        for keyword, event_type in event_type_mapping.items():
            if keyword in query_lower:
                filters["event_type"] = event_type
                keywords.append(keyword)
        
        # Extract severity levels
        severity_mapping = {
            "critical": Severity.CRITICAL,
            "high": Severity.HIGH,
            "medium": Severity.MEDIUM,
            "low": Severity.LOW,
            "info": Severity.INFO
        }
        
        for keyword, severity in severity_mapping.items():
            if keyword in query_lower:
                filters["severity"] = severity
                keywords.append(keyword)
        
        # Extract service names
        service_keywords = ["api", "frontend", "backend", "database", "auth", "user"]
        for keyword in service_keywords:
            if keyword in query_lower:
                filters["service_name"] = keyword
                keywords.append(keyword)
        
        # Extract status
        if "success" in query_lower:
            filters["status"] = "success"
            keywords.append("success")
        elif "failed" in query_lower or "failure" in query_lower or "error" in query_lower:
            filters["status"] = "failed"
            keywords.append("failed")
        
        # Extract limit
        if "top" in query_lower or "latest" in query_lower:
            limit = 10
        elif "recent" in query_lower:
            limit = 20
        
        # Determine query type
        if any(word in query_lower for word in ["count", "how many", "total"]):
            query_type = QueryType.ANALYTICS
            aggregation = "count"
        elif any(word in query_lower for word in ["trend", "pattern", "over time"]):
            query_type = QueryType.TREND
        elif any(word in query_lower for word in ["alert", "critical", "urgent"]):
            query_type = QueryType.ALERT
        elif any(word in query_lower for word in ["summary", "overview"]):
            query_type = QueryType.SUMMARY
        else:
            query_type = QueryType.SEARCH
        
        return QueryIntent(
            query_type=query_type,
            filters=filters,
            time_range=time_range,
            limit=limit,
            aggregation=aggregation,
            keywords=keywords
        )
    
    async def _execute_query(self, intent: QueryIntent) -> Dict[str, Any]:
        """Execute query based on parsed intent"""
        db = next(get_db())
        
        try:
            if intent.query_type == QueryType.SEARCH:
                return await self._search_audit_events(db, intent)
            elif intent.query_type == QueryType.ANALYTICS:
                return await self._get_audit_analytics(db, intent)
            elif intent.query_type == QueryType.TREND:
                return await self._get_audit_trends(db, intent)
            elif intent.query_type == QueryType.SUMMARY:
                return await self._get_audit_summary(db, intent)
            elif intent.query_type == QueryType.ALERT:
                return await self._get_audit_alerts(db, intent)
            else:
                return await self._search_audit_events(db, intent)
        finally:
            db.close()
    
    async def _search_audit_events(self, db: Session, intent: QueryIntent) -> Dict[str, Any]:
        """Search audit events based on filters"""
        query = db.query(AuditLog)
        
        # Apply filters
        if intent.filters.get("event_type"):
            query = query.filter(AuditLog.event_type == intent.filters["event_type"])
        
        if intent.filters.get("severity"):
            query = query.filter(AuditLog.severity == intent.filters["severity"])
        
        if intent.filters.get("service_name"):
            query = query.filter(AuditLog.service_name.ilike(f"%{intent.filters['service_name']}%"))
        
        if intent.filters.get("status"):
            if intent.filters["status"] == "success":
                query = query.filter(AuditLog.status == "success")
            else:
                query = query.filter(AuditLog.status != "success")
        
        # Apply time range
        if intent.time_range:
            query = query.filter(
                and_(
                    AuditLog.timestamp >= intent.time_range["start"],
                    AuditLog.timestamp <= intent.time_range["end"]
                )
            )
        
        # Apply limit
        if intent.limit:
            query = query.limit(intent.limit)
        else:
            query = query.limit(50)
        
        # Order by timestamp
        query = query.order_by(AuditLog.timestamp.desc())
        
        events = query.all()
        
        return {
            "type": "search_results",
            "count": len(events),
            "events": [
                {
                    "audit_id": str(event.audit_id),
                    "event_type": event.event_type,
                    "action": event.action,
                    "status": event.status,
                    "severity": event.severity,
                    "service_name": event.service_name,
                    "user_id": event.user_id,
                    "timestamp": event.timestamp.isoformat(),
                    "ip_address": event.ip_address,
                    "metadata": event.event_metadata
                }
                for event in events
            ],
            "filters_applied": intent.filters,
            "keywords": intent.keywords
        }
    
    async def _get_audit_analytics(self, db: Session, intent: QueryIntent) -> Dict[str, Any]:
        """Get analytics for audit events"""
        query = db.query(AuditLog)
        
        # Apply filters
        if intent.filters.get("event_type"):
            query = query.filter(AuditLog.event_type == intent.filters["event_type"])
        
        if intent.filters.get("severity"):
            query = query.filter(AuditLog.severity == intent.filters["severity"])
        
        if intent.time_range:
            query = query.filter(
                and_(
                    AuditLog.timestamp >= intent.time_range["start"],
                    AuditLog.timestamp <= intent.time_range["end"]
                )
            )
        
        # Get counts by different dimensions
        total_count = query.count()
        
        # Count by event type
        event_type_counts = db.query(
            AuditLog.event_type,
            func.count(AuditLog.audit_id).label('count')
        ).filter(query.whereclause).group_by(AuditLog.event_type).all()
        
        # Count by severity
        severity_counts = db.query(
            AuditLog.severity,
            func.count(AuditLog.audit_id).label('count')
        ).filter(query.whereclause).group_by(AuditLog.severity).all()
        
        # Count by status
        status_counts = db.query(
            AuditLog.status,
            func.count(AuditLog.audit_id).label('count')
        ).filter(query.whereclause).group_by(AuditLog.status).all()
        
        return {
            "type": "analytics",
            "total_events": total_count,
            "by_event_type": {str(et.event_type): et.count for et in event_type_counts},
            "by_severity": {str(sev.severity): sev.count for sev in severity_counts},
            "by_status": {str(st.status): st.count for st in status_counts},
            "filters_applied": intent.filters,
            "keywords": intent.keywords
        }
    
    async def _get_audit_trends(self, db: Session, intent: QueryIntent) -> Dict[str, Any]:
        """Get trends in audit events over time"""
        query = db.query(AuditLog)
        
        # Apply filters
        if intent.filters.get("event_type"):
            query = query.filter(AuditLog.event_type == intent.filters["event_type"])
        
        if intent.filters.get("severity"):
            query = query.filter(AuditLog.severity == intent.filters["severity"])
        
        if intent.time_range:
            query = query.filter(
                and_(
                    AuditLog.timestamp >= intent.time_range["start"],
                    AuditLog.timestamp <= intent.time_range["end"]
                )
            )
        
        # Get hourly trends for the last 24 hours
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        hourly_trends = db.query(
            func.date_trunc('hour', AuditLog.timestamp).label('hour'),
            func.count(AuditLog.audit_id).label('count')
        ).filter(
            and_(
                AuditLog.timestamp >= start_time,
                AuditLog.timestamp <= end_time
            )
        ).group_by(
            func.date_trunc('hour', AuditLog.timestamp)
        ).order_by(
            func.date_trunc('hour', AuditLog.timestamp)
        ).all()
        
        return {
            "type": "trends",
            "time_range": "24h",
            "trends": [
                {
                    "hour": trend.hour.isoformat(),
                    "count": trend.count
                }
                for trend in hourly_trends
            ],
            "filters_applied": intent.filters,
            "keywords": intent.keywords
        }
    
    async def _get_audit_summary(self, db: Session, intent: QueryIntent) -> Dict[str, Any]:
        """Get a summary of audit events"""
        # Get recent events
        recent_events = db.query(AuditLog).order_by(
            AuditLog.timestamp.desc()
        ).limit(10).all()
        
        # Get counts by severity
        severity_summary = db.query(
            AuditLog.severity,
            func.count(AuditLog.audit_id).label('count')
        ).group_by(AuditLog.severity).all()
        
        # Get top services
        service_summary = db.query(
            AuditLog.service_name,
            func.count(AuditLog.audit_id).label('count')
        ).group_by(AuditLog.service_name).order_by(
            func.count(AuditLog.audit_id).desc()
        ).limit(5).all()
        
        return {
            "type": "summary",
            "recent_events": [
                {
                    "audit_id": str(event.audit_id),
                    "event_type": event.event_type,
                    "action": event.action,
                    "severity": event.severity,
                    "timestamp": event.timestamp.isoformat()
                }
                for event in recent_events
            ],
            "severity_breakdown": {str(sev.severity): sev.count for sev in severity_summary},
            "top_services": {str(svc.service_name): svc.count for svc in service_summary},
            "filters_applied": intent.filters,
            "keywords": intent.keywords
        }
    
    async def _get_audit_alerts(self, db: Session, intent: QueryIntent) -> Dict[str, Any]:
        """Get alerts based on audit events"""
        # Get high severity events in the last hour
        alert_time = datetime.now() - timedelta(hours=1)
        
        high_severity_events = db.query(AuditLog).filter(
            and_(
                AuditLog.severity.in_([Severity.HIGH, Severity.CRITICAL]),
                AuditLog.timestamp >= alert_time
            )
        ).order_by(AuditLog.timestamp.desc()).all()
        
        # Get failed events
        failed_events = db.query(AuditLog).filter(
            and_(
                AuditLog.status != "success",
                AuditLog.timestamp >= alert_time
            )
        ).order_by(AuditLog.timestamp.desc()).limit(10).all()
        
        return {
            "type": "alerts",
            "high_severity_events": [
                {
                    "audit_id": str(event.audit_id),
                    "event_type": event.event_type,
                    "action": event.action,
                    "severity": event.severity,
                    "timestamp": event.timestamp.isoformat(),
                    "service_name": event.service_name
                }
                for event in high_severity_events
            ],
            "failed_events": [
                {
                    "audit_id": str(event.audit_id),
                    "event_type": event.event_type,
                    "action": event.action,
                    "status": event.status,
                    "timestamp": event.timestamp.isoformat(),
                    "service_name": event.service_name
                }
                for event in failed_events
            ],
            "alert_count": len(high_severity_events) + len(failed_events),
            "filters_applied": intent.filters,
            "keywords": intent.keywords
        }


# Global instance
mcp_service = MCPAuditService()
