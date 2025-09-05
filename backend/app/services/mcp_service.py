"""
FastMCP Service for Natural Language Queries

This service provides a FastMCP server that allows users to query audit events,
cloud events, and incidents using natural language. It integrates with the audit service,
events service, and incidents service to provide intelligent search and analysis capabilities.
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from fastmcp import FastMCP
from sqlalchemy import text, and_, or_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_database_manager
from app.db.schemas import AuditLog
from app.models.audit import AuditEventType, AuditEventStatus
from app.services.audit_service import AuditService
import httpx

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of natural language queries supported"""
    SEARCH = "search"
    ANALYTICS = "analytics"
    SUMMARY = "summary"
    TREND = "trend"
    ALERT = "alert"
    EVENTS = "events"
    INCIDENTS = "incidents"
    OUTAGES = "outages"


@dataclass
class QueryIntent:
    """Represents the intent extracted from a natural language query"""
    query_type: QueryType
    filters: Dict[str, Any]
    time_range: Optional[Dict[str, datetime]]
    limit: Optional[int]
    aggregation: Optional[str]
    keywords: List[str]
    original_query: str


class MCPAuditService:
    """FastMCP service for audit event queries"""
    
    def __init__(self):
        self.audit_service = None
        self.mcp = FastMCP(
            name="audit-events-incidents-mcp",
            instructions="""
                This server provides natural language query capabilities for audit events,
                cloud events, and incidents. You can ask questions about audit logs, 
                cloud provider events, incidents, outages, and get analytics and trends.
                
                Available query types:
                - Search: Find specific audit events, cloud events, or incidents
                - Analytics: Get counts and statistics across all data types
                - Trends: Analyze patterns over time
                - Alerts: Get high-priority events and incidents
                - Summary: Get overview reports
                - Events: Query cloud provider events specifically
                - Incidents: Query incidents and outages specifically
                
                Examples:
                - "Show me all login events from today"
                - "How many failed authentication attempts in the last hour?"
                - "Get high severity events from the API service"
                - "Show me trends in user activity over the past week"
                - "What are the recent security alerts?"
                - "Show me all AWS events from today"
                - "What incidents are currently active?"
                - "Show me cloud provider outages"
                - "How many incidents were created this week?"
                - "What are the recent Azure service disruptions?"
            """,
            include_tags={"audit", "security", "analytics", "events", "incidents", "outages"}
        )
        self._setup_tools()
    
    def _get_audit_service(self):
        """Lazy initialization of audit service"""
        if self.audit_service is None:
            self.audit_service = AuditService()
        return self.audit_service
    
    def _setup_tools(self):
        """Setup FastMCP tools"""
        
        @self.mcp.tool(tags={"audit", "search"})
        async def query_audit_events(query: str, limit: int = 50) -> Dict[str, Any]:
            """
            Query audit events using natural language.
            
            Args:
                query: Natural language query for audit events
                limit: Maximum number of results to return (default: 50)
            
            Returns:
                Dictionary containing query results and metadata
            """
            try:
                # Parse the natural language query
                intent = self._parse_query_intent(query)
                
                # Execute the query based on intent
                result = await self._execute_query(intent)
                
                return {
                    "success": True,
                    "data": result,
                    "query_processed": query,
                    "query_type": result.get("type", "search"),
                    "result_count": result.get("count", 0)
                }
                
            except Exception as e:
                logger.error(f"Error processing MCP query: {e}")
                return {
                    "success": False,
                    "error": f"Failed to process query: {str(e)}",
                    "query_processed": query
                }
        
        @self.mcp.tool(tags={"audit", "analytics"})
        async def get_audit_summary(time_range: str = "24h") -> Dict[str, Any]:
            """
            Get a summary of audit events.
            
            Args:
                time_range: Time range for summary (e.g., "1h", "24h", "7d", "30d")
            
            Returns:
                Dictionary containing audit summary data
            """
            try:
                summary_query = f"Give me a summary of audit events for the last {time_range}"
                intent = self._parse_query_intent(summary_query)
                result = await self._execute_query(intent)
                
                return {
                    "success": True,
                    "data": result,
                    "time_range": time_range
                }
                
            except Exception as e:
                logger.error(f"Error getting audit summary: {e}")
                return {
                    "success": False,
                    "error": f"Failed to get summary: {str(e)}",
                    "time_range": time_range
                }
        
        @self.mcp.tool(tags={"audit", "trends"})
        async def get_audit_trends(time_range: str = "7d", metric: str = "count") -> Dict[str, Any]:
            """
            Get trends in audit events.
            
            Args:
                time_range: Time range for trends (e.g., "1h", "24h", "7d", "30d")
                metric: Metric to analyze (e.g., "count", "severity", "service")
            
            Returns:
                Dictionary containing trend analysis data
            """
            try:
                trends_query = f"Show me trends in {metric} over the last {time_range}"
                intent = self._parse_query_intent(trends_query)
                result = await self._execute_query(intent)
                
                return {
                    "success": True,
                    "data": result,
                    "time_range": time_range,
                    "metric": metric
                }
                
            except Exception as e:
                logger.error(f"Error getting audit trends: {e}")
                return {
                    "success": False,
                    "error": f"Failed to get trends: {str(e)}",
                    "time_range": time_range,
                    "metric": metric
                }
        
        @self.mcp.tool(tags={"audit", "alerts"})
        async def get_audit_alerts(severity: str = "high", time_range: str = "1h") -> Dict[str, Any]:
            """
            Get alerts based on audit events.
            
            Args:
                severity: Minimum severity level (e.g., "low", "medium", "high", "critical")
                time_range: Time range for alerts (e.g., "1h", "24h", "7d")
            
            Returns:
                Dictionary containing alert data
            """
            try:
                alerts_query = f"Show me {severity} severity alerts from the last {time_range}"
                intent = self._parse_query_intent(alerts_query)
                result = await self._execute_query(intent)
                
                return {
                    "success": True,
                    "data": result,
                    "severity": severity,
                    "time_range": time_range
                }
                
            except Exception as e:
                logger.error(f"Error getting audit alerts: {e}")
                return {
                    "success": False,
                    "error": f"Failed to get alerts: {str(e)}",
                    "severity": severity,
                    "time_range": time_range
                }
        
        @self.mcp.tool(tags={"audit", "info"})
        async def get_audit_capabilities() -> Dict[str, Any]:
            """
            Get the capabilities of the MCP service.
            
            Returns:
                Dictionary containing service capabilities and supported features
            """
            return {
                "service": "audit-events-mcp",
                "version": "1.0.0",
                "capabilities": {
                    "natural_language_search": {
                        "description": "Search audit events using natural language",
                        "examples": [
                            "Show me all login events from today",
                            "How many failed authentication attempts in the last hour?",
                            "Get high severity events from the API service"
                        ]
                    },
                    "audit_analytics": {
                        "description": "Get analytics and statistics for audit events",
                        "examples": [
                            "Count all events by severity",
                            "How many events occurred today?",
                            "Show me event distribution by service"
                        ]
                    },
                    "trend_analysis": {
                        "description": "Analyze trends in audit events over time",
                        "examples": [
                            "Show me trends in user activity over the past week",
                            "What's the pattern of login attempts?",
                            "Analyze security event trends"
                        ]
                    },
                    "alert_generation": {
                        "description": "Generate alerts based on audit events",
                        "examples": [
                            "Show me critical alerts from the last hour",
                            "What are the recent security alerts?",
                            "Get high severity events that need attention"
                        ]
                    },
                    "summary_reports": {
                        "description": "Generate summary reports of audit events",
                        "examples": [
                            "Give me a summary of today's events",
                            "Show me an overview of the last week",
                            "Summarize recent activity"
                        ]
                    }
                },
                "supported_time_ranges": [
                    "last hour", "today", "yesterday", "last week", "last month"
                ],
                "supported_event_types": [
                    "login", "logout", "create", "update", "delete", "read", 
                    "access", "permission", "security", "error", "warning", "info"
                ],
                "supported_severities": [
                    "critical", "high", "medium", "low", "info"
                ],
                "supported_services": [
                    "api", "frontend", "backend", "database", "auth", "user"
                ]
            }
        
        # Events and Incidents Tools
        @self.mcp.tool(tags={"events", "search"})
        async def query_cloud_events(query: str, limit: int = 50) -> Dict[str, Any]:
            """
            Query cloud provider events using natural language.
            
            Args:
                query: Natural language query for cloud events
                limit: Maximum number of results to return (default: 50)
            
            Returns:
                Dictionary containing cloud events query results
            """
            try:
                intent = self._parse_query_intent(query)
                intent.query_type = QueryType.EVENTS
                result = await self._execute_query(intent)
                
                return {
                    "success": True,
                    "data": result,
                    "query": query,
                    "limit": limit
                }
                
            except Exception as e:
                logger.error(f"Error querying cloud events: {e}")
                return {
                    "success": False,
                    "error": f"Failed to query cloud events: {str(e)}",
                    "query": query
                }
        
        @self.mcp.tool(tags={"incidents", "search"})
        async def query_incidents(query: str, limit: int = 50) -> Dict[str, Any]:
            """
            Query incidents using natural language.
            
            Args:
                query: Natural language query for incidents
                limit: Maximum number of results to return (default: 50)
            
            Returns:
                Dictionary containing incidents query results
            """
            try:
                intent = self._parse_query_intent(query)
                intent.query_type = QueryType.INCIDENTS
                result = await self._execute_query(intent)
                
                return {
                    "success": True,
                    "data": result,
                    "query": query,
                    "limit": limit
                }
                
            except Exception as e:
                logger.error(f"Error querying incidents: {e}")
                return {
                    "success": False,
                    "error": f"Failed to query incidents: {str(e)}",
                    "query": query
                }
        
        @self.mcp.tool(tags={"outages", "search"})
        async def query_outages(query: str, limit: int = 50) -> Dict[str, Any]:
            """
            Query cloud provider outages using natural language.
            
            Args:
                query: Natural language query for outages
                limit: Maximum number of results to return (default: 50)
            
            Returns:
                Dictionary containing outages query results
            """
            try:
                intent = self._parse_query_intent(query)
                intent.query_type = QueryType.OUTAGES
                result = await self._execute_query(intent)
                
                return {
                    "success": True,
                    "data": result,
                    "query": query,
                    "limit": limit
                }
                
            except Exception as e:
                logger.error(f"Error querying outages: {e}")
                return {
                    "success": False,
                    "error": f"Failed to query outages: {str(e)}",
                    "query": query
                }
    
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
            "login": "user_login",
            "logout": "user_logout",
            "create": "CREATE",
            "update": "UPDATE",
            "delete": "DELETE",
            "read": "READ",
            "access": "file_access",
            "permission": "permission_grant",
            "security": "security_alert",
            "error": "error",
            "warning": "warning",
            "info": "info"
        }
        
        for keyword, event_type in event_type_mapping.items():
            if keyword in query_lower:
                filters["event_type"] = event_type
                keywords.append(keyword)
        
        # Extract severity levels
        severity_mapping = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low",
            "info": "info"
        }
        
        for keyword, severity in severity_mapping.items():
            if keyword in query_lower:
                filters["severity"] = severity
                keywords.append(keyword)
        
        # Extract user IDs (look for various user reference patterns)
        user_patterns = [
            r'by user (\w+)',
            r'for user (\w+)',
            r'from user (\w+)',
            r'user_id (\w+)',
            r'user (\w+)',
            r'for the user_id (\w+)',
            r'get me the event for the user_id (\w+)'
        ]
        
        # Extract user ID from various patterns
        for pattern in user_patterns:
            match = re.search(pattern, query_lower)
            if match:
                user_id = match.group(1)
                # Skip if this looks like an event type (e.g., "user_login")
                if not any(event_type in user_id for event_type in ["login", "logout", "create", "update", "delete"]):
                    filters["user_id"] = user_id
                    keywords.append(f"user:{user_id}")
                    break
        
        # Extract service names (only if not already extracted as user_id)
        if "user_id" not in filters:
            service_keywords = ["api", "frontend", "backend", "database", "auth", "s3", "ec2", "lambda", "rds", "dynamodb", "cloudfront", "route53"]
            for keyword in service_keywords:
                if keyword in query_lower:
                    filters["service_name"] = keyword
                    keywords.append(keyword)
        
        # Extract cloud providers
        provider_mapping = {
            "aws": "aws",
            "amazon": "aws",
            "azure": "azure",
            "microsoft": "azure",
            "gcp": "gcp",
            "google": "gcp",
            "google cloud": "gcp"
        }
        
        for keyword, provider in provider_mapping.items():
            if keyword in query_lower:
                filters["provider"] = provider
                keywords.append(keyword)
        
        # Extract regions
        region_keywords = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1", "north america", "europe", "asia"]
        for keyword in region_keywords:
            if keyword in query_lower:
                filters["region"] = keyword
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
        if any(word in query_lower for word in ["incident", "incidents", "outage", "outages"]):
            if any(word in query_lower for word in ["outage", "outages", "cloud provider", "aws", "azure", "gcp", "google"]):
                query_type = QueryType.OUTAGES
            else:
                query_type = QueryType.INCIDENTS
        elif any(word in query_lower for word in ["cloud event", "cloud events", "aws event", "azure event", "gcp event", "provider event"]):
            query_type = QueryType.EVENTS
        elif any(word in query_lower for word in ["count", "how many", "total", "unique", "distinct", "types", "kinds", "categories"]):
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
            keywords=keywords,
            original_query=query
        )
    
    async def _execute_query(self, intent: QueryIntent, provider_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute query based on parsed intent"""
        db_manager = get_database_manager()
        session = db_manager.get_session()
        
        try:
            if intent.query_type == QueryType.SEARCH:
                result = await self._search_audit_events(session, intent)
            elif intent.query_type == QueryType.ANALYTICS:
                result = await self._get_audit_analytics(session, intent)
            elif intent.query_type == QueryType.TREND:
                result = await self._get_audit_trends(session, intent)
            elif intent.query_type == QueryType.SUMMARY:
                result = await self._get_audit_summary(session, intent)
            elif intent.query_type == QueryType.ALERT:
                result = await self._get_audit_alerts(session, intent)
            elif intent.query_type == QueryType.EVENTS:
                result = await self._query_cloud_events(intent)
            elif intent.query_type == QueryType.INCIDENTS:
                result = await self._query_incidents(intent)
            elif intent.query_type == QueryType.OUTAGES:
                result = await self._query_outages(intent)
            else:
                result = await self._search_audit_events(session, intent)
            
            # Add LLM summarization if provider is specified or default provider exists
            from app.services.llm_service import get_llm_service
            from app.models.llm import LLMSummaryRequest
            
            llm_service = get_llm_service()
            
            # Use specified provider_id or get default provider
            effective_provider_id = provider_id
            if not effective_provider_id:
                default_provider = await llm_service.get_default_provider()
                if default_provider:
                    effective_provider_id = default_provider.provider_id
            
            if effective_provider_id:
                summary_request = LLMSummaryRequest(
                    query=intent.original_query,
                    mcp_result=result,
                    provider_id=effective_provider_id
                )
                
                try:
                    summary_response = await llm_service.summarize_mcp_result(summary_request)
                    result["llm_summary"] = {
                        "summary": summary_response.summary,
                        "provider_used": summary_response.provider_used,
                        "has_llm_analysis": summary_response.has_llm_analysis
                    }
                except Exception as e:
                    logger.error(f"Error generating LLM summary: {e}")
                    # Fallback to mock LLM service
                    try:
                        from app.services.mock_llm_service import mock_llm_service
                        mock_summary = await mock_llm_service.summarize_mcp_result(
                            intent.original_query, result
                        )
                        result["llm_summary"] = {
                            "summary": mock_summary["summary"],
                            "provider_used": mock_summary["provider_used"],
                            "has_llm_analysis": mock_summary["has_llm_analysis"],
                            "fallback_to_mock": True
                        }
                    except Exception as mock_error:
                        logger.error(f"Error generating mock summary: {mock_error}")
                        result["llm_summary"] = {
                            "summary": "Error generating summary. Showing raw results.",
                            "provider_used": effective_provider_id,
                            "has_llm_analysis": False
                        }
            
            return result
        finally:
            await session.close()
    
    async def _search_audit_events(self, db: AsyncSession, intent: QueryIntent) -> Dict[str, Any]:
        """Search audit events based on filters"""
        try:
            query = select(AuditLog)
            
            # Apply filters
            if intent.filters.get("event_type"):
                query = query.where(AuditLog.event_type == intent.filters["event_type"])
            
            if intent.filters.get("user_id"):
                query = query.where(AuditLog.user_id == intent.filters["user_id"])
            
            if intent.filters.get("service_name"):
                query = query.where(AuditLog.service_name.ilike(f"%{intent.filters['service_name']}%"))
            
            if intent.filters.get("status"):
                if intent.filters["status"] == "success":
                    query = query.where(AuditLog.status == "success")
                else:
                    query = query.where(AuditLog.status != "success")
            
            # Apply time range
            if intent.time_range:
                query = query.where(
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
            
            result = await db.execute(query)
            events = result.scalars().all()
            
            return {
                "type": "search_results",
                "count": len(events),
                "events": [
                    {
                        "audit_id": str(event.audit_id),
                        "event_type": event.event_type,
                        "action": event.action,
                        "status": event.status,
                        "service_name": event.service_name,
                        "user_id": event.user_id,
                        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                        "ip_address": str(event.ip_address) if event.ip_address else None,
                        "metadata": event.event_metadata
                    }
                    for event in events
                ],
                "filters_applied": intent.filters,
                "keywords": intent.keywords
            }
        except Exception as e:
            logger.error(f"Error in _search_audit_events: {e}")
            # Return empty results instead of raising
            return {
                "type": "search_results",
                "count": 0,
                "events": [],
                "filters_applied": intent.filters,
                "keywords": intent.keywords
            }
    
    async def _get_audit_analytics(self, db: AsyncSession, intent: QueryIntent) -> Dict[str, Any]:
        """Get analytics for audit events"""
        # Build base filter conditions
        conditions = []
        
        if intent.filters.get("event_type"):
            conditions.append(AuditLog.event_type == intent.filters["event_type"])
        
        if intent.filters.get("user_id"):
            conditions.append(AuditLog.user_id == intent.filters["user_id"])
        
        # Note: AuditLog doesn't have a severity field, only status
        # if intent.filters.get("severity"):
        #     conditions.append(AuditLog.severity == intent.filters["severity"])
        
        if intent.time_range:
            conditions.append(
                and_(
                    AuditLog.timestamp >= intent.time_range["start"],
                    AuditLog.timestamp <= intent.time_range["end"]
                )
            )
        
        # Get total count
        total_query = select(func.count(AuditLog.audit_id))
        if conditions:
            total_query = total_query.where(and_(*conditions))
        total_count_result = await db.execute(total_query)
        total_count = total_count_result.scalar()
        
        # Count by event type
        event_type_counts_query = select(
            AuditLog.event_type,
            func.count(AuditLog.audit_id).label('count')
        ).group_by(AuditLog.event_type)
        if conditions:
            event_type_counts_query = event_type_counts_query.where(and_(*conditions))
        event_type_counts_result = await db.execute(event_type_counts_query)
        event_type_counts = event_type_counts_result.all()
        
        # Count by status (AuditLog doesn't have severity field)
        status_counts_query = select(
            AuditLog.status,
            func.count(AuditLog.audit_id).label('count')
        ).group_by(AuditLog.status)
        if conditions:
            status_counts_query = status_counts_query.where(and_(*conditions))
        status_counts_result = await db.execute(status_counts_query)
        status_counts = status_counts_result.all()
        

        
        return {
            "type": "analytics",
            "total_events": total_count,
            "by_event_type": {str(et.event_type): et.count for et in event_type_counts},
            "by_status": {str(st.status): st.count for st in status_counts},
            "filters_applied": intent.filters,
            "keywords": intent.keywords
        }
    
    async def _get_audit_trends(self, db: AsyncSession, intent: QueryIntent) -> Dict[str, Any]:
        """Get trends in audit events over time"""
        try:
            # Get hourly trends for the last 24 hours
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            # Use a simpler approach to avoid PostgreSQL GROUP BY issues
            try:
                hourly_trends_query = select(
                    func.date_trunc('hour', AuditLog.timestamp).label('hour'),
                    func.count(AuditLog.audit_id).label('count')
                ).where(
                    and_(
                        AuditLog.timestamp >= start_time,
                        AuditLog.timestamp <= end_time
                    )
                ).group_by(
                    func.date_trunc('hour', AuditLog.timestamp)
                ).order_by(
                    func.date_trunc('hour', AuditLog.timestamp)
                )
                hourly_trends_result = await db.execute(hourly_trends_query)
                hourly_trends = hourly_trends_result.all()
            except Exception as e:
                logger.warning(f"Hourly trends query failed, using simple count: {e}")
                # Rollback the transaction and try a simple count
                await db.rollback()
                
                simple_count_query = select(func.count(AuditLog.audit_id)).where(
                    and_(
                        AuditLog.timestamp >= start_time,
                        AuditLog.timestamp <= end_time
                    )
                )
                simple_count_result = await db.execute(simple_count_query)
                total_count = simple_count_result.scalar()
                
                hourly_trends = [
                    type('HourlyTrend', (), {
                        'hour': datetime.now(),
                        'count': total_count
                    })()
                ]
            
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
        except Exception as e:
            logger.error(f"Error in _get_audit_trends: {e}")
            # Return empty results instead of raising
            return {
                "type": "trends",
                "time_range": "24h",
                "trends": [],
                "filters_applied": intent.filters,
                "keywords": intent.keywords
            }
    
    async def _get_audit_summary(self, db: AsyncSession, intent: QueryIntent) -> Dict[str, Any]:
        """Get a summary of audit events"""
        # Get recent events
        recent_events_query = select(AuditLog).order_by(
            AuditLog.timestamp.desc()
        ).limit(10)
        recent_events_result = await db.execute(recent_events_query)
        recent_events = recent_events_result.scalars().all()
        
        # Get counts by status (AuditLog doesn't have severity field)
        status_summary_query = select(
            AuditLog.status,
            func.count(AuditLog.audit_id).label('count')
        ).group_by(AuditLog.status)
        status_summary_result = await db.execute(status_summary_query)
        status_summary = status_summary_result.all()
        
        # Get top services
        service_summary_query = select(
            AuditLog.service_name,
            func.count(AuditLog.audit_id).label('count')
        ).group_by(AuditLog.service_name).order_by(
            func.count(AuditLog.audit_id).desc()
        ).limit(5)
        service_summary_result = await db.execute(service_summary_query)
        service_summary = service_summary_result.all()
        
        return {
            "type": "summary",
            "recent_events": [
                {
                    "audit_id": str(event.audit_id),
                    "event_type": event.event_type,
                    "action": event.action,
                    "status": event.status,
                    "timestamp": event.timestamp.isoformat()
                }
                for event in recent_events
            ],
            "status_breakdown": {str(st.status): st.count for st in status_summary},
            "top_services": {str(svc.service_name): svc.count for svc in service_summary},
            "filters_applied": intent.filters,
            "keywords": intent.keywords
        }
    
    async def _get_audit_alerts(self, db: AsyncSession, intent: QueryIntent) -> Dict[str, Any]:
        """Get alerts based on audit events"""
        # Get high severity events in the last hour
        alert_time = datetime.now() - timedelta(hours=1)
        
        # Get failed events (since AuditLog doesn't have severity field)
        failed_events_query = select(AuditLog).where(
            and_(
                AuditLog.status != "success",
                AuditLog.timestamp >= alert_time
            )
        ).order_by(AuditLog.timestamp.desc())
        failed_events_result = await db.execute(failed_events_query)
        failed_events = failed_events_result.scalars().all()
        
        return {
            "type": "alerts",
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
            "alert_count": len(failed_events),
            "filters_applied": intent.filters,
            "keywords": intent.keywords
        }
    
    async def _query_cloud_events(self, intent: QueryIntent) -> Dict[str, Any]:
        """Query cloud events from the events service"""
        try:
            # Build query parameters based on intent
            params = {}
            
            # Add time range filters
            if intent.time_range:
                if intent.time_range.get('start'):
                    params['start_time'] = intent.time_range['start'].isoformat()
                if intent.time_range.get('end'):
                    params['end_time'] = intent.time_range['end'].isoformat()
            
            # Add other filters
            if intent.filters.get('severity'):
                params['severity'] = intent.filters['severity']
            if intent.filters.get('provider'):
                params['cloud_provider'] = intent.filters['provider']
            if intent.filters.get('service'):
                params['service_name'] = intent.filters['service']
            if intent.filters.get('region'):
                params['region'] = intent.filters['region']
            
            # Add limit
            if intent.limit:
                params['limit'] = intent.limit
            
            # Query the events service
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://events:8003/api/v1/events/events",
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    events = data.get('events', [])
                    
                    return {
                        "type": "cloud_events",
                        "events": events,
                        "count": len(events),
                        "filters_applied": intent.filters,
                        "keywords": intent.keywords,
                        "query": intent.original_query
                    }
                else:
                    return {
                        "type": "cloud_events",
                        "events": [],
                        "count": 0,
                        "error": f"Events service returned status {response.status_code}",
                        "filters_applied": intent.filters,
                        "keywords": intent.keywords
                    }
                    
        except Exception as e:
            logger.error(f"Error querying cloud events: {e}")
            return {
                "type": "cloud_events",
                "events": [],
                "count": 0,
                "error": f"Failed to query cloud events: {str(e)}",
                "filters_applied": intent.filters,
                "keywords": intent.keywords
            }
    
    async def _query_incidents(self, intent: QueryIntent) -> Dict[str, Any]:
        """Query incidents from the events service"""
        try:
            # Build query parameters based on intent
            params = {}
            
            # Add time range filters
            if intent.time_range:
                if intent.time_range.get('start'):
                    params['start_time'] = intent.time_range['start'].isoformat()
                if intent.time_range.get('end'):
                    params['end_time'] = intent.time_range['end'].isoformat()
            
            # Add other filters
            if intent.filters.get('severity'):
                params['severity'] = intent.filters['severity']
            if intent.filters.get('status'):
                params['status'] = intent.filters['status']
            if intent.filters.get('service'):
                params['affected_services'] = intent.filters['service']
            if intent.filters.get('region'):
                params['affected_regions'] = intent.filters['region']
            
            # Add limit
            if intent.limit:
                params['limit'] = intent.limit
            
            # Query the events service for incidents
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://events:8003/api/v1/incidents/",
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    incidents = data.get('incidents', [])
                    
                    return {
                        "type": "incidents",
                        "incidents": incidents,
                        "count": len(incidents),
                        "filters_applied": intent.filters,
                        "keywords": intent.keywords,
                        "query": intent.original_query
                    }
                else:
                    return {
                        "type": "incidents",
                        "incidents": [],
                        "count": 0,
                        "error": f"Events service returned status {response.status_code}",
                        "filters_applied": intent.filters,
                        "keywords": intent.keywords
                    }
                    
        except Exception as e:
            logger.error(f"Error querying incidents: {e}")
            return {
                "type": "incidents",
                "incidents": [],
                "count": 0,
                "error": f"Failed to query incidents: {str(e)}",
                "filters_applied": intent.filters,
                "keywords": intent.keywords
            }
    
    async def _query_outages(self, intent: QueryIntent) -> Dict[str, Any]:
        """Query cloud provider outages from the events service"""
        try:
            # Build query parameters based on intent
            params = {}
            
            # Add time range filters
            if intent.time_range:
                if intent.time_range.get('start'):
                    params['start_time'] = intent.time_range['start'].isoformat()
                if intent.time_range.get('end'):
                    params['end_time'] = intent.time_range['end'].isoformat()
            
            # Add other filters
            if intent.filters.get('provider'):
                params['provider'] = intent.filters['provider']
            if intent.filters.get('service'):
                params['service'] = intent.filters['service']
            if intent.filters.get('region'):
                params['region'] = intent.filters['region']
            if intent.filters.get('severity'):
                params['severity'] = intent.filters['severity']
            
            # Query the events service for outages
            async with httpx.AsyncClient() as client:
                # Try active outages first
                response = await client.get(
                    "http://events:8003/api/v1/outages/active",
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    outages = data.get('outages', [])
                    
                    return {
                        "type": "outages",
                        "outages": outages,
                        "count": len(outages),
                        "filters_applied": intent.filters,
                        "keywords": intent.keywords,
                        "query": intent.original_query
                    }
                else:
                    # Try historical outages if active fails
                    response = await client.get(
                        "http://events:8003/api/v1/outages/history",
                        params=params,
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        outages = data.get('outages', [])
                        
                        return {
                            "type": "outages",
                            "outages": outages,
                            "count": len(outages),
                            "filters_applied": intent.filters,
                            "keywords": intent.keywords,
                            "query": intent.original_query
                        }
                    else:
                        return {
                            "type": "outages",
                            "outages": [],
                            "count": 0,
                            "error": f"Events service returned status {response.status_code}",
                            "filters_applied": intent.filters,
                            "keywords": intent.keywords
                        }
                    
        except Exception as e:
            logger.error(f"Error querying outages: {e}")
            return {
                "type": "outages",
                "outages": [],
                "count": 0,
                "error": f"Failed to query outages: {str(e)}",
                "filters_applied": intent.filters,
                "keywords": intent.keywords
            }
    
    def get_mcp_server(self) -> FastMCP:
        """Get the FastMCP server instance"""
        return self.mcp
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8001):
        """Start the FastMCP server"""
        logger.info(f"Starting FastMCP server on {host}:{port}")
        await self.mcp.run_async(transport="http", host=host, port=port)


# Global instance
mcp_service = MCPAuditService()
