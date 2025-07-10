"""
MCP Server handlers for the user router.
Includes endpoints for managing mcpserver-specific environment variables and private mcpserver instances.
"""
from . import router
from pydantic import BaseModel, Field
from typing import TYPE_CHECKING
from fastapi import Depends, HTTPException, status, Body, Request
from loguru import logger
from mcpo_simple_server.services.auth import get_current_user
if TYPE_CHECKING:
    from mcpo_simple_server.services.config import ConfigService
    from mcpo_simple_server.services.auth.models import AuthUserModel


class UserEnvUpdateRequest(BaseModel):
    """Model for updating a single environment variable."""
    value: str = Field(
        ...,
        description="Value for the environment variable",
        examples=["your-api-key-value"]
    )


@router.put("/{mcpserver_name}/env/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def update_mcpserver_env_key(
    request: Request,
    mcpserver_name: str,
    key: str,
    env_value: UserEnvUpdateRequest = Body(...),
    current_user: 'AuthUserModel' = Depends(get_current_user)
):
    """
    Update a specific environment variable key for a specific mcpserver for the current user.
    """
    config_service: 'ConfigService' = request.app.state.config_service
    user_config = await config_service.user_config.get_config(current_user.username)
    if not user_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user_config.mcpServers or mcpserver_name not in user_config.mcpServers:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="McpServer not found")

    # Update the key
    mcpserver = user_config.mcpServers[mcpserver_name]
    if not mcpserver.env:
        mcpserver.env = {}
    mcpserver.env[key] = env_value.value
    user_config.mcpServers[mcpserver_name] = mcpserver

    # Save the updated user data
    success = await config_service.user_config.save_config(user_config)
    if not success:
        logger.error(f"Failed to update mcpserver environment key '{key}' for mcpserver '{mcpserver_name}' for user '{current_user.username}' in config.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update mcpserver environment variable")

    logger.info(f"Updated environment variable key '{key}' for mcpserver '{mcpserver_name}' for user '{current_user.username}'")

    return
