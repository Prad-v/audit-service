"""
LLM Service for MCP Integration

This service handles LLM provider configuration and integration
with the MCP service for result summarization.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import uuid4

import httpx
from sqlalchemy import select, func, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_database_manager
from app.db.schemas import LLMProvider
from app.models.llm import (
    LLMProviderConfig,
    LLMProviderCreate,
    LLMProviderUpdate,
    LLMProviderResponse,
    LLMProviderListResponse,
    LLMSummaryRequest,
    LLMSummaryResponse,
    LLMProviderType,
    LLMProviderStatus
)
from app.core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class LLMService:
    """Service for managing LLM providers and integration"""
    
    def __init__(self):
        self.db_manager = get_database_manager()
    
    async def create_provider(self, provider_data: LLMProviderCreate, user_id: str) -> LLMProviderResponse:
        """Create a new LLM provider"""
        provider_id = f"{provider_data.provider_type.value}-{uuid4().hex[:8]}"
        
        provider = LLMProvider(
            provider_id=provider_id,
            name=provider_data.name,
            provider_type=provider_data.provider_type.value,
            status=provider_data.status.value,
            api_key=provider_data.api_key,
            base_url=provider_data.base_url,
            model_name=provider_data.model_name,
            litellm_config=provider_data.litellm_config,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=user_id,
            is_enabled=provider_data.is_enabled,
            is_default=provider_data.is_default
        )
        
        async with self.db_manager.get_session() as session:
            # If this provider is being set as default, unset any existing default
            if provider_data.is_default:
                await self._unset_existing_default(session)
            
            session.add(provider)
            await session.commit()
            await session.refresh(provider)
        
        return LLMProviderResponse(
            provider_id=provider.provider_id,
            name=provider.name,
            provider_type=LLMProviderType(provider.provider_type),
            status=LLMProviderStatus(provider.status),
            model_name=provider.model_name,
            base_url=provider.base_url,
            created_at=provider.created_at,
            updated_at=provider.updated_at,
            created_by=provider.created_by,
            is_enabled=provider.is_enabled,
            is_default=provider.is_default
        )
    
    async def get_provider(self, provider_id: str) -> LLMProviderResponse:
        """Get LLM provider by ID"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(LLMProvider).where(LLMProvider.provider_id == provider_id)
            )
            provider = result.scalar_one_or_none()
            
            if not provider:
                raise NotFoundError(f"LLM provider {provider_id} not found")
            
            return LLMProviderResponse(
                provider_id=provider.provider_id,
                name=provider.name,
                provider_type=LLMProviderType(provider.provider_type),
                status=LLMProviderStatus(provider.status),
                model_name=provider.model_name,
                base_url=provider.base_url,
                created_at=provider.created_at,
                updated_at=provider.updated_at,
                created_by=provider.created_by,
                is_enabled=provider.is_enabled,
                is_default=provider.is_default
            )
    
    async def _get_provider_with_api_key(self, provider_id: str) -> Optional[LLMProvider]:
        """Get LLM provider with API key for internal use"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(LLMProvider).where(LLMProvider.provider_id == provider_id)
            )
            return result.scalar_one_or_none()
    
    async def _update_provider_status(self, provider_id: str, status: LLMProviderStatus) -> None:
        """Update provider status"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(LLMProvider).where(LLMProvider.provider_id == provider_id)
            )
            provider = result.scalar_one_or_none()
            
            if provider:
                provider.status = status.value
                provider.updated_at = datetime.utcnow()
                await session.commit()
    
    async def list_providers(self, skip: int = 0, limit: int = 100) -> LLMProviderListResponse:
        """List all LLM providers"""
        async with self.db_manager.get_session() as session:
            # Get total count
            count_result = await session.execute(select(func.count(LLMProvider.provider_id)))
            total = count_result.scalar()
            
            # Get providers
            result = await session.execute(
                select(LLMProvider)
                .offset(skip)
                .limit(limit)
                .order_by(LLMProvider.created_at.desc())
            )
            providers = result.scalars().all()
            
            return LLMProviderListResponse(
                providers=[
                    LLMProviderResponse(
                        provider_id=p.provider_id,
                        name=p.name,
                        provider_type=LLMProviderType(p.provider_type),
                        status=LLMProviderStatus(p.status),
                        model_name=p.model_name,
                        base_url=p.base_url,
                        created_at=p.created_at,
                        updated_at=p.updated_at,
                        created_by=p.created_by,
                        is_enabled=p.is_enabled,
                        is_default=p.is_default
                    )
                    for p in providers
                ],
                total=total
            )
    
    async def update_provider(self, provider_id: str, update_data: LLMProviderUpdate) -> LLMProviderResponse:
        """Update LLM provider"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(LLMProvider).where(LLMProvider.provider_id == provider_id)
            )
            provider = result.scalar_one_or_none()
            
            if not provider:
                raise NotFoundError(f"LLM provider {provider_id} not found")
            
            # Update fields
            if update_data.name is not None:
                provider.name = update_data.name
            if update_data.provider_type is not None:
                provider.provider_type = update_data.provider_type.value
            if update_data.status is not None:
                provider.status = update_data.status.value
            if update_data.api_key is not None:
                provider.api_key = update_data.api_key
            if update_data.base_url is not None:
                provider.base_url = update_data.base_url
            if update_data.model_name is not None:
                provider.model_name = update_data.model_name
            if update_data.litellm_config is not None:
                provider.litellm_config = update_data.litellm_config
            if update_data.is_enabled is not None:
                provider.is_enabled = update_data.is_enabled
            if update_data.is_default is not None:
                # If setting as default, unset any existing default
                if update_data.is_default:
                    await self._unset_existing_default(session)
                provider.is_default = update_data.is_default
            
            provider.updated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(provider)
            
            return LLMProviderResponse(
                provider_id=provider.provider_id,
                name=provider.name,
                provider_type=LLMProviderType(provider.provider_type),
                status=LLMProviderStatus(provider.status),
                model_name=provider.model_name,
                base_url=provider.base_url,
                created_at=provider.created_at,
                updated_at=provider.updated_at,
                created_by=provider.created_by,
                is_enabled=provider.is_enabled,
                is_default=provider.is_default
            )
    
    async def delete_provider(self, provider_id: str) -> bool:
        """Delete LLM provider"""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(LLMProvider).where(LLMProvider.provider_id == provider_id)
            )
            provider = result.scalar_one_or_none()
            
            if not provider:
                raise NotFoundError(f"LLM provider {provider_id} not found")
            
            await session.delete(provider)
            await session.commit()
            
            return True
    
    async def test_provider(self, provider_id: str) -> Dict[str, Any]:
        """Test LLM provider connection"""
        # Get provider with API key for testing
        provider = await self._get_provider_with_api_key(provider_id)
        if not provider:
            raise ValueError(f"Provider {provider_id} not found")

        try:
            if provider.provider_type == LLMProviderType.LITELLM:
                # Test LiteLLM connection
                from litellm import completion
                
                # Use the provider's configuration
                model_name = provider.model_name
                api_key = provider.api_key
                base_url = provider.base_url
                litellm_config = provider.litellm_config or {}
                
                # Prepare test parameters
                test_params = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": "Hello, this is a test message."}],
                    "max_tokens": 10
                }
                
                # Add provider-specific configuration
                if api_key:
                    test_params["api_key"] = api_key
                if base_url:
                    test_params["api_base"] = base_url
                
                # Add any additional LiteLLM config
                test_params.update(litellm_config)
                
                response = completion(**test_params)
                
                # Update provider status to active on successful test
                await self._update_provider_status(provider_id, LLMProviderStatus.ACTIVE)
                
                return {
                    "success": True,
                    "message": "Connection successful",
                    "response": response.choices[0].message.content if response.choices else "No response content"
                }
                
            elif provider.provider_type == LLMProviderType.OPENAI:
                # Test OpenAI connection
                import httpx
                
                headers = {"Authorization": f"Bearer {provider.api_key}"}
                url = f"{provider.base_url or 'https://api.openai.com'}/v1/models"
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    
                return {
                    "success": True,
                    "message": "Connection successful",
                    "models_count": len(response.json().get("data", []))
                }
                
            elif provider.provider_type == LLMProviderType.ANTHROPIC:
                # Test Anthropic connection
                import httpx
                
                headers = {"x-api-key": provider.api_key}
                # Ensure we don't double up on /v1 in the URL
                if provider.base_url and provider.base_url.endswith('/v1'):
                    url = f"{provider.base_url}/models"
                elif provider.base_url:
                    url = f"{provider.base_url}/v1/models"
                else:
                    url = "https://api.anthropic.com/v1/models"
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    
                return {
                    "success": True,
                    "message": "Connection successful",
                    "models_count": len(response.json().get("data", []))
                }
                
            else:
                return {
                    "success": False,
                    "message": f"Testing not implemented for provider type: {provider.provider_type}"
                }
                
        except Exception as e:
            logger.error(f"Error testing provider {provider_id}: {e}")
            # Update provider status to error on failed test
            await self._update_provider_status(provider_id, LLMProviderStatus.ERROR)
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}"
            }

    async def get_provider_models(self, provider_type: str, api_key: str = None, base_url: str = None, litellm_config: Dict = None) -> Dict[str, Any]:
        """Get available models from a provider"""
        try:
            # Get default base URL if not provided
            if not base_url:
                base_url = self._get_default_base_url(provider_type)
            
            if provider_type == LLMProviderType.LITELLM:
                # For LiteLLM, we need to know which provider to query
                # This is a simplified approach - in practice, you might need more configuration
                if not litellm_config:
                    return {
                        "success": False,
                        "message": "LiteLLM requires configuration to determine which provider to query"
                    }
                
                # Try to get models from the configured provider
                try:
                    from litellm import get_llm_provider
                    provider_name = litellm_config.get("provider", "openai")
                    models = get_llm_provider(provider_name)
                    return {
                        "success": True,
                        "models": models,
                        "message": f"Retrieved models from {provider_name}",
                        "status": "active",
                        "base_url": base_url
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"Failed to get LiteLLM models: {str(e)}",
                        "status": "error",
                        "error_details": str(e)
                    }
                
            elif provider_type == LLMProviderType.OPENAI:
                # Get OpenAI models
                import httpx
                
                headers = {"Authorization": f"Bearer {api_key}"}
                # Ensure we don't double up on /v1 in the URL
                if base_url and base_url.endswith('/v1'):
                    url = f"{base_url}/models"
                elif base_url:
                    url = f"{base_url}/v1/models"
                else:
                    url = "https://api.openai.com/v1/models"
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    
                models_data = response.json().get("data", [])
                models = [
                    {
                        "id": model["id"],
                        "name": model["id"],
                        "object": model.get("object", "model"),
                        "created": model.get("created"),
                        "owned_by": model.get("owned_by", "openai")
                    }
                    for model in models_data
                ]
                
                return {
                    "success": True,
                    "models": models,
                    "message": f"Retrieved {len(models)} models from OpenAI",
                    "status": "active",
                    "base_url": base_url
                }
                
            elif provider_type == LLMProviderType.ANTHROPIC:
                # Get Anthropic models
                import httpx
                
                # Anthropic doesn't have a /models endpoint like OpenAI
                # Instead, we'll provide common Anthropic models
                common_models = [
                    {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "object": "model"},
                    {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "object": "model"},
                    {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "object": "model"},
                    {"id": "claude-2.1", "name": "Claude 2.1", "object": "model"},
                    {"id": "claude-2.0", "name": "Claude 2.0", "object": "model"},
                    {"id": "claude-instant-1.2", "name": "Claude Instant 1.2", "object": "model"}
                ]
                
                # If API key is provided, try to test the connection
                if api_key:
                    try:
                        headers = {
                            "x-api-key": api_key,
                            "anthropic-version": "2023-06-01",
                            "Content-Type": "application/json"
                        }
                        
                        # Test with a simple message request to verify the API key
                        # Ensure we don't double up on /v1 in the URL
                        if base_url and base_url.endswith('/v1'):
                            test_url = f"{base_url}/messages"
                        elif base_url:
                            test_url = f"{base_url}/v1/messages"
                        else:
                            test_url = "https://api.anthropic.com/v1/messages"
                        test_data = {
                            "model": "claude-3-haiku-20240307",
                            "max_tokens": 1,
                            "messages": [{"role": "user", "content": "test"}]
                        }
                        
                        async with httpx.AsyncClient() as client:
                            response = await client.post(test_url, headers=headers, json=test_data)
                            response.raise_for_status()
                        
                        return {
                            "success": True,
                            "models": common_models,
                            "message": f"Retrieved {len(common_models)} common Anthropic models",
                            "status": "active",
                            "base_url": base_url
                        }
                    except Exception as e:
                        return {
                            "success": False,
                            "models": common_models,
                            "message": f"API key validation failed: {str(e)}",
                            "status": "error",
                            "error_details": str(e),
                            "base_url": base_url
                        }
                else:
                    return {
                        "success": True,
                        "models": common_models,
                        "message": f"Retrieved {len(common_models)} common Anthropic models (API key required for validation)",
                        "status": "inactive",
                        "base_url": base_url
                    }
                
            elif provider_type == LLMProviderType.GOOGLE:
                # Get Google models (simplified - you might need more configuration)
                return {
                    "success": True,
                    "models": [
                        {"id": "gemini-pro", "name": "Gemini Pro", "object": "model"},
                        {"id": "gemini-pro-vision", "name": "Gemini Pro Vision", "object": "model"},
                        {"id": "text-bison-001", "name": "Text Bison", "object": "model"}
                    ],
                    "message": "Common Google models (API key required for full list)",
                    "status": "active" if api_key else "inactive",
                    "base_url": base_url
                }
                
            elif provider_type == LLMProviderType.AZURE:
                # Get Azure models (simplified - you might need more configuration)
                return {
                    "success": True,
                    "models": [
                        {"id": "gpt-35-turbo", "name": "GPT-3.5 Turbo", "object": "model"},
                        {"id": "gpt-4", "name": "GPT-4", "object": "model"},
                        {"id": "gpt-4-32k", "name": "GPT-4 32K", "object": "model"}
                    ],
                    "message": "Common Azure models (API key and endpoint required for full list)",
                    "status": "active" if api_key else "inactive",
                    "base_url": base_url
                }
                
            elif provider_type == LLMProviderType.CUSTOM:
                return {
                    "success": True,
                    "models": [
                        {"id": "custom-model", "name": "Custom Model", "object": "model"}
                    ],
                    "message": "Custom provider - configure model name manually",
                    "status": "inactive",
                    "base_url": base_url
                }
                
            else:
                return {
                    "success": False,
                    "message": f"Provider type {provider_type} not supported for model listing",
                    "status": "error"
                }
                
        except Exception as e:
            logger.error(f"Error getting models for provider type {provider_type}: {e}")
            return {
                "success": False,
                "message": f"Failed to get models: {str(e)}",
                "status": "error",
                "error_details": str(e)
            }

    def _get_default_base_url(self, provider_type: str) -> str:
        """Get default base URL for a provider type"""
        default_urls = {
            LLMProviderType.OPENAI: "https://api.openai.com/v1",
            LLMProviderType.ANTHROPIC: "https://api.anthropic.com/v1",
            LLMProviderType.GOOGLE: "https://generativelanguage.googleapis.com/v1",
            LLMProviderType.AZURE: "https://your-resource.openai.azure.com",
            LLMProviderType.LITELLM: "https://api.openai.com/v1",  # Default to OpenAI
            LLMProviderType.CUSTOM: ""
        }
        return default_urls.get(provider_type, "")

    async def test_provider_connection(self, provider_type: str, api_key: str = None, base_url: str = None, litellm_config: Dict = None) -> Dict[str, Any]:
        """Test provider connection and return status with models"""
        try:
            # Get default base URL if not provided
            if not base_url:
                base_url = self._get_default_base_url(provider_type)
            
            # Test connection and get models
            result = await self.get_provider_models(provider_type, api_key, base_url, litellm_config)
            
            # Add connection test result
            if result.get("success"):
                result["connection_test"] = {
                    "success": True,
                    "message": "Connection successful"
                }
            else:
                result["connection_test"] = {
                    "success": False,
                    "message": result.get("message", "Connection failed")
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error testing provider connection: {e}")
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}",
                "status": "error",
                "error_details": str(e),
                "connection_test": {
                    "success": False,
                    "message": f"Connection test failed: {str(e)}"
                }
            }
    
    async def summarize_mcp_result(self, request: LLMSummaryRequest) -> LLMSummaryResponse:
        """Summarize MCP result using LLM"""
        if not request.provider_id:
            # Return raw result if no provider specified
            return LLMSummaryResponse(
                summary="No LLM provider configured. Showing raw results.",
                provider_used=None,
                raw_result=request.mcp_result,
                has_llm_analysis=False
            )
        
        try:
            # Get the provider with API key for internal use
            provider = await self._get_provider_with_api_key(request.provider_id)
            if not provider:
                raise NotFoundError(f"LLM provider {request.provider_id} not found")
            
            if provider.status != LLMProviderStatus.ACTIVE:
                return LLMSummaryResponse(
                    summary="LLM provider is not active. Showing raw results.",
                    provider_used=provider.provider_id,
                    raw_result=request.mcp_result,
                    has_llm_analysis=False
                )
            
            # Generate summary using LLM
            summary = await self._generate_summary(provider, request.query, request.mcp_result)
            
            return LLMSummaryResponse(
                summary=summary,
                provider_used=provider.provider_id,
                raw_result=request.mcp_result,
                has_llm_analysis=True
            )
            
        except Exception as e:
            logger.error(f"Error summarizing MCP result: {e}")
            # Re-raise the exception so MCP service can handle fallback
            raise
    
    async def _generate_summary(self, provider: LLMProvider, query: str, mcp_result: Dict[str, Any]) -> str:
        """Generate summary using LLM"""
        try:
            if provider.provider_type == LLMProviderType.LITELLM:
                return await self._generate_litellm_summary(provider, query, mcp_result)
            else:
                return await self._generate_standard_summary(provider, query, mcp_result)
        except Exception as e:
            logger.error(f"Error generating summary with {provider.provider_type}: {str(e)}")
            raise
    
    async def _generate_litellm_summary(self, provider: LLMProvider, query: str, mcp_result: Dict[str, Any]) -> str:
        """Generate summary using LiteLLM"""
        from litellm import completion
        
        # Prepare prompt
        prompt = self._create_summary_prompt(query, mcp_result)
        
        # Call LiteLLM
        response = completion(
            model=provider.model_name,
            messages=[{"role": "user", "content": prompt}],
            api_key=provider.api_key,
            base_url=provider.base_url,
            **(provider.litellm_config or {})
        )
        
        return response.choices[0].message.content
    
    async def _generate_standard_summary(self, provider: LLMProvider, query: str, mcp_result: Dict[str, Any]) -> str:
        """Generate summary using standard provider"""
        # Prepare prompt
        prompt = self._create_summary_prompt(query, mcp_result)
        
        if provider.provider_type == LLMProviderType.OPENAI:
            return await self._call_openai_summary(provider, prompt)
        elif provider.provider_type == LLMProviderType.ANTHROPIC:
            return await self._call_anthropic_summary(provider, prompt)
        else:
            raise ValidationError(f"Provider type {provider.provider_type} not implemented for summarization")
    
    async def _call_openai_summary(self, provider: LLMProvider, prompt: str) -> str:
        """Call OpenAI for summarization"""
        url = f"{provider.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": provider.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    async def _call_anthropic_summary(self, provider: LLMProvider, prompt: str) -> str:
        """Call Anthropic for summarization"""
        # Ensure we don't double up on /v1 in the URL
        if provider.base_url and provider.base_url.endswith('/v1'):
            url = f"{provider.base_url}/messages"
        elif provider.base_url:
            url = f"{provider.base_url}/v1/messages"
        else:
            url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": provider.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        data = {
            "model": provider.model_name,
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result["content"][0]["text"]
    
    def _create_summary_prompt(self, query: str, mcp_result: Dict[str, Any]) -> str:
        """Create prompt for LLM summarization"""
        result_type = mcp_result.get("type", "unknown")
        
        if result_type == "search_results":
            count = mcp_result.get("count", 0)
            events = mcp_result.get("events", [])
            
            prompt = f"""
