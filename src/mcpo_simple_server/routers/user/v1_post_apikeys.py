"""
API Key handlers for the user router.
Includes endpoints for creating and managing API Keys used for tool access.
"""
from . import router
from fastapi import Depends, HTTPException, status, Request
from loguru import logger
from pydantic import BaseModel
from typing import TYPE_CHECKING, Optional
from mcpo_simple_server.services.auth import get_current_user, api_key
if TYPE_CHECKING:
    from mcpo_simple_server.services.config import ConfigService
    from mcpo_simple_server.services.auth.models import AuthUserModel
    from mcpo_simple_server.services.config.models import UserConfigModel


class APIKeyResponse(BaseModel):
    """Response model when creating an API key (shows plain text key once)."""
    api_key: str
    detail: str = "API key created successfully. Store it securely, it won't be shown again."


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_my_api_key(
    request: Request,
    current_user: 'AuthUserModel' = Depends(get_current_user)
):
    """
    Generates a new API Key for the currently authenticated user,
    stores its plain text, and returns the plain text key ONCE.
    API Keys are used for tool access and authentication.
    """
    config_service: 'ConfigService' = request.app.state.config_service

    # Generate a new API Key
    plain_api_key = api_key.create_api_key(current_user.username)

    # Update user data with the new API key
    try:
        # Get the current user config

        user_config: Optional['UserConfigModel'] = await config_service.user_config.get_config(current_user.username)

        # Add the new key
        if user_config is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if user_config.api_keys is None:
            user_config.api_keys = []
        user_config.api_keys.append(plain_api_key)

        # Save the updated config and refresh the cache
        await config_service.user_config.save_config(user_config)
        await config_service.user_config.refresh_users_cache()
    except Exception as e:
        logger.error(f"Failed to save API Key for user '{current_user.username}' in config: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create API Key") from e

    logger.info(f"API Key created successfully for user '{current_user.username}'.")
    return APIKeyResponse(api_key=plain_api_key, detail="API Key created successfully. Store it securely, it won't be shown again.")
