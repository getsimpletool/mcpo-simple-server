"""
Admin Tools Router

This module provides functionality for managing dynamic tool endpoints.
"""
from fastapi import Depends, Request, status
from loguru import logger
from mcpo_simple_server.services.config.models import UserConfigPublicModel
from mcpo_simple_server.services.auth import get_current_admin_user
from mcpo_simple_server.routers.admin import router
import mcpo_simple_server.routers.public.mcpo_public_tools as public_tools_module
import mcpo_simple_server.routers.user.mcpo_user_tools as user_tools_module


@router.post("/tools/reload", status_code=status.HTTP_200_OK)
async def reload_tools(
    request: Request,
    _: UserConfigPublicModel = Depends(get_current_admin_user)
):
    """
    Reload all dynamic tool endpoints without restarting the application.

    This will create a new tools router instance, remove the old router, and re-include the new one.
    This ensures all dynamic endpoints and OpenAPI schema are properly updated.

    Returns:
        Dict containing status and message of the reload operation.
    """
    # Remove all existing /tool/ routes from FastAPI
    routes_to_keep = []
    for route in request.app.routes:
        if not hasattr(route, "path") or not route.path.startswith("/tool/"):
            routes_to_keep.append(route)

    # Use API methods to properly rebuild routes
    request.app.router.routes = routes_to_keep

    # Replace the global tools routers with new instances
    public_tools_module.mcpo_public_tools_router = public_tools_module.MCPOPublicToolsRouter()
    user_tools_module.mcpo_user_tools_router = user_tools_module.MCPOUserToolsRouter()

    # Initialize the new routers
    await public_tools_module.mcpo_public_tools_router.initialize()
    await user_tools_module.mcpo_user_tools_router.initialize()

    # Include the new routers in the app
    request.app.include_router(public_tools_module.mcpo_public_tools_router.router)
    request.app.include_router(user_tools_module.mcpo_user_tools_router.router)

    # Force OpenAPI schema to be rebuilt
    request.app.openapi_schema = None
    _ = request.app.openapi()

    logger.info("Dynamic tool endpoints reloaded")

    return {"status": "success", "message": "Tool endpoints reloaded with fresh router instance"}
