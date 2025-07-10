"""
Module/Package: Storage - Storage backends for configuration data

High Level Concept:
-------------------
This module provides storage backends for the configuration system.
It serves as an abstraction layer for different storage technologies
like NoSQLite, TinyDB, Redis, MongoDB, etc.

Architecture:
-------------
- StorageBackendAbstract: Abstract base class defining the storage interface
- Concrete Implementations: Specific implementations for different storage technologies
- Caching Layer: From Abstract StorageBackend we dont care about caching, this needs to be handled by storage technology implementation level

Workflow:
---------
1. Configuration service initializes the appropriate storage backend
2. Storage backend handles CRUD operations for configuration data

Notes:
------
- All storage backends implement the same interface
- The current implementation uses: NoSQLite
- Future implementations may include: Redis, MongoDB, etc.
"""

# Import available storage backends
from mcpo_simple_server.services.config.storage.nosqlite_storage import NoSQLiteStorage
from mcpo_simple_server.services.config.storage.ddb_storage import DDBStorage

# Re-export concrete implementations
__all__ = ["NoSQLiteStorage", "DDBStorage"]
