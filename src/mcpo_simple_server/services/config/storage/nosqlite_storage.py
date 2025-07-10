"""
Module/Package: NoSQLiteStorage - Configuration storage backend implementation using NoSQLite

High Level Concept:
-------------------
NoSQLiteStorage provides an implementation of the StorageBackend interface using
the NoSQLite module for storing global and user configurations.
It stores data in a single SQLite file, providing better performance and reliability.

Architecture:
-------------
- NoSQLiteStorage: StorageBackend implementation using NoSQLite
- Collections: 'global' for global configuration, 'users' for user configurations

Workflow:
---------
1. Initialize with database path
2. Load configuration data from SQLite
3. Cache frequently accessed data
4. Provide CRUD operations for configuration data

Notes:
------
- Uses NoSQLite for persistent storage
- Implements caching for performance optimization
- Thread-safe operations through appropriate locking
- All configuration is stored in a single SQLite file
- Global config is stored in 'global' collection with 'global_config' as ID
- User configs are stored in 'users' collection with <username> as ID
"""

import os
import threading
from typing import Dict, Optional, Any

from loguru import logger
import nosqlite

from mcpo_simple_server.services.config.models import GlobalConfigModel, UserConfigModel
from mcpo_simple_server.services.config.abstracts.storage_backend import StorageBackendAbstract


import json


