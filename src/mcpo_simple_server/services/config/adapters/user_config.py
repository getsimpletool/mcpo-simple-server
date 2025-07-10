from loguru import logger
from typing import Dict, Optional, TYPE_CHECKING
from abc import ABC
from mcpo_simple_server.services.config.models import UserConfigModel
if TYPE_CHECKING:
    from mcpo_simple_server.services.config import ConfigService
    from mcpo_simple_server.services.config.abstracts.storage_backend import StorageBackendAbstract


class UserConfigAdapter(ABC):
    """Compatibility adapter for existing code using config_service.users interface."""

    def __init__(self, parent: 'ConfigService'):
        self.parent = parent
        self._storage_backend: 'StorageBackendAbstract' = parent._storage_backend

    async def delete_config(self, username: str) -> bool:
        """Delete a user configuration."""
        try:
            result = await self._storage_backend.delete_user_config(username)
            return result
        except Exception as e:
            logger.error(f"Error deleting user '{username}': {str(e)}")
            return False

    async def get_config(self, username: str) -> Optional[UserConfigModel]:
        """Get user configuration by username."""
        user_config = await self._storage_backend.get_user_config(username)
        if user_config:
            return user_config
        return None

    async def save_config(self, user_data: UserConfigModel) -> bool:
        """Save user configuration."""
        try:
            await self._storage_backend.save_user_config(user_data)
            return True
        except Exception as e:
            logger.error(f"Error saving user config: {str(e)}")
            return False

    async def get_all_users_configs(self) -> Dict[str, UserConfigModel]:
        """Get all user configurations.

        Returns:
            Dictionary mapping usernames to user configuration data
        """
        try:
            user_models = await self._storage_backend.list_users()
            return {username: model for username, model in user_models.items()}
        except Exception as e:
            logger.error(f"Error getting all users: {str(e)}")
            return {}

    async def refresh_users_cache(self, username: Optional[str] = None) -> None:
        """Refresh the users cache. If username is provided, refresh only that user; otherwise, refresh all.

        Args:
            username (Optional[str]): Username to refresh cache for. If None, refresh all users.

        Notes:
            This method is depend on the storage backend implementation.
            Some storage backend may not support this method and will always pass None to the storage backend.
        """
        await self._storage_backend.clear_cache(username)
