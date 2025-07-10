"""
Environment variable handlers for the user router.
Includes endpoints for managing global environment variables.
"""
from . import router
from typing import TYPE_CHECKING, Optional
from fastapi import Depends, HTTPException, status, Body, Request
from loguru import logger
from pydantic import BaseModel, Field
from mcpo_simple_server.services.auth import get_current_user
if TYPE_CHECKING:
    from mcpo_simple_server.services.config import ConfigService
    from mcpo_simple_server.services.auth.models import AuthUserModel
    from mcpo_simple_server.services.config.models import UserConfigModel


class UserEnvUpdateRequest(BaseModel):
    """Model for updating a single environment variable."""
    value: str = Field(
        ...,
        description="Value for the environment variable",
        examples=["your-api-key-value"]
    )


@router.put("/env/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def update_my_env_key(
    request: Request,
    key: str,
    env_value: UserEnvUpdateRequest = Body(...),
    current_user: 'AuthUserModel' = Depends(get_current_user)
):
    """
    Update a specific user environment variable key for the current user.
    This only affects the specified key and leaves other user environment variables unchanged.
    """
    config_service: 'ConfigService' = request.app.state.config_service
    user_data: Optional[UserConfigModel] = await config_service.user_config.get_config(current_user.username)
    if not user_data:
        logger.error(f"Failed to retrieve user '{current_user.username}' for user environment key update.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user environment variable")
    user_env = user_data.env
    user_env[key] = env_value.value
    user_data.env = user_env
    success = await config_service.user_config.save_config(user_data)
    if not success:
        logger.error(f"Failed to update user environment key '{key}' for user '{current_user.username}' in config.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user environment variable")
    logger.info(f"User environment key '{key}' updated successfully for user '{current_user.username}'.")
    return
