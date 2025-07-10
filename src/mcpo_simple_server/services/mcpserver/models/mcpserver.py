"""
Package/Module: McpServerModel - Core data model for MCP server configuration
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
import datetime
import subprocess
import asyncio


class McpServerModel(BaseModel):
    """
    Unified model for MCP server configuration.
    This model is used for both global and user-specific servers.
    """
    name: str = Field(..., description="The name of the MCP server")
    command: str = Field(..., description="The command to run the server")
    args: List[str] = Field(default_factory=list, description="Command line arguments")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    description: Optional[str] = Field(None, description="Server description")
    username: str = Field(..., description="MCPServer owner username")
    mcpserver_type: str = Field("private", alias="type", description="MCP server type: 'public' or 'private'")
    status: str = Field("configured", description="Current server status")
    tools: List[Dict[str, Any]] = Field(default_factory=list, description="Available tools")
    tools_blacklist: Optional[List[str]] = Field(default=None, description="List of blocked tool names")
    disabled: bool = Field(False, description="Whether the server is disabled")
    pid: Optional[int] = Field(None, description="Process ID of the running server instance")
    start_time: Optional[datetime.datetime] = Field(None, description="Server start time")
    last_activity: Optional[datetime.datetime] = Field(None, description="Last activity time of the server")
    process: Optional[Any] = Field(None, description="Process object of the running server instance")

    class Config:
        """Pydantic model configuration."""
        extra = "allow"  # Allow extra fields for backward compatibility
        arbitrary_types_allowed = True  # Allow subprocess.Popen as a field type
        populate_by_name = True  # Allow both field names and aliases to be used

    @validator('process', pre=True)
    def validate_process(cls, v: Any) -> Any:
        if v is not None and not (isinstance(v, subprocess.Popen) or isinstance(v, asyncio.subprocess.Process)):
            raise ValueError('process must be a subprocess.Popen or asyncio.subprocess.Process instance')
        return v


class McpServersListResponse(BaseModel):
    mcpServers: Dict[str, McpServerModel]
