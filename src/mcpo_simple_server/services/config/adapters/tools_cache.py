from loguru import logger
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from abc import ABC
if TYPE_CHECKING:
    from mcpo_simple_server.services.config import ConfigService
    from mcpo_simple_server.services.config.abstracts.storage_backend import StorageBackendAbstract


class ToolsCacheAdapter(ABC):
    """Adapter for tool cache operations via config service."""

    def __init__(self, parent: 'ConfigService') -> None:
        self.parent = parent
        self._storage_backend: 'StorageBackendAbstract' = parent._storage_backend

    async def get_all_tool_caches(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all tool caches from storage."""
        try:
            return await self._storage_backend.get_all_tool_caches()
        except Exception as e:
            logger.error(f"Failed to get all tool caches: {e}")
            return {}

    async def write_tool_cache(self, mcpserver_id: str, cache: List[Dict[str, Any]]) -> None:
        """Write the tool cache for a specific MCP server.

        Args:
            mcpserver_id: The MCP server ID (used as file key)
            cache: List of tool dicts to store
        """
        try:
            await self._storage_backend.write_tool_cache(mcpserver_id, cache)
        except Exception as e:
            logger.error(f"Failed to write tool cache for {mcpserver_id}: {e}")
            raise

    async def get_tool_cache(self, mcpserver_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get the tool cache for a specific MCP server.

        Args:
            mcpserver_id: The MCP server ID (used as file key)
        Returns:
            List of tool dicts, or None if not found
        """
        try:
            return await self._storage_backend.read_tool_cache(mcpserver_id)
        except Exception as e:
            logger.error(f"Failed to read tool cache for {mcpserver_id}: {e}")
            return None

    async def delete_tool_cache(self, mcpserver_id: str) -> None:
        """Delete the tool cache for a specific MCP server.

        Args:
            mcpserver_id: The MCP server ID (used as file key)
        """
        try:
            await self._storage_backend.delete_tool_cache(mcpserver_id)
        except Exception as e:
            logger.error(f"Failed to delete tool cache for {mcpserver_id}: {e}")
            raise
