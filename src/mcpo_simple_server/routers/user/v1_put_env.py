"""
Environment variable handlers for the user router.
Includes endpoints for managing global environment variables.
"""
from . import router
from typing import TYPE_CHECKING, Dict
from fastapi import Depends, HTTPException, status, Body, Request
from loguru import logger
from pydantic import BaseModel, Field
from mcpo_simple_server.services.auth import get_current_user
if TYPE_CHECKING:
    from mcpo_simple_server.services.config import ConfigService
    from mcpo_simple_server.services.auth.models import AuthUserModel


class UserUpdateEnvRequest(BaseModel):
    """Model for updating user environment variables."""
    env: Dict[str, str] = Field(
        ...,
        description="Dictionary of global environment variables as key-value pairs",
        examples=[{"API_KEY": "your-api-key", "DEBUG": "true", "ADDITIONAL_PROP": "value"}]
    )


@router.put("/env", status_code=status.HTTP_204_NO_CONTENT)
async def update_my_env(
    request: Request,
    env_update: UserUpdateEnvRequest = Body(...),
    current_user: 'AuthUserModel' = Depends(get_current_user)
):
    """
    Update global environment variables for the current user.
    These variables apply to all servers and take precedence over server-specific variables.
    This replaces the entire 'env' dictionary for the user.
    """
    config_service: 'ConfigService' = request.app.state.config_service

    try:
        # Get the current user data
        user_data = await config_service.user_config.get_config(current_user.username)
        if not user_data:
            logger.error(f"Failed to retrieve user '{current_user.username}' for global environment variables update.")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Failed to retrieve global environment variables for update")

        # Update the user's global environment variables
        # The env_update contains the environment variables dictionary
        if "env" not in env_update.model_dump():
            logger.error(f"Failed to update global environment variables for user '{current_user.username}'.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Missing 'env' key in request body")

        user_data.env = env_update.model_dump()["env"]

        # Save the updated user data
        await config_service.user_config.save_config(user_data)
        logger.info(f"Updated global environment variables for user '{current_user.username}'.")
        user_config = await config_service.user_config.get_config(current_user.username)
        if not user_config:
            logger.error(f"Failed to retrieve user '{current_user.username}' for global environment variables update.")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Failed to retrieve global environment variables for update")
        return
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save global environment variables for user '{current_user.username}': {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to update global environment variables") from e
