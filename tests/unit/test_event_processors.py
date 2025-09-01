"""
Functional tests for Event Processor transformations

This module tests all transformation functions, filter operations, enrichment rules,
and routing logic for the event processor system.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
import uuid

# Import the functions to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'events-service'))

from app.api.v1.processors import (
    _apply_processor_transformations,
    _apply_transformer_rules,
    _apply_enrichment_rules,
    _apply_filter_rules,
    _apply_routing_rules,
    _apply_transformation_function,
    _get_nested_value,
    _set_nested_value,
    _convert_value_type,
    _evaluate_filter_condition,
    _evaluate_routing_condition
)


class TestEventProcessorTransformations:
    """Test suite for event processor transformation functions"""

    @pytest.fixture
    def sample_event_data(self):
        """Sample event data for testing"""
        return {
            "event_type": "log",
            "severity": "error",
            "message": "database connection failed",
            "source": "app-server-01",
            "user_id": "user123",
            "session_id": "sess456",
            "timestamp": "2024-01-15T10:30:45Z",
            "metadata": {
                "service": "auth-service",
                "region": "us-west-1",
                "environment": "production"
            },
            "numeric_field": 42,
            "boolean_field": True,
            "float_field": 3.14
        }

    @pytest.fixture
    def mock_processor(self):
        """Mock processor object for testing"""
        processor = MagicMock()
        processor.processor_type = "transformer"
        processor.transformations = {}
        return processor

    @pytest.mark.asyncio
    async def test_apply_processor_transformations_transformer(self, sample_event_data, mock_processor):
        """Test applying transformer processor transformations"""
        mock_processor.processor_type = "transformer"
        mock_processor.transformations = {
            "rules": [
                {
                    "source_field": "message",
                    "target_field": "processed_message",
                    "function": "uppercase"
                }
            ]
        }

        result = await _apply_processor_transformations(mock_processor, sample_event_data)
        
        assert "processed_message" in result
        assert result["processed_message"] == "DATABASE CONNECTION FAILED"
        assert result["message"] == "database connection failed"  # Original preserved

    @pytest.mark.asyncio
    async def test_apply_processor_transformations_enricher(self, sample_event_data, mock_processor):
        """Test applying enricher processor transformations"""
        mock_processor.processor_type = "enricher"
        mock_processor.transformations = {
            "enrichments": [
                {
                    "target_field": "correlation_id",
                    "value": "test-uuid",
                    "value_type": "string"
                }
            ]
        }

        result = await _apply_processor_transformations(mock_processor, sample_event_data)
        
        assert "correlation_id" in result
        assert result["correlation_id"] == "test-uuid"

    @pytest.mark.asyncio
    async def test_apply_processor_transformations_filter(self, sample_event_data, mock_processor):
        """Test applying filter processor transformations"""
        mock_processor.processor_type = "filter"
        mock_processor.transformations = {
            "filters": [
                {
                    "field": "severity",
                    "operator": "equals",
                    "value": "error"
                }
            ]
        }

        result = await _apply_processor_transformations(mock_processor, sample_event_data)
        
        # Should return the data since filter condition is met
        assert result is not None
        assert result["severity"] == "error"

    @pytest.mark.asyncio
    async def test_apply_processor_transformations_router(self, sample_event_data, mock_processor):
        """Test applying router processor transformations"""
        mock_processor.processor_type = "router"
        mock_processor.transformations = {
            "routes": [
                {
                    "condition": {
                        "field": "event_type",
                        "operator": "equals",
                        "value": "log"
                    },
                    "destination": "log-queue",
                    "priority": 1
                }
            ]
        }

        result = await _apply_processor_transformations(mock_processor, sample_event_data)
        
        assert "_routing" in result
        assert result["_routing"]["destination"] == "log-queue"
        assert result["_routing"]["priority"] == 1


class TestTransformationFunctions:
    """Test suite for individual transformation functions"""

    def test_uppercase_transformation(self):
        """Test uppercase transformation function"""
        result = asyncio.run(_apply_transformation_function("uppercase", "hello world"))
        assert result == "HELLO WORLD"

    def test_lowercase_transformation(self):
        """Test lowercase transformation function"""
        result = asyncio.run(_apply_transformation_function("lowercase", "HELLO WORLD"))
        assert result == "hello world"

    def test_titlecase_transformation(self):
        """Test titlecase transformation function"""
        result = asyncio.run(_apply_transformation_function("titlecase", "hello world"))
        assert result == "Hello World"

    def test_trim_transformation(self):
        """Test trim transformation function"""
        result = asyncio.run(_apply_transformation_function("trim", "  hello world  "))
        assert result == "hello world"

    def test_reverse_transformation(self):
        """Test reverse transformation function"""
        result = asyncio.run(_apply_transformation_function("reverse", "hello"))
        assert result == "olleh"

    def test_length_transformation(self):
        """Test length transformation function"""
        result = asyncio.run(_apply_transformation_function("length", "hello"))
        assert result == 5

    def test_to_string_transformation(self):
        """Test to_string transformation function"""
        result = asyncio.run(_apply_transformation_function("to_string", 42))
        assert result == "42"

    def test_to_number_transformation(self):
        """Test to_number transformation function"""
        result = asyncio.run(_apply_transformation_function("to_number", "42"))
        assert result == 42

    def test_to_number_float_transformation(self):
        """Test to_number transformation function with float"""
        result = asyncio.run(_apply_transformation_function("to_number", "3.14"))
        assert result == 3.14

    def test_to_boolean_transformation(self):
        """Test to_boolean transformation function"""
        result = asyncio.run(_apply_transformation_function("to_boolean", "true"))
        assert result is True

    def test_timestamp_transformation(self):
        """Test timestamp transformation function"""
        result = asyncio.run(_apply_transformation_function("timestamp", "any_value"))
        # Should return current timestamp in ISO format
        assert isinstance(result, str)
        assert "T" in result
        # Check for either 'Z' or '+00:00' format (both are valid ISO 8601)
        assert "Z" in result or "+00:00" in result

    def test_uuid_transformation(self):
        """Test uuid transformation function"""
        result = asyncio.run(_apply_transformation_function("uuid", "any_value"))
        # Should return a UUID string
        assert isinstance(result, str)
        assert len(result) == 36
        assert result.count("-") == 4

    def test_unknown_transformation_function(self):
        """Test handling of unknown transformation function"""
        result = asyncio.run(_apply_transformation_function("unknown_function", "test"))
        assert result == "test"  # Should return original value


class TestTransformerRules:
    """Test suite for transformer rule processing"""

    @pytest.mark.asyncio
    async def test_apply_transformer_rules_single_rule(self):
        """Test applying a single transformer rule"""
        transformations = {
            "rules": [
                {
                    "source_field": "message",
                    "target_field": "processed_message",
                    "function": "uppercase"
                }
            ]
        }
        
        data = {"message": "hello world"}
        result = await _apply_transformer_rules(transformations, data)
        
        assert result["processed_message"] == "HELLO WORLD"
        assert result["message"] == "hello world"  # Original preserved

    @pytest.mark.asyncio
    async def test_apply_transformer_rules_multiple_rules(self):
        """Test applying multiple transformer rules"""
        transformations = {
            "rules": [
                {
                    "source_field": "message",
                    "target_field": "processed_message",
                    "function": "uppercase"
                },
                {
                    "source_field": "severity",
                    "target_field": "level",
                    "function": "titlecase"
                }
            ]
        }
        
        data = {
            "message": "hello world",
            "severity": "error"
        }
        result = await _apply_transformer_rules(transformations, data)
        
        assert result["processed_message"] == "HELLO WORLD"
        assert result["level"] == "Error"
        assert result["message"] == "hello world"  # Original preserved
        assert result["severity"] == "error"  # Original preserved

    @pytest.mark.asyncio
    async def test_apply_transformer_rules_incomplete_rule(self):
        """Test handling of incomplete transformer rules"""
        transformations = {
            "rules": [
                {
                    "source_field": "message",
                    "target_field": "processed_message"
                    # Missing function
                }
            ]
        }
        
        data = {"message": "hello world"}
        result = await _apply_transformer_rules(transformations, data)
        
        # Should skip incomplete rule and return original data
        assert "processed_message" not in result
        assert result["message"] == "hello world"

    @pytest.mark.asyncio
    async def test_apply_transformer_rules_missing_source_field(self):
        """Test handling of missing source field"""
        transformations = {
            "rules": [
                {
                    "source_field": "nonexistent_field",
                    "target_field": "processed_message",
                    "function": "uppercase"
                }
            ]
        }
        
        data = {"message": "hello world"}
        result = await _apply_transformer_rules(transformations, data)
        
        # Should skip rule with missing source field
        assert "processed_message" not in result
        assert result["message"] == "hello world"


class TestEnrichmentRules:
    """Test suite for enrichment rule processing"""

    @pytest.mark.asyncio
    async def test_apply_enrichment_rules_string(self):
        """Test applying string enrichment rule"""
        transformations = {
            "enrichments": [
                {
                    "target_field": "environment",
                    "value": "production",
                    "value_type": "string"
                }
            ]
        }
        
        data = {"message": "test"}
        result = await _apply_enrichment_rules(transformations, data)
        
        assert result["environment"] == "production"

    @pytest.mark.asyncio
    async def test_apply_enrichment_rules_number(self):
        """Test applying number enrichment rule"""
        transformations = {
            "enrichments": [
                {
                    "target_field": "priority",
                    "value": "1",
                    "value_type": "number"
                }
            ]
        }
        
        data = {"message": "test"}
        result = await _apply_enrichment_rules(transformations, data)
        
        assert result["priority"] == 1

    @pytest.mark.asyncio
    async def test_apply_enrichment_rules_boolean(self):
        """Test applying boolean enrichment rule"""
        transformations = {
            "enrichments": [
                {
                    "target_field": "is_critical",
                    "value": "true",
                    "value_type": "boolean"
                }
            ]
        }
        
        data = {"message": "test"}
        result = await _apply_enrichment_rules(transformations, data)
        
        assert result["is_critical"] is True

    @pytest.mark.asyncio
    async def test_apply_enrichment_rules_timestamp(self):
        """Test applying timestamp enrichment rule"""
        transformations = {
            "enrichments": [
                {
                    "target_field": "processed_at",
                    "value": "now",
                    "value_type": "timestamp"
                }
            ]
        }
        
        data = {"message": "test"}
        result = await _apply_enrichment_rules(transformations, data)
        
        assert "processed_at" in result
        assert isinstance(result["processed_at"], str)

    @pytest.mark.asyncio
    async def test_apply_enrichment_rules_incomplete(self):
        """Test handling of incomplete enrichment rules"""
        transformations = {
            "enrichments": [
                {
                    "target_field": "environment"
                    # Missing value
                }
            ]
        }
        
        data = {"message": "test"}
        result = await _apply_enrichment_rules(transformations, data)
        
        # Should skip incomplete enrichment
        assert "environment" not in result


class TestFilterRules:
    """Test suite for filter rule processing"""

    @pytest.mark.asyncio
    async def test_apply_filter_rules_equals_true(self):
        """Test filter rule with equals operator that passes"""
        transformations = {
            "filters": [
                {
                    "field": "severity",
                    "operator": "equals",
                    "value": "error"
                }
            ]
        }
        
        data = {"severity": "error", "message": "test"}
        result = await _apply_filter_rules(transformations, data)
        
        # Should return data since filter condition is met
        assert result is not None
        assert result["severity"] == "error"

    @pytest.mark.asyncio
    async def test_apply_filter_rules_equals_false(self):
        """Test filter rule with equals operator that fails"""
        transformations = {
            "filters": [
                {
                    "field": "severity",
                    "operator": "equals",
                    "value": "error"
                }
            ]
        }
        
        data = {"severity": "info", "message": "test"}
        result = await _apply_filter_rules(transformations, data)
        
        # Should return None since filter condition is not met
        assert result is None

    @pytest.mark.asyncio
    async def test_apply_filter_rules_contains_true(self):
        """Test filter rule with contains operator that passes"""
        transformations = {
            "filters": [
                {
                    "field": "message",
                    "operator": "contains",
                    "value": "error"
                }
            ]
        }
        
        data = {"message": "database error occurred"}
        result = await _apply_filter_rules(transformations, data)
        
        assert result is not None
        assert result["message"] == "database error occurred"

    @pytest.mark.asyncio
    async def test_apply_filter_rules_contains_false(self):
        """Test filter rule with contains operator that fails"""
        transformations = {
            "filters": [
                {
                    "field": "message",
                    "operator": "contains",
                    "value": "error"
                }
            ]
        }
        
        data = {"message": "database connection successful"}
        result = await _apply_filter_rules(transformations, data)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_apply_filter_rules_greater_than(self):
        """Test filter rule with greater_than operator"""
        transformations = {
            "filters": [
                {
                    "field": "priority",
                    "operator": "greater_than",
                    "value": 5
                }
            ]
        }
        
        data = {"priority": 8, "message": "high priority"}
        result = await _apply_filter_rules(transformations, data)
        
        assert result is not None
        assert result["priority"] == 8

    @pytest.mark.asyncio
    async def test_apply_filter_rules_multiple_filters(self):
        """Test multiple filter rules"""
        transformations = {
            "filters": [
                {
                    "field": "severity",
                    "operator": "equals",
                    "value": "error"
                },
                {
                    "field": "priority",
                    "operator": "greater_than",
                    "value": 5
                }
            ]
        }
        
        data = {"severity": "error", "priority": 8, "message": "test"}
        result = await _apply_filter_rules(transformations, data)
        
        # Should pass both filters
        assert result is not None
        assert result["severity"] == "error"
        assert result["priority"] == 8

    @pytest.mark.asyncio
    async def test_apply_filter_rules_multiple_filters_one_fails(self):
        """Test multiple filter rules where one fails"""
        transformations = {
            "filters": [
                {
                    "field": "severity",
                    "operator": "equals",
                    "value": "error"
                },
                {
                    "field": "priority",
                    "operator": "greater_than",
                    "value": 5
                }
            ]
        }
        
        data = {"severity": "error", "priority": 3, "message": "test"}
        result = await _apply_filter_rules(transformations, data)
        
        # Should fail on second filter
        assert result is None


class TestRoutingRules:
    """Test suite for routing rule processing"""

    @pytest.mark.asyncio
    async def test_apply_routing_rules_condition_met(self):
        """Test routing rule where condition is met"""
        transformations = {
            "routes": [
                {
                    "condition": {
                        "field": "event_type",
                        "operator": "equals",
                        "value": "security"
                    },
                    "destination": "security-queue",
                    "priority": 1
                }
            ]
        }
        
        data = {"event_type": "security", "message": "security alert"}
        result = await _apply_routing_rules(transformations, data)
        
        assert "_routing" in result
        assert result["_routing"]["destination"] == "security-queue"
        assert result["_routing"]["priority"] == 1

    @pytest.mark.asyncio
    async def test_apply_routing_rules_condition_not_met(self):
        """Test routing rule where condition is not met"""
        transformations = {
            "routes": [
                {
                    "condition": {
                        "field": "event_type",
                        "operator": "equals",
                        "value": "security"
                    },
                    "destination": "security-queue",
                    "priority": 1
                }
            ]
        }
        
        data = {"event_type": "log", "message": "log message"}
        result = await _apply_routing_rules(transformations, data)
        
        # Should not add routing info
        assert "_routing" not in result

    @pytest.mark.asyncio
    async def test_apply_routing_rules_multiple_routes(self):
        """Test multiple routing rules"""
        transformations = {
            "routes": [
                {
                    "condition": {
                        "field": "event_type",
                        "operator": "equals",
                        "value": "security"
                    },
                    "destination": "security-queue",
                    "priority": 1
                },
                {
                    "condition": {
                        "field": "severity",
                        "operator": "equals",
                        "value": "error"
                    },
                    "destination": "error-queue",
                    "priority": 2
                }
            ]
        }
        
        data = {"event_type": "log", "severity": "error", "message": "error log"}
        result = await _apply_routing_rules(transformations, data)
        
        # Should match second route
        assert "_routing" in result
        assert result["_routing"]["destination"] == "error-queue"
        assert result["_routing"]["priority"] == 2


class TestUtilityFunctions:
    """Test suite for utility functions"""

    def test_get_nested_value_simple(self):
        """Test getting simple nested value"""
        data = {"field": "value"}
        result = _get_nested_value(data, "field")
        assert result == "value"

    def test_get_nested_value_nested(self):
        """Test getting nested value with dot notation"""
        data = {"metadata": {"service": "auth-service"}}
        result = _get_nested_value(data, "metadata.service")
        assert result == "auth-service"

    def test_get_nested_value_deep_nested(self):
        """Test getting deeply nested value"""
        data = {"level1": {"level2": {"level3": "deep_value"}}}
        result = _get_nested_value(data, "level1.level2.level3")
        assert result == "deep_value"

    def test_get_nested_value_missing(self):
        """Test getting missing nested value"""
        data = {"field": "value"}
        result = _get_nested_value(data, "missing")
        assert result is None

    def test_get_nested_value_partial_missing(self):
        """Test getting value with partially missing path"""
        data = {"level1": {"level2": "value"}}
        result = _get_nested_value(data, "level1.level2.level3")
        assert result is None

    def test_set_nested_value_simple(self):
        """Test setting simple value"""
        data = {}
        _set_nested_value(data, "field", "value")
        assert data["field"] == "value"

    def test_set_nested_value_nested(self):
        """Test setting nested value"""
        data = {}
        _set_nested_value(data, "metadata.service", "auth-service")
        assert data["metadata"]["service"] == "auth-service"

    def test_set_nested_value_deep_nested(self):
        """Test setting deeply nested value"""
        data = {}
        _set_nested_value(data, "level1.level2.level3", "deep_value")
        assert data["level1"]["level2"]["level3"] == "deep_value"

    def test_set_nested_value_existing(self):
        """Test setting value in existing nested structure"""
        data = {"level1": {"level2": {"existing": "old"}}}
        _set_nested_value(data, "level1.level2.new", "new_value")
        assert data["level1"]["level2"]["new"] == "new_value"
        assert data["level1"]["level2"]["existing"] == "old"  # Preserved

    def test_convert_value_type_string(self):
        """Test string type conversion"""
        result = _convert_value_type("test", "string")
        assert result == "test"

    def test_convert_value_type_number_int(self):
        """Test number type conversion to int"""
        result = _convert_value_type("42", "number")
        assert result == 42

    def test_convert_value_type_number_float(self):
        """Test number type conversion to float"""
        result = _convert_value_type("3.14", "number")
        assert result == 3.14

    def test_convert_value_type_boolean_true(self):
        """Test boolean type conversion for true values"""
        for value in ["true", "1", "yes", "on"]:
            result = _convert_value_type(value, "boolean")
            assert result is True

    def test_convert_value_type_boolean_false(self):
        """Test boolean type conversion for false values"""
        for value in ["false", "0", "no", "off"]:
            result = _convert_value_type(value, "boolean")
            assert result is False

    def test_convert_value_type_timestamp(self):
        """Test timestamp type conversion"""
        result = _convert_value_type("2024-01-15T10:30:45Z", "timestamp")
        assert result == "2024-01-15T10:30:45Z"  # Should preserve valid timestamp

        result = _convert_value_type("invalid", "timestamp")
        assert isinstance(result, str)  # Should return current timestamp


class TestFilterConditionEvaluation:
    """Test suite for filter condition evaluation"""

    def test_evaluate_filter_condition_equals_true(self):
        """Test equals operator that evaluates to true"""
        result = _evaluate_filter_condition("error", "equals", "error")
        assert result is True

    def test_evaluate_filter_condition_equals_false(self):
        """Test equals operator that evaluates to false"""
        result = _evaluate_filter_condition("error", "equals", "warning")
        assert result is False

    def test_evaluate_filter_condition_not_equals_true(self):
        """Test not_equals operator that evaluates to true"""
        result = _evaluate_filter_condition("error", "not_equals", "warning")
        assert result is True

    def test_evaluate_filter_condition_not_equals_false(self):
        """Test not_equals operator that evaluates to false"""
        result = _evaluate_filter_condition("error", "not_equals", "error")
        assert result is False

    def test_evaluate_filter_condition_contains_true(self):
        """Test contains operator that evaluates to true"""
        result = _evaluate_filter_condition("database error occurred", "contains", "error")
        assert result is True

    def test_evaluate_filter_condition_contains_false(self):
        """Test contains operator that evaluates to false"""
        result = _evaluate_filter_condition("database connection successful", "contains", "error")
        assert result is False

    def test_evaluate_filter_condition_starts_with_true(self):
        """Test starts_with operator that evaluates to true"""
        result = _evaluate_filter_condition("error message", "starts_with", "error")
        assert result is True

    def test_evaluate_filter_condition_starts_with_false(self):
        """Test starts_with operator that evaluates to false"""
        result = _evaluate_filter_condition("this is an error message", "starts_with", "error")
        assert result is False

    def test_evaluate_filter_condition_ends_with_true(self):
        """Test ends_with operator that evaluates to true"""
        result = _evaluate_filter_condition("this is an error", "ends_with", "error")
        assert result is True

    def test_evaluate_filter_condition_ends_with_false(self):
        """Test ends_with operator that evaluates to false"""
        result = _evaluate_filter_condition("error message", "ends_with", "error")
        assert result is False

    def test_evaluate_filter_condition_greater_than_true(self):
        """Test greater_than operator that evaluates to true"""
        result = _evaluate_filter_condition(10, "greater_than", 5)
        assert result is True

    def test_evaluate_filter_condition_greater_than_false(self):
        """Test greater_than operator that evaluates to false"""
        result = _evaluate_filter_condition(3, "greater_than", 5)
        assert result is False

    def test_evaluate_filter_condition_less_than_true(self):
        """Test less_than operator that evaluates to true"""
        result = _evaluate_filter_condition(3, "less_than", 5)
        assert result is True

    def test_evaluate_filter_condition_less_than_false(self):
        """Test less_than operator that evaluates to false"""
        result = _evaluate_filter_condition(10, "less_than", 5)
        assert result is False

    def test_evaluate_filter_condition_unknown_operator(self):
        """Test handling of unknown operator"""
        result = _evaluate_filter_condition("value", "unknown_operator", "other")
        assert result is True  # Should default to True for unknown operators


class TestIntegrationScenarios:
    """Test suite for integration scenarios"""

    @pytest.mark.asyncio
    async def test_complex_transformation_scenario(self):
        """Test a complex transformation scenario with multiple rules"""
        mock_processor = MagicMock()
        mock_processor.processor_type = "transformer"
        mock_processor.transformations = {
            "rules": [
                {
                    "source_field": "message",
                    "target_field": "processed_message",
                    "function": "uppercase"
                },
                {
                    "source_field": "severity",
                    "target_field": "level",
                    "function": "titlecase"
                },
                {
                    "source_field": "user_id",
                    "target_field": "user_hash",
                    "function": "length"
                }
            ]
        }

        event_data = {
            "message": "database connection failed",
            "severity": "error",
            "user_id": "user123",
            "event_type": "log"
        }

        result = await _apply_processor_transformations(mock_processor, event_data)

        assert result["processed_message"] == "DATABASE CONNECTION FAILED"
        assert result["level"] == "Error"
        assert result["user_hash"] == 7  # Length of "user123"
        assert result["message"] == "database connection failed"  # Original preserved
        assert result["severity"] == "error"  # Original preserved
        assert result["user_id"] == "user123"  # Original preserved

    @pytest.mark.asyncio
    async def test_transformer_with_filter_scenario(self):
        """Test transformer followed by filter"""
        # First apply transformer
        mock_transformer = MagicMock()
        mock_transformer.processor_type = "transformer"
        mock_transformer.transformations = {
            "rules": [
                {
                    "source_field": "message",
                    "target_field": "processed_message",
                    "function": "uppercase"
                }
            ]
        }

        event_data = {
            "message": "database connection failed",
            "severity": "error",
            "priority": 8
        }

        # Apply transformer
        transformed_data = await _apply_processor_transformations(mock_transformer, event_data)
        assert transformed_data["processed_message"] == "DATABASE CONNECTION FAILED"

        # Then apply filter
        mock_filter = MagicMock()
        mock_filter.processor_type = "filter"
        mock_filter.transformations = {
            "filters": [
                {
                    "field": "priority",
                    "operator": "greater_than",
                    "value": 5
                }
            ]
        }

        filtered_data = await _apply_processor_transformations(mock_filter, transformed_data)
        assert filtered_data is not None  # Should pass filter
        assert filtered_data["processed_message"] == "DATABASE CONNECTION FAILED"

    @pytest.mark.asyncio
    async def test_enricher_with_routing_scenario(self):
        """Test enricher followed by routing"""
        # First apply enricher
        mock_enricher = MagicMock()
        mock_enricher.processor_type = "enricher"
        mock_enricher.transformations = {
            "enrichments": [
                {
                    "target_field": "correlation_id",
                    "value": "test-uuid-123",
                    "value_type": "string"
                },
                {
                    "target_field": "environment",
                    "value": "production",
                    "value_type": "string"
                }
            ]
        }

        event_data = {
            "event_type": "security",
            "severity": "critical",
            "message": "security breach detected"
        }

        # Apply enricher
        enriched_data = await _apply_processor_transformations(mock_enricher, event_data)
        assert enriched_data["correlation_id"] == "test-uuid-123"
        assert enriched_data["environment"] == "production"

        # Then apply routing
        mock_router = MagicMock()
        mock_router.processor_type = "router"
        mock_router.transformations = {
            "routes": [
                {
                    "condition": {
                        "field": "event_type",
                        "operator": "equals",
                        "value": "security"
                    },
                    "destination": "security-queue",
                    "priority": 1
                }
            ]
        }

        routed_data = await _apply_processor_transformations(mock_router, enriched_data)
        assert "_routing" in routed_data
        assert routed_data["_routing"]["destination"] == "security-queue"
        assert routed_data["_routing"]["priority"] == 1
        assert routed_data["correlation_id"] == "test-uuid-123"  # Enrichment preserved
        assert routed_data["environment"] == "production"  # Enrichment preserved


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
