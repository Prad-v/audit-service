"""
Cloud Provider API Endpoints

This module contains FastAPI endpoints for managing cloud provider projects and configurations.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schemas import CloudProject
from app.models.events import (
    CloudProjectCreate, CloudProjectUpdate, CloudProjectResponse, CloudProjectListResponse,
    CloudProvider
)
from app.core.database import get_db
from app.core.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/projects", response_model=CloudProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_cloud_project(
    project_data: CloudProjectCreate,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new cloud project"""
    try:
        # Generate project ID
        project_id = f"{project_data.cloud_provider.value}-project-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{current_user[:8]}"
        
        # Create project
        project = CloudProject(
            project_id=project_id,
            name=project_data.name,
            description=project_data.description,
            cloud_provider=project_data.cloud_provider,
            project_identifier=project_data.project_identifier,
            config=project_data.config,
            enabled=project_data.enabled,
            auto_subscribe=project_data.auto_subscribe,
            tenant_id="default",  # TODO: Get from user context
            created_by=current_user
        )
        
        db.add(project)
        await db.commit()
        await db.refresh(project)
        
        return CloudProjectResponse.from_orm(project)
        
    except Exception as e:
        logger.error(f"Error creating cloud project: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating cloud project: {str(e)}")


@router.get("/projects", response_model=CloudProjectListResponse)
async def list_cloud_projects(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    cloud_provider: Optional[CloudProvider] = None,
    enabled: Optional[bool] = None,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List cloud projects"""
    try:
        # Build query
        query = select(CloudProject).where(CloudProject.tenant_id == "default")
        
        if cloud_provider:
            query = query.where(CloudProject.cloud_provider == cloud_provider)
        if enabled is not None:
            query = query.where(CloudProject.enabled == enabled)
        
        # Get total count
        count_query = select(func.count(CloudProject.project_id)).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # Get paginated results
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        result = await db.execute(query)
        projects = result.scalars().all()
        
        return CloudProjectListResponse(
            projects=[CloudProjectResponse.from_orm(project) for project in projects],
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error listing cloud projects: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing cloud projects: {str(e)}")


@router.get("/projects/{project_id}", response_model=CloudProjectResponse)
async def get_cloud_project(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific cloud project"""
    try:
        result = await db.execute(
            select(CloudProject).where(
                and_(
                    CloudProject.project_id == project_id,
                    CloudProject.tenant_id == "default"
                )
            )
        )
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Cloud project not found")
        
        return CloudProjectResponse.from_orm(project)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cloud project: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting cloud project: {str(e)}")


@router.put("/projects/{project_id}", response_model=CloudProjectResponse)
async def update_cloud_project(
    project_id: str,
    project_data: CloudProjectUpdate,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a cloud project"""
    try:
        result = await db.execute(
            select(CloudProject).where(
                and_(
                    CloudProject.project_id == project_id,
                    CloudProject.tenant_id == "default"
                )
            )
        )
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Cloud project not found")
        
        # Update fields
        update_data = project_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)
        
        project.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(project)
        
        return CloudProjectResponse.from_orm(project)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating cloud project: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating cloud project: {str(e)}")


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cloud_project(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a cloud project"""
    try:
        result = await db.execute(
            select(CloudProject).where(
                and_(
                    CloudProject.project_id == project_id,
                    CloudProject.tenant_id == "default"
                )
            )
        )
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Cloud project not found")
        
        await db.delete(project)
        await db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting cloud project: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting cloud project: {str(e)}")


@router.get("/projects/{project_id}/test-connection")
async def test_cloud_project_connection(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Test connection to cloud project"""
    try:
        result = await db.execute(
            select(CloudProject).where(
                and_(
                    CloudProject.project_id == project_id,
                    CloudProject.tenant_id == "default"
                )
            )
        )
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Cloud project not found")
        
        # Test connection based on provider
        try:
            if project.cloud_provider == CloudProvider.GCP:
                # Test GCP connection
                from app.services.cloud_providers.gcp import GCPProvider
                provider = GCPProvider(project.config)
                success = await provider.test_connection()
            elif project.cloud_provider == CloudProvider.AWS:
                # Test AWS connection
                from app.services.cloud_providers.aws import AWSProvider
                provider = AWSProvider(project.config)
                success = await provider.test_connection()
            elif project.cloud_provider == CloudProvider.AZURE:
                # Test Azure connection
                from app.services.cloud_providers.azure import AzureProvider
                provider = AzureProvider(project.config)
                success = await provider.test_connection()
            elif project.cloud_provider == CloudProvider.OCI:
                # Test OCI connection
                from app.services.cloud_providers.oci import OCIProvider
                provider = OCIProvider(project.config)
                success = await provider.test_connection()
            else:
                success = False
                
            return {
                "success": success,
                "message": "Connection successful" if success else "Connection failed",
                "provider": project.cloud_provider.value
            }
            
        except Exception as conn_error:
            logger.error(f"Connection test failed for project {project_id}: {conn_error}")
            return {
                "success": False,
                "message": f"Connection failed: {str(conn_error)}",
                "provider": project.cloud_provider.value
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing cloud project connection: {e}")
        raise HTTPException(status_code=500, detail=f"Error testing connection: {str(e)}")


@router.get("/projects/{project_id}/services")
async def get_cloud_project_services(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get available services for a cloud project"""
    try:
        result = await db.execute(
            select(CloudProject).where(
                and_(
                    CloudProject.project_id == project_id,
                    CloudProject.tenant_id == "default"
                )
            )
        )
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Cloud project not found")
        
        # Get services based on provider
        try:
            if project.cloud_provider == CloudProvider.GCP:
                from app.services.cloud_providers.gcp import GCPProvider
                provider = GCPProvider(project.config)
                services = await provider.get_available_services()
            elif project.cloud_provider == CloudProvider.AWS:
                from app.services.cloud_providers.aws import AWSProvider
                provider = AWSProvider(project.config)
                services = await provider.get_available_services()
            elif project.cloud_provider == CloudProvider.AZURE:
                from app.services.cloud_providers.azure import AzureProvider
                provider = AzureProvider(project.config)
                services = await provider.get_available_services()
            elif project.cloud_provider == CloudProvider.OCI:
                from app.services.cloud_providers.oci import OCIProvider
                provider = OCIProvider(project.config)
                services = await provider.get_available_services()
            else:
                services = []
                
            return {
                "project_id": project_id,
                "provider": project.cloud_provider.value,
                "services": services
            }
            
        except Exception as service_error:
            logger.error(f"Failed to get services for project {project_id}: {service_error}")
            return {
                "project_id": project_id,
                "provider": project.cloud_provider.value,
                "services": [],
                "error": str(service_error)
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cloud project services: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting services: {str(e)}")


@router.get("/projects/{project_id}/regions")
async def get_cloud_project_regions(
    project_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get available regions for a cloud project"""
    try:
        result = await db.execute(
            select(CloudProject).where(
                and_(
                    CloudProject.project_id == project_id,
                    CloudProject.tenant_id == "default"
                )
            )
        )
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail="Cloud project not found")
        
        # Get regions based on provider
        try:
            if project.cloud_provider == CloudProvider.GCP:
                from app.services.cloud_providers.gcp import GCPProvider
                provider = GCPProvider(project.config)
                regions = await provider.get_available_regions()
            elif project.cloud_provider == CloudProvider.AWS:
                from app.services.cloud_providers.aws import AWSProvider
                provider = AWSProvider(project.config)
                regions = await provider.get_available_regions()
            elif project.cloud_provider == CloudProvider.AZURE:
                from app.services.cloud_providers.azure import AzureProvider
                provider = AzureProvider(project.config)
                regions = await provider.get_available_regions()
            elif project.cloud_provider == CloudProvider.OCI:
                from app.services.cloud_providers.oci import OCIProvider
                provider = OCIProvider(project.config)
                regions = await provider.get_available_regions()
            else:
                regions = []
                
            return {
                "project_id": project_id,
                "provider": project.cloud_provider.value,
                "regions": regions
            }
            
        except Exception as region_error:
            logger.error(f"Failed to get regions for project {project_id}: {region_error}")
            return {
                "project_id": project_id,
                "provider": project.cloud_provider.value,
                "regions": [],
                "error": str(region_error)
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cloud project regions: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting regions: {str(e)}")
