"""
User configuration models.

This module defines the Pydantic models for user-specific configuration.
"""

from typing import Dict, List, Any
from pydantic import BaseModel, Field

from .mcpserver import McpServerConfigModel

__all__ = ['UserConfigModel', 'UserConfigPublicModel']


class UserConfigModel(BaseModel):
    """User-specific configuration model."""
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    hashed_password: str
    group: str = Field(default="user", pattern=r"^(users|admins)$")
    disabled: bool = Field(default=False, description="Whether the user account is disabled")
    api_keys: List[str] = Field(default_factory=list, description="User API keys for authentication")
    env: Dict[str, str] = Field(default_factory=dict, description="User-specific environment variables")
    mcpServers: Dict[str, McpServerConfigModel] = Field(default_factory=dict, description="User-specific MCP server configuration overrides")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User interface and behavioral preferences")


class UserConfigPublicModel(BaseModel):
    """User-specific configuration model for public responses (omits sensitive data)."""
    username: str
    group: str = Field(default="user", pattern=r"^(users|admins)$")
    disabled: bool = Field(default=False, description="Whether the user account is disabled")
    env: Dict[str, str] = Field(
        default_factory=dict,
        description="User-specific environment variables"
    )
    mcpServers: Dict[str, McpServerConfigModel] = Field(
        default_factory=dict,
        description="User-specific MCP server configuration overrides"
    )
    preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="User interface and behavioral preferences"
    )
