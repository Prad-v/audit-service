"""
Mock LLM Service for Development and Testing

This service provides mock LLM responses for development and testing purposes
when real LLM providers are not available or configured.
"""

import json
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class MockLLMService:
    """Mock LLM service for development and testing"""
    
    def __init__(self):
        self.provider_id = "mock-llm-service"
        self.name = "Mock LLM Service"
    
    async def summarize_mcp_result(self, query: str, mcp_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a mock summary for MCP results"""
        try:
            result_type = mcp_result.get("type", "unknown")
            count = mcp_result.get("count", 0)
            
            # Generate appropriate mock summary based on result type
            if result_type == "incidents":
                incidents = mcp_result.get("incidents", [])
                active_count = len([i for i in incidents if i.get("status") == "investigating"])
                resolved_count = len([i for i in incidents if i.get("status") == "resolved"])
                
                summary = f"Found {count} total incidents. {active_count} are currently being investigated, {resolved_count} have been resolved. "
                
                if active_count > 0:
                    summary += "Active incidents include: "
                    active_incidents = [i for i in incidents if i.get("status") == "investigating"][:3]
                    for incident in active_incidents:
                        summary += f"'{incident.get('title', 'Unknown')}' ({incident.get('severity', 'unknown')} severity), "
                    summary = summary.rstrip(", ") + "."
                
            elif result_type == "outages":
                outages = mcp_result.get("outages", [])
                summary = f"Found {count} cloud provider outages. "
                if count > 0:
                    providers = set()
                    services = set()
                    for outage in outages:
                        if outage.get("provider"):
                            providers.add(outage["provider"])
                        if outage.get("service"):
                            services.add(outage["service"])
                    
                    if providers:
                        summary += f"Affected providers: {', '.join(providers)}. "
                    if services:
                        summary += f"Affected services: {', '.join(services)}."
                
            elif result_type == "cloud_events":
                events = mcp_result.get("events", [])
                summary = f"Found {count} cloud provider events. "
                if count > 0:
                    # Group by severity
                    severity_counts = {}
                    for event in events:
                        severity = event.get("severity", "unknown")
                        severity_counts[severity] = severity_counts.get(severity, 0) + 1
                    
                    severity_summary = ", ".join([f"{count} {severity}" for severity, count in severity_counts.items()])
                    summary += f"Severity breakdown: {severity_summary}."
                
            elif result_type == "search_results":
                events = mcp_result.get("events", [])
                summary = f"Found {count} audit events matching your query. "
                if count > 0:
                    # Group by event type
                    event_types = {}
                    for event in events:
                        event_type = event.get("event_type", "unknown")
                        event_types[event_type] = event_types.get(event_type, 0) + 1
                    
                    type_summary = ", ".join([f"{count} {event_type}" for event_type, count in event_types.items()])
                    summary += f"Event types: {type_summary}."
                
            else:
                summary = f"Found {count} results matching your query. This is a mock summary for development purposes."
            
            return {
                "summary": summary,
                "provider_used": self.provider_id,
                "has_llm_analysis": True,
                "mock_response": True
            }
            
        except Exception as e:
            logger.error(f"Error generating mock summary: {e}")
            return {
                "summary": f"Mock summary generation failed: {str(e)}. Showing raw results.",
                "provider_used": self.provider_id,
                "has_llm_analysis": False,
                "mock_response": True
            }


# Global instance
mock_llm_service = MockLLMService()
