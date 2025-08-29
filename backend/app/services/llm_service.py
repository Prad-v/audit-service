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
from sqlalchemy import select, func
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
            status=LLMProviderStatus.INACTIVE.value,
            api_key=provider_data.api_key,
            base_url=provider_data.base_url,
            model_name=provider_data.model_name,
            litellm_config=provider_data.litellm_config,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=user_id
        )
        
        async with self.db_manager.get_session() as session:
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
            created_by=provider.created_by
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
                created_by=provider.created_by
            )
    
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
                        created_by=p.created_by
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
                created_by=provider.created_by
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
        provider = await self.get_provider(provider_id)
        
        try:
            if provider.provider_type == LLMProviderType.LITELLM:
                return await self._test_litellm_provider(provider)
            else:
                return await self._test_standard_provider(provider)
        except Exception as e:
            logger.error(f"Error testing provider {provider_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider_id": provider_id
            }
    
    async def _test_litellm_provider(self, provider: LLMProviderResponse) -> Dict[str, Any]:
        """Test LiteLLM provider"""
        try:
            # Get provider config from database
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    select(LLMProvider).where(LLMProvider.provider_id == provider.provider_id)
                )
                db_provider = result.scalar_one()
            
            # Use LiteLLM for testing
            from litellm import completion
            
            # Prepare test message
            test_message = "Hello, this is a test message. Please respond with 'Test successful' if you can see this."
            
            # Call LiteLLM
            response = completion(
                model=provider.model_name,
                messages=[{"role": "user", "content": test_message}],
                api_key=db_provider.api_key,
                base_url=db_provider.base_url,
                **(db_provider.litellm_config or {})
            )
            
            return {
                "success": True,
                "provider_id": provider.provider_id,
                "response": response.choices[0].message.content,
                "model": provider.model_name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider_id": provider.provider_id
            }
    
    async def _test_standard_provider(self, provider: LLMProviderResponse) -> Dict[str, Any]:
        """Test standard provider (OpenAI, Anthropic, etc.)"""
        try:
            # Get provider config from database
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    select(LLMProvider).where(LLMProvider.provider_id == provider.provider_id)
                )
                db_provider = result.scalar_one()
            
            # Prepare test message
            test_message = "Hello, this is a test message. Please respond with 'Test successful' if you can see this."
            
            # Make API call based on provider type
            if provider.provider_type == LLMProviderType.OPENAI:
                return await self._test_openai_provider(db_provider, test_message)
            elif provider.provider_type == LLMProviderType.ANTHROPIC:
                return await self._test_anthropic_provider(db_provider, test_message)
            else:
                return {
                    "success": False,
                    "error": f"Provider type {provider.provider_type} not implemented for testing",
                    "provider_id": provider.provider_id
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider_id": provider.provider_id
            }
    
    async def _test_openai_provider(self, provider: LLMProvider, test_message: str) -> Dict[str, Any]:
        """Test OpenAI provider"""
        url = f"{provider.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": provider.model_name,
            "messages": [{"role": "user", "content": test_message}],
            "max_tokens": 50
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return {
                "success": True,
                "provider_id": provider.provider_id,
                "response": result["choices"][0]["message"]["content"],
                "model": provider.model_name
            }
    
    async def _test_anthropic_provider(self, provider: LLMProvider, test_message: str) -> Dict[str, Any]:
        """Test Anthropic provider"""
        url = f"{provider.base_url}/messages"
        headers = {
            "x-api-key": provider.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        data = {
            "model": provider.model_name,
            "max_tokens": 50,
            "messages": [{"role": "user", "content": test_message}]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return {
                "success": True,
                "provider_id": provider.provider_id,
                "response": result["content"][0]["text"],
                "model": provider.model_name
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
            # Get the provider
            provider = await self.get_provider(request.provider_id)
            
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
            return LLMSummaryResponse(
                summary=f"Error generating summary: {str(e)}. Showing raw results.",
                provider_used=request.provider_id,
                raw_result=request.mcp_result,
                has_llm_analysis=False
            )
    
    async def _generate_summary(self, provider: LLMProviderResponse, query: str, mcp_result: Dict[str, Any]) -> str:
        """Generate summary using LLM"""
        try:
            if provider.provider_type == LLMProviderType.LITELLM:
                return await self._generate_litellm_summary(provider, query, mcp_result)
            else:
                return await self._generate_standard_summary(provider, query, mcp_result)
        except Exception as e:
            logger.error(f"Error generating summary with {provider.provider_type}: {e}")
            raise
    
    async def _generate_litellm_summary(self, provider: LLMProviderResponse, query: str, mcp_result: Dict[str, Any]) -> str:
        """Generate summary using LiteLLM"""
        from litellm import completion
        
        # Get provider config from database
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(LLMProvider).where(LLMProvider.provider_id == provider.provider_id)
            )
            db_provider = result.scalar_one()
        
        # Prepare prompt
        prompt = self._create_summary_prompt(query, mcp_result)
        
        # Call LiteLLM
        response = completion(
            model=provider.model_name,
            messages=[{"role": "user", "content": prompt}],
            api_key=db_provider.api_key,
            base_url=db_provider.base_url,
            **(db_provider.litellm_config or {})
        )
        
        return response.choices[0].message.content
    
    async def _generate_standard_summary(self, provider: LLMProviderResponse, query: str, mcp_result: Dict[str, Any]) -> str:
        """Generate summary using standard provider"""
        # Get provider config from database
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(LLMProvider).where(LLMProvider.provider_id == provider.provider_id)
            )
            db_provider = result.scalar_one()
        
        # Prepare prompt
        prompt = self._create_summary_prompt(query, mcp_result)
        
        if provider.provider_type == LLMProviderType.OPENAI:
            return await self._call_openai_summary(db_provider, prompt)
        elif provider.provider_type == LLMProviderType.ANTHROPIC:
            return await self._call_anthropic_summary(db_provider, prompt)
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
        url = f"{provider.base_url}/messages"
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


# Global LLM service instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get the global LLM service instance"""
    global _llm_service
    if not _llm_service:
        _llm_service = LLMService()
    return _llm_service
