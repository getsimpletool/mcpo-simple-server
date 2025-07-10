import types
from fastapi import HTTPException, status
from loguru import logger
from typing import Dict, Optional, Any
from mcpo_simple_server.config import CONFIG_STORAGE_PATH, CONFIG_STORAGE_TYPE
from mcpo_simple_server.services.config.storage import NoSQLiteStorage, DDBStorage
from mcpo_simple_server.services.config.abstracts.storage_backend import StorageBackendAbstract
from mcpo_simple_server.services.config.models import ConfigModel
from mcpo_simple_server.services.config.adapters.global_config import GlobalConfigAdapter
from mcpo_simple_server.services.config.adapters.user_config import UserConfigAdapter
from mcpo_simple_server.services.config.adapters.tools_cache import ToolsCacheAdapter


SELECTED_STORAGE_BACKEND: Optional[StorageBackendAbstract] = None


def _select_storage_backend(db_path: str) -> StorageBackendAbstract:
    """
    Select storage backend based on CONFIG_STORAGE_TYPE env var.

    Returns:
        StorageBackendAbstract: Our own storage backend instance
    """
    if CONFIG_STORAGE_TYPE == "ddb":
        return DDBStorage(db_path)
    if CONFIG_STORAGE_TYPE == "nosqlite":
        return NoSQLiteStorage(db_path)
    raise ValueError(f"Unknown storage type: {CONFIG_STORAGE_TYPE}")


# Rebuild ConfigResponse model to resolve forward references
ConfigModel.model_rebuild()


class ConfigService:
    """
    Configuration service that provides access to the application configuration.
    This is the main entry point for all configuration operations.
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """
        Initialize the ConfigService with DDBStorage backend.

        Args:
            options: Additional settings for the storage backend
        """
        logger.info("🚀 Storage Service: Initializing")
        global SELECTED_STORAGE_BACKEND

        # Configure DynamoDB storage path
        db_path = options.get("db_path", CONFIG_STORAGE_PATH) if options else CONFIG_STORAGE_PATH

        # Initialize the DDBStorage if not already initialized
        if SELECTED_STORAGE_BACKEND is None:
            SELECTED_STORAGE_BACKEND = _select_storage_backend(db_path)
            self._storage_backend: StorageBackendAbstract = SELECTED_STORAGE_BACKEND

        # Initialize adapters for configuration access
        self.global_config = GlobalConfigAdapter(self)
        self.user_config = UserConfigAdapter(self)
        self.tools_cache = ToolsCacheAdapter(self)

    async def get_config(self, username: Optional[str] = None) -> ConfigModel:
        """
        Get the configuration for the application with optional user-specific settings.

        Args:
            username: If provided, includes user-specific configuration

        Returns:
            ConfigResponse with global and user-specific settings
        """

        # Always get global config
        global_config = await self._storage_backend.get_global_config()

        # Get user config if username provided
        user_config = None
        if username:
            user_config = await self._storage_backend.get_user_config(username)

        # Create response object with save method implementation
        response = ConfigModel(
            global_config=global_config,
            user_config=user_config
        )

        # Expose tool cache operations via response
        response.tools_cache = await self.tools_cache.get_all_tool_caches()

        # Add dynamic save method
        async def save_config() -> ConfigModel:
            """Save the current configuration state."""

            # Save username for later use
            current_username = username

            # Save global config
            if self._storage_backend is not None:
                await self._storage_backend.save_global_config(response.global_config)

            # Save user config if present
            if response.user_config and self._storage_backend is not None:
                await self._storage_backend.save_user_config(response.user_config)

            # Create new response object without recursive get_config call
            new_response = ConfigModel(
                global_config=response.global_config,
                user_config=response.user_config
            )

            # Add save method to new response with username retention
            async def _dynamic_save_implementation(self) -> ConfigModel:
                return await self.get_config(current_username)

            # Assign save method to new object
            new_response.save = types.MethodType(_dynamic_save_implementation, new_response)
            return new_response

        # Implement save method for the response object
        response.save = types.MethodType(save_config, response)

        return response

    async def close(self):
        """
        Close the database connection.

        This method should be called when the service is no longer needed
        to properly release database resources.
        """
        if self._storage_backend is not None:
            try:
                await self._storage_backend.close()
                logger.debug("Closed storage connection")
            except Exception as e:
                logger.error(f"Error closing storage connection: {e}")


# -------------------------------------------------------------------------------------------------
# - Global config service
# -------------------------------------------------------------------------------------------------
CONFIG_SERVICE: Optional[ConfigService] = None   # pylint: disable=C0103


def set_config_service(config_srv: ConfigService) -> ConfigService:
    """Set the config service instance to be used by auth dependencies."""
    global CONFIG_SERVICE
    CONFIG_SERVICE = config_srv
    logger.info("🔧 Storage Service: Set Global CONFIG_SERVICE")
    return CONFIG_SERVICE


def get_config_service() -> ConfigService:
    if CONFIG_SERVICE is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Global config service not initialized"
        )
    return CONFIG_SERVICE
