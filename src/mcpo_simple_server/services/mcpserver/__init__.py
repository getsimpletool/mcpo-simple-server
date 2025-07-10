"""
Package/Module: MCP Server Manager - Core service for managing MCP servers

High Level Concept:
-------------------
This module provides a unified service for managing MCP servers, including
process management, tool invocation, and user-specific server instances.
The service uses a modular architecture with specialized components.

Architecture:
-------------
1. Controller: Orchestrates operations between components
2. ProcessManager: Manages server processes (starting, stopping, monitoring)
3. ToolsHandler: Handles tool discovery, validation and invocation
4. Metadata: Manages metadata about servers and interactions
5. Admin: Provides administrative capabilities

McpServer Identification Strategy:
----------------------------------
- Mcpservers: Identified by format mcpserver_id = "<mcpserver_name>-<username>" (e.g., "time-donald")
- All operations requiring mcpserver identification should use `mcpserver_id`

Workflow:
---------
1. Services initialize and register with the main service
2. Operations flow from routes through the McpServerService
3. Controller orchestrates operations between specialized components
4. Components maintain consistency with persistent configuration

Notes:
------
- All persistent configuration is handled through the `services.config` module
- User mcpservers are identified by combining username and mcpserver name as `mcpserver_id`
- Methods accept `mcpserver_name` and `username` parameters for clear identification
"""

from .service import (McpServerService,
                      MCPSERVER_SERVICE,
                      get_mcpserver_service,
                      set_mcpserver_service)

__all__ = [
    "McpServerService",
    "MCPSERVER_SERVICE",
    "get_mcpserver_service",
    "set_mcpserver_service"
]
