"""
Unit tests for the Audit Service.

This module tests all audit log functionality including event creation,
querying, filtering, caching, and NATS integration.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.models.audit import (
    AuditLogEventCreate, 
    AuditLogQuery, 
    EventType, 
    Severity,
    BatchAuditLogCreate
)
from app.core.exceptions import ValidationError, NotFoundError


class TestAuditService:
    """Test cases for AuditService."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, audit_service, test_tenant_id):
        """Set up test data for each test."""
        self.audit_service = audit_service
        self.tenant_id = test_tenant_id
        self.user_id = "test-user-123"

    async def test_create_event_success(self, test_audit_event_data):
        """Test successful audit event creation."""
        event_create = AuditLogEventCreate(**test_audit_event_data)
        
        event = await self.audit_service.create_event(
            event_create, 
            self.tenant_id, 
            self.user_id
        )

        assert event.id is not None
        assert event.tenant_id == self.tenant_id
        assert event.event_type == test_audit_event_data["event_type"]
        assert event.resource_type == test_audit_event_data["resource_type"]
        assert event.action == test_audit_event_data["action"]
        assert event.severity == test_audit_event_data["severity"]
        assert event.description == test_audit_event_data["description"]
        assert event.user_id == test_audit_event_data["user_id"]
        assert event.resource_id == test_audit_event_data["resource_id"]
        assert event.ip_address == test_audit_event_data["ip_address"]
        assert event.user_agent == test_audit_event_data["user_agent"]
        assert event.session_id == test_audit_event_data["session_id"]
        assert event.correlation_id == test_audit_event_data["correlation_id"]
        assert event.event_metadata == test_audit_event_data["metadata"]
        assert event.created_at is not None
        assert event.timestamp is not None

    async def test_create_event_minimal_data(self):
        """Test audit event creation with minimal required data."""
        event_data = {
            "event_type": EventType.SYSTEM_EVENT,
            "resource_type": "system",
            "action": "startup",
            "severity": Severity.INFO,
            "description": "System startup event"
        }
        
        event_create = AuditLogEventCreate(**event_data)
        
        event = await self.audit_service.create_event(
            event_create, 
            self.tenant_id, 
            self.user_id
        )

        assert event.id is not None
        assert event.tenant_id == self.tenant_id
        assert event.event_type == EventType.SYSTEM_EVENT
        assert event.resource_type == "system"
        assert event.action == "startup"
        assert event.severity == Severity.INFO
        assert event.description == "System startup event"
        # Optional fields should be None
        assert event.resource_id is None
        assert event.ip_address is None
        assert event.user_agent is None
        assert event.session_id is None
        assert event.correlation_id is None
        assert event.event_metadata is None

    async def test_create_event_with_custom_timestamp(self):
        """Test audit event creation with custom timestamp."""
        custom_timestamp = datetime.utcnow() - timedelta(hours=1)
        
        event_data = {
            "event_type": EventType.USER_ACTION,
            "resource_type": "user",
            "action": "login",
            "severity": Severity.INFO,
            "description": "User login with custom timestamp",
            "timestamp": custom_timestamp
        }
        
        event_create = AuditLogEventCreate(**event_data)
        
        event = await self.audit_service.create_event(
            event_create, 
            self.tenant_id, 
            self.user_id
        )

        assert event.timestamp == custom_timestamp

    async def test_create_event_nats_publish(self, test_audit_event_data):
        """Test that NATS message is published when creating event."""
        event_create = AuditLogEventCreate(**test_audit_event_data)
        
        event = await self.audit_service.create_event(
            event_create, 
            self.tenant_id, 
            self.user_id
        )

        # Verify NATS publish was called
        self.audit_service.nats_client.publish.assert_called_once()
        call_args = self.audit_service.nats_client.publish.call_args
        
        assert call_args[0][0] == "audit.events.created"  # Subject
        
        # Verify message content
        message_data = json.loads(call_args[0][1])
        assert message_data["event_id"] == event.id
        assert message_data["tenant_id"] == self.tenant_id
        assert message_data["event_type"] == test_audit_event_data["event_type"].value

    async def test_create_events_batch_success(self, test_batch_audit_events):
        """Test successful batch audit event creation."""
        batch_create = BatchAuditLogCreate(
            audit_logs=[AuditLogEventCreate(**event_data) for event_data in test_batch_audit_events]
        )
        
        events = await self.audit_service.create_events_batch(
            batch_create, 
            self.tenant_id, 
            self.user_id
        )

        assert len(events) == len(test_batch_audit_events)
        
        for i, event in enumerate(events):
            assert event.id is not None
            assert event.tenant_id == self.tenant_id
            assert event.event_type == test_batch_audit_events[i]["event_type"]
            assert event.resource_type == test_batch_audit_events[i]["resource_type"]
            assert event.action == test_batch_audit_events[i]["action"]
            assert event.description == test_batch_audit_events[i]["description"]

    async def test_create_events_batch_nats_publish(self, test_batch_audit_events):
        """Test that NATS messages are published for batch creation."""
        batch_create = BatchAuditLogCreate(
            audit_logs=[AuditLogEventCreate(**event_data) for event_data in test_batch_audit_events]
        )
        
        events = await self.audit_service.create_events_batch(
            batch_create, 
            self.tenant_id, 
            self.user_id
        )

        # Verify NATS publish was called for batch
        self.audit_service.nats_client.publish.assert_called()
        
        # Should be called once for the batch
        assert self.audit_service.nats_client.publish.call_count == 1
        
        call_args = self.audit_service.nats_client.publish.call_args
        assert call_args[0][0] == "audit.events.batch_created"  # Subject

    async def test_get_event_by_id_success(self, test_audit_events):
        """Test successful event retrieval by ID."""
        test_event = test_audit_events[0]
        
        event = await self.audit_service.get_event_by_id(
            test_event.id, 
            self.tenant_id
        )

        assert event is not None
        assert event.id == test_event.id
        assert event.tenant_id == self.tenant_id

    async def test_get_event_by_id_not_found(self):
        """Test event retrieval with non-existent ID."""
        event = await self.audit_service.get_event_by_id(
            "non-existent-id", 
            self.tenant_id
        )
        
        assert event is None

    async def test_get_event_by_id_wrong_tenant(self, test_audit_events):
        """Test event retrieval with wrong tenant."""
        test_event = test_audit_events[0]
        
        event = await self.audit_service.get_event_by_id(
            test_event.id, 
            "wrong-tenant-id"
        )
        
        assert event is None

    async def test_query_events_no_filters(self, test_audit_events):
        """Test querying events without filters."""
        results = await self.audit_service.query_events(
            None,  # No query filters
            self.tenant_id,
            page=1,
            size=10
        )

        assert results.total >= len(test_audit_events)
        assert len(results.items) <= 10
        assert results.page == 1
        assert results.size == 10
        assert results.pages >= 1

        # All events should belong to the correct tenant
        for event in results.items:
            assert event.tenant_id == self.tenant_id

    async def test_query_events_with_date_filter(self, test_audit_events):
        """Test querying events with date filters."""
        start_date = datetime.utcnow() - timedelta(hours=1)
        end_date = datetime.utcnow() + timedelta(hours=1)
        
        query = AuditLogQuery(
            start_date=start_date,
            end_date=end_date
        )
        
        results = await self.audit_service.query_events(
            query,
            self.tenant_id,
            page=1,
            size=10
        )

        assert results.total >= 0
        
        # All events should be within the date range
        for event in results.items:
            assert start_date <= event.timestamp <= end_date

    async def test_query_events_with_event_type_filter(self, test_audit_events):
        """Test querying events with event type filter."""
        query = AuditLogQuery(
            event_types=[EventType.USER_ACTION]
        )
        
        results = await self.audit_service.query_events(
            query,
            self.tenant_id,
            page=1,
            size=10
        )

        # All events should be USER_ACTION type
        for event in results.items:
            assert event.event_type == EventType.USER_ACTION

    async def test_query_events_with_severity_filter(self, test_audit_events):
        """Test querying events with severity filter."""
        query = AuditLogQuery(
            severities=[Severity.INFO, Severity.WARNING]
        )
        
        results = await self.audit_service.query_events(
            query,
            self.tenant_id,
            page=1,
            size=10
        )

        # All events should have INFO or WARNING severity
        for event in results.items:
            assert event.severity in [Severity.INFO, Severity.WARNING]

    async def test_query_events_with_resource_type_filter(self, test_audit_events):
        """Test querying events with resource type filter."""
        query = AuditLogQuery(
            resource_types=["user"]
        )
        
        results = await self.audit_service.query_events(
            query,
            self.tenant_id,
            page=1,
            size=10
        )

        # All events should have "user" resource type
        for event in results.items:
            assert event.resource_type == "user"

    async def test_query_events_with_search_filter(self, test_audit_events):
        """Test querying events with search filter."""
        query = AuditLogQuery(
            search="login"
        )
        
        results = await self.audit_service.query_events(
            query,
            self.tenant_id,
            page=1,
            size=10
        )

        # All events should contain "login" in description or action
        for event in results.items:
            assert ("login" in event.description.lower() or 
                   "login" in event.action.lower())

    async def test_query_events_with_multiple_filters(self, test_audit_events):
        """Test querying events with multiple filters."""
        query = AuditLogQuery(
            event_types=[EventType.USER_ACTION],
            severities=[Severity.INFO],
            resource_types=["user"],
            actions=["login"]
        )
        
        results = await self.audit_service.query_events(
            query,
            self.tenant_id,
            page=1,
            size=10
        )

        # All events should match all filters
        for event in results.items:
            assert event.event_type == EventType.USER_ACTION
            assert event.severity == Severity.INFO
            assert event.resource_type == "user"
            assert event.action == "login"

    async def test_query_events_pagination(self, test_audit_events):
        """Test event query pagination."""
        # First page
        results_page1 = await self.audit_service.query_events(
            None,
            self.tenant_id,
            page=1,
            size=2
        )

        assert results_page1.page == 1
        assert results_page1.size == 2
        assert len(results_page1.items) <= 2

        if results_page1.total > 2:
            # Second page
            results_page2 = await self.audit_service.query_events(
                None,
                self.tenant_id,
                page=2,
                size=2
            )

            assert results_page2.page == 2
            assert results_page2.size == 2
            
            # Items should be different
            page1_ids = {event.id for event in results_page1.items}
            page2_ids = {event.id for event in results_page2.items}
            assert page1_ids.isdisjoint(page2_ids)

    async def test_query_events_sorting(self, test_audit_events):
        """Test event query sorting."""
        # Sort by timestamp ascending
        query = AuditLogQuery(
            sort_by="timestamp",
            sort_order="asc"
        )
        
        results = await self.audit_service.query_events(
            query,
            self.tenant_id,
            page=1,
            size=10
        )

        # Events should be sorted by timestamp ascending
        if len(results.items) > 1:
            for i in range(len(results.items) - 1):
                assert results.items[i].timestamp <= results.items[i + 1].timestamp

    async def test_get_summary_no_filters(self, test_audit_events):
        """Test getting audit log summary without filters."""
        summary = await self.audit_service.get_summary(
            None,
            self.tenant_id
        )

        assert summary.total_count >= len(test_audit_events)
        assert isinstance(summary.event_types, dict)
        assert isinstance(summary.severities, dict)
        assert isinstance(summary.resource_types, dict)
        assert isinstance(summary.date_range, dict)

        # Should have counts for different categories
        assert len(summary.event_types) > 0
        assert len(summary.severities) > 0
        assert len(summary.resource_types) > 0

    async def test_get_summary_with_filters(self, test_audit_events):
        """Test getting audit log summary with filters."""
        query = AuditLogQuery(
            event_types=[EventType.USER_ACTION],
            start_date=datetime.utcnow() - timedelta(hours=1)
        )
        
        summary = await self.audit_service.get_summary(
            query,
            self.tenant_id
        )

        assert summary.total_count >= 0
        
        # Should only have USER_ACTION events in summary
        if summary.total_count > 0:
            assert EventType.USER_ACTION.value in summary.event_types

    async def test_export_events_json(self, test_audit_events):
        """Test exporting events in JSON format."""
        query = AuditLogQuery(
            start_date=datetime.utcnow() - timedelta(hours=1)
        )
        
        export_result = await self.audit_service.export_events(
            query,
            self.tenant_id,
            format="json"
        )

        assert export_result.format == "json"
        assert export_result.count >= 0
        assert isinstance(export_result.data, list)
        assert export_result.generated_at is not None

        # Each item should be a dictionary
        for item in export_result.data:
            assert isinstance(item, dict)
            assert "id" in item
            assert "tenant_id" in item
            assert "event_type" in item

    async def test_export_events_csv(self, test_audit_events):
        """Test exporting events in CSV format."""
        query = AuditLogQuery(
            start_date=datetime.utcnow() - timedelta(hours=1)
        )
        
        export_result = await self.audit_service.export_events(
            query,
            self.tenant_id,
            format="csv"
        )

        assert export_result.format == "csv"
        assert export_result.count >= 0
        assert isinstance(export_result.data, list)

    async def test_cache_integration(self, test_audit_events):
        """Test Redis cache integration."""
        query = AuditLogQuery(
            event_types=[EventType.USER_ACTION]
        )
        
        # First query - should miss cache
        results1 = await self.audit_service.query_events(
            query,
            self.tenant_id,
            page=1,
            size=10
        )

        # Verify cache get was called
        self.audit_service.redis_client.get.assert_called()

        # Second query - should hit cache (if implemented)
        results2 = await self.audit_service.query_events(
            query,
            self.tenant_id,
            page=1,
            size=10
        )

        # Results should be the same
        assert results1.total == results2.total

    async def test_tenant_isolation(self):
        """Test that events are isolated by tenant."""
        # Create event in tenant 1
        event_data = {
            "event_type": EventType.USER_ACTION,
            "resource_type": "user",
            "action": "login",
            "severity": Severity.INFO,
            "description": "Tenant 1 event"
        }
        
        event_create = AuditLogEventCreate(**event_data)
        
        event1 = await self.audit_service.create_event(
            event_create, 
            "tenant-1", 
            self.user_id
        )

        # Try to get event from tenant 2
        event_from_tenant2 = await self.audit_service.get_event_by_id(
            event1.id,
            "tenant-2"
        )
        
        assert event_from_tenant2 is None

        # Query events from tenant 2 should not include tenant 1 events
        results = await self.audit_service.query_events(
            None,
            "tenant-2",
            page=1,
            size=10
        )
        
        event_ids = {event.id for event in results.items}
        assert event1.id not in event_ids


