"""
Package/Module: MCP Streamable Setup - FastAPI integration for MCP Streamable HTTP

High Level Concept:
-------------------
This module provides integration between FastAPI and the MCP Streamable HTTP protocol.
It initializes the MCP session manager and mounts it to a FastAPI app.

Architecture:
-------------
- Direct integration with FastAPI lifecycle
- Synchronous initialization of session manager
- Simple ASGI application that handles HTTP requests

Workflow:
---------
1. Create the MCP server using the McpServerService
2. Create and initialize the session manager during startup
3. Mount the ASGI handler at the specified path
4. Handle MCP requests through the mounted endpoint
"""

from mcpo_simple_server.logger import logger
from mcpo_simple_server.services.mcpserver import get_mcpserver_service
from mcpo_simple_server.services.mcp_streamable.server import create_mcp_server, _request_usernames
from mcpo_simple_server.services.auth.api_key import get_username_from_api_key
from typing import Optional, Dict
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.types import Scope, Receive, Send
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager


# Global session manager instance
_session_manager: Optional[StreamableHTTPSessionManager] = None

# Store authenticated usernames by session ID
_authenticated_users: Dict[str, str] = {}


def get_session_manager() -> Optional[StreamableHTTPSessionManager]:
    """Get the global session manager instance."""
    global _session_manager  # pylint: disable=global-variable-not-assigned
    if _session_manager is None:
        raise ValueError("Session manager not initialized")
    return _session_manager


class MCPStreamableHandler:
    """ASGI handler for MCP Streamable HTTP requests."""

    def __init__(self):
        # The session manager will be accessed via the global _session_manager
        # in the __call__ method, after the lifespan has initialized it.
        logger.debug("MCPStreamableHandler instance created. Session manager will be accessed at request time via global.")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Handle an ASGI HTTP request."""
        global _session_manager  # pylint: disable=global-variable-not-assigned

        if scope["type"] != "http":
            await send({
                "type": "http.response.start",
                "status": 400,
                "headers": [(b"content-type", b"text/plain")]
            })
            await send({
                "type": "http.response.body",
                "body": b"Only HTTP requests are supported"
            })
            return

        # Log request details
        path = scope.get("path", "<unknown>")
        method = scope.get("method", "<unknown>")
        logger.debug(f"MCP Streamable handling {method} request for {path}")

        # Extract and validate auth header
        headers = scope.get("headers", [])
        auth_header_bytes = next(
            (value for key, value in headers if key == b"authorization"),
            None
        )

        # Store username in scope for the MCP server to access
        username = None
        if auth_header_bytes:
            auth_header = auth_header_bytes.decode("utf-8")
            if auth_header.lower().startswith("bearer "):
                api_key = auth_header[7:]  # Remove "Bearer " prefix
                username = get_username_from_api_key(api_key)
                if username:
                    logger.debug(f"Authenticated request from user: {username}")
                    # Use the existing MCP server instance from session manager
                    mcp_server_instance = _session_manager.app  # type: ignore
                    _request_usernames[id(mcp_server_instance)] = username
                    logger.debug(f"Stored username for server instance {id(mcp_server_instance)}")
                else:
                    logger.debug("Invalid API key provided")
                    await send({
                        "type": "http.response.start",
                        "status": 401,
                        "headers": [(b"content-type", b"text/plain")]
                    })
                    await send({
                        "type": "http.response.body",
                        "body": b"Unauthorized: Invalid API key"
                    })
                    return
            else:
                logger.debug("Authorization header is not a Bearer token")
                await send({
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [(b"content-type", b"text/plain")]
                })
                await send({
                    "type": "http.response.body",
                    "body": b"Unauthorized: Invalid Authorization format"
                })
                return
        else:
            logger.debug("No Authorization header found - allowing anonymous access")

        # Ensure session manager is available
        if not _session_manager:
            logger.error("Session manager not initialized")
            await send({
                "type": "http.response.start",
                "status": 503,
                "headers": [(b"content-type", b"text/plain")]
            })
            await send({
                "type": "http.response.body",
                "body": b"MCP session manager not initialized"
            })
            return

        try:
            # Forward the request to the MCP session manager
            await _session_manager.handle_request(scope, receive, send)
            logger.debug(f"MCP Streamable successfully handled {method} request for {path}")
        except Exception as e:
            logger.error(f"Error in MCP Streamable HTTP request: {e}")
            # Return a 500 error response
            await send({
                "type": "http.response.start",
                "status": 500,
                "headers": [(b"content-type", b"text/plain")]
            })
            await send({
                "type": "http.response.body",
                "body": f"MCP Streamable Error: {str(e)}".encode("utf-8")
            })


@asynccontextmanager
async def mcp_streamable_lifespan():
    """Lifespan context manager for MCP Streamable HTTP."""
    global _session_manager

    # Get the McpServerService
    mcpserver_service = get_mcpserver_service()
    if not mcpserver_service:
        logger.error("McpServerService not initialized")
        yield
        return

    # Create the MCP server
    logger.debug("Creating MCP server for Streamable HTTP integration")
    mcp_server = create_mcp_server()

    # Create the session manager
    logger.debug("Creating session manager for Streamable HTTP integration")
    _session_manager = StreamableHTTPSessionManager(
        app=mcp_server,
        json_response=False,  # Use SSE streaming by default
        stateless=False,      # Use stateful mode for session tracking
    )

    try:
        # Run the session manager in the lifespan context
        logger.info("Starting MCP Streamable HTTP session manager")
        async with _session_manager.run():
            logger.info("MCP Streamable HTTP session manager initialized and running")
            yield
    except Exception as e:
        logger.error(f"Error in MCP Streamable HTTP integration: {e}")
    finally:
        logger.info("Shutting down MCP Streamable HTTP session manager")
        _session_manager = None


def setup_mcp_streamable(app: FastAPI, mount_path: str = "/api/v1/mcp") -> None:
    """
    Mounts the MCP Streamable HTTP handler to the FastAPI application.
    The MCP session manager lifecycle should be handled by the main application's lifespan.

    Args:
        app: The FastAPI application
        mount_path: The path to mount the MCP Streamable HTTP endpoint
    """
    logger.info(f"Mounting MCP Streamable HTTP handler at {mount_path}")
    app.mount(mount_path, MCPStreamableHandler())
