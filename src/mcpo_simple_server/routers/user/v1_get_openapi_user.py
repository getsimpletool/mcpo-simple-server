from . import router
from fastapi import HTTPException, Depends, status
from fastapi.responses import JSONResponse
from mcpo_simple_server.services.auth.models import AuthUserModel
from mcpo_simple_server.services.auth import get_authenticated_user
from .mcpo_user_tools import MCPOUserToolsRouter, get_tools_router


@router.get("/tools/openapi.json", include_in_schema=True, tags=["User"])
async def get_user_tools_openapi(
    mcpo_user_tools_router: MCPOUserToolsRouter = Depends(get_tools_router),
    current_user: AuthUserModel = Depends(get_authenticated_user)
):
    """
    Return a filtered OpenAPI schema containing only the user-specific tools endpoints.

    This endpoint requires authentication and the authenticated user must match the username in the URL.
    """
    # Verify that the authenticated user matches the URL username parameter
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own tools schema. Use API key authentication."
        )
    response = await mcpo_user_tools_router.get_user_openapi_schema(current_user.username)

    return JSONResponse(content=response)