class TestAuditServiceCaching:
    """Test cases for audit service caching functionality."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, audit_service, test_tenant_id):
        """Set up test data for caching tests."""
        self.audit_service = audit_service
        self.tenant_id = test_tenant_id

    async def test_cache_key_generation(self):
        """Test cache key generation for queries."""
        query = AuditLogQuery(
            event_types=[EventType.USER_ACTION],
            severities=[Severity.INFO]
        )
        
        # This would test the internal cache key generation
        # In a real implementation, you'd have a method to generate cache keys
        cache_key = self.audit_service._generate_cache_key(
            query, self.tenant_id, 1, 10
        )
        
        assert isinstance(cache_key, str)
        assert self.tenant_id in cache_key
        assert "user_action" in cache_key.lower()

    async def test_cache_invalidation_on_create(self, test_audit_event_data):
        """Test that cache is invalidated when new events are created."""
        event_create = AuditLogEventCreate(**test_audit_event_data)
        
        # Create event
        await self.audit_service.create_event(
            event_create, 
            self.tenant_id, 
            "test-user"
        )

        # Verify cache delete was called (for cache invalidation)
        self.audit_service.redis_client.delete.assert_called()


class TestAuditServiceErrors:
    """Test cases for audit service error handling."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, audit_service, test_tenant_id):
        """Set up test data for error tests."""
        self.audit_service = audit_service
        self.tenant_id = test_tenant_id

    async def test_create_event_validation_error(self):
        """Test validation error when creating event with invalid data."""
        # Missing required fields
        with pytest.raises(ValidationError):
            invalid_event = AuditLogEventCreate(
                event_type=EventType.USER_ACTION,
                # Missing required fields
            )

    async def test_query_events_invalid_page(self):
        """Test query with invalid page number."""
        with pytest.raises(ValidationError):
            await self.audit_service.query_events(
                None,
                self.tenant_id,
                page=0,  # Invalid page number
                size=10
            )

    async def test_query_events_invalid_size(self):
        """Test query with invalid page size."""
        with pytest.raises(ValidationError):
            await self.audit_service.query_events(
                None,
                self.tenant_id,
                page=1,
                size=0  # Invalid page size
            )

    async def test_export_events_invalid_format(self):
        """Test export with invalid format."""
        with pytest.raises(ValidationError):
            await self.audit_service.export_events(
                None,
                self.tenant_id,
                format="invalid_format"
            )

    @patch('app.services.audit_service.AuditService._publish_to_nats')
    async def test_nats_publish_failure_handling(self, mock_publish, test_audit_event_data):
        """Test handling of NATS publish failures."""
        # Mock NATS publish to raise an exception
        mock_publish.side_effect = Exception("NATS connection failed")
        
        event_create = AuditLogEventCreate(**test_audit_event_data)
        
        # Event creation should still succeed even if NATS fails
        event = await self.audit_service.create_event(
            event_create, 
            self.tenant_id, 
            "test-user"
        )

        assert event.id is not None
        # The event should be created in the database despite NATS failure

    async def test_database_connection_error(self):
        """Test handling of database connection errors."""
        # This would test database connection error handling
        # In a real implementation, you'd mock the database session
        # to raise connection errors and verify proper error handling
        pass


