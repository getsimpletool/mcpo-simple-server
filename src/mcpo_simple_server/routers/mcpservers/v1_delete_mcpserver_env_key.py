"""
MCP Server environment variable management endpoints.
Handles deletion of specific environment variables for MCP server instances.
"""
from . import router
from fastapi import Depends, HTTPException, status, Request
from loguru import logger
from typing import TYPE_CHECKING
from mcpo_simple_server.services.auth import get_current_user
if TYPE_CHECKING:
    from mcpo_simple_server.services.config import ConfigService
    from mcpo_simple_server.services.auth.models import AuthUserModel


@router.delete("/{mcpserver_name}/env/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mcpserver_env_key(
    request: Request,
    mcpserver_name: str,
    key: str,
    current_user: 'AuthUserModel' = Depends(get_current_user)
):
    """
    Delete a specific environment variable from an MCP server.

    Args:
        request: The FastAPI request object
        mcpserver_name: Name of the MCP server
        key: Environment variable key to delete
        current_user: The currently authenticated user
    """
    config_service: 'ConfigService' = request.app.state.config_service

    if not config_service or not hasattr(config_service, 'user_config'):
        logger.error("Config service not available or misconfigured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuration service unavailable"
        )

    try:
        # Get the current user data
        user_data = await config_service.user_config.get_config(current_user.username)
        if not user_data:
            logger.error(f"User '{current_user.username}' not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get the mcpserver configuration
        mcpserver_configs = user_data.mcpServers
        if not mcpserver_configs:
            logger.warning(
                f"McpServer '{mcpserver_name}' not found for user '{current_user.username}'"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"McpServer '{mcpserver_name}' not found"
            )

        # Get the mcpserver environment variables
        mcpserver_env = mcpserver_configs[mcpserver_name].env or {}

        # Check if the key exists
        if key not in mcpserver_env:
            logger.warning(
                f"Environment variable '{key}' not found in mcpserver "
                f"'{mcpserver_name}' for user '{current_user.username}'"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Environment variable '{key}' not found"
            )

        # Remove the environment variable
        del mcpserver_env[key]

        # Save the updated configuration
        await config_service.user_config.save_config(user_data)
        logger.info(
            f"Deleted environment variable '{key}' from mcpserver "
            f"'{mcpserver_name}' for user '{current_user.username}'"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error deleting environment variable '{key}' from mcpserver "
            f"'{mcpserver_name}' for user '{current_user.username}': {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update mcpserver configuration"
        ) from e
