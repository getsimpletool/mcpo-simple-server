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


@router.post("/{mcpserver_name}/start", response_model=McpServerModel)
async def start_mcpserver(
    request: Request,
    mcpserver_name: str,
    current_user: 'AuthUserModel' = Depends(get_current_user)
):
    """
    Start a mcpserver instance.
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

        # Start the server using the lifecycle service
        start_result = await mcpserver_service.process_manager.start_mcpserver(mcpserver_id)
        start_result.process = None
        for env in start_result.env:
            start_result.env[env] = "hidden"
        logger.info(f"Started mcpserver '{mcpserver_name}' for user '{current_user.username}'")
        return start_result
    except Exception as e:
        logger.error(f"Error starting mcpserver '{mcpserver_name}' for user '{current_user.username}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start mcpserver: {str(e)}"
        ) from e
