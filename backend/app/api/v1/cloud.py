"""
Cloud Management API endpoints.

This module provides REST API endpoints for managing cloud provider projects
including AWS, GCP, Azure, and OCI integrations.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.api.middleware import get_current_user
from app.models.cloud import CloudProjectCreate, CloudProjectUpdate, CloudProjectResponse, CloudProvider
from app.services.cloud_management_service import get_cloud_management_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cloud", tags=["cloud-management"])





@router.get("/health")
async def health_check():
    """Health check endpoint for cloud management service"""
    return {"status": "healthy", "service": "cloud_management"}


@router.post("/projects", response_model=CloudProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_cloud_project(
    request: Request,
    project_data: CloudProjectCreate,
):
    """Create a new cloud project."""
    try:
        user_id, tenant_id, _, _ = get_current_user(request)
        cloud_service = get_cloud_management_service()
        project = await cloud_service.create_cloud_project(
            project_data=project_data,
            tenant_id=tenant_id,
            user_id=user_id
        )
        return CloudProjectResponse.from_orm(project)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating cloud project: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/projects", response_model=List[CloudProjectResponse])
async def list_cloud_projects(
    request: Request,
    cloud_provider: Optional[CloudProvider] = None,
    status_filter: Optional[str] = None,
):
    """List cloud projects with optional filtering."""
    try:
        user_id, tenant_id, _, _ = get_current_user(request)
        cloud_service = get_cloud_management_service()
        projects = await cloud_service.list_cloud_projects(
            tenant_id=tenant_id,
            cloud_provider=cloud_provider,
            status_filter=status_filter
        )
        return [CloudProjectResponse.from_orm(project) for project in projects]
    except Exception as e:
        logger.error(f"Error listing cloud projects: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/projects/{project_id}", response_model=CloudProjectResponse)
async def get_cloud_project(
    request: Request,
    project_id: UUID,
):
    """Get a specific cloud project by ID."""
    try:
        user_id, tenant_id, _, _ = get_current_user(request)
        cloud_service = get_cloud_management_service()
        project = await cloud_service.get_cloud_project(
            project_id=project_id,
            tenant_id=tenant_id
        )
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cloud project not found")
        return CloudProjectResponse.from_orm(project)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cloud project: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.put("/projects/{project_id}", response_model=CloudProjectResponse)
async def update_cloud_project(
    request: Request,
    project_id: UUID,
    project_data: CloudProjectUpdate,
):
    """Update a cloud project."""
    try:
        user_id, tenant_id, _, _ = get_current_user(request)
        cloud_service = get_cloud_management_service()
        project = await cloud_service.update_cloud_project(
            project_id=project_id,
            project_data=project_data,
            tenant_id=tenant_id,
            user_id=user_id
        )
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cloud project not found")
        return CloudProjectResponse.from_orm(project)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating cloud project: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cloud_project(
    request: Request,
    project_id: UUID,
):
    """Delete a cloud project."""
    try:
        user_id, tenant_id, _, _ = get_current_user(request)
        cloud_service = get_cloud_management_service()
        success = await cloud_service.delete_cloud_project(
            project_id=project_id,
            tenant_id=tenant_id,
            user_id=user_id
        )
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cloud project not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting cloud project: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/projects/{project_id}/test-connection")
async def test_cloud_connection(
    request: Request,
    project_id: UUID,
):
    """Test connection to a cloud project."""
    try:
        user_id, tenant_id, _, _ = get_current_user(request)
        cloud_service = get_cloud_management_service()
        result = await cloud_service.test_cloud_connection(
            project_id=project_id,
            tenant_id=tenant_id
        )
        return {"status": "success", "message": "Connection successful", "details": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing cloud connection: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
