"""
Package/Module: MCP Server - Core MCP server implementation

High Level Concept:
-------------------
This module provides the core MCP server implementation that integrates with the
existing McpServerService. It handles tool registration, server initialization,
and proper lifecycle management.

Architecture:
-------------
- MCP server factory for creating MCP server instances
- Tool registration from existing McpServerService
- Integration with the McpServerService lifecycle

Workflow:
---------
1. Create an MCP server instance during application startup
2. Register tools from the existing McpServerService
3. Handle MCP protocol messages and invoke appropriate tools
4. Properly shut down the server during application shutdown

"""

from loguru import logger
from typing import Dict, Any, List, Optional, AsyncIterator
from contextlib import asynccontextmanager
from mcp.types import ErrorData, Tool as MCPTool, TextContent, ImageContent, EmbeddedResource
from mcp.server.lowlevel.server import Server as MCPServer
from mcpo_simple_server.services.mcp_core_logic.mcp_server_functions import _global_list_tools_handler
from mcpo_simple_server.services.mcp_core_logic.call_tool import mcp_call_tool
# Dictionary to store current request username by server instance ID
_request_usernames: Dict[int, str] = {}


@asynccontextmanager
async def custom_lifespan(server: MCPServer[None]) -> AsyncIterator[None]:
    """Custom lifespan manager that correctly yields None."""
    # You can put startup logic here, e.g., initializing resources.
    # Access server state via server.state if needed (similar to app.state in FastAPI).
    logger.debug(f"Lifespan: Server '{getattr(server, 'name', 'unknown')}' starting up...")
    try:
        yield  # Crucially, this yields None implicitly
    finally:
        # You can put shutdown logic here, e.g., cleaning up resources.
        logger.debug(f"Lifespan: Server '{getattr(server, 'name', 'unknown')}' shutting down...")


def create_mcp_server() -> MCPServer[None]:
    """
    Create an MCP server instance that integrates with the existing McpServerService.

    Returns:
        An MCP server instance
    """
    # Create a new MCP server instance
    mcp_server = MCPServer[None](
        name="MCPoSimpleServer",
        instructions="A simple MCP server for MCPoSimpleServer",
        lifespan=custom_lifespan  # Use the custom lifespan manager
    )

    # Helper function to get username from the server instance ID
    def _get_username() -> Optional[str]:
        """Extract username from the global tracking dictionary if available."""
        try:
            server_id = id(mcp_server)
            return _request_usernames.get(server_id)
        except Exception as e:
            logger.error(f"Error getting username from context: {e}")
            return None

    # ---------------------------------------------------------------------------------------------
    # --- MCP Tool Handlers -----------------------------------------------------------------------
    # ---------------------------------------------------------------------------------------------
    @mcp_server.list_tools()
    async def _list_tools_handler() -> List[MCPTool]:
        username = _get_username()
        return await _global_list_tools_handler(username=username)

    @mcp_server.call_tool()
    async def _call_tool_handler(tool_name: str, arguments: Dict[str, Any] | None) -> list[TextContent | ImageContent | EmbeddedResource]:
        username = _get_username()
        result = await mcp_call_tool(username=username, tool_name=tool_name, arguments=arguments)
        if isinstance(result, ErrorData):
            # Raise a specific JSONRPCError instead of a generic Exception
            # The MCP server framework will catch this and format it properly
            raise SystemError(result.message)
        return result

    # ---------------------------------------------------------------------------------------------
    # ---------------------------------------------------------------------------------------------
    # ---------------------------------------------------------------------------------------------
    return mcp_server
