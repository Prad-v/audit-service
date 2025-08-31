"""
Authentication Middleware

This module handles authentication and authorization for the Events Service.
"""

import os
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# For now, use a simple token-based auth
# In production, this should be replaced with proper JWT validation
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Get current user from token"""
    token = credentials.credentials
    
    # Simple token validation for development
    # In production, validate JWT token here
    if token == "test-token":
        return "test-user"
    
    # Check for API key
    api_key = os.getenv("EVENTS_API_KEY")
    if api_key and token == api_key:
        return "api-user"
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """Get current user from token (optional)"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
