"""
LLM Provider API endpoints for MCP Integration

This module provides REST API endpoints for managing LLM providers
and integrating them with the MCP service.
"""

from typing import List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, Form

from app.api.middleware import get_current_user
from app.models.llm import (
    LLMProviderCreate,
    LLMProviderUpdate,
    LLMProviderResponse,
    LLMProviderListResponse,
    LLMSummaryRequest,
    LLMSummaryResponse,
    LLMProviderType,
    LLMProviderStatus
)
from app.services.llm_service import get_llm_service
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter()


@router.post("/providers", response_model=LLMProviderResponse, tags=["LLM Providers"])
async def create_llm_provider(
    provider_data: LLMProviderCreate,
    current_user: Tuple[str, str, list, list] = Depends(get_current_user),
    llm_service = Depends(get_llm_service)
):
    """Create a new LLM provider"""
    try:
        user_id, tenant_id, roles, permissions = current_user
        return await llm_service.create_provider(provider_data, user_id)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create provider: {str(e)}")


@router.get("/providers", response_model=LLMProviderListResponse, tags=["LLM Providers"])
async def list_llm_providers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    llm_service = Depends(get_llm_service)
):
    """List all LLM providers"""
    try:
        return await llm_service.list_providers(skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list providers: {str(e)}")


@router.get("/providers/types", tags=["LLM Providers"])
async def get_provider_types():
    """Get available LLM provider types"""
    return {
        "provider_types": [
            {
                "value": provider_type.value,
                "label": provider_type.value.replace("_", " ").title(),
                "description": f"Support for {provider_type.value} models"
            }
            for provider_type in LLMProviderType
        ]
    }


@router.get("/providers/statuses", tags=["LLM Providers"])
async def get_provider_statuses():
    """Get available LLM provider statuses"""
    return {
        "statuses": [
            {
                "value": status.value,
                "label": status.value.title(),
                "description": f"Provider is {status.value}"
            }
            for status in LLMProviderStatus
        ]
    }

@router.post("/providers/models", tags=["LLM Providers"])
async def get_provider_models(
    provider_type: str = Form(..., description="Provider type"),
    api_key: Optional[str] = Form(None, description="API key for the provider"),
    base_url: Optional[str] = Form(None, description="Base URL for the provider"),
    litellm_config: Optional[str] = Form(None, description="LiteLLM configuration as JSON string"),
    llm_service = Depends(get_llm_service)
):
    """Get available models from a provider type"""
    try:
        # Parse litellm_config if provided
        parsed_litellm_config = None
        if litellm_config:
            import json
            parsed_litellm_config = json.loads(litellm_config)
        
        result = await llm_service.get_provider_models(
            provider_type=provider_type,
            api_key=api_key,
            base_url=base_url,
            litellm_config=parsed_litellm_config
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")

@router.post("/providers/test-connection", tags=["LLM Providers"])
async def test_provider_connection(
    provider_type: str = Form(..., description="Provider type"),
    api_key: Optional[str] = Form(None, description="API key for the provider"),
    base_url: Optional[str] = Form(None, description="Base URL for the provider"),
    litellm_config: Optional[str] = Form(None, description="LiteLLM configuration as JSON string"),
    llm_service = Depends(get_llm_service)
):
    """Test provider connection and get models"""
    try:
        # Parse litellm_config if provided
        parsed_litellm_config = None
        if litellm_config:
            import json
            parsed_litellm_config = json.loads(litellm_config)
        
        result = await llm_service.test_provider_connection(
            provider_type=provider_type,
            api_key=api_key,
            base_url=base_url,
            litellm_config=parsed_litellm_config
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test connection: {str(e)}")





@router.get("/providers/{provider_id}", response_model=LLMProviderResponse, tags=["LLM Providers"])
async def get_llm_provider(
    provider_id: str,
    llm_service = Depends(get_llm_service)
):
    """Get LLM provider by ID"""
    provider = await llm_service.get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.put("/providers/{provider_id}", response_model=LLMProviderResponse, tags=["LLM Providers"])
async def update_llm_provider(
    provider_id: str,
    update_data: LLMProviderUpdate,
    llm_service = Depends(get_llm_service)
):
    """Update LLM provider"""
    try:
        return await llm_service.update_provider(provider_id, update_data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update provider: {str(e)}")


@router.delete("/providers/{provider_id}", tags=["LLM Providers"])
async def delete_llm_provider(
    provider_id: str,
    llm_service = Depends(get_llm_service)
):
    """Delete LLM provider"""
    try:
        await llm_service.delete_provider(provider_id)
        return {"message": "Provider deleted successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete provider: {str(e)}")


@router.post("/providers/{provider_id}/test", tags=["LLM Providers"])
async def test_llm_provider(
    provider_id: str,
    llm_service = Depends(get_llm_service)
):
    """Test LLM provider connection"""
    try:
        result = await llm_service.test_provider(provider_id)
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test provider: {str(e)}")


@router.post("/summarize", response_model=LLMSummaryResponse, tags=["LLM Integration"])
async def summarize_mcp_result(
    request: LLMSummaryRequest,
    llm_service = Depends(get_llm_service)
):
    """Summarize MCP result using LLM"""
    try:
        return await llm_service.summarize_mcp_result(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to summarize result: {str(e)}")


@router.get("/default-provider", response_model=LLMProviderResponse, tags=["LLM Providers"])
async def get_default_provider(
    llm_service = Depends(get_llm_service)
):
    """Get the default LLM provider"""
    try:
        provider = await llm_service.get_default_provider()
        if not provider:
            raise HTTPException(status_code=404, detail="No default provider configured")
        return provider
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get default provider: {str(e)}")


@router.post("/providers/{provider_id}/set-default", response_model=LLMProviderResponse, tags=["LLM Providers"])
async def set_default_provider(
    provider_id: str,
    llm_service = Depends(get_llm_service)
):
    """Set a provider as the default"""
    try:
        return await llm_service.set_default_provider(provider_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set default provider: {str(e)}")
