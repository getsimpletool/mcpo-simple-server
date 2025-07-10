"""
Package/Module: MCP Streamable HTTP Integration - Native MCP protocol support

High Level Concept:
-------------------
This package provides integration with the Model Context Protocol (MCP) Streamable HTTP
transport layer. It enables bidirectional communication between clients and MCP servers
using the standard MCP protocol with HTTP streaming capabilities.

Architecture:
-------------
- MCP Session Manager for FastAPI integration
- Streamable HTTP transport for bidirectional communication
- Lifespan context management for proper session handling
- Router integration with existing FastAPI app

Workflow:
---------
1. Initialize MCP Session Manager during application startup
2. Register MCP routes with the FastAPI application
3. Handle client requests through the Streamable HTTP transport
4. Process MCP protocol messages and invoke appropriate tools

Usage Example:
--------------
>>> from mcpo_simple_server.services.mcp_streamable import setup_mcp_streamable
>>> # In your FastAPI app initialization
>>> setup_mcp_streamable(app)

Notes:
------
- This implementation uses the native MCP module's capabilities
- Maintains backward compatibility with existing API contracts
- Provides a clean upgrade path for future MCP updates
"""

# Import directly from the module files
from .setup import setup_mcp_streamable, get_session_manager

__all__ = ["setup_mcp_streamable", "get_session_manager"]
