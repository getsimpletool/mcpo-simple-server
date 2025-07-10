"""
Environment variable handlers for the user router.
Includes endpoints for managing global environment variables.
"""
from . import router
from typing import TYPE_CHECKING
from fastapi import Depends, HTTPException, status, Request
from loguru import logger
from mcpo_simple_server.services.auth import get_current_user
if TYPE_CHECKING:
    from mcpo_simple_server.services.config import ConfigService
    from mcpo_simple_server.services.auth.models import AuthUserModel


@router.delete("/env/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_env_key(
    request: Request,
    key: str,
    current_user: 'AuthUserModel' = Depends(get_current_user)
):
    """
    Delete a specific global environment variable key for the current user.
    """
    config_service: 'ConfigService' = request.app.state.config_service

    # Get the current user data
    user_data = await config_service.user_config.get_config(current_user.username)
    if not user_data:
        logger.error(f"Failed to retrieve user '{current_user.username}' for global environment key deletion.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete global environment variable")

    # Get the user's global environment variables
    user_env = user_data.env

    # Check if the key exists
    if key not in user_env:
        logger.warning(f"Global environment key '{key}' not found for user '{current_user.username}'.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Environment variable '{key}' not found")

    # Delete the key
    del user_env[key]

    # Update the user data
    user_data.env = user_env

    # Save the updated user data
    success = await config_service.user_config.save_config(user_data)
    if not success:
        logger.error(f"Failed to update global environment after deleting key '{key}' for user '{current_user.username}'.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update global environment variables")

    logger.info(f"Global environment key '{key}' deleted successfully for user '{current_user.username}'.")
