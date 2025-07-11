"""
Package/Module: McpServer Tools Handler - Manages MCP server tools

High Level Concept:
-------------------
This module provides functionality for managing MCP server tools,
including tool registration, validation, and invocation.
It focuses on the interaction between clients and MCP server tools.

Architecture:
-------------
- Tool discovery and registration
- Tool invocation and response handling
- Tool blacklisting and validation
- Caching of tool metadata

Workflow:
---------
1. Register tools from server
2. Validate tool access based on blacklists
3. Handle tool invocation requests
4. Process and return tool responses

Notes:
------
This module replaces functionality previously in the "tools" service
but with improved structure and naming.
"""
import json
import asyncio
from datetime import datetime
from pydantic import BaseModel
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from loguru import logger
from fastapi import HTTPException
from mcpo_simple_server.services.mcpserver.models.mcpotool import MCPoTool
from mcpo_simple_server.services.config import get_config_service
if TYPE_CHECKING:
    from mcpo_simple_server.services.mcpserver import McpServerService
_INTERNAL_ERROR_CODE = -32603


class McpServerToolsService:
    """
    Manages MCP server tools including registration, validation, and invocation.

    This component handles all aspects of tool management for MCP servers,
    providing a clean interface for tool discovery and usage.
    """

    def __init__(self, parent: "McpServerService"):
        """
        Initialize the McpServer Tools Handler.

        Args:
            parent: Reference to the parent McpServerService
        """
        self.parent = parent
        self._mcpservers = parent._mcpservers
        self.config_service = get_config_service()
        self.global_blacklist_tools = parent.global_blacklist_tools
        self.env_blacklist_tools = parent.env_blacklist_tools

        # Initialize request tracking structures
        self.pending_requests = {}
        self.request_counters = {}
        self.write_locks = {}

        # Register with process manager to handle JSON-RPC responses
        if hasattr(self.parent.process_manager, 'register_json_message_handler'):
            self.parent.process_manager.register_json_message_handler(self._process_json_response)

    async def invoke_tool(self, mcpserver_id: str, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke a tool on a specific MCP server.

        Args:
            mcpserver_id: The identifier of the server
            tool_name: The name of the tool to invoke
            parameters: The parameters to pass to the tool

        Returns:
            The response from the tool invocation
        """

        if mcpserver_id not in self._mcpservers:
            raise HTTPException(status_code=404, detail=f"McpServer '{mcpserver_id}' not found")

        mcpserver = self._mcpservers[mcpserver_id]

        # Check if server is running
        # If not - then run it
        if mcpserver.status != "running" or not mcpserver.process:
            logger.info(f"McpServer '{mcpserver_id}' is not running (status: {mcpserver.status})")
            await self.parent.start_mcpserver(mcpserver_id)

        # Invoke the tool
        try:
            # Implementation depends on the specific MCP server communication protocol
            # This is a placeholder for the actual implementation
            response = await self._send_tool_request(mcpserver_id, tool_name, parameters)
            self._mcpservers[mcpserver_id].last_activity = datetime.now()
            return response
        except Exception as e:
            logger.error(f"Failed to invoke tool {tool_name} on mcpserver {mcpserver_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to invoke tool: {str(e)}") from e

    async def discover_tools(self, mcpserver_id: str) -> List[Dict[str, Any]]:
        """
        Get tools metadata from an MCP mcpserver using the tools/list request.

        Args:
            mcpserver_id: The identifier of the mcpserver to fetch metadata for

        Returns:
            List of tools metadata if successful
        """
        logger.info(f"Fetching metadata for mcpserver: {mcpserver_id}")

        if not self._mcpservers.get(mcpserver_id):
            logger.error(f"mcpserver.process_manager.get_mcpserver_tools_metadata: McpServer-ID '{mcpserver_id}' not found")
            del self._mcpservers[mcpserver_id]
            raise HTTPException(status_code=404, detail=f"McpServer '{mcpserver_id}' not found")

        process_info = self._mcpservers[mcpserver_id].pid
        process = self._mcpservers[mcpserver_id].process
        logger.info(f"mcpserver.process_manager.get_mcpserver_tools_metadata: McpServer {mcpserver_id} is running with PID {process_info}")

        # Check if process is still running
        if process is None or process.returncode is not None:
            exit_code_msg = f" (exit code: {process.returncode})" if process and process.returncode is not None else ""
            logger.warning(f"mcpserver.process_manager.get_mcpserver_tools_metadata: McpServer {mcpserver_id} is not running{exit_code_msg}")
            del self._mcpservers[mcpserver_id]
            raise HTTPException(status_code=400, detail=f"McpServer '{mcpserver_id}' is not running")

        # Prepare tools/list request according to MCP protocol
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }

        # Send request to stdin
        logger.debug(f"Sending tools/list request to {mcpserver_id}")
        logger.debug("\n" + json.dumps(request, indent=2))

        request_str = json.dumps(request) + "\n"
        process.stdin.write(request_str.encode())
        await process.stdin.drain()

        # Read response from stdout
        response_line = await process.stdout.readline()

        if not response_line:
            logger.warning(f"Empty response from mcpserver-id {mcpserver_id}")
            del self._mcpservers[mcpserver_id]
            raise HTTPException(status_code=400, detail="Empty response from mcpserver")

        # Parse JSON response
        try:
            response = json.loads(response_line)

            # Check if response is valid
            if "jsonrpc" not in response or "result" not in response:
                logger.warning(f"Invalid JSON-RPC response from mcpserver-id {mcpserver_id}")
                del self._mcpservers[mcpserver_id]
                raise HTTPException(status_code=400, detail="Invalid JSON-RPC response")

            logger.debug(f"Received response from mcpserver-id {mcpserver_id}")
            logger.debug("\n" + json.dumps(response, indent=2))

            # Extract tools from response
            tools_data = response.get("result", {}).get("tools", [])
            next_cursor = response.get("result", {}).get("nextCursor")

            # Handle pagination if needed
            while next_cursor:
                # Prepare next request with cursor
                cursor_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {"cursor": next_cursor}
                }

                # Send request
                logger.debug(f"Sending paginated tools/list request to {mcpserver_id}")
                logger.debug("\n" + json.dumps(cursor_request, indent=2))

                cursor_request_str = json.dumps(cursor_request) + "\n"
                process.stdin.write(cursor_request_str.encode())
                await process.stdin.drain()

                # Read response
                cursor_response_line = await process.stdout.readline()

                if not cursor_response_line:
                    logger.warning(f"Empty paginated response from mcpserver-id {mcpserver_id}")
                    break

                # Parse response
                cursor_response = json.loads(cursor_response_line)
                logger.debug(f"Received paginated response from mcpserver-id {mcpserver_id}")
                logger.debug("\n" + json.dumps(cursor_response, indent=2))

                # Add tools to the list
                cursor_tools = cursor_response.get("result", {}).get("tools", [])
                tools_data.extend(cursor_tools)

                # Update cursor
                next_cursor = cursor_response.get("result", {}).get("nextCursor")

            # Get full list of tools without filtering
            logger.debug(f"Discovered {len(tools_data)} total tools for mcpserver-id {mcpserver_id}")

            # Update mcpserver metadata with all tools
            self._mcpservers[mcpserver_id].tools = tools_data
            self._mcpservers[mcpserver_id].status = "running"

            # Generate mcpserver description that lists the tools it contains
            if not self._mcpservers[mcpserver_id].description:
                tool_names = [str(tool.get("name", "")) for tool in tools_data]
                tools_list = ", ".join(tool_names)
                self._mcpservers[mcpserver_id].description = f"McpServer-id '{mcpserver_id}' containing {len(tools_data)} tools: {tools_list}"

            # Return the full, unfiltered list of tools
            return tools_data
        except Exception as e:
            logger.error(f"Error fetching tools for mcpserver-id '{mcpserver_id}': {str(e)}")
            del self._mcpservers[mcpserver_id]
            raise HTTPException(status_code=500, detail=f"Error fetching tools for mcpserver-id '{mcpserver_id}': {str(e)}") from e

    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific tool across all controller servers.

        Args:
            tool_name: The name of the tool to find

        Returns:
            Tool with server information or None if not found
        """
        for mcpserver_id, mcpserver_info in self._mcpservers.items():
            # Get tools based on server_info structure
            tools = []
            if hasattr(mcpserver_info, "tools") and mcpserver_info.tools:
                tools = mcpserver_info.tools
            elif isinstance(mcpserver_info, dict) and "tools" in mcpserver_info:
                tools = mcpserver_info.tools

            # Find the requested tool
            for tool in tools:
                if isinstance(tool, dict) and tool.get("name") == tool_name:
                    # Add server information to the tool metadata
                    tool_copy = tool.copy()
                    tool_copy["mcpserver"] = mcpserver_id
                    return tool_copy

        return None

    async def _send_tool_request(
        self,
        mcpserver_id: str,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send a tool request to a specific MCP server.

        Args:
            mcpserver_id: The identifier of the server
            tool_name: The name of the tool to invoke
            parameters: The parameters to pass to the tool

        Returns:
            The response from the tool invocation
        """
        # Get server information
        mcpserver = self._mcpservers[mcpserver_id]
        process = mcpserver.process

        if not process:
            logger.error(f"Cannot send tool request: no process for server '{mcpserver_id}'")
            return {"status": "error", "message": f"Server process not available for '{mcpserver_id}'"}

        # Initialize tracking for this server if needed
        if mcpserver_id not in self.pending_requests:
            self.pending_requests[mcpserver_id] = {}
            self.request_counters[mcpserver_id] = 0
            self.write_locks[mcpserver_id] = asyncio.Lock()

        # Generate unique JSON-RPC request ID
        if mcpserver_id not in self.request_counters:
            self.request_counters[mcpserver_id] = 0
        self.request_counters[mcpserver_id] += 1
        req_id = self.request_counters[mcpserver_id]

        # Prepare future to receive response
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        self.pending_requests[mcpserver_id][req_id] = future

        # Build and send JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": parameters}
        }
        logger.debug(f"Sending request {req_id} to server '{mcpserver_id}'")
        logger.debug("\n" + json.dumps(request, indent=2))

        # Get or create write lock for this server
        if mcpserver_id not in self.write_locks:
            self.write_locks[mcpserver_id] = asyncio.Lock()

        # Send the request with proper locking
        async with self.write_locks[mcpserver_id]:
            request_str = json.dumps(request) + "\n"
            process.stdin.write(request_str.encode())
            await process.stdin.drain()

        # Wait for the matching response with timeout
        try:
            response = await asyncio.wait_for(future, timeout=30.0)
        except asyncio.TimeoutError:
            self.pending_requests[mcpserver_id].pop(req_id, None)
            return {"status": "error", "message": f"Timeout waiting for tool response (req_id: {req_id})"}

        # Return RAW reponse
        return response

    def _process_json_response(self, mcpserver_id: str, message: Dict[str, Any]) -> None:
        """
        Process a JSON-RPC response from a server process.

        Args:
            mcpserver_id: The ID of the server that sent the message
            message: The parsed JSON message
        """
        # Only process messages with an ID (responses to our requests)
        msg_id = message.get("id")
        if msg_id is None or mcpserver_id not in self.pending_requests:
            return

        # Find the matching future for this response ID
        fut = self.pending_requests[mcpserver_id].pop(msg_id, None)
        if fut and not fut.done():
            # Set the result to resolve the future
            fut.set_result(message)
            logger.debug(f"Resolved future for request {msg_id} from server '{mcpserver_id}'")

    async def list_all_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools across all running mcpservers.

        Returns:
            List of tools
        """
        all_tools = []

        for mcpserver_id, mcpserver_data in self._mcpservers.items():
            # Get tools from this mcpserver
            server_tools = mcpserver_data.tools

            # Add mcpserver name to each tool metadata
            for tool in server_tools:
                tool_copy = tool.copy()
                tool_copy["mcpserver"] = mcpserver_id
                all_tools.append(tool_copy)

        return all_tools

    def filter_tools(self, tools: List[Dict[str, Any]], tools_blacklist: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Filter out blacklisted tools based on server-specific and global blacklists.

        Args:
            tools: List of tool metadata dictionaries to filter.
                Example: [{'name': 'tool1', ...}, {'name': 'tool2', ...}]

        Returns:
            List of tools that are not blacklisted.
        """
        if not tools:
            return []

        # Get the combined set of blacklisted tool names
        blacklist = set()

        # 1. Add global blacklist
        if hasattr(self, 'global_blacklist_tools') and self.global_blacklist_tools:
            blacklist.update(self.global_blacklist_tools)

        # 2. Add environment blacklist if available
        if hasattr(self, 'env_blacklist_tools') and self.env_blacklist_tools:
            blacklist.update(self.env_blacklist_tools)

        # 3. Add server-specific blacklist if available (from mcpServere config level)
        if tools_blacklist:
            blacklist.update(tools_blacklist)

        # Filter out blacklisted tools
        filtered_tools = [
            tool for tool in tools
            if tool.get('name') and tool['name'] not in blacklist
        ]

        # Log filtering results if any tools were filtered out
        if len(filtered_tools) != len(tools):
            logger.info(f"🧹 Filtered tools: {len(tools) - len(filtered_tools)} removed, {len(filtered_tools)} remaining")

        return filtered_tools

    async def get_tools(self, username: Optional[str] = None) -> List[MCPoTool]:
        """
        Core logic to fetch and filter MCPoTool objects.

        Args:
            username: Optional username for user-specific tool filtering.

        Returns:
            A list of MCPoTool objects. Can be empty if no tools are found
            or if user configuration is missing/invalid.
        """
        config_service = get_config_service()
        processed_mcp_tools: List[MCPoTool] = []

        try:
            active_mcpservers: Dict[str, Any] = self.parent.controller.list_mcpservers()
            if username:
                user_config = await config_service.user_config.get_config(username)
                if not user_config or not hasattr(user_config, 'mcpServers'):
                    logger.warning(f"User config not found or invalid for {username}. Returning empty tool list.")
                    return []  # Return empty list

                user_defined_mcpservers = user_config.mcpServers
                user_tool_blacklist = getattr(user_config, 'blacklist_tools', [])
                if not isinstance(user_tool_blacklist, list):
                    user_tool_blacklist = []

                for server_base_name, _ in user_defined_mcpservers.items():
                    mcpserver_id_in_controller = f"{server_base_name}-{username}"

                    if mcpserver_id_in_controller in active_mcpservers:
                        server_instance = active_mcpservers[mcpserver_id_in_controller]
                        current_tools_on_instance = server_instance.tools

                        if not current_tools_on_instance and hasattr(config_service, 'tools_cache'):
                            logger.debug(f"Attempting to load tools from cache for {mcpserver_id_in_controller}")
                            cached_tools = await config_service.tools_cache.get_tool_cache(mcpserver_id_in_controller)
                            if cached_tools:
                                current_tools_on_instance = cached_tools
                                logger.debug(f"Loaded {len(cached_tools)} tools from cache for {mcpserver_id_in_controller}")
                            else:
                                logger.debug(f"No tools found in cache for {mcpserver_id_in_controller}")

                        if current_tools_on_instance:
                            for tool_obj in current_tools_on_instance:
                                tool_name = getattr(tool_obj, 'name', None)
                                if tool_name and tool_name in user_tool_blacklist:
                                    logger.debug(f"Tool '{tool_name}' on server '{mcpserver_id_in_controller}' is blacklisted for user '{username}'.")
                                    continue
                                try:
                                    if isinstance(tool_obj, BaseModel):
                                        tool_dict = tool_obj.model_dump()
                                    elif isinstance(tool_obj, dict):
                                        tool_dict = tool_obj
                                    else:
                                        logger.warning(f"Tool object {tool_name or 'UnknownTool'} on {mcpserver_id_in_controller} is not a Pydantic model or dict.")
                                        continue

                                    tool_dict.pop("mcpserver", None)
                                    tool_dict["mcpserver_id"] = mcpserver_id_in_controller
                                    mcp_tool = MCPoTool(**tool_dict)
                                    processed_mcp_tools.append(mcp_tool)
                                except Exception as e_conv:
                                    logger.error(f"Error converting tool {getattr(tool_obj, 'name', 'UnknownTool')} for server {mcpserver_id_in_controller}: {e_conv}")
                    else:
                        logger.debug(f"Server {mcpserver_id_in_controller} (defined in user config) not found in active_mcpservers.")

            else:  # Public/unauthenticated path
                for mcpserver_id, server_instance in active_mcpservers.items():
                    if getattr(server_instance, 'type', None) == 'public' or getattr(server_instance, 'mcpserver_type', None) == 'public':
                        public_tools_on_instance = server_instance.tools
                        if public_tools_on_instance:
                            for tool_obj in public_tools_on_instance:
                                try:
                                    if hasattr(tool_obj, 'model_dump'):
                                        tool_dict = tool_obj.model_dump()
                                    elif isinstance(tool_obj, dict):
                                        tool_dict = tool_obj
                                    else:
                                        logger.warning(f"Public tool object {getattr(tool_obj, 'name', 'UnknownTool')} on {mcpserver_id} is not a Pydantic model or dict.")
                                        continue

                                    tool_dict.pop("mcpserver", None)
                                    tool_dict["mcpserver_id"] = mcpserver_id
                                    mcp_tool = MCPoTool(**tool_dict)
                                    processed_mcp_tools.append(mcp_tool)
                                except Exception as e_conv_public:
                                    logger.error(f"Error converting public tool {getattr(tool_obj, 'name', 'UnknownTool')} for server {mcpserver_id}: {e_conv_public}")
                    else:
                        logger.debug(f"Server {mcpserver_id} is not public, skipping for unauthenticated list_tools.")

        except Exception as e_core:
            logger.error(f"Core tool fetching/filtering failed unexpectedly: {e_core}", exc_info=True)
            # Re-raise to allow the caller (e.g., JSON-RPC layer) to format the error appropriately.
            raise

        return processed_mcp_tools
