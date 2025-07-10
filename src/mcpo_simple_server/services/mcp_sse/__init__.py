"""
Package/Module: mcp_sse - MCP SSE Transport Service

High Level Concept:
-------------------
This package implements the MCP (Model Context Protocol) SSE (Server-Sent Events)
Transport Layer. It provides the necessary infrastructure to handle MCP communication
over SSE, enabling real-time, unidirectional event streams from the server to the client.
It mirrors the design philosophy of the mcp_streamable service, utilizing the core
'mcp' module for protocol handling and session management.

Architecture:
-------------
- Server: Manages SSE connections and event streaming.
- Manager: Handles MCP session lifecycle and integration with the 'mcp' module.
- Setup: Configures and initializes the SSE service and its routes.

Workflow:
---------
1. Client establishes an SSE connection to a designated MCP endpoint.
2. The 'mcp_sse' service, via its 'Server' and 'Manager' components, initializes an MCP session.
3. MCP messages are processed by the 'mcp' module and then streamed to the client as SSE events.
4. The connection remains open for the duration of the MCP session, or until explicitly closed.

Usage Example:
--------------
# To integrate the MCP SSE service with a FastAPI application:
#
# 1. Ensure McpServerService is initialized and available (e.g., via get_mcpserver_service()).
# 2. In your main application setup (e.g., main.py or app.py):
#
# from fastapi import FastAPI
# from mcpo_simple_server.services.mcp_sse.setup import setup_mcp_sse, mcp_sse_lifespan
# from mcpo_simple_server.services.mcpserver import McpServerService # and its setup
#
# # Initialize McpServerService (example, actual init might be elsewhere)
# mcpserver_service = McpServerService()
# # mcpserver_service.initialize_components() # or similar setup call
#
# app = FastAPI(lifespan=mcp_sse_lifespan) # Integrate the lifespan
#
# # Mount the MCP SSE endpoint
# # This uses the default mount path "/api/v1/mcp_sse"
# setup_mcp_sse(app)
#
# # Now, clients can connect to ws://<your_server>/api/v1/mcp_sse to establish
# # an MCP session over Server-Sent Events.

Notes:
------
- This service is designed to be a direct replacement for the previous 'mcp_sse_transport'.
- It leverages the robust 'mcp' module for core protocol logic.

"""

from .setup import setup_mcp_sse

__all__ = ["setup_mcp_sse"]
