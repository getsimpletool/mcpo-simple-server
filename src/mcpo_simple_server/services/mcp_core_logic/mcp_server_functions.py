

from loguru import logger
from typing import List, Optional
from mcp.types import Tool as MCPTool, JSONRPCError, ListToolsResult
from mcpo_simple_server.services.mcp_core_logic import mcp_list_tools


async def _global_list_tools_handler(username: Optional[str] = None) -> List[MCPTool]:
    mcp_tools: List[MCPTool] = []

    logger.debug(f"MCP _list_tools_handler invoked by user: {username}")
    response_data = await mcp_list_tools(username=username)

    if isinstance(response_data, JSONRPCError):
        logger.warning(f"list_tools_response: {response_data.error.message} (Code: {response_data.error.code})")
        return mcp_tools

    if response_data.result:
        try:
            list_tools_result_model = ListToolsResult(**response_data.result)
            mcp_tools = list_tools_result_model.tools
        except Exception as e:
            logger.error(f"Unexpected error processing list_tools result: {e}. Response result: {response_data.result}")
            return mcp_tools
    else:
        logger.error("list_tools response was successful but 'result' field is missing or None.")
        return mcp_tools

    return mcp_tools
