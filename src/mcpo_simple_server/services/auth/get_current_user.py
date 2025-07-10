from typing import Optional
from fastapi import Depends, HTTPException, status
from loguru import logger
from mcpo_simple_server.services.auth import get_authenticated_by_jwt_token
from mcpo_simple_server.services.auth.models import AuthUserModel


async def get_current_user(current_user: Optional[AuthUserModel] = Depends(get_authenticated_by_jwt_token)) -> AuthUserModel:
    """
    Get the current authenticated user via access token only (no API key).
    """
    if current_user is None:
        logger.warning("Access token authentication failed. No valid token provided.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if current_user.disabled:
        logger.warning(f"Authentication failed. User '{current_user.username}' is disabled.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user
