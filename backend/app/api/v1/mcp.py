"""
FastMCP API endpoints for natural language audit event queries

This module provides REST API endpoints that integrate with the FastMCP service
to allow users to query audit events using natural language.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.services.mcp_service import mcp_service
from app.api.middleware import get_current_user

router = APIRouter(prefix="/mcp", tags=["MCP - Natural Language Queries"])


class NaturalLanguageQuery(BaseModel):
    """Request model for natural language queries"""
    query: str = Field(..., description="Natural language query for audit events")
    limit: Optional[int] = Field(50, description="Maximum number of results to return")
    include_metadata: Optional[bool] = Field(True, description="Include metadata in results")


class MCPQueryResponse(BaseModel):
    """Response model for MCP queries"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    query_processed: str
    query_type: str
    result_count: Optional[int] = None


class MCPHealthResponse(BaseModel):
    """Health check response for MCP service"""
    status: str
    service: str
    version: str
    capabilities: List[str]


@router.get("/health", response_model=MCPHealthResponse)
async def mcp_health_check():
    """Health check endpoint for MCP service"""
    return MCPHealthResponse(
        status="healthy",
        service="audit-events-mcp",
        version="1.0.0",
        capabilities=[
            "natural_language_search",
            "audit_analytics",
            "trend_analysis",
            "alert_generation",
            "summary_reports"
        ]
    )


@router.post("/query", response_model=MCPQueryResponse)
async def query_audit_events(
    request: NaturalLanguageQuery,
    provider_id: Optional[str] = Query(None, description="LLM provider ID for summarization"),
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Query audit events using natural language
    
    Examples:
    - "Show me all login events from today"
    - "How many failed authentication attempts in the last hour?"
    - "Get high severity events from the API service"
    - "Show me trends in user activity over the past week"
    - "What are the recent security alerts?"
    """
    try:
        # Process the query through MCP service
        result = await mcp_service._execute_query(
            mcp_service._parse_query_intent(request.query),
            provider_id
        )
        
        return MCPQueryResponse(
            success=True,  # Query was processed successfully
            data=result,
            error=None,
            query_processed=request.query,
            query_type=result.get("type", "search"),
            result_count=result.get("count", 0)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


@router.get("/query", response_model=MCPQueryResponse)
async def query_audit_events_get(
    q: str = Query(..., description="Natural language query"),
    limit: int = Query(50, description="Maximum number of results"),
    provider_id: Optional[str] = Query(None, description="LLM provider ID for summarization"),
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Query audit events using natural language (GET method)
    
    Examples:
    - /mcp/query?q=Show me all login events from today
    - /mcp/query?q=How many failed authentication attempts&limit=10
    """
    try:
        # Process the query through MCP service
        result = await mcp_service._execute_query(
            mcp_service._parse_query_intent(q),
            provider_id
        )
        
        return MCPQueryResponse(
            success=True,  # Query was processed successfully
            data=result,
            error=None,
            query_processed=q,
            query_type=result.get("type", "search"),
            result_count=result.get("count", 0)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


@router.get("/summary", response_model=MCPQueryResponse)
async def get_audit_summary(
    time_range: str = Query("24h", description="Time range for summary"),
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Get a summary of audit events
    
    Args:
        time_range: Time range for summary (e.g., "1h", "24h", "7d", "30d")
    """
    try:
        # Process the summary query through MCP service
        summary_query = f"Give me a summary of audit events for the last {time_range}"
        result = await mcp_service._execute_query(
            mcp_service._parse_query_intent(summary_query)
        )
        
        return MCPQueryResponse(
            success=result.get("success", False),
            data=result.get("data"),
            error=result.get("error"),
            query_processed=f"Get audit summary for {time_range}",
            query_type="summary",
            result_count=result.get("data", {}).get("count", 0) if result.get("data") else 0
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get summary: {str(e)}"
        )


@router.get("/trends", response_model=MCPQueryResponse)
async def get_audit_trends(
    time_range: str = Query("7d", description="Time range for trends"),
    metric: str = Query("count", description="Metric to analyze"),
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Get trends in audit events
    
    Args:
        time_range: Time range for trends (e.g., "1h", "24h", "7d", "30d")
        metric: Metric to analyze (e.g., "count", "severity", "service")
    """
    try:
        # Process the trends query through MCP service
        trends_query = f"Show me trends in {metric} over the last {time_range}"
        result = await mcp_service._execute_query(
            mcp_service._parse_query_intent(trends_query)
        )
        
        return MCPQueryResponse(
            success=result.get("success", False),
            data=result.get("data"),
            error=result.get("error"),
            query_processed=f"Get trends for {metric} over {time_range}",
            query_type="trends",
            result_count=result.get("data", {}).get("count", 0) if result.get("data") else 0
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get trends: {str(e)}"
        )


@router.get("/alerts", response_model=MCPQueryResponse)
async def get_audit_alerts(
    severity: str = Query("high", description="Minimum severity level"),
    time_range: str = Query("1h", description="Time range for alerts"),
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Get alerts based on audit events
    
    Args:
        severity: Minimum severity level (e.g., "low", "medium", "high", "critical")
        time_range: Time range for alerts (e.g., "1h", "24h", "7d")
    """
    try:
        # Process the alerts query through MCP service
        alerts_query = f"Show me {severity} severity alerts from the last {time_range}"
        result = await mcp_service._execute_query(
            mcp_service._parse_query_intent(alerts_query)
        )
        
        return MCPQueryResponse(
            success=result.get("success", False),
            data=result.get("data"),
            error=result.get("error"),
            query_processed=f"Get {severity} alerts for {time_range}",
            query_type="alerts",
            result_count=result.get("data", {}).get("alert_count", 0) if result.get("data") else 0
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get alerts: {str(e)}"
        )


@router.get("/capabilities")
async def get_mcp_capabilities():
    """Get the capabilities of the MCP service"""
    try:
        # Return capabilities directly
        result = {
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
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get capabilities: {str(e)}"
        )



