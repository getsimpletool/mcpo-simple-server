"""
Configuration response model.

This module defines the Pydantic model for configuration responses.
"""

from typing import Dict, Optional, Any
from pydantic import BaseModel, Field
from .tools_config_model import ToolsConfigModel
from .user_config_model import UserConfigModel


class GlobalConfigModel(BaseModel):
    """Global configuration model with server-wide settings."""
    tools: ToolsConfigModel = Field(
        default_factory=ToolsConfigModel,
        description="Global tool filtering configuration"
    )


class ConfigModel(BaseModel):
    """
    Combined configuration object returned by the get_config function.
    Contains both global and user-specific configurations.
    """
    global_config: GlobalConfigModel
    user_config: Optional[UserConfigModel] = None
    tools_cache: Optional[Dict[str, Any]] = None

    class Config:
        # Allow arbitrary attributes to dynamically assign the save method
        arbitrary_types_allowed = True
        extra = "allow"

    async def save(self, clear_cache: bool = True) -> "ConfigModel":
        """
        Save the current configuration state.

        Args:
            clear_cache: Whether to clear the cache after saving

        Returns:
            Updated ConfigModel object with fresh data
        """
        return self
