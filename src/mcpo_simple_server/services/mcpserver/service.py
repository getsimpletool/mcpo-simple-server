from typing import Optional, Dict, TYPE_CHECKING
from fastapi import HTTPException, status
from loguru import logger
from mcpo_simple_server.config import TOOLS_BLACKLIST
from mcpo_simple_server.services.mcpserver.controller import McpServerController
from mcpo_simple_server.services.mcpserver.process_manager import McpServerProcessManager
from mcpo_simple_server.services.mcpserver.tools import McpServerToolsService
from mcpo_simple_server.services.mcpserver.admin import McpServerAdminManager
from mcpo_simple_server.services.mcpserver.models.mcpserver import McpServerModel
from mcpo_simple_server.services.config import get_config_service
if TYPE_CHECKING:
    from mcpo_simple_server.services.config import ConfigService


class McpServerService:
    """
    Unified MCP Server Manager that provides all functionality for managing MCP servers.

    This class serves as the main entry point for MCP server operations and delegates
    to specialized components for specific responsibilities:

    - Controller (McpServerController): Core server lifecycle operations
      - add_mcpserver: Register a new MCP server
      - delete_mcpserver: Remove an MCP server
      - restart_mcpserver: Restart a server with latest config
      - list_mcpservers: Get all registered servers

    - Process Manager (McpServerProcessManager): Process management
      - start_mcpserver: Start a server process
      - stop_mcpserver: Stop a running server process

    - Tools Service (McpServerToolsService): Tool management
      - invoke_tool: Execute a tool on a server
      - discover_tools: Find available tools
      - get_tool_metadata: Get metadata for a specific tool
      - list_all_tools: List all available tools across servers

    - Admin Manager (McpServerAdminManager): Administrative operations
      - load_all_servers: Load all server configurations
      - start_all_servers: Start all configured servers
      - stop_all_servers: Stop all running servers
      - cleanup_idle_servers: Clean up inactive servers
      - update_global_blacklist: Update tool blacklist

    The service maintains shared state and coordinates between these components
    while providing a clean, unified API for consumers.
    """

    def __init__(self):
        # Keep information and status of mcpServers in memory
        logger.info("🚀 MCP Server Service: Initializing")
        self._mcpservers: Dict[str, McpServerModel] = {}        # {mcpserver_id: McpServerModel}  <- this is controller database
        self.config_service: Optional['ConfigService'] = None
        self.env_blacklist_tools = TOOLS_BLACKLIST or []
        self.global_blacklist_tools = []

        # Main Subservices
        self.controller = McpServerController(self)
        self.process_manager = McpServerProcessManager(self)
        self.tools = McpServerToolsService(self)
        self.admin = McpServerAdminManager(self)

        # Delegate controller methods
        self.add_mcpserver = self.controller.add_mcpserver
        self.delete_mcpserver = self.controller.delete_mcpserver
        self.restart_mcpserver = self.controller.restart_mcpserver
        self.list_mcpservers = self.controller.list_mcpservers

        # Delegate process manager methods
        self.start_mcpserver = self.process_manager.start_mcpserver
        self.stop_mcpserver = self.process_manager.stop_mcpserver

        # Delegate tools handler methods
        self.invoke_tool = self.tools.invoke_tool
        self.discover_tools = self.tools.discover_tools
        self.list_all_tools = self.tools.list_all_tools
        self.get_tools = self.tools.get_tools

        # Delegate admin methods
        self.load_all_mcpservers = self.admin.load_all_mcpservers
        self.start_all_mcpservers = self.admin.start_all_mcpservers
        self.stop_all_mcpservers = self.admin.stop_all_mcpservers
        self.cleanup_idle_mcpservers = self.admin.cleanup_idle_mcpservers
        self.update_global_blacklist = self.admin.update_global_blacklist

    async def load_blacklist_tools(self):
        """
        Load tool blacklist configuration from environment and global config on start.
        """
        self.config_service = get_config_service()
        config = await self.config_service.get_config()
        self.global_blacklist_tools = config.global_config.tools.blackList or []
        logger.info(f"🔧 TOOLS BLACKLIST (ENV): {', '.join(self.env_blacklist_tools)}")
        logger.info(f"🔧 TOOLS BLACKLIST (CONFIG): {', '.join(self.global_blacklist_tools)}")

    def get_mcpserver(self, mcpserver_id: str) -> Optional[McpServerModel]:
        return self._mcpservers.get(mcpserver_id)


MCPSERVER_SERVICE: Optional[McpServerService] = None


def set_mcpserver_service(mcpserver_srv: McpServerService) -> McpServerService:
    """Set the mcpserver service instance to be used by auth dependencies."""
    global MCPSERVER_SERVICE
    MCPSERVER_SERVICE = mcpserver_srv
    logger.info("🔧 MCP Server Service: Set Global MCPSERVER_SERVICE")
    return MCPSERVER_SERVICE


def get_mcpserver_service() -> McpServerService:
    if MCPSERVER_SERVICE is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Global mcpserver service not initialized"
        )
    return MCPSERVER_SERVICE