You are an AI assistant analyzing audit log search results. Please provide a clear, concise summary of the findings.

Original Query: "{query}"

Search Results:
- Total events found: {count}
- Query type: {result_type}

{f"Events found: {len(events)}" if events else "No events found"}

Please provide a natural language summary that:
1. Answers the user's original question
2. Highlights key findings and patterns
3. Mentions the number of results found
4. Provides insights about the data

Keep the summary concise but informative.
"""
            
            if events:
                # Add sample events for context
                sample_events = events[:3]  # Show first 3 events
                prompt += f"\nSample events:\n{json.dumps(sample_events, indent=2)}"
        
        elif result_type == "analytics":
            total_events = mcp_result.get("total_events", 0)
            by_event_type = mcp_result.get("by_event_type", {})
            by_status = mcp_result.get("by_status", {})
            
            prompt = f"""
You are an AI assistant analyzing audit log analytics. Please provide a clear, concise summary of the findings.

Original Query: "{query}"

Analytics Results:
- Total events: {total_events}
- Event types: {json.dumps(by_event_type, indent=2)}
- Status breakdown: {json.dumps(by_status, indent=2)}

Please provide a natural language summary that:
1. Answers the user's original question
2. Highlights key statistics and trends
3. Identifies the most common event types
4. Provides insights about the data distribution

