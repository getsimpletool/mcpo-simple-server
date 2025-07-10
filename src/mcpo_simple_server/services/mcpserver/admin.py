"""
Package/Module: McpServer Admin - Administrative operations for MCP mcpservers

High Level Concept:
-------------------
This module provides administrative functionality for MCP mcpservers,
including bulk operations, system-wide configurations, and management
capabilities reserved for administrators.

Architecture:
-------------
- Bulk mcpserver operations
- System-wide configuration management
- Administrative monitoring and control

Workflow:
---------
1. Authenticate administrative requests
2. Process administrative operations
3. Apply changes to multiple mcpservers if needed
4. Return consolidated operation results

Notes:
------
This module contains operations that should only be accessible to system administrators.
"""
import datetime
from typing import Dict, List, Any, TYPE_CHECKING
from loguru import logger
from mcpo_simple_server.services.config import get_config_service
from mcpo_simple_server.services.mcpserver.models import McpServerModel
if TYPE_CHECKING:
    from mcpo_simple_server.services.mcpserver import McpServerService
    from mcpo_simple_server.services.config.models import McpServerConfigModel


class McpServerAdminManager:
    """
    Provides administrative operations for MCP servers.

    This component handles operations that require administrative privileges,
    such as bulk server management and system-wide configurations.
    """

    def __init__(self, parent: "McpServerService"):
        """
        Initialize the McpServer Admin Manager.

        Args:
            parent: Reference to the parent McpServerService
        """
        self.parent = parent
        self._mcpservers = parent._mcpservers
        self.config_service = get_config_service()
        self.global_blacklist_tools = parent.global_blacklist_tools
        self.env_blacklist_tools = parent.env_blacklist_tools

    async def load_all_mcpservers(self) -> Dict[str, Any]:
        """
        Load all MCP mcpservers from configuration.

        This administrative operation loads all mcpserver configurations
        from the persistent storage and prepares them for use.

        Returns:
            Dict with status and count of loaded mcpservers
        """
        logger.info("Loading all MCP mcpservers from configuration")
        try:
            # Get all user configurations
            config = await self.config_service.user_config.get_all_users_configs()
            loaded_count = 0

            for username, user_config in config.items():
                if user_config.disabled:
                    continue

                mcpservers: Dict[str, McpServerConfigModel] = getattr(user_config, "mcpServers", {})
                for server_name, server_config in mcpservers.items():
                    # Build mcpserver identifier
                    mcpserver_id = f"{server_name}-{username}"

                    self._mcpservers[mcpserver_id] = McpServerModel(
                        name=server_name,
                        command=server_config.command,
                        args=server_config.args or [],
                        env=server_config.env or {},
                        description=server_config.description or "",
                        username=username,
                        type=server_config.mcpserver_type or "private",
                        status="configured",
                        tools_blacklist=getattr(server_config, "tools_blacklist", []),
                        disabled=getattr(server_config, "disabled", False),
                        pid=None,
                        start_time=None,
                        last_activity=None,
                        process=None
                    )
                    # Load cached tools if available
                    try:
                        tools_cache = await self.config_service.tools_cache.get_tool_cache(mcpserver_id)
                        if tools_cache:
                            self._mcpservers[mcpserver_id].tools = tools_cache
                            logger.info(f"Loaded {len(tools_cache)} tools from cache for {mcpserver_id}")
                        else:
                            # If no tool cache is available, start the server and discover tools
                            logger.info(f"Tool cache not found for MCP server '{mcpserver_id}', starting server to discover tools")
                            if not self._mcpservers[mcpserver_id].disabled:
                                try:
                                    # Start the server
                                    await self.parent.start_mcpserver(mcpserver_id)
                                    logger.info(f"Started MCP server '{mcpserver_id}' and discovered tools")
                                except Exception as e:
                                    logger.error(f"Failed to start MCP server '{mcpserver_id}': {str(e)}")
                    except Exception as e:
                        logger.error(f"Failed to load tools cache for {mcpserver_id}: {str(e)}")

                    loaded_count += 1
                    logger.info(f"Loaded MCP mcpserver metadata: {mcpserver_id}")

            logger.info(f"Loaded {loaded_count} MCP mcpservers from configuration")
            return {
                "status": "success",
                "message": f"Loaded {loaded_count} MCP mcpservers from configuration",
                "count": loaded_count
            }

        except Exception as e:
            logger.error(f"Failed to load MCP mcpservers: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to load MCP mcpservers: {str(e)}"
            }

    async def start_all_mcpservers(self, disabled: bool = False) -> Dict[str, Any]:
        """
        Start all configured MCP mcpservers.

        Args:
            disabled: Whether to start disabled mcpservers as well

        Returns:
            Dict with status and results of operations
        """
        logger.info(f"Starting all MCP mcpservers (including disabled: {disabled})")

        results = {
            "status": "success",
            "message": "Started MCP mcpservers",
            "mcpservers": {},
            "count": {
                "total": 0,
                "success": 0,
                "failed": 0,
                "skipped": 0
            }
        }

        for mcpserver_id, mcpserver in self._mcpservers.items():
            # Skip disabled mcpservers unless explicitly requested
            if mcpserver.disabled and not disabled:
                results["mcpservers"][mcpserver_id] = {
                    "status": "skipped",
                    "message": "Mcpserver is disabled"
                }
                results["count"]["skipped"] += 1
                continue

            # Skip already running mcpservers
            if mcpserver.status == "running" and mcpserver.process and mcpserver.process.returncode is None:
                results["mcpservers"][mcpserver_id] = {
                    "status": "skipped",
                    "message": "Mcpserver is already running"
                }
                results["count"]["skipped"] += 1
                continue

            # Start the mcpserver
            try:
                start_result = await self.parent.process_manager.start_mcpserver(mcpserver_id=mcpserver_id)

                results["mcpservers"][mcpserver_id] = start_result

                if start_result.status in ("success", "running"):
                    results["count"]["success"] += 1
                else:
                    results["count"]["failed"] += 1
                    # Mark overall status as partial if any mcpserver fails
                    results["status"] = "partial"

            except Exception as e:
                results["mcpservers"][mcpserver_id] = {
                    "status": "error",
                    "message": f"Failed to start mcpserver: {str(e)}"
                }
                results["count"]["failed"] += 1
                results["status"] = "partial"

            results["count"]["total"] += 1

        return results

    async def stop_all_mcpservers(self) -> Dict[str, Any]:
        """
        Stop all running MCP mcpservers.

        Returns:
            Dict with status and results of operations
        """
        logger.info("Stopping all MCP mcpservers")

        results = {
            "status": "success",
            "message": "Stopped MCP mcpservers",
            "mcpservers": {},
            "count": {
                "total": 0,
                "success": 0,
                "failed": 0,
                "skipped": 0
            }
        }

        for mcpserver_id, mcpserver in self._mcpservers.items():
            # Skip mcpservers that are not running
            if mcpserver.status != "running" or not mcpserver.process or mcpserver.process.returncode is not None:
                results["mcpservers"][mcpserver_id] = {
                    "status": "skipped",
                    "message": "Mcpserver is not running"
                }
                results["count"]["skipped"] += 1
                continue

            # Stop the mcpserver
            try:
                stop_result = await self.parent.process_manager.stop_mcpserver(
                    mcpserver_id=mcpserver_id
                )

                results["mcpservers"][mcpserver_id] = stop_result

                if stop_result.status == "success":
                    results["count"]["success"] += 1
                else:
                    results["count"]["failed"] += 1
                    # Mark overall status as partial if any mcpserver fails
                    results["status"] = "partial"

            except Exception as e:
                results["mcpservers"][mcpserver_id] = {
                    "status": "error",
                    "message": f"Failed to stop mcpserver: {str(e)}"
                }
                results["count"]["failed"] += 1
                results["status"] = "partial"

            results["count"]["total"] += 1

        return results

    async def update_global_blacklist(self, tools: List[str]) -> Dict[str, Any]:
        """
        Update the global tool blacklist.

        Args:
            tools: List of tool names to blacklist globally

        Returns:
            Dict with status and updated blacklist
        """
        logger.info(f"Updating global tool blacklist: {', '.join(tools)}")

        try:
            # Update in-memory blacklist
            self.parent.global_blacklist_tools = tools

            # Update in configuration
            config = await self.config_service.global_config.get_config()
            config.tools.blackList = tools
            await self.config_service.global_config.save_config(config)

            return {
                "status": "success",
                "message": "Global tool blacklist updated",
                "blacklist": tools
            }

        except Exception as e:
            logger.error(f"Failed to update global tool blacklist: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to update global tool blacklist: {str(e)}"
            }

    async def cleanup_idle_mcpservers(self, idle_timeout_seconds: int = 3600) -> Dict[str, Any]:
        """
        Clean up idle user-scoped MCP mcpservers that have been inactive for longer than
        the specified timeout.

        Args:
            idle_timeout_seconds: Number of seconds of inactivity after which a
                                mcpserver is considered idle

        Returns:
            Dict with status and information about cleaned up mcpservers
        """

        result = {"status": "success", "cleaned_servers": [], "message": ""}
        current_time = datetime.datetime.now()

        try:
            # Find idle mcpservers
            idle_mcpservers = self._find_idle_mcpservers(current_time, idle_timeout_seconds)

            # Clean up idle mcpservers
            if idle_mcpservers:
                for mcpserver_id in idle_mcpservers:
                    try:
                        # Stop the mcpserver
                        stop_result = await self.parent.process_manager.stop_mcpserver(
                            mcpserver_id=mcpserver_id
                        )

                        if stop_result.status == "success":
                            result["cleaned_servers"].append({
                                "mcpserver_id": mcpserver_id,
                            })
                            logger.info(f"Cleaned up idle mcpserver: {mcpserver_id}")
                    except Exception as e:
                        logger.error(f"Error cleaning up mcpserver {mcpserver_id}: {str(e)}")

                result["message"] = f"Cleaned up {len(result['cleaned_servers'])} idle mcpservers"
            else:
                result["message"] = "No idle mcpservers found"

        except Exception as e:
            error_msg = f"Error during mcpservers cleanup: {str(e)}"
            logger.error(error_msg)
            result["status"] = "error"
            result["message"] = error_msg

        return result

    def _find_idle_mcpservers(self, current_time: datetime.datetime, idle_timeout_seconds: int) -> List[str]:
        """
        Find mcpservers that have been idle longer than the timeout.

        Args:
            current_time: Current datetime for comparison
            idle_timeout_seconds: Timeout in seconds

        Returns:
            List of server IDs that are considered idle
        """
        idle_mcpservers = []

        for server_id, server_info in self._mcpservers.items():
            # Skip mcpservers without a username component (not user-scoped)
            if '-' not in server_id:
                continue

            # Get last activity time or use start time as fallback
            last_activity = getattr(server_info, "last_activity", None)
            mcpserver_status = getattr(server_info, "status", None)

            if mcpserver_status != "running":
                continue

            if not last_activity and hasattr(server_info, "start_time"):
                last_activity = server_info.start_time

            if not last_activity:
                logger.warning(f"Cannot determine activity time for {server_id} (status: {mcpserver_status}), skipping")
                continue

            # Check if mcpserver is idle
            try:
                idle_time = (current_time - last_activity).total_seconds()
                logger.debug(f"mcpserver-id: {server_id}, status: {mcpserver_status}, last_activity: {last_activity}, idle_time: {idle_time}")
                if idle_time > idle_timeout_seconds:
                    idle_mcpservers.append(server_id)
            except Exception as e:
                logger.warning(f"Error calculating idle time for {server_id}: {str(e)}")

        return idle_mcpservers
