"""
MCP CallTool Core Logic - Handles MCP call_tool requests.

High Level Concept:
    This module centralizes the logic for finding and executing an MCP tool.
    It identifies the correct server instance and delegates the tool call.
    It's designed to be used by transport-specific handlers (e.g., SSE, HTTP).

Architecture:
    - mcp_call_tool: Async function that:
        - Takes username, tool_name, and arguments.
        - Uses `get_tools` to find the MCPoTool object and its mcpserver_id.
        - Retrieves the McpServerService.
        - Gets the specific server instance using mcpserver_id.
        - Calls the tool on the server instance.
        - Returns the direct result of the tool execution or raises an appropriate exception.
"""

from typing import Optional, Dict, Any, List, Union, Iterable
from loguru import logger

from mcp.types import (
    TextContent,
    ImageContent,
    EmbeddedResource,
    ErrorData,
    ContentBlock
)
from mcp.server.lowlevel.server import StructuredContent, UnstructuredContent, CombinationContent
from mcpo_simple_server.services.mcpserver.models import MCPoTool
from mcpo_simple_server.services import get_mcpserver_service


async def mcp_call_tool(
    username: Optional[str],
    tool_name: str,
    arguments: Optional[Dict[str, Any]]
) -> Union[StructuredContent, UnstructuredContent, CombinationContent, ErrorData]:
    """
    Core logic to find and execute an MCP tool.

    Args:
        username: Optional username of the user making the call.
        tool_name: The name of the tool to call.
        arguments: The arguments to pass to the tool.

    Returns:
        The direct result from the tool execution (list of content items).

    """
    mcpserver_service = get_mcpserver_service()
    mcp_tools: List[MCPoTool] = await mcpserver_service.get_tools(username=username)

    logger.info(f"Core: mcp_call_tool invoked for tool '{tool_name}' by user '{username}' with args: {arguments}")

    # If mcp_tools is empty, the loop below won't find the tool, and ToolNotFoundException will be raised.

    target_tool: Optional[MCPoTool] = None
    for tool_obj in mcp_tools:
        if tool_obj.name == tool_name:
            target_tool = tool_obj
            break
    if not target_tool:
        logger.warning(f"Core: Tool '{tool_name}' not found for user '{username}'. Available tools: {[t.name for t in mcp_tools]}")
        return ErrorData(
            code=-32601,
            message=f"Tool '{tool_name}' not found for user '{username}'."
        )

    mcpserver_id = target_tool.mcpserver_id
    if not mcpserver_id:  # Should not happen if get_tools populates it correctly
        logger.error(f"Core: Tool '{tool_name}' found, but mcpserver_id is missing from MCPoTool object.")
        return ErrorData(
            code=-32601,
            message=f"Internal configuration error: mcpserver_id missing for tool '{tool_name}'."
        )

    mcpserver_service = get_mcpserver_service()
    server_instance = mcpserver_service.controller.get_mcpserver(mcpserver_id)

    if not server_instance:
        logger.error(f"Core: MCP server instance with ID '{mcpserver_id}' for tool '{tool_name}' not found.")
        return ErrorData(
            code=-32601,
            message=f"Server instance '{mcpserver_id}' for tool '{tool_name}' not available."
        )

    call_args = arguments if arguments is not None else {}
    logger.info(f"Core: Executing tool '{tool_name}' on server '{mcpserver_id}' with args: {call_args}")

    try:
        # Invoke the tool and get the JSON-RPC response
        full_json_rpc_response = await mcpserver_service.invoke_tool(mcpserver_id, tool_name, call_args)
        if "error" in full_json_rpc_response and full_json_rpc_response["error"] is not None:
            logger.error(f"Core: JSON-RPC error from tool '{tool_name}'")
            return ErrorData(
                code=full_json_rpc_response["error"]["code"],
                message=full_json_rpc_response["error"]["message"]
            )

        # Check for tool-specific error (isError=true in result)
        result_field = full_json_rpc_response.get("result", {})
        content_list = result_field.get("content", [])
        unstructured_content: UnstructuredContent = list(content_list)
        if result_field.get("isError", False):
            if isinstance(unstructured_content, list) and len(unstructured_content) > 0 and isinstance(unstructured_content[0], TextContent):
                error_message = unstructured_content[0].text
            else:
                error_message = str("Content which was returned was not match UnstructuredContent object: " + str(unstructured_content))
            logger.error(f"Core: Tool '{tool_name}' execution error: {error_message}")
            return ErrorData(
                code=-32000,  # Custom error code for tool execution errors
                message=error_message
            )

        structured_content: StructuredContent | None = result_field.get("structuredContent", None)

        logger.info(f"Core: Tool '{tool_name}' executed successfully. ")
        # If structuredContent and unstructuredContent are both present, return CombinationContent
        if len(unstructured_content) > 0 and structured_content is not None:
            logger.info(f"Result contains unstructured_content {len(unstructured_content)} content items and structured_content {len(structured_content)} content items.")
            # CombinationContent constructor takes a single argument - a dict with both content types
            combination_data: CombinationContent = (unstructured_content, structured_content)
            return combination_data

        if len(unstructured_content) > 0 and structured_content is None:
            logger.info(f"Result contains unstructured_content {len(unstructured_content)} content items.")
            return unstructured_content

        if len(unstructured_content) == 0 and structured_content is not None:
            logger.info(f"Result contains structured_content {len(structured_content.__dict__)} content items.")
            return structured_content

    except Exception as e:  # Catch all exceptions and convert to JSONRPCError
        logger.error(f"Core: Error while executing tool '{tool_name}' on server '{mcpserver_id}': {e}", exc_info=True)
        return ErrorData(
            code=-32603,  # Internal error code
            message=f"Error executing tool '{tool_name}': {str(e)}"
        )