Keep the summary concise but informative.
"""
        
        else:
            prompt = f"""
You are an AI assistant analyzing audit log results. Please provide a clear, concise summary of the findings.

Original Query: "{query}"

Results: {json.dumps(mcp_result, indent=2)}

Please provide a natural language summary that answers the user's original question and highlights key findings.
"""
        
        return prompt

    async def _unset_existing_default(self, session: AsyncSession) -> None:
        """Unset any existing default provider"""
        await session.execute(
            update(LLMProvider)
            .where(LLMProvider.is_default == True)
            .values(is_default=False)
        )
        await session.commit()

    async def get_default_provider(self) -> Optional[LLMProviderResponse]:
        """Get the default LLM provider"""
        async with self.db_manager.get_session() as session:
            logger.info("Searching for default provider...")
            result = await session.execute(
                select(LLMProvider)
                .where(and_(LLMProvider.is_default == True, LLMProvider.is_enabled == True))
            )
            provider = result.scalar_one_or_none()
            
            if not provider:
                logger.warning("No default provider found")
                return None
            
            logger.info(f"Found default provider: {provider.provider_id}")
            return LLMProviderResponse(
                provider_id=provider.provider_id,
                name=provider.name,
                provider_type=LLMProviderType(provider.provider_type),
                status=LLMProviderStatus(provider.status),
                model_name=provider.model_name,
                base_url=provider.base_url,
                created_at=provider.created_at,
                updated_at=provider.updated_at,
                created_by=provider.created_by,
                is_enabled=provider.is_enabled,
                is_default=provider.is_default
            )

    async def set_default_provider(self, provider_id: str) -> LLMProviderResponse:
        """Set a provider as the default"""
        async with self.db_manager.get_session() as session:
            # Get the provider
            result = await session.execute(
                select(LLMProvider).where(LLMProvider.provider_id == provider_id)
            )
            provider = result.scalar_one_or_none()
            
            if not provider:
                raise NotFoundError(f"LLM provider {provider_id} not found")
            
            # Unset existing default
            await self._unset_existing_default(session)
            
            # Set new default
            provider.is_default = True
            provider.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(provider)
            
            return LLMProviderResponse(
                provider_id=provider.provider_id,
                name=provider.name,
                provider_type=LLMProviderType(provider.provider_type),
                status=LLMProviderStatus(provider.status),
                model_name=provider.model_name,
                base_url=provider.base_url,
                created_at=provider.created_at,
                updated_at=provider.updated_at,
                created_by=provider.created_by,
                is_enabled=provider.is_enabled,
                is_default=provider.is_default
            )


# Global LLM service instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get the global LLM service instance"""
    global _llm_service
    if not _llm_service:
        _llm_service = LLMService()
    return _llm_service
