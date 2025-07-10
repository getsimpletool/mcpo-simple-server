"""
Package/Module: McpServer Controller - Core orchestration for MCP servers

High Level Concept:
-------------------
This module provides the main controller component for orchestrating MCP server operations.
It coordinates between different specialized components to provide a unified interface
for managing MCP servers in the system.

Architecture:
-------------
The controller delegates to specialized components:
- ProcessManager: For process handling operations
- ToolsHandler: For tool management and invocation 
- ConfigService: For persistent configuration

Workflow:
---------
1. Controller receives high-level operation requests
2. Delegates implementation details to specialized components
3. Maintains consistency between runtime state and persistent config
4. Returns unified responses with operation results

Notes:
------
This controller replaces the previous "lifecycle" concept with a more standard
service orchestration approach.
"""
import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING
from loguru import logger
from fastapi import HTTPException
from mcpo_simple_server.services.mcpserver.models import McpServerModel
from mcpo_simple_server.services.config import get_config_service
if TYPE_CHECKING:
    from mcpo_simple_server.services.mcpserver import McpServerService
    from mcpo_simple_server.services.config import ConfigService


class McpServerController:
    """
    Core controller for orchestrating MCP server operations.

    This component coordinates between different specialized components to manage
    MCP servers effectively. It handles the high-level logic while delegating
    specific implementation details to specialized components.
    """

    def __init__(self, parent: "McpServerService"):
        """
        Initialize the McpServer Controller with parent service reference.

        Args:
            parent: Reference to the parent McpServerService
        """
        self.parent = parent
        self._mcpservers = parent._mcpservers
        self.config_service: 'ConfigService' = get_config_service()
        self.global_blacklist_tools = parent.global_blacklist_tools
        self.env_blacklist_tools = parent.env_blacklist_tools

    async def add_mcpserver(self, mcpserver_model: McpServerModel) -> McpServerModel:
        """
        Add and optionally start a new mcpserver in the system.

        Args:
            mcpserver_model: The McpServerModel containing mcpserver configuration
            username: The username for the user-scoped mcpserver (required)
            start: Whether to start the server immediately after adding (default: True)

        Returns:
            McpServerModel with status and metadata of the operation
        """
        mcpserver_name = mcpserver_model.name
        mcpserver_id = f"{mcpserver_name}-{mcpserver_model.username}"

        # Check if mcpserver already exists
        if mcpserver_id in self._mcpservers:
            raise HTTPException(status_code=400, detail=f"McpServer '{mcpserver_name}' already exists for user '{mcpserver_model.username}'")
        else:
            self._mcpservers[mcpserver_id] = McpServerModel(
                name=mcpserver_name,
                command=mcpserver_model.command,
                args=mcpserver_model.args,
                env=mcpserver_model.env,
                description=mcpserver_model.description,
                tools_blacklist=mcpserver_model.tools_blacklist,
                disabled=mcpserver_model.disabled,
                username=mcpserver_model.username,
                type="private",
                status="init",
                pid=None,
                start_time=None,
                last_activity=None,
                process=None
            )

        try:
            # Start server
            self._mcpservers[mcpserver_id] = await self.parent.process_manager.start_mcpserver(mcpserver_id)
            self._mcpservers[mcpserver_id].start_time = datetime.datetime.now()
        except Exception as e:
            logger.error(f"Failed to start mcpserver {mcpserver_name} for user {mcpserver_model.username}: {str(e)}")
            del self._mcpservers[mcpserver_id]
            raise

        logger.debug(f"McpServer '{mcpserver_name}' started successfully (PID: {self._mcpservers[mcpserver_id].pid}) - status: {self._mcpservers[mcpserver_id].status}")

        if self._mcpservers[mcpserver_id].status not in ["success", "running"]:
            logger.error(f"Failed to start mcpserver {mcpserver_name} for user {mcpserver_model.username}: {self._mcpservers[mcpserver_id].status}")
            del self._mcpservers[mcpserver_id]
            raise HTTPException(status_code=500, detail=self._mcpservers[mcpserver_id].status)

        return self._mcpservers[mcpserver_id]

    async def delete_mcpserver(self, mcpserver_name: str, username: str) -> Dict[str, Any]:
        """
        Delete a mcpserver, stopping it first if it's running.

        Args:
            mcpserver_name: The name of the mcpserver to delete
            username: The username of the owner

        Returns:
            Dict with status and result of the operation
        """
        mcpserver_id = f"{mcpserver_name}-{username}"
        logger.info(f"Deleting mcpserver: {mcpserver_name} for user: {username}")

        # Check if mcpserver exists
        if mcpserver_id not in self._mcpservers:
            return {"status": "warning", "message": f"McpServer '{mcpserver_name}' not found"}

        # Stop first if running
        stop_result = await self.parent.process_manager.stop_mcpserver(mcpserver_id)
        if stop_result.status not in ["success", "warning"]:
            logger.warning(f"Failed to stop mcpserver {mcpserver_name} during deletion: {stop_result.status}")

        # Remove mcpserver from controller
        del self._mcpservers[mcpserver_id]

        return {"status": "success", "message": f"McpServer '{mcpserver_name}' deleted successfully"}

    async def restart_mcpserver(self, mcpserver_name: str, username: str) -> Dict[str, Any]:
        """
        Restart a mcpserver, fetching latest configuration.

        Args:
            mcpserver_name: The name of the mcpserver to restart
            username: The username of the owner

        Returns:
            Dict with status and result of the operation
        """
        mcpserver_id = f"{mcpserver_name}-{username}"
        logger.info(f"Restarting mcpserver: {mcpserver_name} for user: {username}")

        # Check if mcpserver exists
        if mcpserver_id not in self._mcpservers:
            return {"status": "error", "message": f"McpServer '{mcpserver_name}' not found"}

        try:
            # Get latest configuration
            config = await self.config_service.get_config(username)
            if not config or not config.user_config:
                return {"status": "error", "message": f"User configuration for '{username}' not found"}

            # Stop the server
            stop_result = await self.parent.process_manager.stop_mcpserver(mcpserver_id)
            if stop_result.status not in ["success", "warning"]:
                logger.warning(f"Failed to stop mcpserver {mcpserver_id} during restart: {stop_result.status}")
                # Continue with restart even if stop failed

            # Start the server with updated configuration
            start_result = await self.parent.process_manager.start_mcpserver(mcpserver_id)

            if start_result.status != "success":
                return {
                    "status": "error",
                    "message": f"Failed to restart mcpserver {mcpserver_id}: {start_result.status}"
                }

            return {
                "status": "success",
                "message": f"McpServer '{mcpserver_name}' restarted successfully",
                "mcpserver_name": mcpserver_name,
                "mcpserver_id": mcpserver_id,
                "tool_count": len(self._mcpservers[mcpserver_id].tools)
            }

        except Exception as e:
            logger.error(f"Failed to restart mcpserver {mcpserver_name}: {str(e)}")
            return {"status": "error", "message": f"Failed to restart mcpserver: {str(e)}"}

    def get_mcpserver(self, mcpserver_id: str) -> Optional[McpServerModel]:
        """
        Get information about a specific mcpserver by its ID.

        Args:
            mcpserver_id: The ID of the mcpserver to retrieve

        Returns:
            McpServerModel or None if not found
        """
        return self._mcpservers.get(mcpserver_id)

    def list_mcpservers(self) -> Dict[str, McpServerModel]:
        """
        List all registered mcpservers in the system.

        Returns:
            Dict of McpServerModel objects
        """
        return self._mcpservers
