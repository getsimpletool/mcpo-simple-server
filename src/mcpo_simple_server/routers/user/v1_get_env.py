"""
Environment variable handlers for the user router.
Includes endpoints for managing global environment variables.
"""
from . import router
from typing import Dict, TYPE_CHECKING
from fastapi import Depends, HTTPException, status, Request
from loguru import logger
from mcpo_simple_server.services.auth import get_current_user
if TYPE_CHECKING:
    from mcpo_simple_server.services.config import ConfigService
    from mcpo_simple_server.services.auth.models import AuthUserModel


@router.get("/env", response_model=Dict[str, str])
async def get_my_env(
    request: Request,
    current_user: 'AuthUserModel' = Depends(get_current_user)
):
    """
    Get global environment variables for the current user.
    These variables apply to all servers and take precedence over server-specific variables.
    """
    config_service: 'ConfigService' = request.app.state.config_service

    try:
        # Get the current user data
        user_data = await config_service.user_config.get_config(current_user.username)
        if not user_data:
            logger.error(f"Failed to retrieve user '{current_user.username}' for global environment variables.")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve global environment variables")

        # Return the global environment variables if they exist, otherwise return an empty dict
        if hasattr(user_data, 'env') and user_data.env is not None:
            return user_data.env
        return {}
    except Exception as e:
        logger.error(f"Error retrieving environment variables for user '{current_user.username}': {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve environment variables") from e
