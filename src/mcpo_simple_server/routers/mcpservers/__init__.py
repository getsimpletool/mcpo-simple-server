from fastapi import APIRouter


# Create the main router
router = APIRouter(
    prefix="/api/v1/mcpservers",
    tags=["MCP Servers"],
    responses={404: {"description": "Not found"}},
)

__all__ = ["router"]
from . import v1_post_mcpservers            # noqa: F401, E402
from . import v1_get_mcpservers_config      # noqa: F401, E402
from . import v1_get_mcpservers_status      # noqa: F401, E402
from . import v1_post_mcpserver_start       # noqa: F401, E402
from . import v1_post_mcpserver_stop        # noqa: F401, E402
from . import v1_get_mcpserver_status       # noqa: F401, E402
from . import v1_get_mcpserver_config       # noqa: F401, E402
from . import v1_delete_mcpserver           # noqa: F401, E402
from . import v1_put_mcpserver_env          # noqa: F401, E402
from . import v1_delete_mcpserver_env       # noqa: F401, E402
from . import v1_delete_mcpserver_env_key   # noqa: F401, E402
from . import v1_put_mcpserver_env_key      # noqa: F401, E402
