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


@router.delete("/env", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_env(
    request: Request,
    current_user: 'AuthUserModel' = Depends(get_current_user)
):
    """
    Delete all global environment variables for the current user.
    """
    config_service: 'ConfigService' = request.app.state.config_service

    # Get the current user data
    user_data = await config_service.user_config.get_config(current_user.username)
    if not user_data:
        logger.error(f"Failed to retrieve user '{current_user.username}' for global environment deletion.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete global environment variables")

    # Delete the user's global environment variables
    user_data.env = {}

    # Save the updated user data
    success = await config_service.user_config.save_config(user_data)
    if not success:
        logger.error(f"Failed to delete global environment variables for user '{current_user.username}' in config.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete global environment variables")

    logger.info(f"Global environment variables deleted successfully for user '{current_user.username}'.")
