"""
Tools configuration model.

This module defines the Pydantic model for tool filtering configuration.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

__all__ = ['ToolsConfigModel']


class ToolsConfigModel(BaseModel):
    """Configuration model for tool filtering."""
    blackList: Optional[List[str]] = Field(default_factory=list, description="List of blocked tools")
