"""
Module/Package: DDBStorage - Configuration storage backend implementation using DictDataBase

High Level Concept:
-------------------
DDBStorage provides an implementation of the StorageBackend interface using
DictDataBase for storing global and user configurations. It stores data
in a file-based dictionary database, providing simple persistence.

Architecture:
-------------
- DDBStorage: StorageBackend implementation using DictDataBase
- Collections: 'config' for global configuration, 'users' for user configurations

Workflow:
---------
1. Initialize with database path
2. Load configuration data from the database
3. Cache frequently accessed data
4. Provide CRUD operations for configuration data

Notes:
------
- Uses DictDataBase for persistent storage
- Caching for performance optimization
- All collections are created on first access
"""
import threading
import os
import dictdatabase as DDB
from typing import Any, Dict, List, Optional
from loguru import logger
from mcpo_simple_server.services.config.models import GlobalConfigModel, UserConfigModel
from mcpo_simple_server.services.config.abstracts.storage_backend import StorageBackendAbstract


class DDBStorage(StorageBackendAbstract):
    """DictDataBase implementation of the storage backend."""

    async def write_tool_cache(self, mcpserver_name: str, cache: list[dict]) -> None:
        """
        Write the tool cache for a specific MCP server as a DDB file.
        """
        tools_cache_path = f"tools_cache/{mcpserver_name}"
        with self._lock:
            try:
                DDB.at(tools_cache_path).create(cache, force_overwrite=True)  # type: ignore
                logger.info(f"Tool cache saved for MCP server '{mcpserver_name}' at {tools_cache_path}")
            except Exception as e:
                logger.error(f"Error writing tool cache for '{mcpserver_name}': {e}")

    async def read_tool_cache(self, mcpserver_name: str) -> Optional[List[Dict[str, Any]]]:
        """
        Read the tool cache for a specific MCP server from a DDB file.
        """
        tools_cache_path = f"tools_cache/{mcpserver_name}"
        with self._lock:
            try:
                if not DDB.at(tools_cache_path).exists():  # type: ignore
                    logger.debug(f"Tool cache not found for MCP server '{mcpserver_name}' at {tools_cache_path}")
                    return None
                cache = DDB.at(tools_cache_path).read()  # type: ignore
                # Ensure we return a list of dicts as expected by the abstract class
                if isinstance(cache, list):
                    return cache
                # If we got a dict instead of a list, wrap it in a list
                if isinstance(cache, dict):
                    return [cache]
                logger.error(f"Unexpected cache format for MCP server '{mcpserver_name}': {type(cache)}")
                return None
            except Exception as e:
                logger.error(f"Error reading tool cache for '{mcpserver_name}': {e}")
                return None

    async def delete_tool_cache(self, mcpserver_name: str) -> None:
        """
        Delete the tool cache DDB file for a specific MCP server.
        """
        tools_cache_path = f"tools_cache/{mcpserver_name}"
        with self._lock:
            try:
                if DDB.at(tools_cache_path).exists():  # type: ignore
                    DDB.at(tools_cache_path).delete()  # type: ignore
                    logger.info(f"Tool cache deleted for MCP server '{mcpserver_name}' at {tools_cache_path}")
                else:
                    logger.debug(f"Tool cache not found for MCP server '{mcpserver_name}' at {tools_cache_path}")
            except Exception as e:
                logger.error(f"Error deleting tool cache for '{mcpserver_name}': {e}")

    def __init__(self, db_path: str):
        """
        Initialize the DDBStorage backend.

        Args:
            db_path: Path to the database file
        """
        # Use db_path itself as storage directory
        base_dir = db_path
        # ensure config directory exists
        os.makedirs(base_dir, exist_ok=True)
        DDB.config.storage_directory = base_dir
        self._global_config_cache: Optional[GlobalConfigModel] = None
        self._user_config_cache: Dict[str, UserConfigModel] = {}
        self._lock = threading.Lock()
        logger.info("📦 Selected DDBStorage backend.")
        logger.info(f"📦 Path: {base_dir}")

    async def get_global_config(self) -> GlobalConfigModel:
        # Read or initialize global config file
        path = "config"
        with self._lock:
            raw = DDB.at(path).read()  # type: ignore
        if raw:
            config = GlobalConfigModel(**raw)
        else:
            config = GlobalConfigModel()
            try:
                DDB.at(path).create(config.model_dump(), force_overwrite=True)  # type: ignore
            except Exception as e:
                logger.error(f"Error saving default global config: {e}")
        self._global_config_cache = config
        return config

    async def save_global_config(self, config: GlobalConfigModel) -> None:
        # Overwrite global config file
        path = "config"   # will become config.json
        try:
            DDB.at(path).create(config.model_dump(), force_overwrite=True)  # type: ignore
            logger.info("Saved global config")
            self._global_config_cache = config
        except Exception as e:
            logger.error(f"Error saving global config: {e}")

    async def get_user_config(self, username: str) -> Optional[UserConfigModel]:
        # Read user config from 'users/username'
        path = f"users/{username}"
        with self._lock:
            raw = DDB.at(path).read()  # type: ignore
        if raw:
            # MIGRATION: If api_keys is a list, convert to dict with default metadata
            if "api_keys" in raw and isinstance(raw["api_keys"], list):
                from mcpo_simple_server.services.config.models.user_config_model import ApiKeyMetadataModel
                migrated = {}
                for k in raw["api_keys"]:
                    migrated[k] = ApiKeyMetadataModel().model_dump()
                raw["api_keys"] = migrated
            user_config = UserConfigModel(**raw)
            self._user_config_cache[username] = user_config
            return user_config
        return None

    async def save_user_config(self, config: UserConfigModel) -> None:
        # Write user config to 'users/username'
        path = f"users/{config.username}"
        try:
            DDB.at(path).create(config.model_dump(), force_overwrite=True)  # type: ignore
            logger.info(f"Saved user config for {config.username}")
            self._user_config_cache[config.username] = config
        except Exception as e:
            logger.error(f"Error saving user config: {e}")

    async def delete_user_config(self, username: str) -> bool:
        # Delete user config file
        path = f"users/{username}"
        exists = DDB.at(path).exists()  # type: ignore
        try:
            DDB.at(path).delete()  # type: ignore
            if exists:
                self._user_config_cache.pop(username, None)
            return exists
        except Exception as e:
            logger.error(f"Error deleting user config: {e}")
            return False

    async def list_users(self) -> Dict[str, UserConfigModel]:
        # List all user configs in 'users' directory
        result: Dict[str, UserConfigModel] = {}

        try:
            # Use find_all to get all files in the users directory
            # This returns the file paths without the extension
            user_files = DDB.utils.find_all("users/*")  # type: ignore

            if not user_files:
                logger.warning("No user files found in the database")
                return {}

            logger.debug(f"Found {len(user_files)} user files in the database")

            # Process each user file
            for user_path in user_files:
                try:
                    # Extract username from the path
                    # The path will be in the format "users/username"
                    username = user_path.split("/")[-1]

                    # Load the user data
                    user_data = DDB.at(user_path).read()  # type: ignore
                    if user_data:
                        result[username] = UserConfigModel(**user_data)
                        # Cache the user config
                        self._user_config_cache[username] = result[username]
                    else:
                        logger.warning(f"Empty user data for {username} at {user_path}")
                except Exception as e:
                    logger.error(f"Error loading user config from {user_path}: {e}")
        except Exception as e:
            logger.error(f"Error listing users: {e}")

        return result

    async def clear_cache(self, username: Optional[str] = None) -> None:
        with self._lock:
            if username:
                self._user_config_cache.pop(username, None)
            else:
                self._global_config_cache = None
                self._user_config_cache.clear()

    async def close(self) -> None:
        """
        Close the database connection, ensuring data is saved.
        """
        try:
            # Persist all changes
            # No need to call save() explicitly with DDB.at() API
            logger.debug("DDBStorage database saved on close")
        except Exception as e:
            logger.error(f"Error closing DDBStorage: {e}")

    async def get_all_tool_caches(self) -> Dict[str, Any]:
        """
        Get all tool caches from storage.

        Returns:
            Dict mapping MCP server names to their tool caches
        """
        tools_caches: Dict[str, Any] = {}

        try:
            # List all entries in the tools_cache directory
            tools_cache_dir = "tools_cache"
            if not DDB.at(tools_cache_dir).exists():  # type: ignore
                return {}

            # Get all server names (keys in the tools_cache directory)
            server_names = DDB.at(tools_cache_dir).read().keys()  # type: ignore

            # Load each tool cache
            for server_name in server_names:
                cache = await self.read_tool_cache(server_name)
                if cache is not None:
                    tools_caches[server_name] = cache

            return tools_caches

        except Exception as e:
            logger.error(f"Error getting all tool caches: {e}")
            return {}
