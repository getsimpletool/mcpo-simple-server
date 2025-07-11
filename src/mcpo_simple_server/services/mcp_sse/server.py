"""
Package/Module: MCP Server - Core MCP SSE server implementation

High Level Concept:
-------------------
This module provides the core MCP server implementation for SSE transport that integrates
with the existing McpServerService. It handles tool registration, server initialization,
and proper lifecycle management for SSE communication.

Architecture:
-------------
- MCP server factory for creating MCP server instances tailored for SSE.
- Tool registration from existing McpServerService.
- Integration with the McpServerService lifecycle.

Workflow:
---------
1. Create an MCP server instance (for SSE) during application startup.
2. Register tools from the existing McpServerService.
3. Handle MCP protocol messages over SSE and invoke appropriate tools.
4. Properly shut down the server during application shutdown.

Usage Example:
--------------
>>> from mcpo_simple_server.services.mcp_sse.server import create_mcp_server
>>> from mcpo_simple_server.services.mcpserver import McpServerService
>>> # Create an MCP server instance for SSE
>>> mcpserver_service = McpServerService()
>>> mcp_sse_server = create_mcp_server(mcpserver_service)
"""

from loguru import logger
from typing import Dict, Any, List, AsyncIterator, Union
from contextlib import asynccontextmanager
# MCP specific imports
from mcp.server.lowlevel.server import Server as MCPServer, StructuredContent, UnstructuredContent, CombinationContent
from mcp.types import ErrorData, Tool as MCPTool
from mcpo_simple_server.services.auth.api_key import get_username_from_api_key
from mcpo_simple_server.services.mcp_core_logic.mcp_server_functions import _global_list_tools_handler
from mcpo_simple_server.services.mcp_core_logic.call_tool import mcp_call_tool


@asynccontextmanager
async def custom_lifespan(server: MCPServer[None]) -> AsyncIterator[None]:
    """Custom lifespan manager that correctly yields None."""
    # You can put startup logic here, e.g., initializing resources.
    # Access server state via server.state if needed (similar to app.state in FastAPI).
    # Use getattr to safely access the dynamically attached attribute
    scope = getattr(server, '_current_asgi_scope', None)
    client_info = "unknown"
    if scope and "client" in scope:
        client_ip, client_port = scope["client"]
        client_info = f"{client_ip}:{client_port}"

    logger.debug(f"Lifespan (SSE): Server '{getattr(server, 'name', 'unknown')}' starting up - Client: {client_info}")
    try:
        yield  # Crucially, this yields None implicitly
    finally:
        # You can put shutdown logic here, e.g., cleaning up resources.
        logger.debug(f"Lifespan (SSE): Server '{getattr(server, 'name', 'unknown')}' shutting down - Client: {client_info}")


def create_mcp_server() -> MCPServer[None]:
    """
    Create an MCP server instance for SSE that integrates with the existing McpServerService.


    Returns:
        An MCP server instance configured for SSE
    """
    # Create a new MCP server instance
    mcp_server = MCPServer[None](
        name="MCPoSimpleServer-SSE",
        instructions="A simple MCP server for MCPoSimpleServer (SSE Transport)",
        lifespan=custom_lifespan
    )

    def _get_username() -> str | None:
        """Helper to extract username from API key using scope attached to mcp_server instance."""
        try:
            scope: Dict | None = getattr(mcp_server, '_current_asgi_scope', None)
            if not (scope and isinstance(scope, dict)):
                logger.debug("SSE: _get_username: ASGI scope not found on mcp_server instance or not a dict.")
                return None

            headers = scope.get("headers", [])
            auth_header_bytes = next(
                (value for key, value in headers if key == b"authorization"),
                None
            )

            if not auth_header_bytes:
                logger.debug("SSE: _get_username: Authorization header not found in attached scope.")
                return None

            auth_header = auth_header_bytes.decode("utf-8")
            if not auth_header.lower().startswith("bearer "):
                logger.debug("SSE: _get_username: Authorization header is not a Bearer token.")
                return None

            api_key = auth_header[7:]  # Remove "Bearer " prefix
            username = get_username_from_api_key(api_key)
            if not username:
                logger.debug("SSE: _get_username: API key is not valid or no username associated.")
                return None

            return username
        except Exception as e:
            logger.error(f"SSE: _get_username: Unexpected error: {e}")
            return None

    # ---------------------------------------------------------------------------------------------
    # --- MCP Tool Handlers -----------------------------------------------------------------------
    # ---------------------------------------------------------------------------------------------
    @mcp_server.list_tools()
    async def _list_tools_handler() -> List[MCPTool]:
        username = _get_username()
        return await _global_list_tools_handler(username=username)

    @mcp_server.call_tool()
    async def _call_tool_handler(tool_name: str, arguments: Dict[str, Any] | None) -> StructuredContent | UnstructuredContent | CombinationContent:
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
