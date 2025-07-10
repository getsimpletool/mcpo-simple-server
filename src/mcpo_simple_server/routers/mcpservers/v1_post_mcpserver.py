"""
MCP Server handlers for the user router.
Includes endpoints for managing mcpserver-specific environment variables and private mcpserver instances.
"""
import datetime
from . import router
from typing import Dict, Any, TYPE_CHECKING, Optional, List
from fastapi import Depends, HTTPException, status, Body, Request
from loguru import logger
from pydantic import BaseModel
from mcpo_simple_server.services.config.models import McpServerConfigModel
from mcpo_simple_server.services.mcpserver.models import McpServerModel
from mcpo_simple_server.services.auth import get_current_user
if TYPE_CHECKING:
    from mcpo_simple_server.services.mcpserver import McpServerService
    from mcpo_simple_server.services.config import ConfigService
    from mcpo_simple_server.services.auth.models import AuthUserModel

# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------


class McpServerResponse(BaseModel):
    """Information about a server instance."""
    name: str
    status: str
    pid: Optional[int] = None
    uptime_seconds: int = 0
    tools: List[str] = []
    tool_count: int = 0
    type: str = "private"


@router.post("", status_code=status.HTTP_201_CREATED, response_model=McpServerResponse)
async def add_mcpserver(
    request: Request,
    request_body: Dict[str, Any] = Body(
        ...,
        description="mcpServer configuration in the same format as config.json",
        example={
            "mcpServers": {
                "time": {
                    "command": "uvx",
                    "args": [
                        "mcp-server-time",
                        "--local-timezone=Europe/Warsaw"
                    ]
                }
            }
        }
    ),
    current_user: 'AuthUserModel' = Depends(get_current_user)
):
    """
    Add a new mcpserver configuration. Only one server can be added at a time.
    The configuration should match the structure of common known MCP config.json format.

    Returns:
        Dict containing the result of the operation and mcpserver details
    """
    logger.info(f"User '{current_user.username}' attempting to add new mcpserver configuration")
    mcpserver_service: 'McpServerService' = request.app.state.mcpserver_service
    config_service: 'ConfigService' = request.app.state.config_service

    # Get the current user config
    user_config = await config_service.user_config.get_config(current_user.username)
    if not user_config:
        logger.error(f"Failed to retrieve user '{current_user.username}' for adding mcpserver.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add mcpserver configuration") from None

    # Extract the mcpserver configuration
    if "mcpServers" not in request_body:
        logger.error("Invalid mcpserver configuration format: missing 'mcpServers' key")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid mcpserver configuration format: missing 'mcpServers' key")

    # Get the mcpserver name
    mcpserver_name = next(iter(request_body["mcpServers"]))
    mcpserver_id = f"{mcpserver_name}-{current_user.username}"
    mcpserver_config = request_body["mcpServers"][mcpserver_name]

    # Validate if the mcpserver configuration is valid
    try:
        mcpserver_model = McpServerConfigModel(**mcpserver_config)
    except Exception as e:
        logger.error(f"Invalid mcpserver configuration: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid mcpserver configuration") from e

    # Add or update the mcpserver configuration in the user's profile
    # Use attribute access for Pydantic models
    if not hasattr(user_config, "mcpServers") or user_config.mcpServers is None:
        user_config.mcpServers = {}

    try:
        # Start the server using mcpserver_service process_manager
        start_result: 'McpServerModel' = await mcpserver_service.controller.add_mcpserver(
            mcpserver_model=McpServerModel(**mcpserver_model.model_dump(), name=mcpserver_name, username=current_user.username)
        )
        logger.debug(start_result)
    except Exception as e:
        logger.warning(f"McpServer '{mcpserver_name}' not started")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to start mcpserver - {str(e)}") from e

    if start_result.status in ["success", "running"]:
        user_config.mcpServers[mcpserver_name] = mcpserver_model
        await config_service.user_config.save_config(user_config)
        logger.info(f"McpServer '{mcpserver_name}' added and started for user '{current_user.username}'")
    else:
        del mcpserver_service._mcpservers[mcpserver_id]     # pylint: disable=protected-access
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to add mcpserver - status: {start_result.status}")

    if start_result.status == "running":
        # Calculate uptime
        if start_result.start_time is None:
            uptime_seconds = 0
        else:
            uptime_seconds = int((int(datetime.datetime.now().timestamp()) - int(start_result.start_time.timestamp())))
    else:
        uptime_seconds = 0

    return McpServerResponse(
        name=start_result.name,
        status=start_result.status,
        pid=start_result.pid,
        uptime_seconds=uptime_seconds,
        tools=[tool["name"] for tool in start_result.tools],
        tool_count=len(start_result.tools)
    )
