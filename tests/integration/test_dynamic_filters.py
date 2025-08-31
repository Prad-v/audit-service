"""
Integration tests for dynamic filtering functionality.
"""

import json
import pytest
from datetime import datetime, timezone
from typing import Dict, Any

from app.models.audit import DynamicFilter, DynamicFilterGroup, FilterOperator
from app.services.dynamic_filter_service import dynamic_filter_service


class TestDynamicFilters:
    """Test dynamic filtering functionality."""
    
    def test_dynamic_filter_creation(self):
        """Test creating dynamic filters."""
        # Test basic filter
        filter1 = DynamicFilter(
            field="event_type",
            operator=FilterOperator.EQUALS,
            value="user_login"
        )
        assert filter1.field == "event_type"
        assert filter1.operator == FilterOperator.EQUALS
        assert filter1.value == "user_login"
        assert filter1.case_sensitive is True
        
        # Test filter with case insensitive
        filter2 = DynamicFilter(
            field="status",
            operator=FilterOperator.NOT_EQUALS,
            value="success",
            case_sensitive=False
        )
        assert filter2.case_sensitive is False
        
        # Test list value
        filter3 = DynamicFilter(
            field="event_type",
            operator=FilterOperator.IN,
            value=["user_login", "user_logout"]
        )
        assert filter3.value == ["user_login", "user_logout"]
        
        # Test null check
        filter4 = DynamicFilter(
            field="correlation_id",
            operator=FilterOperator.IS_NULL
        )
        assert filter4.value is None
    
    def test_dynamic_filter_validation(self):
        """Test dynamic filter validation."""
        # Test empty field
        with pytest.raises(ValueError, match="Field name cannot be empty"):
            DynamicFilter(
                field="",
                operator=FilterOperator.EQUALS,
                value="test"
            )
        
        # Test value required for non-null operators
        with pytest.raises(ValueError, match="Value is required"):
            DynamicFilter(
                field="event_type",
                operator=FilterOperator.EQUALS,
                value=None
            )
        
        # Test value not allowed for null operators
        with pytest.raises(ValueError, match="Value should not be provided"):
            DynamicFilter(
                field="correlation_id",
                operator=FilterOperator.IS_NULL,
                value="test"
            )
    
    def test_filter_group_creation(self):
        """Test creating filter groups."""
        filters = [
            DynamicFilter(field="event_type", operator=FilterOperator.EQUALS, value="user_login"),
            DynamicFilter(field="status", operator=FilterOperator.EQUALS, value="success")
        ]
        
        group = DynamicFilterGroup(filters=filters, operator="AND")
        assert len(group.filters) == 2
        assert group.operator == "AND"
        
        # Test OR operator
        group_or = DynamicFilterGroup(filters=filters, operator="OR")
        assert group_or.operator == "OR"
    
    def test_filter_group_validation(self):
        """Test filter group validation."""
        # Test empty filters
        with pytest.raises(ValueError, match="At least one filter must be provided"):
            DynamicFilterGroup(filters=[], operator="AND")
        
        # Test invalid operator
        filters = [DynamicFilter(field="event_type", operator=FilterOperator.EQUALS, value="test")]
        with pytest.raises(ValueError, match="Operator must be 'AND' or 'OR'"):
            DynamicFilterGroup(filters=filters, operator="XOR")
    
    def test_dynamic_filter_service_field_mappings(self):
        """Test field mappings in dynamic filter service."""
        # Test standard fields
        assert 'event_type' in dynamic_filter_service.field_mappings
        assert 'user_id' in dynamic_filter_service.field_mappings
        assert 'timestamp' in dynamic_filter_service.field_mappings
        
        # Test JSON fields
        assert 'request_data' in dynamic_filter_service.field_mappings
        assert 'response_data' in dynamic_filter_service.field_mappings
        assert 'metadata' in dynamic_filter_service.field_mappings
    
    def test_dynamic_filter_service_available_fields(self):
        """Test getting available fields."""
        fields = dynamic_filter_service.get_available_fields()
        
        # Check standard fields
        assert 'event_type' in fields
        assert 'user_id' in fields
        assert 'timestamp' in fields
        
        # Check JSON nested fields
        assert 'request_data.method' in fields
        assert 'response_data.status_code' in fields
        assert 'metadata.user_id' in fields
    
    def test_dynamic_filter_service_supported_operators(self):
        """Test getting supported operators."""
        operators = dynamic_filter_service.get_supported_operators()
        
        expected_operators = [
            'eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'in', 'not_in',
            'contains', 'not_contains', 'starts_with', 'ends_with',
            'is_null', 'is_not_null', 'regex'
        ]
        
        for op in expected_operators:
            assert op in operators
    
    def test_dynamic_filter_service_examples(self):
        """Test filter examples."""
        examples = dynamic_filter_service.create_filter_examples()
        
        assert len(examples) > 0
        
        # Check example structure
        for example in examples:
            assert 'field' in example
            assert 'operator' in example
            assert 'value' in example
            assert 'description' in example
    
    def test_field_validation(self):
        """Test field access validation."""
        # Valid fields
        assert dynamic_filter_service.validate_field_access("event_type")
        assert dynamic_filter_service.validate_field_access("user_id")
        assert dynamic_filter_service.validate_field_access("request_data.method")
        assert dynamic_filter_service.validate_field_access("metadata.user_id")
        
        # Invalid fields
        assert not dynamic_filter_service.validate_field_access("invalid_field")
        assert not dynamic_filter_service.validate_field_access("invalid.json.field")
    
    def test_json_filter_serialization(self):
        """Test JSON serialization of filters."""
        filter1 = DynamicFilter(
            field="event_type",
            operator=FilterOperator.EQUALS,
            value="user_login"
        )
        
        filter_json = filter1.json()
        filter_dict = json.loads(filter_json)
        
        assert filter_dict["field"] == "event_type"
        assert filter_dict["operator"] == "eq"
        assert filter_dict["value"] == "user_login"
        assert filter_dict["case_sensitive"] is True
    
    def test_filter_group_serialization(self):
        """Test JSON serialization of filter groups."""
        filters = [
            DynamicFilter(field="event_type", operator=FilterOperator.EQUALS, value="user_login"),
            DynamicFilter(field="status", operator=FilterOperator.EQUALS, value="success")
        ]
        
        group = DynamicFilterGroup(filters=filters, operator="AND")
        group_json = group.json()
        group_dict = json.loads(group_json)
        
        assert group_dict["operator"] == "AND"
        assert len(group_dict["filters"]) == 2
        assert group_dict["filters"][0]["field"] == "event_type"
        assert group_dict["filters"][1]["field"] == "status"


