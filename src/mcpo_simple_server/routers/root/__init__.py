"""
Package/Module: Root Router - Basic server endpoints

High Level Concept:
-------------------
The Root Router provides basic endpoints for server status and health checks.
These endpoints are accessible without authentication and provide essential
information about the server's operational status.

Architecture:
-------------
- Simple endpoints for health and ping checks
- No authentication requirements
- Minimal response payloads for quick response times

Endpoints:
----------
* /health - Health check endpoint
  - GET /health - Check server health status (returns {"status": "ok"})
* /ping - Ping check endpoint
  - GET /ping - Simple ping-pong response (returns {"response": "pong"})

Workflow:
---------
1. Client requests server status via health or ping endpoints
2. Server processes request without authentication
3. Server returns standardized response indicating operational status

Notes:
------
- These endpoints are primarily used for monitoring and uptime checks
- They should return quickly and with minimal processing overhead
- They do not interact with any database or external services
"""
from fastapi import APIRouter

router = APIRouter(
    tags=["Root"],
)


# Import modules to register routes
from . import root              # noqa: F401, E402
from . import v1_get_health     # noqa: F401, E402
from . import v1_get_ping       # noqa: F401, E402
from . import v1_get_version    # noqa: F401, E402
