"""
MCP Models - Pydantic models for MCP protocol

High Level Concept:
    Provides Pydantic models for MCP protocol messages, ensuring proper
    validation and documentation of the protocol structures.

Architecture:
    - Request models: Define the structure of incoming MCP requests
    - Response models: Define the structure of outgoing MCP responses
    - Tool models: Define the structure of MCP tools and their parameters

Workflow:
    Models are used throughout the application to validate and structure
    MCP protocol messages for consistent handling.

Notes:
    These models correspond to the MCP protocol specification and should
    be kept in sync with the protocol version in use.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class MCPTool(BaseModel):
    """Model representing an MCP Tool"""
    name: str = Field(..., description="Unique name of the tool")
    description: str = Field(..., description="Description of what the tool does")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters schema for the tool")
    mcpserver: Optional[str] = Field(None, description="ID of the server providing this tool")


class MCPListToolsResult(BaseModel):
    """Result model for list_tools method"""
    mcp: str = Field(..., description="MCP protocol version")
    tools: List[MCPTool] = Field(default_factory=list, description="List of available tools")


class MCPJsonRpcResponse(BaseModel):
    """JSON-RPC 2.0 response model for MCP"""
    jsonrpc: str = Field("2.0", description="JSON-RPC version, always 2.0")
    id: str = Field(..., description="Request ID that this is responding to")
    result: Optional[MCPListToolsResult] = Field(None, description="Result object if successful")
    error: Optional[Dict[str, Any]] = Field(None, description="Error object if there was an error")

    class Config:
        validate_assignment = True


class MCPErrorResponse(BaseModel):
    """JSON-RPC 2.0 error response model for MCP"""
    jsonrpc: str = Field("2.0", description="JSON-RPC version, always 2.0")
    id: str = Field(..., description="Request ID that this is responding to")
    error: Dict[str, Any] = Field(..., description="Error details")
