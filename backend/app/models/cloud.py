"""
Cloud Management Models

This module defines Pydantic models for cloud provider project management.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class CloudProvider(str, Enum):
    """Supported cloud providers"""
    GCP = "gcp"
    AWS = "aws"
    AZURE = "azure"
    OCI = "oci"


class CloudProjectBase(BaseModel):
    """Base model for cloud project data"""
    name: str = Field(..., description="Project name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Project description", max_length=1000)
    cloud_provider: CloudProvider = Field(..., description="Cloud provider")
    project_identifier: str = Field(..., description="Cloud provider project identifier", min_length=1, max_length=255)
    credentials: Optional[Dict[str, Any]] = Field(None, description="Cloud provider credentials")
    region: Optional[str] = Field(None, description="Cloud region")
    zone: Optional[str] = Field(None, description="Cloud zone")
    tags: Optional[Dict[str, Any]] = Field(None, description="Project tags")


class CloudProjectCreate(CloudProjectBase):
    """Model for creating a cloud project"""
    pass


class CloudProjectUpdate(BaseModel):
    """Model for updating a cloud project"""
    name: Optional[str] = Field(None, description="Project name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Project description", max_length=1000)
    credentials: Optional[Dict[str, Any]] = Field(None, description="Cloud provider credentials")
    region: Optional[str] = Field(None, description="Cloud region")
    zone: Optional[str] = Field(None, description="Cloud zone")
    status: Optional[str] = Field(None, description="Project status")
    tags: Optional[Dict[str, Any]] = Field(None, description="Project tags")


class CloudProjectResponse(CloudProjectBase):
    """Model for cloud project response"""
    id: str = Field(..., description="Unique project identifier")
    tenant_id: str = Field(..., description="Tenant ID")
    user_id: Optional[str] = Field(None, description="User who created the project")
    status: str = Field(..., description="Project status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class CloudProjectListResponse(BaseModel):
    """Model for cloud project list response"""
    projects: list[CloudProjectResponse] = Field(..., description="List of cloud projects")
    total: int = Field(..., description="Total number of projects")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of projects per page")


class CloudConnectionTestResponse(BaseModel):
    """Model for cloud connection test response"""
    success: bool = Field(..., description="Whether connection test was successful")
    connection: str = Field(..., description="Connection status")
    error: Optional[str] = Field(None, description="Error message if connection failed")
    project_id: str = Field(..., description="Project ID")
    cloud_provider: str = Field(..., description="Cloud provider")
