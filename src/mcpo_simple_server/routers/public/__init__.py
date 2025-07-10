"""
Package/Module: Public Router - Publicly accessible endpoints without authentication

High Level Concept:
-------------------
The Public Router provides endpoints that are accessible without authentication,
offering public information about available MCP servers and prompts. It serves as
the entry point for clients to discover available resources before authentication.

Architecture:
-------------
- Modular organization with separate handler files for different public resources
- No authentication requirements for any endpoints
- Read-only access to public MCP server information
- Public prompt management for shared prompt resources

Endpoints:
----------
* /public/mcpservers/* - Public MCP server operations
  - GET /public/mcpservers - List all publicly available MCP servers
  - GET /public/mcpservers/{name} - Get details of a specific public MCP server
* /public/prompts/* - Public prompt operations
  - GET /public/prompts - List all publicly available prompts
  - GET /public/prompts/{prompt_id} - Get a specific public prompt
* /health - Health check endpoint
  - GET /health - Check server health status
* / - Root endpoint
  - GET / - Get basic server information

Workflow:
---------
1. Requests are received without authentication requirements
2. Requests are routed to specialized handlers based on the resource type
3. Public resource data is retrieved from the appropriate service
4. Results are returned with standardized response formats

Notes:
------
- All public endpoints are accessible without authentication
- Only read operations are supported for security reasons
- Public resources are shared across all users of the system
- Sensitive information is filtered from public responses
"""

from fastapi import APIRouter
router = APIRouter(
    prefix="/api/v1/public",
    tags=["Public"],
)


# Import modules to register routes
from . import v1_get_mcpservers             # noqa: F401, E402
from . import v1_get_openapi_public         # noqa: F401, E402
# from . import v1_get_prompts              # noqa: F401, E402
