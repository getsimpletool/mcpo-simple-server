"""
Package/Module: McpServer Process Manager - Manages MCP server processes

High Level Concept:
-------------------
This module provides functionality for managing MCP server processes,
including starting, stopping, and monitoring server processes.
It focuses exclusively on process management concerns.

Architecture:
-------------
- Process creation and monitoring
- Clean process termination
- Process status tracking
- Error handling for process operations

Workflow:
---------
1. Create subprocess with appropriate configuration
2. Monitor process status
3. Handle process termination
4. Maintain process metadata

Notes:
------
This module replaces functionality previously in the "lifecycle" service
but with a more focused scope on just process management.
"""
import json
import os
import asyncio
import datetime
import copy
from loguru import logger
from fastapi import HTTPException
from typing import TYPE_CHECKING
from mcpo_simple_server.services.config import get_config_service
from mcpo_simple_server.services.mcpserver.models import McpServerModel
from asyncio.subprocess import Process as AsyncProcess
if TYPE_CHECKING:
    from mcpo_simple_server.services.mcpserver import McpServerService


class McpServerProcessManager:
    """
    Manages MCP server processes, including starting, stopping and monitoring.

    This component focuses exclusively on process management concerns,
    handling the creation, monitoring, and termination of MCP server processes.
    """

    def __init__(self, parent: "McpServerService"):
        """
        Initialize the McpServer Process Manager.

        Args:
            parent: Reference to the parent McpServerService
        """
        self.parent = parent
        self._mcpservers = parent._mcpservers
        self.config_service = get_config_service()

        # JSON message handlers for process output
        self.json_message_handlers = []

    async def start_mcpserver(self, mcpserver_id: str) -> McpServerModel:
        """
        Start a MCP server subprocess with the given configuration.

        Args:
            mcpserver_id: The identifier of the server to start

        Returns:
            McpServerModel with status and metadata about the started server
        """
        mcpserver = self._mcpservers.get(mcpserver_id)
        if not mcpserver:
            raise HTTPException(status_code=404, detail=f"McpServer '{mcpserver_id}' not found")

        # Check if server is already running
        if self._is_running(mcpserver_id):
            logger.warning(f"mcpserver.process_manager.start_mcpserver: McpServer '{mcpserver_id}' is already running")
            raise HTTPException(status_code=400, detail=f"McpServer '{mcpserver.name}' already exists for user '{mcpserver.username}'")

        try:
            # Replace 'uvx' with 'uv' and handle different command formats
            original_command = copy.deepcopy(mcpserver.command)
            final_args = mcpserver.args.copy()

            if mcpserver.command == "uvx":
                final_command = "uv"

                if len(final_args) > 0:
                    module_name = final_args[0]
                    if len(final_args) > 1:
                        final_args = ["tool", "run", module_name] + final_args[1:]
                    else:
                        # If there are no arguments after the module name
                        final_args = ["tool", "run", module_name]
                    logger.info(
                        f"mcpserver.process_manager.start_mcpserver: Converting command for {mcpserver.name}: '{original_command} {' '.join(final_args)}' to '{final_command} {' '.join(final_args)}'")

            # Handle uvx as the first part of the command string
            elif mcpserver.command.startswith("uvx "):
                final_command = "uv"
                final_args = ["run"] + final_args
                logger.info(
                    f"mcpserver.process_manager.start_mcpserver: Converting command for {mcpserver.name}: '{original_command} {' '.join(final_args)}' to '{final_command} {' '.join(final_args)}'")
            elif mcpserver.command.startswith("npx"):
                final_command = "npm"
                final_args = ["exec"] + final_args
                logger.info(
                    f"mcpserver.process_manager.start_mcpserver: Converting command for {mcpserver.name}: '{original_command} {' '.join(final_args)}' to '{final_command} {' '.join(final_args)}'")
            else:
                final_command = copy.deepcopy(mcpserver.command)
                final_args = copy.deepcopy(mcpserver.args)
                logger.info(f"mcpserver.process_manager.start_mcpserver: Command for {mcpserver.name}: '{final_command}' + args: '{final_args}'")

            # Prepare environment variables
            process_env = {}
            if mcpserver.env:
                # Start with current environment
                process_env = os.environ.copy()
                # Add or override with provided environment variables
                for key, value in mcpserver.env.items():
                    process_env[key] = value
                logger.info(f"mcpserver.process_manager.start_mcpserver: Setting environment variables for mcpserver {mcpserver.name}: {', '.join(list(mcpserver.env.keys()))}")
            else:
                process_env = os.environ.copy()
                logger.info(f"mcpserver.process_manager.start_mcpserver: No environment variables provided for mcpserver {mcpserver.name}")

            # Get subprocess stream limit from env, default 5MB
            stream_limit = int(os.getenv("SUBPROCESS_STREAM_LIMIT", str(5 * 1024 * 1024)))

            # Start the subprocess
            process = await asyncio.create_subprocess_exec(
                final_command,
                *final_args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=process_env,
                limit=stream_limit
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create environment for mcpserver {mcpserver.name}: {str(e)}") from e

        # Check if process was created successfully
        if not process:
            raise HTTPException(status_code=500, detail=f"Failed to start mcpserver {mcpserver.name}: Process creation failed")

        logger.info(f"mcpserver.process_manager.start_mcpserver: McpServer '{mcpserver.name}' started successfully (PID: {process.pid})")
        start_time = datetime.datetime.now()

        # Update server model
        self._mcpservers[mcpserver_id].status = "running"
        self._mcpservers[mcpserver_id].process = process
        self._mcpservers[mcpserver_id].pid = process.pid
        self._mcpservers[mcpserver_id].start_time = start_time
        self._mcpservers[mcpserver_id].last_activity = start_time

        # Send initialization notification per MCP protocol
        logger.debug("Sending initialization notification")
        init_request = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        init_request_str = json.dumps(init_request) + "\n"
        if process.stdin:
            process.stdin.write(init_request_str.encode())
            _ = await process.stdin.drain()
            logger.debug("Initialization notification send")
        else:
            logger.warning(f"Cannot send initialization to {mcpserver.name}: stdin is not available")

        # Check if mcpserver has tools cache
        mcpserver_tool_cache = await self.config_service.tools_cache.get_tool_cache(mcpserver_id)
        if mcpserver_tool_cache:
            logger.info(f"McpServer '{mcpserver_id}' has tools cache - count: {len(mcpserver_tool_cache)}")
            # Apply the blacklist filter to the cached tools
            filtered_tools = self.parent.tools.filter_tools(
                mcpserver_tool_cache,  # Full list of tools from cache
                self._mcpservers[mcpserver_id].tools_blacklist
            )
            # Store the filtered list in the model
            self._mcpservers[mcpserver_id].tools = filtered_tools
            logger.info(f"After applying blacklist: {len(filtered_tools)} of {len(mcpserver_tool_cache)} tools available for {mcpserver_id}")
        else:
            logger.info(f"McpServer '{mcpserver_id}' does not have tools cache")
            # Discover tools - this returns the full, unfiltered list
            unfiltered_tools = await self.parent.tools.discover_tools(mcpserver_id)
            if unfiltered_tools:
                logger.info(f"McpServer '{mcpserver_id}' discovered {len(unfiltered_tools)} tools")
                # Cache the full set of tools (unfiltered)
                await self.config_service.tools_cache.write_tool_cache(mcpserver_id, unfiltered_tools)
                logger.info(f"Cached {len(unfiltered_tools)} tools for {mcpserver_id}")

                # Apply blacklist filter to the tools we just discovered
                filtered_tools = self.parent.tools.filter_tools(
                    unfiltered_tools,
                    self._mcpservers[mcpserver_id].tools_blacklist
                )
                # Update the model with filtered tools
                self._mcpservers[mcpserver_id].tools = filtered_tools
                logger.info(f"After applying blacklist: {len(filtered_tools)} of {len(unfiltered_tools)} tools available for {mcpserver_id}")
            else:
                logger.info(f"McpServer '{mcpserver_id}' does not have any tools")

        # Start log monitoring task
        asyncio.create_task(self._monitor_process_logs(mcpserver_id, process))

        print(self._mcpservers[mcpserver_id])
        logger.info(f"mcpserver.process_manager.start_mcpserver: McpServer-ID: '{mcpserver_id}' started successfully (PID: {process.pid})")
        return McpServerModel(**self._mcpservers[mcpserver_id].model_dump())

    async def stop_mcpserver(self, mcpserver_id: str, timeout: float = 5.0) -> McpServerModel:
        """
        Stop a running MCP server subprocess.

        Args:
            mcpserver_id: The identifier of the server to stop
            timeout: Timeout in seconds to wait for the process to terminate

        Returns:
            McpServerModel with status and result of the operation
        """
        logger.info(f"mcpserver.process_manager.stop_mcpserver: Stopping mcpserver: {mcpserver_id}")

        # Check if server exists
        if mcpserver_id not in self._mcpservers:
            raise HTTPException(status_code=404, detail=f"McpServer '{mcpserver_id}' not found")

        # Get process
        process = self._mcpservers[mcpserver_id].process

        if not process or process.returncode is not None:
            logger.info(f"McpServer '{mcpserver_id}' is not running")
            self._mcpservers[mcpserver_id].status = "stopped"
            self._mcpservers[mcpserver_id].process = None
            self._mcpservers[mcpserver_id].pid = None
            return self._mcpservers[mcpserver_id]

        try:
            # Try to terminate gracefully
            process.terminate()

            try:
                # Wait for process to terminate
                await asyncio.wait_for(process.wait(), timeout=timeout)
                logger.info(f"McpServer '{mcpserver_id}' stopped gracefully")
            except asyncio.TimeoutError:
                # Force kill if timeout
                logger.warning(f"McpServer '{mcpserver_id}' did not terminate gracefully, killing...")
                process.kill()
                await process.wait()
                logger.info(f"McpServer '{mcpserver_id}' killed")

            # Update server status
            self._mcpservers[mcpserver_id].status = "stopped"
            self._mcpservers[mcpserver_id].process = None
            self._mcpservers[mcpserver_id].pid = None
            return McpServerModel(**self._mcpservers[mcpserver_id].model_dump())

        except Exception as e:
            logger.error(f"Error stopping mcpserver {mcpserver_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to stop mcpserver: {str(e)}") from e

    def _is_running(self, mcpserver_id: str) -> bool:
        """
        Check if a server is currently running.

        Args:
            mcpserver_id: The identifier of the server to check

        Returns:
            True if the server is running, False otherwise
        """
        if mcpserver_id not in self._mcpservers:
            return False

        mcpserver = self._mcpservers[mcpserver_id]
        process = mcpserver.process

        if not process:
            return False

        return process.returncode is None

    def register_json_message_handler(self, handler_func):
        """
        Register a handler function to be called when JSON messages are received from processes.

        Args:
            handler_func: A function that takes (mcpserver_id, json_message) as arguments
        """
        if handler_func not in self.json_message_handlers:
            self.json_message_handlers.append(handler_func)
            logger.debug(f"Registered new JSON message handler: {handler_func.__qualname__}")

    async def _monitor_process_logs(self, mcpserver_id: str, process: AsyncProcess) -> None:
        """
        Monitor and log the output of a server process.

        Args:
            mcpserver_id: The identifier of the server
            process: The subprocess to monitor
        """
        name = mcpserver_id.split('-')[0]
        try:
            # Process stdout
            while True:
                if process.stdout is None:
                    break
                line = await process.stdout.readline()
                if not line:
                    break

                logger.info(f"Received stdout from {name}")
                decoded_line = line.decode('utf-8', errors='replace').strip()

                # Try to parse JSON responses and notify handlers
                if decoded_line.startswith('{'):
                    try:
                        json_msg = json.loads(decoded_line)
                        logger.info("\n" + json.dumps(json_msg, indent=2))
                        # Notify all registered handlers about this JSON message
                        for handler in self.json_message_handlers:
                            try:
                                handler(mcpserver_id, json_msg)
                            except Exception as handler_err:
                                logger.error(f"Error in JSON message handler: {str(handler_err)}")
                        # Log the JSON message
                    except json.JSONDecodeError:
                        # Not valid JSON, just log it
                        logger.warning("Not valid JSON, just log it: " + decoded_line)

            # Process stderr
            while True:
                if process.stderr is None:
                    break
                line = await process.stderr.readline()
                if not line:
                    break
                logger.error(f"Error from {name}: {line.decode('utf-8', errors='replace').strip()}")

            # Wait for process to complete
            await process.wait()

            # Update server status when process completes
            if mcpserver_id in self._mcpservers:
                self._mcpservers[mcpserver_id].status = "stopped"
                self._mcpservers[mcpserver_id].process = None
                self._mcpservers[mcpserver_id].pid = None

            logger.info(f"McpServer '{mcpserver_id}' process completed with exit code {process.returncode}")

        except Exception as e:
            logger.error(f"Error monitoring mcpserver {mcpserver_id}: {str(e)}")

            # Update server status on error
            if mcpserver_id in self._mcpservers:
                self._mcpservers[mcpserver_id].status = "error"
                self._mcpservers[mcpserver_id].process = None
                self._mcpservers[mcpserver_id].pid = None