class TestDynamicFilterOperators:
    """Test different filter operators."""
    
    def test_equals_operator(self):
        """Test equals operator."""
        filter1 = DynamicFilter(
            field="event_type",
            operator=FilterOperator.EQUALS,
            value="user_login"
        )
        assert filter1.operator == FilterOperator.EQUALS
    
    def test_not_equals_operator(self):
        """Test not equals operator."""
        filter1 = DynamicFilter(
            field="status",
            operator=FilterOperator.NOT_EQUALS,
            value="success"
        )
        assert filter1.operator == FilterOperator.NOT_EQUALS
    
    def test_greater_than_operator(self):
        """Test greater than operator."""
        filter1 = DynamicFilter(
            field="timestamp",
            operator=FilterOperator.GREATER_THAN,
            value="2024-01-01T00:00:00Z"
        )
        assert filter1.operator == FilterOperator.GREATER_THAN
    
    def test_contains_operator(self):
        """Test contains operator."""
        filter1 = DynamicFilter(
            field="metadata.user_id",
            operator=FilterOperator.CONTAINS,
            value="admin"
        )
        assert filter1.operator == FilterOperator.CONTAINS
    
    def test_in_operator(self):
        """Test in operator."""
        filter1 = DynamicFilter(
            field="event_type",
            operator=FilterOperator.IN,
            value=["user_login", "user_logout", "data_access"]
        )
        assert filter1.operator == FilterOperator.IN
        assert len(filter1.value) == 3
    
    def test_regex_operator(self):
        """Test regex operator."""
        filter1 = DynamicFilter(
            field="ip_address",
            operator=FilterOperator.REGEX,
            value=r"^192\.168\.",
            case_sensitive=False
        )
        assert filter1.operator == FilterOperator.REGEX
        assert filter1.case_sensitive is False


class TestComplexFilterScenarios:
    """Test complex filtering scenarios."""
    
    def test_nested_json_filter(self):
        """Test filtering on nested JSON fields."""
        filter1 = DynamicFilter(
            field="request_data.method",
            operator=FilterOperator.IN,
            value=["POST", "PUT", "DELETE"]
        )
        assert filter1.field == "request_data.method"
        assert filter1.value == ["POST", "PUT", "DELETE"]
    
    def test_multiple_conditions_group(self):
        """Test filter group with multiple conditions."""
        filters = [
            DynamicFilter(field="event_type", operator=FilterOperator.EQUALS, value="user_login"),
            DynamicFilter(field="status", operator=FilterOperator.EQUALS, value="failed"),
            DynamicFilter(field="ip_address", operator=FilterOperator.STARTS_WITH, value="192.168")
        ]
        
        group = DynamicFilterGroup(filters=filters, operator="AND")
        assert len(group.filters) == 3
        assert group.operator == "AND"
    
    def test_or_condition_group(self):
        """Test filter group with OR conditions."""
        filters = [
            DynamicFilter(field="event_type", operator=FilterOperator.EQUALS, value="user_login"),
            DynamicFilter(field="event_type", operator=FilterOperator.EQUALS, value="user_logout")
        ]
        
        group = DynamicFilterGroup(filters=filters, operator="OR")
        assert group.operator == "OR"
    
    def test_mixed_case_sensitivity(self):
        """Test filters with different case sensitivity settings."""
        filters = [
            DynamicFilter(
                field="event_type",
                operator=FilterOperator.EQUALS,
                value="User_Login",
                case_sensitive=True
            ),
            DynamicFilter(
                field="status",
                operator=FilterOperator.CONTAINS,
                value="SUCCESS",
                case_sensitive=False
            )
        ]
        
        assert filters[0].case_sensitive is True
        assert filters[1].case_sensitive is False


if __name__ == "__main__":
    pytest.main([__file__])
