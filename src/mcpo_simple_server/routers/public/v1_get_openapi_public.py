from . import router
from fastapi import Depends, Request
from fastapi.responses import JSONResponse
# from .mcpo_public_tools import get_enhanced_tools_router, EnhancedToolsRouter
from .mcpo_public_tools import MCPOPublicToolsRouter, get_tools_router


@router.get("/tools/openapi.json", include_in_schema=True, tags=["Public"])
async def get_public_tools_openapi(
    request: Request,
    tools_router: MCPOPublicToolsRouter = Depends(get_tools_router)
):
    """
    Return a filtered OpenAPI schema containing only the public tools endpoints.

    This endpoint is publicly accessible without authentication since it only
    provides schema for public tools.
    """
    # Public tools should be accessible without authentication
    app = request.app
    return JSONResponse(content=tools_router.get_openapi_schema(app))
