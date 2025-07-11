"""
MCP Server configuration endpoints.
Handles retrieval of MCP server configurations.
"""
from . import router
from fastapi import Depends, HTTPException, status, Request
from loguru import logger
from typing import TYPE_CHECKING
from mcpo_simple_server.services.auth import get_current_user
from mcpo_simple_server.services.config.models import McpServerConfigModel
if TYPE_CHECKING:
    from mcpo_simple_server.services.config import ConfigService
    from mcpo_simple_server.services.auth.models import AuthUserModel


@router.get("/{mcpserver_name}/config", response_model=McpServerConfigModel)
async def get_mcpserver_config(
    request: Request,
    mcpserver_name: str,
    current_user: 'AuthUserModel' = Depends(get_current_user)
):
    """
    Get configuration for a specific MCP server.

    Args:
        request: The FastAPI request object
        mcpserver_name: Name of the MCP server
        current_user: The currently authenticated user
    """
    config_service: 'ConfigService' = request.app.state.config_service

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
        mcpserver_configs = user_data.mcpServers or {}

        # Check if the mcpserver exists in the user's configuration
        if mcpserver_name not in mcpserver_configs:
            logger.warning(
                f"McpServer '{mcpserver_name}' not found for user '{current_user.username}'"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"McpServer '{mcpserver_name}' not found"
            )

        mcpserver_config = mcpserver_configs[mcpserver_name]
        print(mcpserver_config)
        return McpServerConfigModel(**mcpserver_config.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving configuration for mcpserver '{mcpserver_name}' "
            f"for user '{current_user.username}': {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve mcpserver configuration"
        ) from e
