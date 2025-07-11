import os
import sys
import asyncio
import signal
from typing import Any, Optional
from contextlib import asynccontextmanager
from mcpo_simple_server.logger import logger
from mcpo_simple_server.config import (
    CONFIG_STORAGE_PATH,
    MCPSERVER_CLEANUP_INTERVAL,
    MCPSERVER_CLEANUP_TIMEOUT,
    APP_VERSION,
    APP_NAME,
    LIB_PATH
)
import mcpo_simple_server.routers.root as root_module
import mcpo_simple_server.routers.user as user_module
import mcpo_simple_server.routers.admin as admin_module
import mcpo_simple_server.routers.public as public_module
import mcpo_simple_server.routers.ui as ui_module
# import mcpo_simple_server.routers.mcp as mcp_module
# import mcpo_simple_server.routers.prompts as prompts_module
import mcpo_simple_server.routers.mcpservers as mcpservers_module
from mcpo_simple_server.middleware import setup_middleware
# Admin manager is now used for cleanup operations
from mcpo_simple_server.services.config import ConfigService
from mcpo_simple_server.services.mcpserver import McpServerService
from mcpo_simple_server.services.config import set_config_service
from mcpo_simple_server.services.mcpserver import set_mcpserver_service
# Import MCP Streamable HTTP integration
from mcpo_simple_server.services.mcp_streamable import setup_mcp_streamable
from mcpo_simple_server.services.mcp_streamable.setup import mcp_streamable_lifespan
# Import MCP SSE integration
from mcpo_simple_server.services.mcp_sse import setup_mcp_sse
from mcpo_simple_server.routers.mcp.v1_api_sse_docs import SSE_OPENAPI_PATHS  # Import custom SSE docs
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

# Load environment variables from .env file
load_dotenv()

_session_manager: Optional[StreamableHTTPSessionManager] = None


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    # Initialize services
    logger.info("Initializing Services")
    fastapi_app.state.config_service = ConfigService(options={"db_path": CONFIG_STORAGE_PATH})
    set_config_service(fastapi_app.state.config_service)
    fastapi_app.state.mcpserver_service = McpServerService()
    await fastapi_app.state.mcpserver_service.load_blacklist_tools()
    set_mcpserver_service(fastapi_app.state.mcpserver_service)

    # Startup tasks
    # Phase 2: Scan and cache all MCPServer metadata for all users (no process start)
    await fastapi_app.state.mcpserver_service.admin.load_all_mcpservers()

    # Initialize tools router with available tools and include it
    from mcpo_simple_server.routers.public.mcpo_public_tools import mcpo_public_tools_router  # pylint: disable=C0415
    # Initialize the router with actual endpoints
    await mcpo_public_tools_router.initialize()
    # Include the router with the dynamically created endpoints
    fastapi_app.include_router(mcpo_public_tools_router.router)

    # Set up MCP Streamable HTTP integration
    setup_mcp_streamable(fastapi_app)
    logger.info("MCP Streamable HTTP integration initialized")

    # Set up MCP SSE integration
    setup_mcp_sse(
        fastapi_app,
        sse_connect_path="/api/v1/sse",
        sse_message_post_path="/api/v1/sse/messages/"
    )
    logger.info("MCP SSE integration initialized")

    # Start periodic cleanup task for idle user-specific server instances
    cleanup_task = asyncio.create_task(periodic_idle_server_cleanup(fastapi_app, 5))

    async with mcp_streamable_lifespan():
        yield  # This is where the FastAPI application runs

    # Shutdown tasks
    logger.info("Shutting down server processes...")

    try:
        # Get the current event loop for scheduling the force exit
        loop = asyncio.get_running_loop()

        # Schedule a force exit after a short delay (3 seconds)
        force_exit_handle = loop.call_later(3.0, lambda: os._exit(0))
        logger.warning("Scheduled force exit in 3 seconds if graceful shutdown fails")

        # First, close all SSE connections
        # from mcpo_simple_server.routers.mcp.messages_handlers.utils import sse_transport    # pylint: disable=C0415
        # logger.info("Shutting down SSE transport...")
        # await sse_transport.shutdown()
        # logger.info("All SSE connections closed successfully")

        # Then shutdown all server processes (both global and user-specific)
        logger.info("Shutting down server manager...")
        await fastapi_app.state.mcpserver_service.admin.stop_all_mcpservers()
        logger.info("All server processes terminated successfully")

        # If we got here successfully, we can cancel the force exit
        logger.info("Graceful shutdown succeeded, cancelling force exit")
        force_exit_handle.cancel()

        # Cleanup the periodic task
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
        # Force exit on error
        logger.critical("Forcing immediate exit due to shutdown error")
        os._exit(1)

app = FastAPI(
    title=APP_NAME,
    description="A simple FastAPI server template",
    version=str(APP_VERSION),
    lifespan=lifespan
)

# Setup middleware
setup_middleware(app)

# Include static files
app.mount("/assets", StaticFiles(directory=str(os.path.join(LIB_PATH, "assets"))), name="assets")

# Include routers
app.include_router(root_module.router)      # Include the root router with health and ping endpoints
app.include_router(user_module.router)      # Test 020
app.include_router(mcpservers_module.router)
# app.include_router(prompts_module.router)
app.include_router(admin_module.router)     # Test 030
app.include_router(public_module.router)
app.include_router(ui_module.router)


def custom_openapi():
    """
    Custom OpenAPI generator that includes dynamic tool endpoints and patches /user/me.
    """
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    # Merge custom SSE paths
    if 'paths' not in schema:
        schema['paths'] = {}
    schema['paths'].update(SSE_OPENAPI_PATHS)

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi


async def periodic_idle_server_cleanup(fastapi_app: FastAPI, cleanup_interval: int = MCPSERVER_CLEANUP_INTERVAL, idle_timeout_seconds: int = MCPSERVER_CLEANUP_TIMEOUT):
    """
    Periodically clean up idle user-specific server instances.
    Runs every 5 seconds by default.
    """
    logger.info(f"Starting periodic cleanup of idle user servers (interval: {cleanup_interval} seconds)")

    while True:
        try:
            # Wait for the specified interval
            await asyncio.sleep(cleanup_interval)

            # Clean up idle user-specific servers using the admin manager
            mcpserver_service: McpServerService = fastapi_app.state.mcpserver_service
            result = await mcpserver_service.admin.cleanup_idle_mcpservers(idle_timeout_seconds)

            if result["cleaned_servers"]:
                logger.info(
                    f"Cleaned up {len(result['cleaned_servers'])} idle user servers: "
                    f"{', '.join([srv['mcpserver_id'] for srv in result['cleaned_servers']])}"
                )
            else:
                logger.debug("No idle user servers to clean up")

        except asyncio.CancelledError:
            logger.info("User server cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in user server cleanup task: {str(e)}")
            # Continue running despite errors
            await asyncio.sleep(60)  # Wait a bit before retrying after an error


# Shutdown logic moved to lifespan context manager


# Register signal handlers
def signal_handler(sig: int, frame: Any) -> None:
    """
    Signal handler to properly shut down the server when SIGINT or SIGTERM is received.

    This ensures graceful shutdown of all server processes.
    """
    logger.debug(f"Received signal {sig} (frame {frame})")
    logger.info("Received termination signal, shutting down...")
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
