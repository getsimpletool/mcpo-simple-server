"""
Module: Dependencies - FastAPI dependency injection utilities

High Level Concept:
-------------------
This module provides FastAPI dependency functions that can be used across
the application for common authentication and authorization patterns.
It offers optional authentication dependencies that don't raise exceptions
for unauthenticated users, allowing for flexible access patterns.

Architecture:
-------------
- get_username: Optional authentication that returns username or None
- Compatible with both JWT tokens and API keys
- Graceful handling of authentication failures

Workflow:
---------
1. Extract authentication credentials from request
2. Attempt to authenticate using available methods
3. Return username if successful, None if not authenticated
4. No exceptions raised for failed authentication

Usage Example:
--------------
>>> from fastapi import Depends
>>> from mcpo_simple_server.middleware.dependencies import get_username
>>> 
>>> @router.get("/public-endpoint")
>>> async def public_endpoint(username: Optional[str] = Depends(get_username)):
>>>     if username:
>>>         return {"message": f"Hello {username}"}
>>>     else:
>>>         return {"message": "Hello anonymous user"}

Notes:
------
- This is for optional authentication scenarios
- Use get_current_user for required authentication
- Supports both JWT and API key authentication methods
"""

from typing import Optional
from fastapi import Request

from mcpo_simple_server.services.auth import (
    get_authenticated_by_jwt_token,
    get_authenticated_by_api_key
)


async def get_username(request: Request) -> Optional[str]:
    """
    Optional authentication dependency that returns username or None.

    This function attempts to authenticate the user using JWT token or API key
    but doesn't raise exceptions if authentication fails. This is useful for
    endpoints that can work with both authenticated and anonymous users.

    Args:
        request: FastAPI request object

    Returns:
        Optional[str]: Username if authenticated, None otherwise
    """
    try:
        # Try JWT authentication first
        user = await get_authenticated_by_jwt_token(request)
        if user:
            return user.username
    except Exception:
        # JWT authentication failed, try API key
        pass

    try:
        # Try API key authentication
        user = await get_authenticated_by_api_key(request)
        if user:
            return user.username
    except Exception:
        # API key authentication failed
        pass

    # No authentication method succeeded
    return None
