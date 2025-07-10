"""
Authentication handlers for the user router.
Includes login and password management endpoints.
"""
from . import router
from fastapi import Depends, HTTPException, status, Request
from loguru import logger
from typing import TYPE_CHECKING
from mcpo_simple_server.services.auth import get_current_user
from mcpo_simple_server.services.config.models import GlobalConfigModel, ConfigModel
if TYPE_CHECKING:
    from mcpo_simple_server.services.config import ConfigService
    from mcpo_simple_server.services.auth.models import AuthUserModel


@router.get("/config", response_model=ConfigModel)
async def get_user_config(
    request: Request,
    current_user: 'AuthUserModel' = Depends(get_current_user)
):
    """
    Get the full user configuration, combining both private (user-specific) and public (global) settings.
    """
    try:
        config_service: 'ConfigService' = request.app.state.config_service

        # Get config
        config_data = await config_service.get_config(current_user.username)
        if not config_data:
            logger.error(f"Failed to retrieve user '{current_user.username}' configuration.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user configuration"
            )

        # Hide sensitive fields for all responses
        if config_data.user_config is not None:
            config_data.user_config.hashed_password = "*************"

        # If user in group admins - then return also global config
        if current_user.group == "admins":
            return config_data

        # Remove tools_cache and global_config from response
        config_data.tools_cache = None
        config_data.global_config = GlobalConfigModel()
        return config_data

    except Exception as e:
        logger.error(f"Error retrieving configuration for user '{current_user.username}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve configuration: {str(e)}"
        ) from e
