"""
LLM Provider Models for MCP Integration

This module defines the data models for LLM provider configuration
and integration with the MCP service.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class LLMProviderType(str, Enum):
    """Supported LLM provider types"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    LITELLM = "litellm"
    CUSTOM = "custom"


class LLMProviderStatus(str, Enum):
    """LLM provider status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class LLMProviderConfig(BaseModel):
    """LLM provider configuration"""
    provider_id: str = Field(..., description="Unique provider identifier")
    name: str = Field(..., description="Provider display name")
    provider_type: LLMProviderType = Field(..., description="Provider type")
    status: LLMProviderStatus = Field(default=LLMProviderStatus.INACTIVE, description="Provider status")
    
    # Connection settings
    api_key: Optional[str] = Field(None, description="API key for the provider")
    base_url: Optional[str] = Field(None, description="Base URL for API calls")
    model_name: str = Field(..., description="Model name to use")
    
    # LiteLLM specific settings
    litellm_config: Optional[Dict[str, Any]] = Field(None, description="LiteLLM specific configuration")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="User who created the provider")
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider_id": "openai-gpt4",
                "name": "OpenAI GPT-4",
                "provider_type": "openai",
                "status": "active",
                "api_key": "sk-...",
                "base_url": "https://api.openai.com/v1",
                "model_name": "gpt-4",
                "created_by": "admin"
            }
        }


class LLMProviderCreate(BaseModel):
    """Request model for creating an LLM provider"""
    name: str
    provider_type: LLMProviderType
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: str
    litellm_config: Optional[Dict[str, Any]] = None
    status: LLMProviderStatus = LLMProviderStatus.INACTIVE
    is_enabled: bool = True
    is_default: bool = False


class LLMProviderUpdate(BaseModel):
    """Request model for updating an LLM provider"""
    name: Optional[str] = None
    provider_type: Optional[LLMProviderType] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None
    litellm_config: Optional[Dict[str, Any]] = None
    status: Optional[LLMProviderStatus] = None
    is_enabled: Optional[bool] = None
    is_default: Optional[bool] = None


class LLMProviderResponse(BaseModel):
    """Response model for LLM provider"""
    provider_id: str
    name: str
    provider_type: LLMProviderType
    status: LLMProviderStatus
    model_name: str
    base_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    is_enabled: bool = True
    is_default: bool = False

    class Config:
        from_attributes = True


class LLMProviderListResponse(BaseModel):
    """Response model for list of LLM providers"""
    providers: List[LLMProviderResponse]
    total: int


class LLMSummaryRequest(BaseModel):
    """Request model for LLM summarization"""
    query: str = Field(..., description="Original user query")
    mcp_result: Dict[str, Any] = Field(..., description="Raw MCP result data")
    provider_id: Optional[str] = Field(None, description="LLM provider to use")


class LLMSummaryResponse(BaseModel):
    """Response model for LLM summarization"""
    summary: str = Field(..., description="Summarized result")
    provider_used: Optional[str] = Field(None, description="Provider used for summarization")
    raw_result: Dict[str, Any] = Field(..., description="Original MCP result")
    has_llm_analysis: bool = Field(..., description="Whether LLM analysis was performed")
