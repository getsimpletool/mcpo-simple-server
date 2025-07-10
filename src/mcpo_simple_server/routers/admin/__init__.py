from fastapi import APIRouter

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin"],  # Tag for OpenAPI documentation
)


# Import modules to register routes
from mcpo_simple_server.routers.admin import v1_post_tools_reload     # noqa: F401, E402
from mcpo_simple_server.routers.admin import v1_post_user             # noqa: F401, E402
from mcpo_simple_server.routers.admin import v1_delete_user           # noqa: F401, E402
