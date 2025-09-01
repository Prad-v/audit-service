#!/usr/bin/env python3
"""
Script to clean up duplicate outage entries from the database.
This script removes duplicate entries based on title, provider, and service.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.append('/app')

from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.db.database import get_database_url
from app.models.audit import CloudEvent
from app.models.base import EventType

async def cleanup_duplicate_outages():
    """Clean up duplicate outage entries from the database"""
    
    # Create database engine
    database_url = get_database_url()
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Get all outage events
            query = select(CloudEvent).where(
                CloudEvent.event_type == EventType.OUTAGE_STATUS
            ).order_by(CloudEvent.event_time.desc())
            
            result = await session.execute(query)
            events = result.scalars().all()
            
            print(f"Found {len(events)} total outage events")
            
            # Group events by title, provider, and service
            grouped_events = {}
            for event in events:
                key = (event.title, event.cloud_provider, event.service_name)
                if key not in grouped_events:
                    grouped_events[key] = []
                grouped_events[key].append(event)
            
            # Find duplicates and keep only the most recent one
            duplicates_to_remove = []
            for key, event_list in grouped_events.items():
                if len(event_list) > 1:
                    print(f"Found {len(event_list)} duplicates for: {key[0]} ({key[1]})")
                    
                    # Sort by event_time (most recent first)
                    sorted_events = sorted(event_list, key=lambda x: x.event_time, reverse=True)
                    
                    # Keep the most recent one, mark others for deletion
                    for event in sorted_events[1:]:
                        duplicates_to_remove.append(event.event_id)
                        print(f"  - Marking for deletion: {event.event_id} (created: {event.event_time})")
            
            if duplicates_to_remove:
                print(f"\nRemoving {len(duplicates_to_remove)} duplicate events...")
                
                # Delete duplicate events
                delete_query = delete(CloudEvent).where(
                    CloudEvent.event_id.in_(duplicates_to_remove)
                )
                
                result = await session.execute(delete_query)
                await session.commit()
                
                print(f"Successfully removed {len(duplicates_to_remove)} duplicate events")
            else:
                print("No duplicates found")
            
            # Verify cleanup
            result = await session.execute(query)
            remaining_events = result.scalars().all()
            print(f"Remaining outage events: {len(remaining_events)}")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(cleanup_duplicate_outages())
