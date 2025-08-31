"""
Cloud Management Service

This service handles cloud provider project management with audit integration.
"""

import logging
import structlog
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from uuid import uuid4

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schemas import CloudProject
from app.models.cloud import (
    CloudProjectCreate,
    CloudProjectUpdate,
    CloudProjectResponse,
    CloudProjectListResponse,
    CloudProvider,
)
from app.models.audit import AuditEventCreate
from app.db.database import get_database_manager
from app.services.audit_service import get_audit_service

logger = structlog.get_logger(__name__)


class CloudManagementService:
    """Service for managing cloud provider projects with audit integration."""
    
    def __init__(self):
        self.db_manager = get_database_manager()
        self.audit_service = get_audit_service()
    
    async def create_cloud_project(
        self,
        project_data: CloudProjectCreate,
        tenant_id: str,
        user_id: str,
    ) -> CloudProjectResponse:
        """Create a new cloud provider project."""
        try:
            # Generate project ID as UUID
            project_id = str(uuid4())
            
            # Create cloud project record
            cloud_project = CloudProject(
                id=project_id,
                name=project_data.name,
                description=project_data.description,
                cloud_provider=project_data.cloud_provider.value,
                project_identifier=project_data.project_identifier,
                tenant_id=tenant_id,
                user_id=user_id,
                credentials=project_data.credentials,
                region=project_data.region,
                zone=project_data.zone,
                tags=project_data.tags,
                status="active",
            )
            
            # Store in database
            async with self.db_manager.get_session() as session:
                session.add(cloud_project)
                await session.commit()
                await session.refresh(cloud_project)
            
            # Post audit event
            audit_data = AuditEventCreate(
                event_type="cloud_project.created",
                action="create",
                status="success",
                resource_type="cloud_project",
                resource_id=str(project_id),
                service_name="cloud_management",
                tenant_id=tenant_id,
                user_id=user_id,
                metadata={
                    "project_name": project_data.name,
                    "cloud_provider": project_data.cloud_provider.value,
                    "project_identifier": project_data.project_identifier,
                }
            )
            
            await self.audit_service.create_audit_event(
                audit_data=audit_data,
                tenant_id=tenant_id,
                user_id=user_id,
            )
            
            # Convert to response model
            return CloudProjectResponse(
                id=str(cloud_project.id),
                name=cloud_project.name,
                description=cloud_project.description,
                cloud_provider=CloudProvider(cloud_project.cloud_provider),
                project_identifier=cloud_project.project_identifier,
                tenant_id=cloud_project.tenant_id,
                user_id=cloud_project.user_id,
                credentials=cloud_project.credentials,
                region=cloud_project.region,
                zone=cloud_project.zone,
                status=cloud_project.status,
                tags=cloud_project.tags,
                created_at=cloud_project.created_at,
                updated_at=cloud_project.updated_at,
            )
            
        except Exception as e:
            logger.error(f"Error creating cloud project: {e}")
            raise Exception(f"Error creating cloud project: {str(e)}")
    
    async def list_cloud_projects(
        self,
        tenant_id: str,
        cloud_provider: Optional[CloudProvider] = None,
        status_filter: Optional[str] = None,
    ) -> List[CloudProjectResponse]:
        """List cloud projects with optional filtering."""
        try:
            async with self.db_manager.get_session() as session:
                # Build query
                query = select(CloudProject).where(CloudProject.tenant_id == tenant_id)
                
                if cloud_provider:
                    query = query.where(CloudProject.cloud_provider == cloud_provider.value)
                
                if status_filter:
                    query = query.where(CloudProject.status == status_filter)
                
                # Execute query
                result = await session.execute(query)
                projects = result.scalars().all()
                
                # Convert to response models
                return [
                    CloudProjectResponse(
                        id=str(project.id),
                        name=project.name,
                        description=project.description,
                        cloud_provider=CloudProvider(project.cloud_provider),
                        project_identifier=project.project_identifier,
                        tenant_id=project.tenant_id,
                        user_id=project.user_id,
                        credentials=project.credentials,
                        region=project.region,
                        zone=project.zone,
                        status=project.status,
                        tags=project.tags,
                        created_at=project.created_at,
                        updated_at=project.updated_at,
                    )
                    for project in projects
                ]
                
        except Exception as e:
            logger.error(f"Error listing cloud projects: {e}")
            raise Exception(f"Error listing cloud projects: {str(e)}")
    
    async def get_cloud_project(
        self,
        project_id: str,
        tenant_id: str,
    ) -> Optional[CloudProjectResponse]:
        """Get a specific cloud project by ID."""
        try:
            async with self.db_manager.get_session() as session:
                query = select(CloudProject).where(
                    and_(
                        CloudProject.id == project_id,
                        CloudProject.tenant_id == tenant_id
                    )
                )
                
                result = await session.execute(query)
                project = result.scalar_one_or_none()
                
                if not project:
                    return None
                
                return CloudProjectResponse(
                    id=str(project.id),
                    name=project.name,
                    description=project.description,
                    cloud_provider=CloudProvider(project.cloud_provider),
                    project_identifier=project.project_identifier,
                    tenant_id=project.tenant_id,
                    user_id=project.user_id,
                    credentials=project.credentials,
                    region=project.region,
                    zone=project.zone,
                    status=project.status,
                    tags=project.tags,
                    created_at=project.created_at,
                    updated_at=project.updated_at,
                )
                
        except Exception as e:
            logger.error(f"Error getting cloud project: {e}")
            raise Exception(f"Error getting cloud project: {str(e)}")
    
    async def update_cloud_project(
        self,
        project_id: str,
        project_data: CloudProjectUpdate,
        tenant_id: str,
        user_id: str,
    ) -> Optional[CloudProjectResponse]:
        """Update a cloud project."""
        try:
            async with self.db_manager.get_session() as session:
                # Get existing project
                query = select(CloudProject).where(
                    and_(
                        CloudProject.id == project_id,
                        CloudProject.tenant_id == tenant_id
                    )
                )
                
                result = await session.execute(query)
                project = result.scalar_one_or_none()
                
                if not project:
                    return None
                
                # Update fields
                if project_data.name is not None:
                    project.name = project_data.name
                if project_data.description is not None:
                    project.description = project_data.description
                if project_data.credentials is not None:
                    project.credentials = project_data.credentials
                if project_data.region is not None:
                    project.region = project_data.region
                if project_data.zone is not None:
                    project.zone = project_data.zone
                if project_data.status is not None:
                    project.status = project_data.status
                if project_data.tags is not None:
                    project.tags = project_data.tags
                
                project.updated_at = datetime.now(timezone.utc)
                
                await session.commit()
                await session.refresh(project)
                
                # Post audit event
                audit_data = AuditEventCreate(
                    event_type="cloud_project.updated",
                    action="update",
                    status="success",
                    resource_type="cloud_project",
                    resource_id=str(project_id),
                    service_name="cloud_management",
                    tenant_id=tenant_id,
                    user_id=user_id,
                    metadata={
                        "project_name": project.name,
                        "cloud_provider": project.cloud_provider,
                        "project_identifier": project.project_identifier,
                    }
                )
                
                await self.audit_service.create_audit_event(
                    audit_data=audit_data,
                    tenant_id=tenant_id,
                    user_id=user_id,
                )
                
                return CloudProjectResponse(
                    id=str(project.id),
                    name=project.name,
                    description=project.description,
                    cloud_provider=CloudProvider(project.cloud_provider),
                    project_identifier=project.project_identifier,
                    tenant_id=project.tenant_id,
                    user_id=project.user_id,
                    credentials=project.credentials,
                    region=project.region,
                    zone=project.zone,
                    status=project.status,
                    tags=project.tags,
                    created_at=project.created_at,
                    updated_at=project.updated_at,
                )
                
        except Exception as e:
            logger.error(f"Error updating cloud project: {e}")
            raise Exception(f"Error updating cloud project: {str(e)}")
    
    async def delete_cloud_project(
        self,
        project_id: str,
        tenant_id: str,
        user_id: str,
    ) -> bool:
        """Delete a cloud project."""
        try:
            async with self.db_manager.get_session() as session:
                # Get existing project
                query = select(CloudProject).where(
                    and_(
                        CloudProject.id == project_id,
                        CloudProject.tenant_id == tenant_id
                    )
                )
                
                result = await session.execute(query)
                project = result.scalar_one_or_none()
                
                if not project:
                    return False
                
                # Store project info for audit
                project_name = project.name
                cloud_provider = project.cloud_provider
                project_identifier = project.project_identifier
                
                # Delete project
                await session.delete(project)
                await session.commit()
                
                # Post audit event
                audit_data = AuditEventCreate(
                    event_type="cloud_project.deleted",
                    action="delete",
                    status="success",
                    resource_type="cloud_project",
                    resource_id=str(project_id),
                    service_name="cloud_management",
                    tenant_id=tenant_id,
                    user_id=user_id,
                    metadata={
                        "project_name": project_name,
                        "cloud_provider": cloud_provider,
                        "project_identifier": project_identifier,
                    }
                )
                
                await self.audit_service.create_audit_event(
                    audit_data=audit_data,
                    tenant_id=tenant_id,
                    user_id=user_id,
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Error deleting cloud project: {e}")
            raise Exception(f"Error deleting cloud project: {str(e)}")
    
    async def test_cloud_connection(
        self,
        project_id: str,
        tenant_id: str,
    ) -> Dict[str, Any]:
        """Test connection to a cloud project."""
        try:
            async with self.db_manager.get_session() as session:
                # Get project
                query = select(CloudProject).where(
                    and_(
                        CloudProject.id == project_id,
                        CloudProject.tenant_id == tenant_id
                    )
                )
                
                result = await session.execute(query)
                project = result.scalar_one_or_none()
                
                if not project:
                    raise Exception("Cloud project not found")
                
                # Mock connection test (in real implementation, this would test actual cloud provider APIs)
                connection_result = {
                    "status": "success",
                    "provider": project.cloud_provider,
                    "project_identifier": project.project_identifier,
                    "region": project.region,
                    "tested_at": datetime.now(timezone.utc).isoformat(),
                    "details": {
                        "authentication": "valid",
                        "permissions": "sufficient",
                        "network": "accessible"
                    }
                }
                
                return connection_result
                
        except Exception as e:
            logger.error(f"Error testing cloud connection: {e}")
            raise Exception(f"Error testing cloud connection: {str(e)}")


# Singleton instance
_cloud_management_service: Optional[CloudManagementService] = None


def get_cloud_management_service() -> CloudManagementService:
    """Get the singleton cloud management service instance."""
    global _cloud_management_service
    if _cloud_management_service is None:
        _cloud_management_service = CloudManagementService()
    return _cloud_management_service
