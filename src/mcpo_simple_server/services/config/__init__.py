"""
Module/Package: ConfigService - Configuration management system for the MCPoSimpleServer

High Level Concept:
-------------------
The ConfigService provides a unified, modular system for managing application configuration
with distinct global and user-specific settings, along with tool cache management.
It serves as the central configuration repository for the MCPoSimpleServer, handling
configuration storage, retrieval, validation, and tool cache operations through a clean,
type-safe interface built on Pydantic models.

Architecture:
-------------
- Core Components:
  - ConfigService: Main entry point that orchestrates configuration access
  - Storage Backends: Pluggable storage implementations (DDBStorage with DictDatabase)
  - Pydantic Models: Type-safe schema definitions for all configuration entities
  - Tools Cache: Persistent storage for MCP server tool configurations

- Configuration Structure:
  - Global Config: Server-wide settings (tools blacklist)
  - User Config: User-specific settings (credentials, preferences, api_keys, env vars, mcpServer)
  - Tool Cache: Per-MCP server tool configurations and metadata

Workflow:
---------
1. Application requests configuration via get_config(username) function
2. System loads appropriate configuration data:
   - Global configuration data always loaded
   - User-specific configuration loaded when username is provided
3. Data is validated against Pydantic models ensuring type safety
4. Configuration objects are returned with separated global/user sections
5. Changes to configuration are persisted through the storage backend
6. Tool cache operations are handled through the ToolsCacheAdapter

Usage Example:
--------------
>>> from mcpo_simple_server.services.config import get_config
>>> 
>>> # Get global configuration only
>>> global_config = get_config(None)
>>> print(global_config.global_config.mcpServers)
>>>
>>> # Get combined configuration for a specific user
>>> user_config = get_config("alice")
>>> print(user_config.global_config.mcpServers)  # Access global section
>>> print(user_config.user_config.api_keys)      # Access user section
>>>
>>> # Update user configuration
>>> user_config.user_config.disabled = True
>>> updated_config = user_config.save()  # Save changes and get updated configuration
>>>
>>> # Access tool caches
>>> tool_caches = user_config.tools_cache
>>> print(tool_caches)  # Dictionary mapping MCP server names to their tool configurations

Notes:
------
- All configuration models are based on Pydantic BaseModel for validation
"""
from .service import (ConfigService,
                      CONFIG_SERVICE,
                      set_config_service,
                      get_config_service)
__all__ = [
    "ConfigService",
    "CONFIG_SERVICE",
    "set_config_service",
    "get_config_service"
]