class NoSQLiteStorage(StorageBackendAbstract):
    """NoSQLite implementation of the storage backend."""

    async def write_tool_cache(self, mcpserver_name: str, cache: list[dict]) -> None:
        """
        Write the tool cache for a specific MCP server to a JSON file.
        """
        tools_cache_dir = os.path.join(os.path.dirname(self.db_path), "tools_cache")
        os.makedirs(tools_cache_dir, exist_ok=True)
        cache_file = os.path.join(tools_cache_dir, f"{mcpserver_name}.json")
        with self._lock:
            try:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache, f)
                logger.info(f"Tool cache saved for MCP server '{mcpserver_name}' at {cache_file}")
            except Exception as e:
                logger.error(f"Error writing tool cache for '{mcpserver_name}': {e}")

    async def read_tool_cache(self, mcpserver_name: str) -> list[dict] | None:
        """
        Read the tool cache for a specific MCP server from a JSON file.
        """
        tools_cache_dir = os.path.join(os.path.dirname(self.db_path), "tools_cache")
        cache_file = os.path.join(tools_cache_dir, f"{mcpserver_name}.json")
        with self._lock:
            try:
                if not os.path.exists(cache_file):
                    logger.debug(f"Tool cache file not found for MCP server '{mcpserver_name}' at {cache_file}")
                    return None
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                logger.info(f"Tool cache loaded for MCP server '{mcpserver_name}' from {cache_file}")
                return cache
            except Exception as e:
                logger.error(f"Error reading tool cache for '{mcpserver_name}': {e}")
                return None

    async def delete_tool_cache(self, mcpserver_name: str) -> None:
        """
        Delete the tool cache file for a specific MCP server.
        """
        tools_cache_dir = os.path.join(os.path.dirname(self.db_path), "tools_cache")
        cache_file = os.path.join(tools_cache_dir, f"{mcpserver_name}.json")
        with self._lock:
            try:
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                    logger.info(f"Tool cache deleted for MCP server '{mcpserver_name}' at {cache_file}")
                else:
                    logger.debug(f"Tool cache file not found for MCP server '{mcpserver_name}' at {cache_file}")
            except Exception as e:
                logger.error(f"Error deleting tool cache for '{mcpserver_name}': {e}")

    def __init__(self, db_path: str):
        """
        Initialize the NoSQLite storage backend.

        Args:
            db_path: Path to the SQLite database file
        """
        # Initialize caches
        self._global_config_cache = None
        self._user_config_cache: Dict[str, UserConfigModel] = {}
        self.config_file = "config.db"

        # Lock for thread safety
        self._lock = threading.Lock()

        # Prepare database file path
        self.db_path = os.path.join(db_path, self.config_file)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Initialize database
        self.store = nosqlite.Connection(self.db_path)

        logger.info("📦 Selected NoSQLiteStorage backend.")
        logger.info(f"📦 Path: {self.db_path}")

    async def get_global_config(self) -> GlobalConfigModel:
        """
        Get the global configuration.

        Returns:
            GlobalConfigModel: The global configuration
        """
        # Najpierw sprawdź cache bez blokady
        if self._global_config_cache is not None:
            return self._global_config_cache

        config_to_save = None

        # Zamknij blok z lockiem przed wywołaniem asynchronicznej metody
        with self._lock:
            # Sprawdź jeszcze raz cache po zdobyciu locka
            if self._global_config_cache is not None:
                return self._global_config_cache

            # Cache miss, load from DB
            if self.store is None:
                logger.error("Database connection is not available")
                return GlobalConfigModel()

            global_collection = self.store['global']
            global_doc = global_collection.find_one({"id": "global_config"})

            if global_doc:
                # Remove _id field which is used internally by NoSQLite
                if "_id" in global_doc:
                    del global_doc["_id"]
                self._global_config_cache = GlobalConfigModel(**global_doc)
            else:
                # Initialize with defaults if not exists
                self._global_config_cache = GlobalConfigModel()
                # Przygotuj konfigurację do zapisania, ale zapisz ją poza blockiem with
                config_to_save = self._global_config_cache

        # Jeśli potrzebujemy zapisać domyślną konfigurację, rób to poza lockiem
        if config_to_save is not None:
            try:
                await self.save_global_config(config_to_save)
            except Exception as e:
                logger.error(f"Error saving default global config: {e}")

        return self._global_config_cache

    async def save_global_config(self, config: GlobalConfigModel) -> None:
        """
        Save the global configuration.

        Args:
            config: The global configuration to save
        """
        with self._lock:
            # Convert to dict
            config_dict = config.model_dump()

            try:
                # Save configuration to database
                if self.store is None:
                    logger.error("Database connection is not available")
                    return

                global_collection = self.store['global']

                # NoSQLite uses id not _id, so we need to handle this
                if "_id" in config_dict:
                    del config_dict["_id"]

                # Find existing document
                existing = global_collection.find_one({"id": "global_config"})

                if existing:
                    # Update existing document
                    config_dict["id"] = "global_config"
                    # Jeśli dokument istnieje, musimy zachować jego _id do aktualizacji
                    if "_id" in existing:
                        config_dict["_id"] = existing["_id"]
                    global_collection.update(config_dict)
                else:
                    # Insert new document
                    config_dict["id"] = "global_config"
                    global_collection.insert(config_dict)

                logger.info(f"Saved global config to {self.db_path}")

                self._global_config_cache = config
            except Exception as e:
                logger.error(f"Error saving global config: {e}")

    async def get_user_config(self, username: str) -> Optional[UserConfigModel]:
        """
        Get a user configuration by username.

        Args:
            username: The username to get configuration for

        Returns:
            UserConfigModel or None: The user configuration if found
        """
        with self._lock:
            if username in self._user_config_cache:
                return self._user_config_cache[username]

            # Cache miss, load from DB
            if self.store is None:
                logger.error("Database connection is not available")
                return None

            users_collection = self.store['users']
            user_doc = users_collection.find_one({"username": username})

            if user_doc:
                # Remove _id field which is used internally by NoSQLite
                if "_id" in user_doc:
                    del user_doc["_id"]
                user_config = UserConfigModel(**user_doc)
                self._user_config_cache[username] = user_config
                logger.debug(f"Loaded user config for {username} from {self.db_path}")
                return user_config

            return None

    async def save_user_config(self, config: UserConfigModel) -> None:
        """
        Save a user configuration.

        Args:
            config: The user configuration to save
        """
        with self._lock:
            username = config.username
            config_dict = config.model_dump()

            try:
                # Save configuration to database
                if self.store is None:
                    logger.error("Database connection is not available")
                    return

                users_collection = self.store['users']

                # Find existing document
                existing = users_collection.find_one({"username": username})

                if existing:
                    # Update existing document
                    # Jeśli dokument istnieje, musimy zachować jego _id do aktualizacji
                    if "_id" in existing:
                        config_dict["_id"] = existing["_id"]
                    users_collection.update(config_dict)
                else:
                    # Insert new document
                    users_collection.insert(config_dict)

                logger.info(f"Saved user config for {username} to {self.db_path}")

                # Update cache
                self._user_config_cache[username] = config
            except Exception as e:
                logger.error(f"Error saving user config for {username}: {e}")

    async def delete_user_config(self, username: str) -> bool:
        """
        Delete a user configuration.

        Args:
            username: The username to delete configuration for

        Returns:
            bool: True if deleted, False if not found
        """
        with self._lock:
            try:
                # Delete configuration from database
                if self.store is None:
                    logger.error("Database connection is not available")
                    return False

                users_collection = self.store['users']
                user_doc = users_collection.find_one({"username": username})

                deleted_count = 0
                if user_doc:
                    users_collection.remove(user_doc)
                    deleted_count = 1

                if deleted_count > 0:
                    logger.info(f"Deleted user config for {username} from {self.db_path}")

                    # Remove from cache
                    if username in self._user_config_cache:
                        del self._user_config_cache[username]

                    return True

                return False
            except Exception as e:
                logger.error(f"Error deleting user config for {username}: {e}")
                return False

    async def list_users(self) -> Dict[str, UserConfigModel]:
        """
        List all user configurations.

        Returns:
            Dict[str, UserConfigModel]: Dictionary of username to user configuration
        """
        with self._lock:
            users = {}

            try:
                # Get all user configurations
                if self.store is None:
                    logger.error("Database connection is not available")
                    return {}

                users_collection = self.store['users']
                user_docs = list(users_collection.find())

                for user_doc in user_docs:
                    # Remove _id field which is used internally by NoSQLite
                    if "_id" in user_doc:
                        del user_doc["_id"]

                    # Create UserConfigModel
                    user_config = UserConfigModel(**user_doc)
                    users[user_config.username] = user_config

                    # Update cache
                    self._user_config_cache[user_config.username] = user_config
            except Exception as e:
                logger.error(f"Error listing users: {e}")

            return users

    async def clear_cache(self, username: Optional[str] = None) -> None:
        """
        Clear the cache.

        Args:
            username: If provided, only clear cache for this user
        """
        with self._lock:
            if username:
                if username in self._user_config_cache:
                    del self._user_config_cache[username]
                    logger.debug(f"Cleared cache for user {username}")
            else:
                self._global_config_cache = None
                self._user_config_cache = {}
                logger.debug("Cleared all configuration caches")

    async def close(self) -> None:
        """
        Close the database connection.

        This method should be called when the storage is no longer needed
        to properly release database resources.
        """
        if self.store is not None:
            try:
                self.store.close()
                logger.debug("Closed NoSQLite storage connection")
            except Exception as e:
                logger.error(f"Error closing NoSQLite storage: {e}")

    async def get_all_tool_caches(self) -> Dict[str, Any]:
        """
        Get all tool caches from storage.

        Returns:
            Dict mapping MCP server names to their tool caches
        """
        tools_cache_dir = os.path.join(os.path.dirname(self.db_path), "tools_cache")
        if not os.path.exists(tools_cache_dir):
            return {}

        result: Dict[str, Any] = {}

        try:
            # Get all JSON files in the tools_cache directory
            for filename in os.listdir(tools_cache_dir):
                if filename.endswith('.json'):
                    server_name = os.path.splitext(filename)[0]
                    cache = await self.read_tool_cache(server_name)
                    if cache is not None:
                        result[server_name] = cache

            return result

        except Exception as e:
            logger.error(f"Error getting all tool caches: {e}")
            return {}
