"""
MCP Server handlers for the user router.
Includes endpoints for managing mcpserver-specific environment variables and private mcpserver instances.
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


class ServerEnvUpdateRequest(BaseModel):
    """Model for updating environment variables for a specific server."""
    env: Dict[str, str] = Field(
        ...,
        description="Dictionary of environment variables for a specific server",
        examples=[{"API_KEY": "your-api-key", "DEBUG": "true", "ADDITIONAL_PROP": "value"}]
    )


@router.put("/{mcpserver_name}/env", status_code=status.HTTP_204_NO_CONTENT)
async def update_mcpserver_env(
    request: Request,
    mcpserver_name: str,
    env_update: ServerEnvUpdateRequest = Body(...),
    current_user: 'AuthUserModel' = Depends(get_current_user)
):
    """
    Update environment variables for a specific mcpserver for the current user.
    """
    config_service: 'ConfigService' = request.app.state.config_service

    # Get the current user data
    user_data = await config_service.user_config.get_config(current_user.username)
    if not user_data:
        logger.error(f"Failed to retrieve user '{current_user.username}' for mcpserver environment update.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update mcpserver environment variables")

    # Check if the mcpserver exists for the user
    if mcpserver_name not in user_data.mcpServers:
        logger.error(f"McpServer '{mcpserver_name}' not found for user '{current_user.username}' for mcpserver environment update.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="McpServer not found")

    # Update the mcpserver environment variables
    user_data.mcpServers[mcpserver_name].env = env_update.env
    success = await config_service.user_config.save_config(user_data)
    if not success:
        logger.error(f"Failed to update mcpserver environment variables for mcpserver '{mcpserver_name}' for user '{current_user.username}' in config.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update mcpserver environment variables")

    logger.info(f"Updated environment variables for mcpserver '{mcpserver_name}' for user '{current_user.username}'")
    return
