"""
Package/Module: MCP Session Manager - Streamable HTTP session management

High Level Concept:
-------------------
This module provides a singleton MCP session manager for the Streamable HTTP transport.
It manages the lifecycle of MCP sessions and provides access to the session manager
throughout the application.

Architecture:
-------------
- Singleton pattern for global access to the session manager
- Integration with MCP's StreamableHTTPSessionManager
- Proper lifecycle management with FastAPI's lifespan

Workflow:
---------
1. Initialize the session manager during application startup
2. Access the session manager throughout the application
3. Properly shut down the session manager during application shutdown

Usage Example:
--------------
>>> from mcpo_simple_server.services.mcp_streamable.manager import get_mcp_session_manager
>>> # Access the session manager
>>> session_manager = get_mcp_session_manager()
"""

import logging
import asyncio
from typing import Optional, Any

from mcp.server.lowlevel.server import Server as MCPServer
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

logger = logging.getLogger(__name__)

# Global session manager instance
_MCP_SESSION_MANAGER: Optional[StreamableHTTPSessionManager] = None

# Task for running the session manager
_SESSION_TASK: Optional[asyncio.Task] = None


def set_mcp_session_manager(session_manager: StreamableHTTPSessionManager) -> None:
    """
    Set the global MCP session manager instance.

    Args:
        session_manager: The StreamableHTTPSessionManager instance to set
    """
    global _MCP_SESSION_MANAGER
    _MCP_SESSION_MANAGER = session_manager
    logger.info("MCP Streamable HTTP session manager initialized")


def get_mcp_session_manager() -> Optional[StreamableHTTPSessionManager]:
    """
    Get the global MCP session manager instance.

    Returns:
        The StreamableHTTPSessionManager instance or None if not initialized
    """
    return _MCP_SESSION_MANAGER


def create_mcp_session_manager(
    mcp_server: MCPServer[Any],
    json_response: bool = False,
    stateless: bool = False,
) -> StreamableHTTPSessionManager:
    """
    Create a new MCP session manager instance.

    Args:
        mcp_server: The MCP server instance
        json_response: Whether to use JSON responses instead of SSE streams
        stateless: If True, creates a fresh transport for each request

    Returns:
        A new StreamableHTTPSessionManager instance
    """
    session_manager = StreamableHTTPSessionManager(
        app=mcp_server,
        event_store=None,  # No event store for now, could be added later
        json_response=json_response,
        stateless=stateless,
    )

    # Set the global instance
    set_mcp_session_manager(session_manager)

    return session_manager


async def start_session_manager() -> None:
    """
    Start the MCP session manager task.

    This function initializes the task group for the session manager,
    which is required for handling requests.
    """
    global _SESSION_TASK

    if _MCP_SESSION_MANAGER is None:
        logger.error("Cannot start session manager: not initialized")
        return

    if _SESSION_TASK is not None and not _SESSION_TASK.done():
        logger.info("Session manager task is already running")
        return

    # Define the task function
    async def run_session_manager():
        try:
            # This will initialize the task group
            # We know _MCP_SESSION_MANAGER is not None because we checked above
            session_manager = _MCP_SESSION_MANAGER
            assert session_manager is not None
            async with session_manager.run():
                # Keep the task running until cancelled
                await asyncio.Future()
        except asyncio.CancelledError:
            logger.info("Session manager task cancelled")
        except Exception as e:
            logger.error("Error in session manager task: %s", str(e))

    # Create and start the task
    _SESSION_TASK = asyncio.create_task(run_session_manager())
    logger.info("MCP session manager task started")


async def stop_session_manager() -> None:
    """
    Stop the MCP session manager task.
    """
    global _SESSION_TASK

    if _SESSION_TASK is None or _SESSION_TASK.done():
        logger.info("No active session manager task to stop")
        return

    # Cancel the task
    _SESSION_TASK.cancel()
    try:
        await _SESSION_TASK
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error("Error stopping session manager task: %s", str(e))

    _SESSION_TASK = None
    logger.info("MCP session manager task stopped")
