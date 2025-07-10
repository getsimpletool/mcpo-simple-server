"""
Public MCP Servers Router

This module provides functionality for managing MCP servers.
"""
from typing import List, Optional
from fastapi import Depends, HTTPException, status, Query
from pydantic import BaseModel
from mcpo_simple_server.services.mcpserver import McpServerService
from mcpo_simple_server.routers.public import router
from mcpo_simple_server.services.mcpserver import get_mcpserver_service
from loguru import logger
from enum import Enum
from datetime import datetime


class ViewType(str, Enum):
    """Server list view type: 'full' or 'simple'."""
    FULL = "full"
    SIMPLE = "simple"


class McpServerPublicMetadata(BaseModel):
    name: str
    description: str = ""
    status: str
    tools: Optional[List[dict]] = None
    toolCount: int
    mcpserver_start_times: Optional[str] = None
    uptime: Optional[int] = None
    pid: Optional[int] = None


class McpServersListResponse(BaseModel):
    mcpservers: List[McpServerPublicMetadata]

# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------


@router.get(
    "/mcpservers",
    response_model=McpServersListResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    summary="List all MCP servers",
    description="Returns a list of all configured MCP servers."
)
async def list_mcpservers(
    view: ViewType = Query(ViewType.FULL, description="Response view: 'full' includes all fields; 'simple' omits the tools section."),
    server_service: McpServerService = Depends(get_mcpserver_service)
):
    """
    List all configured public mcpservers and their status.
    This endpoint is publicly accessible without authentication.

    Returns:
        Dict containing server configurations and status
    """
    logger.info("Public request for MCP server list")
    try:
        all_mcpservers = server_service.controller.list_mcpservers()
        public_mcpservers = {
            name: server
            for name, server in all_mcpservers.items()
            if getattr(server, "mcpserver_type", None) == "public"
        }
    except Exception as e:
        logger.error(f"Failed to list servers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list servers: {str(e)}"
        ) from e

    if view == ViewType.SIMPLE:
        result = [
            McpServerPublicMetadata(
                name=server.name,
                description=server.description or "",
                status=server.status,
                toolCount=len(server.tools) if getattr(server, "tools", None) else 0
            )
            for server in public_mcpservers.values()
        ]
    else:
        result = [
            McpServerPublicMetadata(
                name=server.name,
                description=server.description or "",
                status=server.status,
                tools=server.tools,
                toolCount=len(server.tools) if getattr(server, "tools", None) else 0,
                mcpserver_start_times=str(server.start_time) if server.start_time else None,
                uptime=int((datetime.now() - server.start_time).total_seconds()) if server.start_time else None,
                pid=server.pid
            )
            for server in public_mcpservers.values()
        ]

    return {"mcpservers": result}

# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
