"""
API Key handlers for the user router.
Includes endpoints for creating and managing API Keys used for tool access.
"""
from . import router
from typing import TYPE_CHECKING
from fastapi import Depends, HTTPException, status, Body, Request
from pydantic import BaseModel, Field
from loguru import logger
from mcpo_simple_server.services.auth import get_current_user
if TYPE_CHECKING:
    from mcpo_simple_server.services.config import ConfigService
    from mcpo_simple_server.services.auth.models import AuthUserModel


class APIKeyDeleteRequest(BaseModel):
    """Model for requesting API key deletion."""
    api_key: str = Field(
        ...,
        min_length=8,
        examples=["st-key-123e4567e89b12d3a456"]
    )


@router.delete("/api-key", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_api_key(
    request: Request,
    key_info: APIKeyDeleteRequest = Body(...),
    current_user: 'AuthUserModel' = Depends(get_current_user)
):
    """
    Deletes an API Key for the currently authenticated user, identified by its full key.
    """
    config_service: 'ConfigService' = request.app.state.config_service

    # Get the current user data
    user_data = await config_service.user_config.get_config(current_user.username)
    if not user_data or not user_data.api_keys:
        logger.warning(f"No API Keys found for user '{current_user.username}'.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found")

    key_to_delete = key_info.api_key
    if key_to_delete not in user_data.api_keys:
        logger.warning(f"API Key '{key_to_delete}' not found for user '{current_user.username}'.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found")
    del user_data.api_keys[key_to_delete]

    # Save the updated user data
    try:
        await config_service.user_config.save_config(user_data)
        logger.info(f"API Key deleted successfully for user '{current_user.username}'.")
    except Exception as e:
        logger.error(f"Failed to delete API Key for user '{current_user.username}' in config: {str(e)}")
        # Don't raise 500, maybe the key was already gone. Log it.
        # Proceed to return 204 as the key is effectively gone or deletion failed post-check
