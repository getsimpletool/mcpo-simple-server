from typing import Dict, Any, TYPE_CHECKING
from mcpo_simple_server.services.config.models import GlobalConfigModel
from loguru import logger
if TYPE_CHECKING:
    from mcpo_simple_server.services.config import ConfigService
    from mcpo_simple_server.services.config.abstracts.storage_backend import StorageBackendAbstract


class GlobalConfigAdapter:
    """Storage adapter for accessing configuration data."""

    def __init__(self, parent: 'ConfigService'):
        self.parent = parent
        self._storage_backend: 'StorageBackendAbstract' = parent._storage_backend

    async def dict(self) -> Dict[str, Any]:
        """Get global configuration as dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the global config.
            Returns an empty dict if no configuration is found.

        Raises:
            ValueError: If storage backend is not initialized
        """
        if self._storage_backend is None:
            raise ValueError("Storage backend is not initialized")

        global_config = await self._storage_backend.get_global_config()
        return global_config.model_dump() if global_config else {}

    async def get_config(self) -> GlobalConfigModel:
        """Get the global configuration model.

        Returns:
            GlobalConfigModel: The global configuration model.
            Returns a new empty GlobalConfigModel if no configuration is found.

        Raises:
            ValueError: If storage backend is not initialized
        """
        if self._storage_backend is None:
            raise ValueError("Storage backend is not initialized")

        global_config = await self._storage_backend.get_global_config()
        return global_config or GlobalConfigModel()

    async def save_config(self, global_data: GlobalConfigModel) -> bool:
        """Save global configuration."""
        try:
            await self._storage_backend.save_global_config(global_data)
            return True
        except Exception as e:
            logger.error(f"Error saving global config: {str(e)}")
            return False
