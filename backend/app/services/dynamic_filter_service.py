"""
Dynamic Filter Service

This module provides dynamic filtering capabilities for audit events,
allowing queries on any field with flexible operators.
"""

import re
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from sqlalchemy import and_, or_, text, func, case, cast, String
from sqlalchemy.sql import Select
from sqlalchemy.dialects.postgresql import JSONB

from app.models.audit import DynamicFilter, DynamicFilterGroup, FilterOperator
from app.db.database import AuditLog

logger = logging.getLogger(__name__)


class DynamicFilterService:
    """Service for applying dynamic filters to SQLAlchemy queries."""
    
    def __init__(self):
        """Initialize the dynamic filter service."""
        # Map of field names to their SQLAlchemy column references
        self.field_mappings = {
            # Standard fields
            'audit_id': AuditLog.audit_id,
            'timestamp': AuditLog.timestamp,
            'event_type': AuditLog.event_type,
            'action': AuditLog.action,
            'status': AuditLog.status,
            'tenant_id': AuditLog.tenant_id,
            'service_name': AuditLog.service_name,
            'user_id': AuditLog.user_id,
            'resource_type': AuditLog.resource_type,
            'resource_id': AuditLog.resource_id,
            'correlation_id': AuditLog.correlation_id,
            'session_id': AuditLog.session_id,
            'ip_address': AuditLog.ip_address,
            'user_agent': AuditLog.user_agent,
            'created_at': AuditLog.created_at,
            'updated_at': AuditLog.updated_at,
            
            # JSON fields (for nested access)
            'request_data': AuditLog.request_data,
            'response_data': AuditLog.response_data,
            'metadata': AuditLog.event_metadata,
        }
    
    def apply_dynamic_filters(self, query: Select, filters: List[DynamicFilter]) -> Select:
        """Apply a list of dynamic filters to a query."""
        if not filters:
            return query
        
        filter_conditions = []
        for filter_item in filters:
            condition = self._build_filter_condition(filter_item)
            if condition is not None:
                filter_conditions.append(condition)
        
        if filter_conditions:
            query = query.where(and_(*filter_conditions))
        
        return query
    
    def apply_filter_groups(self, query: Select, filter_groups: List[DynamicFilterGroup]) -> Select:
        """Apply filter groups to a query."""
        if not filter_groups:
            return query
        
        group_conditions = []
        for group in filter_groups:
            group_condition = self._build_group_condition(group)
            if group_condition is not None:
                group_conditions.append(group_condition)
        
        if group_conditions:
            query = query.where(and_(*group_conditions))
        
        return query
    
    def _build_group_condition(self, group: DynamicFilterGroup):
        """Build a condition for a filter group."""
        if not group.filters:
            return None
        
        filter_conditions = []
        for filter_item in group.filters:
            condition = self._build_filter_condition(filter_item)
            if condition is not None:
                filter_conditions.append(condition)
        
        if not filter_conditions:
            return None
        
        if group.operator == "AND":
            return and_(*filter_conditions)
        else:  # OR
            return or_(*filter_conditions)
    
    def _build_filter_condition(self, filter_item: DynamicFilter):
        """Build a SQLAlchemy condition for a single filter."""
        try:
            column = self._get_column_for_field(filter_item.field)
            if column is None:
                logger.warning(f"Unknown field: {filter_item.field}")
                return None
            
            return self._apply_operator(column, filter_item)
            
        except Exception as e:
            logger.error(f"Error building filter condition for {filter_item.field}: {e}")
            return None
    
    def _get_column_for_field(self, field_path: str):
        """Get the SQLAlchemy column for a field path."""
        # Handle nested JSON field access (e.g., "metadata.user_id")
        if '.' in field_path:
            base_field, json_path = field_path.split('.', 1)
            if base_field in ['request_data', 'response_data', 'metadata']:
                column = self.field_mappings.get(base_field)
                if column is not None:
                    # Use JSONB operators for nested field access
                    return column[json_path]
            return None
        
        # Handle direct field access
        return self.field_mappings.get(field_path)
    
    def _apply_operator(self, column, filter_item: DynamicFilter):
        """Apply the filter operator to the column."""
        operator = filter_item.operator
        value = filter_item.value
        case_sensitive = filter_item.case_sensitive
        
        if operator == FilterOperator.EQUALS:
            # Handle JSON field comparison with proper type casting
            if isinstance(value, str):
                # Cast to text for string comparison (works for both JSONB and extracted JSON values)
                return column.cast(String) == value
            return column == value
        
        elif operator == FilterOperator.NOT_EQUALS:
            # Handle JSON field comparison with proper type casting
            if isinstance(value, str):
                # Cast to text for string comparison (works for both JSONB and extracted JSON values)
                return column.cast(String) != value
            return column != value
        
        elif operator == FilterOperator.GREATER_THAN:
            return column > value
        
        elif operator == FilterOperator.GREATER_THAN_EQUAL:
            return column >= value
        
        elif operator == FilterOperator.LESS_THAN:
            return column < value
        
        elif operator == FilterOperator.LESS_THAN_EQUAL:
            return column <= value
        
        elif operator == FilterOperator.IN:
            if isinstance(value, list):
                return column.in_(value)
            else:
                return column == value
        
        elif operator == FilterOperator.NOT_IN:
            if isinstance(value, list):
                return ~column.in_(value)
            else:
                return column != value
        
        elif operator == FilterOperator.CONTAINS:
            # For JSON fields, cast to text first, then use LIKE
            if isinstance(value, str):
                # Cast to text for string comparison (works for both JSONB and extracted JSON values)
                if case_sensitive:
                    return column.cast(String).like(f"%{value}%")
                else:
                    return column.cast(String).ilike(f"%{value}%")
            else:
                # For non-string values, use containment operator for JSONB
                if isinstance(column.type, JSONB):
                    return column.contains(value)
                else:
                    # For text columns, use ILIKE for case-insensitive or LIKE for case-sensitive
                    if case_sensitive:
                        return column.like(f"%{value}%")
                    else:
                        return column.ilike(f"%{value}%")
        
        elif operator == FilterOperator.NOT_CONTAINS:
            # For JSON fields, cast to text first, then use NOT LIKE
            if isinstance(value, str):
                # Cast to text for string comparison (works for both JSONB and extracted JSON values)
                if case_sensitive:
                    return ~column.cast(String).like(f"%{value}%")
                else:
                    return ~column.cast(String).ilike(f"%{value}%")
            else:
                # For non-string values, use NOT containment operator for JSONB
                if isinstance(column.type, JSONB):
                    return ~column.contains(value)
                else:
                    if case_sensitive:
                        return ~column.like(f"%{value}%")
                    else:
                        return ~column.ilike(f"%{value}%")
        
        elif operator == FilterOperator.STARTS_WITH:
            # For JSON fields, cast to text first
            if isinstance(value, str):
                if case_sensitive:
                    return column.cast(String).like(f"{value}%")
                else:
                    return column.cast(String).ilike(f"{value}%")
            else:
                if case_sensitive:
                    return column.like(f"{value}%")
                else:
                    return column.ilike(f"{value}%")
        
        elif operator == FilterOperator.ENDS_WITH:
            # For JSON fields, cast to text first
            if isinstance(value, str):
                if case_sensitive:
                    return column.cast(String).like(f"%{value}")
                else:
                    return column.cast(String).ilike(f"%{value}")
            else:
                if case_sensitive:
                    return column.like(f"%{value}")
                else:
                    return column.ilike(f"%{value}")
        
        elif operator == FilterOperator.IS_NULL:
            return column.is_(None)
        
        elif operator == FilterOperator.IS_NOT_NULL:
            return column.is_not(None)
        
        elif operator == FilterOperator.REGEX:
            if case_sensitive:
                return column.op('~')(value)
            else:
                return column.op('~*')(value)
        
        else:
            logger.warning(f"Unsupported operator: {operator}")
            return None
    
    def validate_field_access(self, field_path: str) -> bool:
        """Validate if a field path is accessible for filtering."""
        if '.' in field_path:
            base_field, json_path = field_path.split('.', 1)
            return base_field in ['request_data', 'response_data', 'metadata']
        else:
            return field_path in self.field_mappings
    
    def get_available_fields(self) -> List[str]:
        """Get list of available fields for filtering."""
        fields = list(self.field_mappings.keys())
        
        # Add common nested fields for JSON columns
        json_fields = ['request_data', 'response_data', 'metadata']
        common_nested_fields = [
            'method', 'path', 'headers', 'body', 'status_code',
            'user_id', 'session_id', 'login_method', 'error_message',
            'duration', 'size', 'count'
        ]
        
        for json_field in json_fields:
            for nested_field in common_nested_fields:
                fields.append(f"{json_field}.{nested_field}")
        
        return sorted(fields)
    
    def get_supported_operators(self) -> List[str]:
        """Get list of supported operators."""
        return [op.value for op in FilterOperator]
    
    def create_filter_examples(self) -> List[Dict[str, Any]]:
        """Create example filters for documentation."""
        return [
            {
                "field": "event_type",
                "operator": "eq",
                "value": "user_login",
                "description": "Find all user login events"
            },
            {
                "field": "status",
                "operator": "ne",
                "value": "success",
                "description": "Find all non-success events"
            },
            {
                "field": "timestamp",
                "operator": "gte",
                "value": "2024-01-01T00:00:00Z",
                "description": "Find events from 2024 onwards"
            },
            {
                "field": "metadata.user_id",
                "operator": "contains",
                "value": "admin",
                "description": "Find events with admin in user_id metadata"
            },
            {
                "field": "request_data.method",
                "operator": "in",
                "value": ["POST", "PUT", "DELETE"],
                "description": "Find events with write operations"
            },
            {
                "field": "ip_address",
                "operator": "starts_with",
                "value": "192.168",
                "description": "Find events from internal network"
            },
            {
                "field": "response_data.status_code",
                "operator": "gte",
                "value": 400,
                "description": "Find events with error status codes"
            }
        ]


# Global instance
dynamic_filter_service = DynamicFilterService()
