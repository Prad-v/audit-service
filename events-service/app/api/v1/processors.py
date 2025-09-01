"""
Event Processors API

This module provides API endpoints for managing event processors that transform,
enrich, filter, and route cloud events.
"""

import logging
import uuid
import json
import re
import os
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.db.schemas import EventProcessor as EventProcessorDB
from app.models.events import (
    EventProcessorCreate, EventProcessorUpdate, EventProcessorResponse,
    EventProcessorListResponse, EventProcessorStats, EventProcessorType
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/processors", response_model=EventProcessorResponse, status_code=status.HTTP_201_CREATED)
async def create_event_processor(
    processor_data: EventProcessorCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new event processor"""
    try:
        # Generate processor ID
        processor_id = f"processor-{uuid.uuid4().hex[:8]}"
        
        # Create processor
        processor = EventProcessorDB(
            processor_id=processor_id,
            name=processor_data.name,
            description=processor_data.description,
            processor_type=processor_data.processor_type.value,
            config=processor_data.config,
            order=processor_data.order,
            depends_on=processor_data.depends_on,
            event_types=processor_data.event_types,
            severity_levels=processor_data.severity_levels,
            cloud_providers=processor_data.cloud_providers,
            conditions=processor_data.conditions,
            transformations=processor_data.transformations,
            enabled=processor_data.enabled,
            tenant_id=processor_data.tenant_id,
            created_by=processor_data.created_by
        )
        
        db.add(processor)
        await db.commit()
        await db.refresh(processor)
        
        logger.info(f"Created event processor: {processor_id}")
        return EventProcessorResponse.from_orm(processor)
        
    except Exception as e:
        logger.error(f"Error creating event processor: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create event processor"
        )


@router.get("/processors", response_model=EventProcessorListResponse)
async def list_event_processors(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    processor_type: Optional[EventProcessorType] = Query(None, description="Filter by processor type"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    db: AsyncSession = Depends(get_db)
):
    """List event processors with filtering and pagination"""
    try:
        # Build query
        query = select(EventProcessorDB)
        
        # Apply filters
        filters = []
        if processor_type:
            filters.append(EventProcessorDB.processor_type == processor_type.value)
        if enabled is not None:
            filters.append(EventProcessorDB.enabled == enabled)
        if tenant_id:
            filters.append(EventProcessorDB.tenant_id == tenant_id)
        if search:
            search_filter = or_(
                EventProcessorDB.name.ilike(f"%{search}%"),
                EventProcessorDB.description.ilike(f"%{search}%")
            )
            filters.append(search_filter)
        
        if filters:
            query = query.where(and_(*filters))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # Apply pagination and ordering
        query = query.order_by(EventProcessorDB.order, EventProcessorDB.created_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)
        
        # Execute query
        result = await db.execute(query)
        processors = result.scalars().all()
        
        # Convert to response models
        processor_responses = [EventProcessorResponse.from_orm(p) for p in processors]
        
        return EventProcessorListResponse(
            processors=processor_responses,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error listing event processors: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list event processors"
        )


@router.get("/processors/{processor_id}", response_model=EventProcessorResponse)
async def get_event_processor(
    processor_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific event processor by ID"""
    try:
        query = select(EventProcessorDB).where(EventProcessorDB.processor_id == processor_id)
        result = await db.execute(query)
        processor = result.scalar_one_or_none()
        
        if not processor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event processor not found"
            )
        
        return EventProcessorResponse.from_orm(processor)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting event processor {processor_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get event processor"
        )


@router.put("/processors/{processor_id}", response_model=EventProcessorResponse)
async def update_event_processor(
    processor_id: str,
    processor_data: EventProcessorUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing event processor"""
    try:
        # Get existing processor
        query = select(EventProcessorDB).where(EventProcessorDB.processor_id == processor_id)
        result = await db.execute(query)
        processor = result.scalar_one_or_none()
        
        if not processor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event processor not found"
            )
        
        # Update fields
        update_data = processor_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "processor_type" and value:
                setattr(processor, field, value.value)
            else:
                setattr(processor, field, value)
        
        await db.commit()
        await db.refresh(processor)
        
        logger.info(f"Updated event processor: {processor_id}")
        return EventProcessorResponse.from_orm(processor)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating event processor {processor_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update event processor"
        )


@router.delete("/processors/{processor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_processor(
    processor_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete an event processor"""
    try:
        # Get existing processor
        query = select(EventProcessorDB).where(EventProcessorDB.processor_id == processor_id)
        result = await db.execute(query)
        processor = result.scalar_one_or_none()
        
        if not processor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event processor not found"
            )
        
        # Check for dependencies
        if processor.depends_on:
            # Check if any other processors depend on this one
            dependent_query = select(EventProcessorDB).where(
                EventProcessorDB.depends_on.contains([processor_id])
            )
            dependent_result = await db.execute(dependent_query)
            dependents = dependent_result.scalars().all()
            
            if dependents:
                dependent_names = [p.name for p in dependents]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot delete processor. Other processors depend on it: {', '.join(dependent_names)}"
                )
        
        # Delete processor
        await db.delete(processor)
        await db.commit()
        
        logger.info(f"Deleted event processor: {processor_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting event processor {processor_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete event processor"
        )


