"""
API Key handlers for the user router.
Includes endpoints for updating API Key metadata.
"""
from . import router
from fastapi import Depends, HTTPException, status, Body, Request
from pydantic import BaseModel, Field
from loguru import logger
from typing import TYPE_CHECKING, Optional, List
import hashlib
from mcpo_simple_server.services.auth import get_current_user
from mcpo_simple_server.services.config.models.user_config_model import ApiKeyMetadataModel

if TYPE_CHECKING:
    from mcpo_simple_server.services.config import ConfigService
    from mcpo_simple_server.services.auth.models import AuthUserModel


class APIKeyMetadataUpdateRequest(BaseModel):
    """Model for updating API key metadata."""
    md5_api_key: str = Field(
        ...,
        description="MD5 hash of the API key to update",
        min_length=32,
        max_length=32
    )
    description: Optional[str] = Field(
        None,
        description="User-provided description for this key",
        max_length=500
    )
    blackListTools: Optional[List[str]] = Field(
        None,
        description="List of tool names that cannot be accessed with this key"
    )


class APIKeyMetadataResponse(BaseModel):
    """Response model when updating API key metadata."""
    md5_api_key: str
    description: str
    blackListTools: List[str]
    detail: str = "API Key metadata updated successfully."


@router.put("/api-key", response_model=APIKeyMetadataResponse)
async def update_api_key_metadata(
    request: Request,
    metadata: APIKeyMetadataUpdateRequest = Body(...),
    current_user: 'AuthUserModel' = Depends(get_current_user)
):
    """
    Updates metadata for an existing API Key.
    You can update the description and blacklisted tools list.
    """
    config_service: 'ConfigService' = request.app.state.config_service

    # Get the current user config
    user_config = await config_service.user_config.get_config(current_user.username)
    if not user_config or not user_config.api_keys:
        logger.warning(f"No API Keys found for user '{current_user.username}'.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found")

    # Handle migration from list to dict if necessary
    if isinstance(user_config.api_keys, list):
        # Convert list of keys to dictionary with metadata
        old_keys = user_config.api_keys.copy()
        user_config.api_keys = {}
        for old_key in old_keys:
            user_config.api_keys[old_key] = ApiKeyMetadataModel()

    # Find the API key by its MD5 hash
    target_api_key = None
    for key in user_config.api_keys:
        key_md5 = hashlib.md5(key.encode()).hexdigest()
        if key_md5 == metadata.md5_api_key:
            target_api_key = key
            break

    # Check if the API key exists
    if not target_api_key:
        logger.warning(f"API Key with MD5 '{metadata.md5_api_key}' not found for user '{current_user.username}'.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found")

    # Update the metadata
    if metadata.description is not None:
        user_config.api_keys[target_api_key].description = metadata.description

    if metadata.blackListTools is not None:
        user_config.api_keys[target_api_key].blackListTools = metadata.blackListTools

    # Save the updated user data
    try:
        await config_service.user_config.save_config(user_config)
        await config_service.user_config.refresh_users_cache()
        logger.info(f"API Key metadata updated successfully for user '{current_user.username}'.")
    except Exception as e:
        logger.error(f"Failed to update API Key metadata for user '{current_user.username}' in config: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update API Key metadata") from e

    # Return the updated metadata
    updated_key = user_config.api_keys[target_api_key]
    return APIKeyMetadataResponse(
        md5_api_key=metadata.md5_api_key,
        description=updated_key.description,
        blackListTools=updated_key.blackListTools,
        detail="API Key metadata updated successfully."
    )
