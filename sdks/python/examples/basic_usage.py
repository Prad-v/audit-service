#!/usr/bin/env python3
"""
Basic usage examples for the Audit Log Framework Python SDK.
"""

import asyncio
from datetime import datetime, timedelta
from audit_log_sdk import (
    AuditLogClient,
    AsyncAuditLogClient,
    AuditLogEventCreate,
    AuditLogQuery,
    EventType,
    Severity,
)


def sync_example():
    """Example using the synchronous client."""
    print("=== Synchronous Client Example ===")
    
    # Initialize client with API key
    client = AuditLogClient(
        base_url="http://localhost:8000",
        api_key="your-api-key",
        tenant_id="your-tenant-id"
    )
    
    try:
        # Create a single audit log event
        event = AuditLogEventCreate(
            event_type=EventType.USER_ACTION,
            resource_type="user",
            action="login",
            severity=Severity.INFO,
            description="User logged in successfully",
            user_id="user-123",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        created_event = client.create_event(event)
        print(f"✓ Created event: {created_event.id}")
        
        # Query events from the last 7 days
        query = AuditLogQuery(
            start_date=datetime.now() - timedelta(days=7),
            event_types=[EventType.USER_ACTION, EventType.API_CALL],
            severities=[Severity.INFO, Severity.WARNING, Severity.ERROR]
        )
        
        results = client.query_events(query, page=1, size=10)
        print(f"✓ Found {results.total} events ({len(results.items)} on this page)")
        
        # Get summary statistics
        summary = client.get_summary(query)
        print(f"✓ Summary: {summary.total_count} total events")
        print(f"  Event types: {summary.event_types}")
        print(f"  Severities: {summary.severities}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        client.close()


async def async_example():
    """Example using the asynchronous client."""
    print("\n=== Asynchronous Client Example ===")
    
    async with AsyncAuditLogClient(
        base_url="http://localhost:8000",
        api_key="your-api-key",
        tenant_id="your-tenant-id"
    ) as client:
        
        try:
            # Create multiple events in batch
            events = [
                AuditLogEventCreate(
                    event_type=EventType.API_CALL,
                    resource_type="api",
                    action="create_user",
                    severity=Severity.INFO,
                    description=f"API call to create user {i}",
                    correlation_id=f"req-{i:03d}",
                    metadata={"batch_id": "batch-001", "user_count": i}
                )
                for i in range(1, 6)
            ]
            
            batch_results = await client.create_events_batch(events)
            print(f"✓ Created {len(batch_results)} events in batch")
            
            # Query events asynchronously
            query = AuditLogQuery(
                event_types=[EventType.API_CALL],
                start_date=datetime.now() - timedelta(hours=1)
            )
            
            results = await client.query_events(query)
            print(f"✓ Found {results.total} API call events")
            
            # Export events
            export_result = await client.export_events(
                query=query,
                format="json"
            )
            print(f"✓ Exported {export_result.count} events")
            
        except Exception as e:
            print(f"✗ Error: {e}")


def authentication_example():
    """Example showing different authentication methods."""
    print("\n=== Authentication Examples ===")
    
    # Method 1: API Key authentication
    print("1. API Key Authentication:")
    client_api_key = AuditLogClient(
        base_url="http://localhost:8000",
        api_key="your-api-key",
        tenant_id="your-tenant-id"
    )
    
    try:
        user = client_api_key.get_current_user()
        print(f"✓ Authenticated as: {user.username} ({user.email})")
    except Exception as e:
        print(f"✗ API Key auth failed: {e}")
    finally:
        client_api_key.close()
    
    # Method 2: Username/Password authentication
    print("\n2. Username/Password Authentication:")
    client_jwt = AuditLogClient(base_url="http://localhost:8000")
    
    try:
        # Login to get JWT token
        token_response = client_jwt.login(
            username="admin",
            password="password",
            tenant_id="tenant-123"
        )
        print(f"✓ Login successful, token type: {token_response.token_type}")
        
        # Now use the client with JWT token
        user = client_jwt.get_current_user()
        print(f"✓ Authenticated as: {user.username}")
        
        # Logout
        client_jwt.logout()
        print("✓ Logged out successfully")
        
    except Exception as e:
        print(f"✗ JWT auth failed: {e}")
    finally:
        client_jwt.close()


def error_handling_example():
    """Example showing comprehensive error handling."""
    print("\n=== Error Handling Example ===")
    
    from audit_log_sdk.exceptions import (
        AuthenticationError,
        ValidationError,
        NotFoundError,
        RateLimitError,
        ServerError,
        NetworkError
    )
    
    client = AuditLogClient(
        base_url="http://localhost:8000",
        api_key="invalid-key",  # Intentionally invalid
        tenant_id="test-tenant"
    )
    
    try:
        # This should fail with authentication error
        event = AuditLogEventCreate(
            event_type=EventType.SYSTEM_EVENT,
            resource_type="test",
            action="test",
            severity=Severity.DEBUG,
            description="Test event"
        )
        
        client.create_event(event)
        
    except AuthenticationError as e:
        print(f"✓ Caught authentication error: {e.message}")
        print(f"  Error code: {e.error_code}")
        print(f"  Status code: {e.status_code}")
        
    except ValidationError as e:
        print(f"✓ Caught validation error: {e.message}")
        print(f"  Details: {e.details}")
        
    except NotFoundError as e:
        print(f"✓ Caught not found error: {e.message}")
        
    except RateLimitError as e:
        print(f"✓ Caught rate limit error: {e.message}")
        if e.retry_after:
            print(f"  Retry after: {e.retry_after} seconds")
            
    except ServerError as e:
        print(f"✓ Caught server error: {e.message}")
        print(f"  Status code: {e.status_code}")
        
    except NetworkError as e:
        print(f"✓ Caught network error: {e.message}")
        if e.original_error:
            print(f"  Original error: {e.original_error}")
            
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        
    finally:
        client.close()


def main():
    """Run all examples."""
    print("Audit Log Framework Python SDK Examples")
    print("=" * 50)
    
    # Run synchronous example
    sync_example()
    
    # Run asynchronous example
    asyncio.run(async_example())
    
    # Run authentication examples
    authentication_example()
    
    # Run error handling example
    error_handling_example()
    
    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nNote: These examples assume the Audit Log API is running at http://localhost:8000")
    print("Make sure to replace 'your-api-key' and 'your-tenant-id' with actual values.")


if __name__ == "__main__":
    main()