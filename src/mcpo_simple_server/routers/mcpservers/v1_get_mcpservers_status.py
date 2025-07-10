"""
MCP Server handlers for the user router.
Includes endpoints for managing mcpserver-specific environment variables and private mcpserver instances.
"""
from . import router
from typing import TYPE_CHECKING
from fastapi import Depends, HTTPException, status, Request, Query
from loguru import logger
from mcpo_simple_server.services.auth import get_current_user
from mcpo_simple_server.services.mcpserver.models import McpServerModel, McpServersListResponse
from enum import Enum
if TYPE_CHECKING:
    from mcpo_simple_server.services.config import ConfigService
    from mcpo_simple_server.services.mcpserver import McpServerService
    from mcpo_simple_server.services.auth.models import AuthUserModel

# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------


class ViewType(str, Enum):
    """Server list view type: 'full' or 'simple'."""
    FULL = "full"
    SIMPLE = "simple"


@router.get("/status", response_model=McpServersListResponse)
async def status_mcpservers(
    request: Request,
    view: ViewType = Query(ViewType.FULL, description="Response view: 'simple' omits the tools section."),
    current_user: 'AuthUserModel' = Depends(get_current_user)
):
    """
    Get the status of a mcpserver instance.
    """
    config_service: 'ConfigService' = request.app.state.config_service
    mcpserver_service: 'McpServerService' = request.app.state.mcpserver_service
    response: McpServersListResponse = McpServersListResponse(mcpServers={})

    user_config = await config_service.user_config.get_config(current_user.username)
    if user_config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        # Get the mcpserver configuration from user data
        mcpserver_configs = user_config.mcpServers
        # create list of user mcpserver names
        mcpservers_user_names = list(mcpserver_configs.keys())
        mcpservers_user_ids = [name + "-" + current_user.username for name in mcpservers_user_names]

        for mcpserver_id in mcpservers_user_ids:
            mcpserver = mcpserver_service.get_mcpserver(mcpserver_id)
            if mcpserver is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"McpServer '{mcpserver_id}' not found"
                )
            mcpserver.process = None
            for env in mcpserver.env:
                mcpserver.env[env] = "hidden"

            if view == ViewType.SIMPLE:
                mcpserver.tools = []

            response.mcpServers[mcpserver.name] = McpServerModel(**mcpserver.model_dump())

        return response

    except Exception as e:
        logger.error(f"Error getting mcpserver status for user '{current_user.username}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to get mcpserver status: {str(e)}"
        ) from e