class TestAuditServicePerformance:
    """Test cases for audit service performance."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, audit_service, test_tenant_id):
        """Set up test data for performance tests."""
        self.audit_service = audit_service
        self.tenant_id = test_tenant_id

    async def test_batch_create_performance(self):
        """Test performance of batch event creation."""
        import time
        
        # Create a large batch of events
        batch_size = 100
        events = []
        
        for i in range(batch_size):
            event_data = {
                "event_type": EventType.API_CALL,
                "resource_type": "api",
                "action": "test_action",
                "severity": Severity.INFO,
                "description": f"Performance test event {i}",
                "correlation_id": f"perf-test-{i:04d}"
            }
            events.append(AuditLogEventCreate(**event_data))

        batch_create = BatchAuditLogCreate(audit_logs=events)
        
        start_time = time.time()
        
        created_events = await self.audit_service.create_events_batch(
            batch_create,
            self.tenant_id,
            "test-user"
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert len(created_events) == batch_size
        # Should complete within reasonable time (adjust threshold as needed)
        assert duration < 5.0  # 5 seconds for 100 events

    async def test_query_performance_with_large_dataset(self):
        """Test query performance with large dataset."""
        # This would test query performance with a large number of events
        # In a real implementation, you'd create a large dataset and measure
        # query response times
        pass