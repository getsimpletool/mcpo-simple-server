"""
MCP Core Logic - Core MCP Protocol implementation utilities

High Level Concept:
    Provides core functionality for generating and processing MCP protocol messages,
    ensuring protocol compliance and centralized handling of MCP-specific logic.

Architecture:
    - json_response: Generates MCP-compliant JSON-RPC responses
    - tools_handler: Manages tools-related MCP operations

Workflow:
    Used by various transport layers (HTTP, SSE, WebSockets) to generate
    standardized responses while maintaining protocol compliance.

Notes:
    This module centralizes all MCP protocol-specific operations to ensure
    consistency across different transport mechanisms.
"""

from .list_tools import mcp_list_tools
from .call_tool import mcp_call_tool

__all__ = [
    "mcp_list_tools",
    "mcp_call_tool"
]
