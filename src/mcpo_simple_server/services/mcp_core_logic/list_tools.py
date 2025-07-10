"""
MCP ListTools Response Generator - Formats list_tools responses.

High Level Concept:
    This module is responsible for generating MCP-compliant JSON-RPC
    responses for the 'list_tools' method. It utilizes core tool fetching
    and filtering logic from the `utils.tools.get_tools` module.

Architecture:
    - generate_list_tools_response: Async function that orchestrates fetching
      tools via `_fetch_and_filter_mcp_tools_core` and then constructs
      either a `JSONRPCResponse` with the `ListToolsResult` or a
      `JSONRPCError` if issues arise.

Workflow:
    1. Call `_fetch_and_filter_mcp_tools_core(username)` from `get_tools.py`.
    2. If tools are returned and no specific error:
        - Create `ListToolsResult`.
        - Create and return `JSONRPCResponse`.
    3. If specific error info is returned (e.g., user config issue):
        - Create `ErrorData` from the error info.
        - Create and return `JSONRPCError`.
    4. If an unexpected exception occurs during the process:
        - Log the exception.
        - Create and return a generic `JSONRPCError`.

Notes:
    Centralizes MCP response formatting to ensure protocol compliance.
"""

from typing import Optional, Union, List
from loguru import logger

from mcpo_simple_server.services import get_mcpserver_service
from mcpo_simple_server.services.mcpserver.models import MCPoTool

from mcp.types import (
    ListToolsResult,
    JSONRPCResponse,
    JSONRPCError,
    ErrorData,
    Tool as MCPTool
)


# TODO: Find the canonical INTERNAL_ERROR constant from the mcp library.
# Using standard JSON-RPC internal error code -32603 for now.
_INTERNAL_ERROR_CODE = -32603


async def mcp_list_tools(
    username: Optional[str] = None,
    request_id: Union[str, int] = "1"  # MCP RequestId can be str or int
) -> Union[JSONRPCResponse, JSONRPCError]:
    """
    Generate a MCP-compliant JSON-RPC response for the list_tools request.

    Utilizes core tool fetching logic and formats the output.
    """
    mcpserver_service = get_mcpserver_service()
    try:
        # get_tools now returns List[MCPoTool] and handles user config errors internally
        # by returning an empty list.
        mcpo_tools_list: List[MCPoTool] = await mcpserver_service.get_tools(username=username)

        # Transform MCPoTools to MCPTools
        mcp_tools_for_response: List[MCPTool] = []
        for mcpo_tool_item in mcpo_tools_list:
            mcp_tools_for_response.append(MCPTool(**mcpo_tool_item.model_dump()))

        # If no specific error, proceed to create successful response
        list_tools_result = ListToolsResult(tools=mcp_tools_for_response)
        return JSONRPCResponse(
            id=request_id,
            result=list_tools_result.model_dump(),
            jsonrpc="2.0"
        )

    except Exception as e:
        # Catch-all for unexpected errors from get_tools (if re-raised)
        # or during response assembly.
        logger.error(
            f"Failed to generate list_tools response for user '{username}' "
            f"(request_id: {request_id}): {e}",
            exc_info=True
        )
        return JSONRPCError(
            jsonrpc="2.0",
            id=request_id,
            error=ErrorData(
                code=_INTERNAL_ERROR_CODE,  # Defined in the file
                message="An internal error occurred while processing the list_tools request."
            )
        )
