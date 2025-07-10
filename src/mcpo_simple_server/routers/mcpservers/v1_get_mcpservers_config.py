"""
MCP Server listing endpoints.
Handles retrieval of all MCP server configurations for the current user.
"""
from . import router
from typing import TYPE_CHECKING
from fastapi import Depends, HTTPException, status, Request
from loguru import logger
from mcpo_simple_server.services.auth import get_current_user
from mcpo_simple_server.services.config.models import McpServerConfigModel, McpServersListResponse
if TYPE_CHECKING:
    from mcpo_simple_server.services.mcpserver import McpServerService
    from mcpo_simple_server.services.config import ConfigService
    from mcpo_simple_server.services.auth.models import AuthUserModel


@router.get("/config", response_model=McpServersListResponse)
async def list_mcpservers(
    request: Request,
    current_user: 'AuthUserModel' = Depends(get_current_user)
):
    """
    List all MCP server instances for the current user.

    Args:
        request: The FastAPI request object
        current_user: The currently authenticated user

    Returns:
        McpServersListResponse: Dictionary with key 'mcpservers' containing a list of MCP server configurations and statuses
    """
    mcpserver_service: 'McpServerService' = request.app.state.mcpserver_service
    config_service: 'ConfigService' = request.app.state.config_service
    try:
        # Get the most up-to-date user configuration
        await config_service.user_config.refresh_users_cache(current_user.username)
        user_config = await config_service.user_config.get_config(current_user.username)

        # Get the list of user's private mcpservers from the service
        _mcpservers = mcpserver_service.controller.list_mcpservers()
        # Create the final list of mcpservers based on user's configuration
        final_mcpservers = {}
        if user_config is not None:
            user_mcpservers = user_config.mcpServers
        else:
            user_mcpservers = {}

        # For each mcpserver in the user's configuration
        for mcpserver_name, mcpserver_config in user_mcpservers.items():
            mcpserver_id = mcpserver_name + "-" + current_user.username
            # Try to find this mcpserver in the service list for additional metadata
            mcpserver_from_service = None
            if _mcpservers.get(mcpserver_name):
                mcpserver_from_service = _mcpservers.get(mcpserver_name)

            # If found in service, use that data
            if mcpserver_from_service:
                # Ensure we have tools data
                if not mcpserver_from_service.tools:
                    # Get the cache name - should be in format "name-username"
                    # The mcpserver_name here is the base name without username
                    # The full name with username is what we need for the cache
                    cache_name = f"{mcpserver_name}-{current_user.username}"
                    logger.info(f"Loading tool cache for {cache_name}")

                    # Load the tools from cache
                    cached_tools = await config_service.tools_cache.get_tool_cache(mcpserver_id)
                    if cached_tools is not None:
                        logger.info(f"Loaded {len(cached_tools)} tools from cache for {cache_name}")
                        mcpserver_from_service.tools = cached_tools
                        # mcpserver_from_service.toolsCount = len(cached_tools)

                final_mcpservers[mcpserver_name] = McpServerConfigModel(**mcpserver_from_service.model_dump())
            else:
                final_mcpservers[mcpserver_name] = McpServerConfigModel(**mcpserver_config.model_dump())

        return McpServersListResponse(mcpServers=final_mcpservers)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error listing private mcpservers for user '{current_user.username}': {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list MCP servers"
        ) from e
