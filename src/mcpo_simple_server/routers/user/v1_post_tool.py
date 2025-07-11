"""
Tool execution handler for the user router.
Provides an endpoint for authenticated users to invoke tools from MCP servers.
"""
from . import router
from typing import Dict, Any, TYPE_CHECKING, List
from fastapi import Depends, HTTPException, status, Request, Body
from loguru import logger
from mcpo_simple_server.services.auth import get_authenticated_user
from mcpo_simple_server.utils.tools.process_tool_response import process_tool_response
if TYPE_CHECKING:
    from mcpo_simple_server.services.auth.models import AuthUserModel
    from mcpo_simple_server.services.mcpserver import McpServerService


@router.post("/tool/{mcpserver}/{tool_name}", response_model=List[Any])
async def execute_tool(
        request: Request,
        mcpserver: str,
        tool_name: str,
        request_body: Dict[str, Any] = Body(...),
        current_user: 'AuthUserModel' = Depends(get_authenticated_user)
):
    """
    Execute a tool from an MCP server with the given parameters.

    Args:
        request: The FastAPI request object
        mcpserver: Name of the MCP server to use
        tool_name: Name of the tool to execute
        tool_request: Request body containing tool arguments
        current_user: Currently authenticated user

    Returns:
        Tool execution result

    Raises:
        HTTPException: If tool execution fails or tool is not found
    """
    # Get the mcpserver service
    mcpserver_service: McpServerService = request.app.state.mcpserver_service

    # Construct the mcpserver_id (using the convention mcpserver_name-username)
    mcpserver_id = mcpserver + "-" + current_user.username

    # Log the tool execution request
    logger.info(f"Tool execution request: user={current_user.username}, mcpserver={mcpserver}, tool={tool_name}")
    logger.info(f"Tool arguments: {request_body}")
    try:
        # Execute the tool with the provided parameters
        response = await mcpserver_service.invoke_tool(
            mcpserver_id=mcpserver_id,
            tool_name=tool_name,
            parameters=request_body or {}
        )
        # print(result)
        # {'jsonrpc': '2.0', 'id': 1, 'result': {'content': [{'type': 'text', 'text': '5'}], 'structuredContent': {'result': '5'}, 'isError': False}}
        result = response.get("result", {})

        # Check for error
        if "isError" in response and response["isError"]:
            raise HTTPException(status_code=404, detail=result)

        # Log successful execution
        logger.info(f"Tool {tool_name} executed successfully for user {current_user.username}")

        # Return 'structuredContent' if present and 'content' is not
        if result is None or result == {}:
            if "structuredContent" in result and result["structuredContent"] is not None:
                return result["structuredContent"]

        # Return 'content' if present
        if "content" in result and result["content"] is not None:
            processed_result = process_tool_response(result)
            return processed_result

        raise HTTPException(status_code=404, detail="No result returned from tool execution")

    except Exception as e:
        # Log the error
        logger.error(f"Failed to execute tool {tool_name} for user {current_user.username}: {str(e)}")

        # Return an appropriate error response
        if isinstance(e, HTTPException):
            raise e
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Tool execution failed: {str(e)}") from e
