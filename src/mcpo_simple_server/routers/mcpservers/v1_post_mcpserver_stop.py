"""
MCP Server handlers for the user router.
Includes endpoints for managing mcpserver-specific environment variables and private mcpserver instances.
"""
from . import router
from typing import TYPE_CHECKING
from fastapi import Depends, HTTPException, status, Request
from loguru import logger
from mcpo_simple_server.services.auth import get_current_user
from mcpo_simple_server.services.mcpserver.models import McpServerModel
if TYPE_CHECKING:
    from mcpo_simple_server.services.config import ConfigService
    from mcpo_simple_server.services.mcpserver import McpServerService
    from mcpo_simple_server.services.auth.models import AuthUserModel

# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------


@router.post("/{mcpserver_name}/stop", response_model=McpServerModel)
async def stop_mcpserver(
    request: Request,
    mcpserver_name: str,
    current_user: 'AuthUserModel' = Depends(get_current_user)
):
    """
    Stop a mcpserver instance.
    """
    config_service: 'ConfigService' = request.app.state.config_service
    mcpserver_service: 'McpServerService' = request.app.state.mcpserver_service

    user_config = await config_service.user_config.get_config(current_user.username)
    if user_config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        # Get the mcpserver configuration from user data
        mcpserver_configs = user_config.mcpServers
        mcpserver_id = mcpserver_name + "-" + current_user.username
        if mcpserver_name not in mcpserver_configs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"McpServer '{mcpserver_name}' not found in your configuration"
            )

        # Stop the server using the lifecycle service
        stop_result = await mcpserver_service.process_manager.stop_mcpserver(mcpserver_id)
        stop_result.process = None
        for env in stop_result.env:
            stop_result.env[env] = "hidden"
        logger.info(f"Stopped mcpserver '{mcpserver_name}' for user '{current_user.username}'")
        return stop_result
    except Exception as e:
        logger.error(f"Error stopping mcpserver '{mcpserver_name}' for user '{current_user.username}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop mcpserver: {str(e)}"
        ) from e
