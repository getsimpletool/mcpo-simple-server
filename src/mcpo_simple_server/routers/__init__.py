"""
Package/Module: Routers - FastAPI route handlers for MCPoSimpleServer

High Level Concept:
-------------------
This package provides all FastAPI route handlers for the MCPoSimpleServer,
organized by functional areas (admin, tools, public, SSE). Each router module
defines endpoints for specific functionality domains, enabling a clean separation
of concerns and modular API design.

Architecture:
-------------
- Modular router organization by functional domain
- Each router handles a specific set of related endpoints
- Consistent error handling and response formatting
- Authentication and permission checks at the router level

Workflow:
---------
1. Incoming requests are routed to the appropriate router based on URL path
2. Router handlers process the request and interact with service layer
3. Services perform business logic and data operations
4. Routers format and return appropriate responses

Router Modules:
--------------
- admin: Administrative operations requiring admin privileges
  * User management (create, update, delete users)
  * MCP server management (add, remove, start, stop servers)
  * Tool management (reload dynamic tool endpoints)

- user: User-specific operations requiring authentication
  * Authentication (login, logout, password management)
  * API key management (create, delete API keys for tool access)
  * Environment variable management (get, update user env vars)
  * User-specific MCP server operations

- public: Publicly accessible endpoints without authentication
  * Public MCP server listing and details
  * Health check and server information

- tool: Dynamic endpoints for MCP tool access
  * Generated based on available MCP servers
  * Requires API key authentication
  * Provides programmatic access to MCP tools

- sse: Server-Sent Events for real-time communication
  * Connection endpoints for event streaming
  * Message publishing for real-time updates

- prompt: Prompt management endpoints
  * Create, read, update, delete operations for prompts
  * Supports both public and user-specific prompts

Notes:
------
- All routers follow RESTful design principles
- SSE (Server-Sent Events) router handles real-time communication
- Admin router requires authentication and proper permissions
"""


# Import the router modules directly
from .admin import router as admin_router
from .public import router as public_router
# from .mcp import router as mcp_router
from .mcpservers import router as mcpservers_router
# from .prompts import router as prompts_router
# from .dynamic_tools import router as dynamic_tools_router
from .ui import router as ui_router

# Define what should be exported from this package
__all__ = ['admin_router',
           'public_router',
           'mcp_router',
           'mcpservers_router',
           'ui_router'
           ]
