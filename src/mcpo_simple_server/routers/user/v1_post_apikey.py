"""
API Key handlers for the user router.
Includes endpoints for creating and managing API Keys used for tool access.
"""
from . import router
from fastapi import Depends, HTTPException, status, Request, Body
from loguru import logger
from pydantic import BaseModel, Field
from typing import TYPE_CHECKING, Optional, List
from datetime import datetime
from mcpo_simple_server.services.auth import get_current_user, api_key
from mcpo_simple_server.services.config.models.user_config_model import ApiKeyMetadataModel
if TYPE_CHECKING:
    from mcpo_simple_server.services.config import ConfigService
    from mcpo_simple_server.services.auth.models import AuthUserModel
    from mcpo_simple_server.services.config.models import UserConfigModel


class APIKeyCreateRequest(BaseModel):
    """Request model for creating a new API key with optional metadata."""
    description: Optional[str] = Field(
        "",
        description="User-provided description for this key",
        max_length=500
    )
    blackListTools: Optional[List[str]] = Field(
        [],
        description="List of tool names that cannot be accessed with this key"
    )


class APIKeyResponse(BaseModel):
    """Response model when creating an API key (shows plain text key once)."""
    api_key: str
    createdAt: datetime
    description: str = ""
    blackListTools: List[str] = []
    detail: str = "API key created successfully. Store it securely, it won't be shown again."


@router.post("/api-key", response_model=APIKeyResponse)
async def create_my_api_key(
    request: Request,
    key_options: APIKeyCreateRequest = Body(default=None),
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

        # Add the new key with metadata
        if user_config is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Handle migration from list to dict if necessary
        if isinstance(user_config.api_keys, list):
            # Convert list of keys to dictionary with metadata
            old_keys = user_config.api_keys.copy()
            user_config.api_keys = {}
            for old_key in old_keys:
                user_config.api_keys[old_key] = ApiKeyMetadataModel()

        # Create metadata for the new key with optional user-provided values
        description = "" if key_options is None or key_options.description is None else key_options.description
        blacklist = [] if key_options is None or key_options.blackListTools is None else key_options.blackListTools
        
        key_metadata = ApiKeyMetadataModel(
            createdAt=datetime.utcnow(),
            description=description,
            blackListTools=blacklist
        )

        # Add the new key with its metadata
        user_config.api_keys[plain_api_key] = key_metadata

        # Save the updated config and refresh the cache
        await config_service.user_config.save_config(user_config)
        await config_service.user_config.refresh_users_cache()
    except Exception as e:
        logger.error(f"Failed to save API Key for user '{current_user.username}' in config: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create API Key") from e

    logger.info(f"API Key created successfully for user '{current_user.username}'.")
    metadata = user_config.api_keys[plain_api_key]
    return APIKeyResponse(
        api_key=plain_api_key,
        createdAt=metadata.createdAt,
        description=metadata.description,
        blackListTools=metadata.blackListTools,
        detail="API Key created successfully. Store it securely, it won't be shown again."
    )
