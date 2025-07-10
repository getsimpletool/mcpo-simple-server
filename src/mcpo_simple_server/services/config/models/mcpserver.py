"""
MCP Server configuration model.

This module defines the Pydantic model for MCP server instance configuration.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

__all__ = ['McpServerConfigModel', 'McpServersListResponse']


class McpServerConfigModel(BaseModel):
    """Configuration for a single MCP server instance."""
    command: str
    args: Optional[List[str]] = Field(default_factory=list)
    env: Optional[Dict[str, str]] = Field(default_factory=dict)
    description: Optional[str] = None
    mcpserver_type: Optional[str] = Field("private", description="MCP server type: 'public' or 'private'")
    tools_blacklist: Optional[List[str]] = Field(default_factory=list, description="List of blocked tool names")
    transport: Optional[str] = Field(default="stdio")
    disabled: Optional[bool] = False

    class Config:
        extra = "allow"
        validate_by_name = True


class McpServersListResponse(BaseModel):
    mcpServers: Dict[str, McpServerConfigModel]