@router.post("/processors/{processor_id}/test", status_code=status.HTTP_200_OK)
async def test_event_processor(
    processor_id: str,
    test_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Test an event processor with sample data"""
    try:
        # Get processor
        query = select(EventProcessorDB).where(EventProcessorDB.processor_id == processor_id)
        result = await db.execute(query)
        processor = result.scalar_one_or_none()
        
        if not processor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event processor not found"
            )
        
        if not processor.enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot test disabled processor"
            )
        
        # Apply processor transformations
        try:
            processed_data = await _apply_processor_transformations(processor, test_data)
            
            # Update processor stats
            processor.processed_count += 1
            processor.last_processed = datetime.utcnow()
            await db.commit()
            
            return {
                "success": True,
                "message": "Processor test completed successfully",
                "result": processed_data,
                "processor_id": processor_id
            }
            
        except Exception as processing_error:
            # Update error stats
            processor.error_count += 1
            await db.commit()
            
            return {
                "success": False,
                "message": f"Processor test failed: {str(processing_error)}",
                "input_data": test_data,
                "error": str(processing_error),
                "processor_id": processor_id
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing event processor {processor_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test event processor"
        )


@router.get("/processors/{processor_id}/stats", response_model=EventProcessorStats)
async def get_event_processor_stats(
    processor_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get statistics for an event processor"""
    try:
        # Get processor
        query = select(EventProcessorDB).where(EventProcessorDB.processor_id == processor_id)
        result = await db.execute(query)
        processor = result.scalar_one_or_none()
        
        if not processor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event processor not found"
            )
        
        # Calculate success rate
        total_processed = processor.processed_count + processor.error_count
        success_rate = (processor.processed_count / total_processed * 100) if total_processed > 0 else 0
        
        return EventProcessorStats(
            processor_id=processor.processor_id,
            name=processor.name,
            processor_type=EventProcessorType(processor.processor_type),
            processed_count=processor.processed_count,
            error_count=processor.error_count,
            last_processed=processor.last_processed,
            avg_processing_time=None,  # Would be calculated from actual processing logs
            success_rate=success_rate,
            enabled=processor.enabled
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stats for event processor {processor_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get event processor stats"
        )


@router.post("/processors/{processor_id}/enable", response_model=EventProcessorResponse)
async def enable_event_processor(
    processor_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Enable an event processor"""
    try:
        # Get processor
        query = select(EventProcessorDB).where(EventProcessorDB.processor_id == processor_id)
        result = await db.execute(query)
        processor = result.scalar_one_or_none()
        
        if not processor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event processor not found"
            )
        
        processor.enabled = True
        await db.commit()
        await db.refresh(processor)
        
        logger.info(f"Enabled event processor: {processor_id}")
        return EventProcessorResponse.from_orm(processor)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling event processor {processor_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable event processor"
        )


@router.post("/processors/{processor_id}/disable", response_model=EventProcessorResponse)
async def disable_event_processor(
    processor_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Disable an event processor"""
    try:
        # Get processor
        result = await db.execute(
            select(EventProcessorDB).where(EventProcessorDB.processor_id == processor_id)
        )
        processor = result.scalar_one_or_none()
        
        if not processor:
            raise HTTPException(status_code=404, detail="Event processor not found")
        
        # Update processor
        processor.enabled = False
        processor.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(processor)
        
        return EventProcessorResponse.from_orm(processor)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disable event processor {processor_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to disable event processor")


async def _apply_processor_transformations(processor: EventProcessorDB, event_data: dict) -> dict:
    """Apply processor transformations to event data"""
    try:
        # Start with a copy of the input data
        result = event_data.copy()
        
        # Get processor configuration
        transformations = processor.transformations or {}
        processor_type = processor.processor_type
        
        if processor_type == "transformer":
            result = await _apply_transformer_rules(transformations, result)
        elif processor_type == "enricher":
            result = await _apply_enrichment_rules(transformations, result)
        elif processor_type == "filter":
            result = await _apply_filter_rules(transformations, result)
        elif processor_type == "router":
            result = await _apply_routing_rules(transformations, result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error applying processor transformations: {e}")
        raise Exception(f"Transformation failed: {str(e)}")


async def _apply_transformer_rules(transformations: dict, data: dict) -> dict:
    """Apply transformation rules to data"""
    try:
        rules = transformations.get("rules", [])
        
        for rule in rules:
            source_field = rule.get("source_field")
            target_field = rule.get("target_field")
            function_name = rule.get("function")
            
            if not all([source_field, target_field, function_name]):
                continue
            
            # Get source value
            source_value = _get_nested_value(data, source_field)
            if source_value is None:
                continue
            
            # Apply transformation function
            transformed_value = await _apply_transformation_function(function_name, source_value)
            
            # Set target value
            _set_nested_value(data, target_field, transformed_value)
        
        return data
        
    except Exception as e:
        logger.error(f"Error applying transformer rules: {e}")
        raise


async def _apply_enrichment_rules(transformations: dict, data: dict) -> dict:
    """Apply enrichment rules to data"""
    try:
        enrichments = transformations.get("enrichments", [])
        
        for enrichment in enrichments:
            target_field = enrichment.get("target_field")
            value = enrichment.get("value")
            value_type = enrichment.get("value_type", "string")
            
            if not all([target_field, value]):
                continue
            
            # Convert value to appropriate type
            converted_value = _convert_value_type(value, value_type)
            
            # Set target value
            _set_nested_value(data, target_field, converted_value)
        
        return data
        
    except Exception as e:
        logger.error(f"Error applying enrichment rules: {e}")
        raise


async def _apply_filter_rules(transformations: dict, data: dict) -> dict:
    """Apply filter rules to data"""
    try:
        filters = transformations.get("filters", [])
        
        for filter_rule in filters:
            field = filter_rule.get("field")
            operator = filter_rule.get("operator")
            value = filter_rule.get("value")
            
            if not all([field, operator, value]):
                continue
            
            # Get field value
            field_value = _get_nested_value(data, field)
            if field_value is None:
                continue
            
            # Apply filter condition
            if not _evaluate_filter_condition(field_value, operator, value):
                # Filter condition failed, return None to indicate event should be filtered out
                return None
        
        return data
        
    except Exception as e:
        logger.error(f"Error applying filter rules: {e}")
        raise


async def _apply_routing_rules(transformations: dict, data: dict) -> dict:
    """Apply routing rules to data"""
    try:
        routes = transformations.get("routes", [])
        
        for route in routes:
            condition = route.get("condition")
            destination = route.get("destination")
            priority = route.get("priority", 1)
            
            if not all([condition, destination]):
                continue
            
            # Evaluate routing condition
            if _evaluate_routing_condition(condition, data):
                # Add routing information to data
                data["_routing"] = {
                    "destination": destination,
                    "priority": priority,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                break
        
        return data
        
    except Exception as e:
        logger.error(f"Error applying routing rules: {e}")
        raise


async def _apply_transformation_function(function_name: str, value: any) -> any:
    """Apply a transformation function to a value"""
    try:
        if function_name == "uppercase":
            return str(value).upper()
        elif function_name == "lowercase":
            return str(value).lower()
        elif function_name == "titlecase":
            return str(value).title()
        elif function_name == "trim":
            return str(value).strip()
        elif function_name == "reverse":
            return str(value)[::-1]
        elif function_name == "length":
            return len(str(value))
        elif function_name == "to_string":
            return str(value)
        elif function_name == "to_number":
            try:
                return float(value) if "." in str(value) else int(value)
            except ValueError:
                return value
        elif function_name == "to_boolean":
            if isinstance(value, bool):
                return value
            return str(value).lower() in ("true", "1", "yes", "on")
        elif function_name == "timestamp":
            return datetime.now(timezone.utc).isoformat()
        elif function_name == "uuid":
            return str(uuid.uuid4())
        else:
            # Unknown function, return original value
            return value
            
    except Exception as e:
        logger.error(f"Error applying transformation function {function_name}: {e}")
        return value


def _get_nested_value(data: dict, field_path: str) -> any:
    """Get nested value from data using dot notation"""
    try:
        keys = field_path.split(".")
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
        
    except Exception:
        return None


def _set_nested_value(data: dict, field_path: str, value: any):
    """Set nested value in data using dot notation"""
    try:
        keys = field_path.split(".")
        current = data
        
        # Navigate to the parent of the target field
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
        
    except Exception as e:
        logger.error(f"Error setting nested value {field_path}: {e}")


def _convert_value_type(value: any, value_type: str) -> any:
    """Convert value to specified type"""
    try:
        if value_type == "string":
            return str(value)
        elif value_type == "number":
            try:
                return float(value) if "." in str(value) else int(value)
            except ValueError:
                return value
        elif value_type == "boolean":
            if isinstance(value, bool):
                return value
            return str(value).lower() in ("true", "1", "yes", "on")
        elif value_type == "timestamp":
            if isinstance(value, str):
                return value
            return datetime.now(timezone.utc).isoformat()
        else:
            return value
            
    except Exception as e:
        logger.error(f"Error converting value type: {e}")
        return value


def _evaluate_filter_condition(field_value: any, operator: str, expected_value: any) -> bool:
    """Evaluate a filter condition"""
    try:
        if operator == "equals":
            return field_value == expected_value
        elif operator == "not_equals":
            return field_value != expected_value
        elif operator == "contains":
            return str(expected_value) in str(field_value)
        elif operator == "not_contains":
            return str(expected_value) not in str(field_value)
        elif operator == "starts_with":
            return str(field_value).startswith(str(expected_value))
        elif operator == "ends_with":
            return str(field_value).endswith(str(expected_value))
        elif operator == "greater_than":
            try:
                return float(field_value) > float(expected_value)
            except (ValueError, TypeError):
                return False
        elif operator == "less_than":
            try:
                return float(field_value) < float(expected_value)
            except (ValueError, TypeError):
                return False
        elif operator == "greater_than_or_equal":
            try:
                return float(field_value) >= float(expected_value)
            except (ValueError, TypeError):
                return False
        elif operator == "less_than_or_equal":
            try:
                return float(field_value) <= float(expected_value)
            except (ValueError, TypeError):
                return False
        else:
            # Unknown operator, default to True
            return True
            
    except Exception as e:
        logger.error(f"Error evaluating filter condition: {e}")
        return True


def _evaluate_routing_condition(condition: dict, data: dict) -> bool:
    """Evaluate a routing condition"""
    try:
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")
        
        if not all([field, operator, value]):
            return False
        
        # Get field value
        field_value = _get_nested_value(data, field)
        if field_value is None:
            return False
        
        # Use the same logic as filter conditions
        return _evaluate_filter_condition(field_value, operator, value)
        
    except Exception as e:
        logger.error(f"Error evaluating routing condition: {e}")
        return False


