from mcpo_simple_server.logger import logger
from mcpo_simple_server.services.auth.api_key import get_username_from_api_key
from fastapi import FastAPI
from starlette.types import Scope, Receive, Send
from mcp.server.lowlevel.server import NotificationOptions
from mcp.server.sse import SseServerTransport
from .server import create_mcp_server


def setup_mcp_sse(
    app: FastAPI,
    sse_connect_path: str,
    sse_message_post_path: str
) -> None:
    """
    Sets up the MCP SSE service for the FastAPI application.

    Args:
        app: The FastAPI application instance.
        sse_connect_path: The path where clients will connect via GET to establish an SSE session.
        sse_message_post_path: The path where the server will listen for POSTed MCP messages from clients.
    """

    # Derive relative endpoint for SSE POST messages within SSE mount
    prefix = sse_connect_path.rstrip("/")
    msg_post = sse_message_post_path.rstrip("/") + "/"
    if msg_post.startswith(prefix):
        endpoint = msg_post[len(prefix):]
    else:
        endpoint = msg_post
    logger.debug(f"SSE endpoint derived: '{endpoint}'")
    # Initialize SseServerTransport with relative endpoint
    sse_transport = SseServerTransport(endpoint=endpoint)

    # Mount the POST handler for messages before the GET sub-app to ensure correct routing
    app.mount(msg_post, sse_transport.handle_post_message, name="mcp_sse_post_messages")

    # SSE GET ASGI sub-app
    async def _sse_asgi(scope: Scope, receive: Receive, send: Send):
        # Only handle HTTP GET
        if scope.get("type") != "http" or scope.get("method") != "GET":
            await send({"type": "http.response.start", "status": 405, "headers": [(b"content-type", b"text/plain")]})
            await send({"type": "http.response.body", "body": b"Method Not Allowed"})
            return

        # Extract and validate auth header early
        headers = scope.get("headers", [])
        auth_header_bytes = next(
            (value for key, value in headers if key == b"authorization"),
            None
        )

        if not auth_header_bytes:
            logger.debug(f"SSE connection request from {scope.get('client')} for path {scope.get('path')}")
            logger.debug("SSE: Authorization header not found in request")
        else:
            auth_header = auth_header_bytes.decode("utf-8")
            if not auth_header.lower().startswith("bearer "):
                logger.debug("SSE: Authorization header is not a Bearer token")
                await send({"type": "http.response.start", "status": 401, "headers": [(b"content-type", b"text/plain")]})
                await send({"type": "http.response.body", "body": b"Unauthorized: Invalid Authorization format"})
                return

            api_key = auth_header[7:]  # Remove "Bearer " prefix
            logger.debug(f"SSE: API key: {api_key}")

            username = get_username_from_api_key(api_key)
            logger.debug(f"SSE: Username: {username}")
            if not username:
                logger.debug("SSE: API key is not valid or no username associated")
                await send({"type": "http.response.start", "status": 401, "headers": [(b"content-type", b"text/plain")]})
                await send({"type": "http.response.body", "body": b"Unauthorized: Invalid API key"})
                return

            logger.debug(f"SSE connection request from {scope.get('client')} for path {scope.get('path')} with username: {username}")

        mcp_server_instance = create_mcp_server()
        setattr(mcp_server_instance, '_current_asgi_scope', scope)  # Attach current scope

        async with sse_transport.connect_sse(scope, receive, send) as (read_stream, write_stream):
            try:
                initialization_opts = mcp_server_instance.create_initialization_options(
                    notification_options=NotificationOptions(prompts_changed=True, resources_changed=True, tools_changed=True)
                )
                await mcp_server_instance.run(read_stream, write_stream, initialization_options=initialization_opts)
            except Exception as e:
                logger.error(f"Error during MCPServer run for SSE: {e}", exc_info=True)
            finally:
                if hasattr(mcp_server_instance, '_current_asgi_scope'):
                    delattr(mcp_server_instance, '_current_asgi_scope')  # Clear current scope
                logger.info(f"MCPServer (id: {id(mcp_server_instance)}) finished for SSE session.")
    # Mount ASGI sub-app for SSE GET (after POST mount)
    app.mount(prefix, _sse_asgi, name="mcp_sse_get")
    logger.info(f"MCP SSE endpoints mounted at '{sse_connect_path}' and '{sse_message_post_path}'.")


__all__ = ["setup_mcp_sse"]
