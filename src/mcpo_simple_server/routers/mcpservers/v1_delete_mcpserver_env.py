"""
MCP Server environment variable management endpoints.
Handles deletion of environment variables for specific mcpserver instances.
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


@router.delete("/{mcpserver_name}/env", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mcpserver_env(
    request: Request,
    mcpserver_name: str,
    current_user: 'AuthUserModel' = Depends(get_current_user)
):
    """
    Delete all environment variables for a specific mcpserver for the current user.

    Args:
        request: The FastAPI request object
        mcpserver_name: Name of the mcpserver instance
        current_user: The currently authenticated user
        mcpserver_service: Injected mcpserver service instance
    """
    mcpserver_service: 'McpServerService' = request.app.state.mcpserver_service
    config_service: 'ConfigService' = request.app.state.config_service
    try:
        # Get the user's config
        user_config = await config_service.user_config.get_config(current_user.username)
        if not user_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{current_user.username}' not found"
            )

        # Get the mcpserver config
        user_mcpservers = user_config.mcpServers or {}
        if mcpserver_name not in user_mcpservers:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"McpServer '{mcpserver_name}' not found"
            )

        # Clear the environment variables
        user_config.mcpServers[mcpserver_name].env = {}

        # Save the updated config
        await config_service.user_config.save_config(user_config)
        await config_service.user_config.refresh_users_cache(current_user.username)
        # We need to restart the mcpserver to apply the changes
        await mcpserver_service.restart_mcpserver(mcpserver_name, current_user.username)
        logger.info(f"Successfully deleted environment variables for mcpserver '{mcpserver_name}' for user '{current_user.username}'")
        return
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting environment variables for mcpserver '{mcpserver_name}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting mcpserver environment variables"
        ) from e
