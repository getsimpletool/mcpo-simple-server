"""
MCP Server management endpoints.
Handles deletion of MCP server instances.
"""
from . import router
from fastapi import Depends, HTTPException, status, Request
from loguru import logger
from typing import TYPE_CHECKING
from mcpo_simple_server.services.auth import get_current_user
if TYPE_CHECKING:
    from mcpo_simple_server.services.mcpserver import McpServerService
    from mcpo_simple_server.services.config import ConfigService
    from mcpo_simple_server.services.auth.models import AuthUserModel


@router.delete("/{mcpserver_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mcpserver(
    request: Request,
    mcpserver_name: str,
    current_user: 'AuthUserModel' = Depends(get_current_user)
):
    """
    Delete a mcpserver instance.
    This will stop the mcpserver if it's running and remove its configuration.
    """
    mcpserver_service: 'McpServerService' = request.app.state.mcpserver_service
    config_service: 'ConfigService' = request.app.state.config_service
    user_config = await config_service.user_config.get_config(current_user.username)

    if not user_config or not user_config.mcpServers:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User mcpServers configuration not found")

    # Delete mcpserver
    action = await mcpserver_service.controller.delete_mcpserver(mcpserver_name, current_user.username)
    if action["status"] != "success":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=action["message"])

    # Remove servere cache
    mcpserver_id = f"{mcpserver_name}-{current_user.username}"
    await config_service.tools_cache.delete_tool_cache(mcpserver_id)

    # Remove from the current user object if it exists there
    user_config.mcpServers.pop(mcpserver_name, None)
    await config_service.user_config.save_config(user_config)

    logger.info(f"Deleted mcpserver '{mcpserver_name}' for user '{current_user.username}'")
