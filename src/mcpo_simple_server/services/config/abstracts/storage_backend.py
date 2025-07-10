"""
Module/Package: StorageBackend - Abstract interface for configuration storage backends

High Level Concept:
-------------------
This module defines the abstract interface for storage backends used by the
configuration system. It provides a common API that all storage implementations
must follow, ensuring consistent behavior regardless of the underlying technology.

Architecture:
-------------
- StorageBackend: Abstract base class with methods for CRUD operations
- Method Contracts: Clear definitions of expected inputs and outputs

Workflow:
---------
1. Storage implementations inherit from StorageBackend
2. Configuration service interacts with storage through this interface
3. New storage technologies can be added by implementing this interface

Notes:
------
- All concrete storage implementations must implement all abstract methods
- This separation allows for easy switching between storage technologies
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List, Any

from mcpo_simple_server.services.config.models import GlobalConfigModel, UserConfigModel


class StorageBackendAbstract(ABC):
    """Abstract interface for configuration storage backends."""

    # --------------------------------------------------------------------------
    # Global Config
    # --------------------------------------------------------------------------
    @abstractmethod
    async def get_global_config(self) -> GlobalConfigModel:
        """Get the global configuration."""

    @abstractmethod
    async def save_global_config(self, config: GlobalConfigModel) -> None:
        """Save the global configuration."""

    # --------------------------------------------------------------------------
    # User Config
    # --------------------------------------------------------------------------
    @abstractmethod
    async def get_user_config(self, username: str) -> Optional[UserConfigModel]:
        """Get a user configuration."""

    @abstractmethod
    async def save_user_config(self, config: UserConfigModel) -> None:
        """Save a user configuration."""

    @abstractmethod
    async def delete_user_config(self, username: str) -> bool:
        """Delete a user configuration."""

    @abstractmethod
    async def list_users(self) -> Dict[str, UserConfigModel]:
        """List all user configurations."""

    @abstractmethod
    async def clear_cache(self, username: Optional[str] = None) -> None:
        """Clear the cache."""

    @abstractmethod
    async def close(self) -> None:
        """
        Close the storage backend.
        """

    # --------------------------------------------------------------------------
    # Tool Caches
    # --------------------------------------------------------------------------
    @abstractmethod
    async def get_all_tool_caches(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all tool caches from storage.
        """

    @abstractmethod
    async def write_tool_cache(self, mcpserver_name: str, cache: list[dict]) -> None:
        """
        Write the tool cache for a specific MCP server.
        Args:
            mcpserver_name: The MCP server name (used as file key)
            cache: List of tool dicts to store
        """

    @abstractmethod
    async def read_tool_cache(self, mcpserver_name: str) -> Optional[list[dict]]:
        """
        Read the tool cache for a specific MCP server.
        Args:
            mcpserver_name: The MCP server name (used as file key)
        Returns:
            List of tool dicts, or None if not found
        """

    @abstractmethod
    async def delete_tool_cache(self, mcpserver_name: str) -> None:
        """
        Delete the tool cache for a specific MCP server.
        Args:
            mcpserver_name: The MCP server name (used as file key)
        """
