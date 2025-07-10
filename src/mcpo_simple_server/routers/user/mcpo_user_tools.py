from typing import Dict, List, Any, Type
from fastapi import APIRouter, HTTPException, status
from loguru import logger
from mcpo_simple_server.services import get_mcpserver_service, get_config_service
from mcpo_simple_server.config import APP_VERSION


class MCPOUserToolsRouter:
    """
    OpenAPI schema generator for user-specific MCP tools.

    This class generates an OpenAPI schema for tools available to a specific user.
    It doesn't create actual endpoints, as invocation happens through v1_post_tool.py.
    """

    def __init__(self):
        """Initialize the tools schema generator."""
        self.mcpserver_service = None
        self.config_service = None
        # Create a router just for OpenAPI schema generation
        self.router = APIRouter()

        # Storage for tool metadata
        self.user_tools: Dict[str, Dict[str, Any]] = {}

    async def initialize(self):
        """
        Initialize by setting up services.
        """
        self.mcpserver_service = get_mcpserver_service()
        self.config_service = get_config_service()

        # Clear any existing tools
        self.user_tools = {}

    async def load_tools(self, username: str) -> Dict[str, Dict[str, Any]]:
        """
        Load tools dynamically from MCP servers.

        Args:
            username: Username of the user to load tools for

        Returns:
            Dictionary containing tool metadata for user-specific tools
        """
        if self.mcpserver_service is None:
            raise ValueError("MCP Server Service is not initialized")

        if self.config_service is None:
            raise ValueError("Config Service is not initialized")

        # Clear existing tools
        self.user_tools = {}

        user_config = await self.config_service.user_config.get_config(username)
        if user_config is None or user_config.mcpServers is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User config not found")
        user_config_mcpservers = user_config.mcpServers

        try:
            # Debug log the available mcpservers
            logger.info(f"🧮 Found {len(user_config_mcpservers)} mcpservers in user config")
            for mcpserver_name, config_mcpserver_model in user_config_mcpservers.items():
                mcpserver_id = mcpserver_name + "-" + username
                logger.info("-------------------------")
                icon = "🌐" if getattr(config_mcpserver_model, "mcpserver_type", None) == "public" else "🔒"
                logger.info(f"{icon} mcpServer '{mcpserver_id}': type={config_mcpserver_model.mcpserver_type}")
                if config_mcpserver_model.mcpserver_type != "private" or config_mcpserver_model.disabled:
                    # We only load private mcpserver/tools
                    # We only load enabled mcpservers
                    continue

                # Get mcpserver service model
                mcpserver_model = self.mcpserver_service.get_mcpserver(mcpserver_id)
                if mcpserver_model is None:
                    logger.error(f"mcpServer '{mcpserver_id}' not found in registry")
                    continue

                try:
                    # Try to get tools - first from cache, then by discovery if mcpserver is running
                    tools = []

                    # Check if there are cached tools in the model
                    if hasattr(mcpserver_model, 'tools') and mcpserver_model.tools:
                        tools = mcpserver_model.tools
                        logger.info(f"Found {len(tools)} cached tools for mcpserver '{mcpserver_name}'")
                    # If mcpserver is running, try to discover tools
                    elif mcpserver_model.status == "running" and mcpserver_model.process:
                        try:
                            logger.info(f"Discovering tools for mcpserver-id '{mcpserver_id}'")
                            tools = await self.mcpserver_service.discover_tools(mcpserver_id)
                            logger.info(f"Found {len(tools)} tools for mcpserver-id {mcpserver_id}")
                        except Exception as e:
                            logger.warning(f"Could not discover tools for mcpserver-id {mcpserver_id}: {e}")
                    else:
                        logger.info(f"mcpserver-id {mcpserver_id} is not running, using empty tools list")
                        # For mcpservers not running, we'll use an empty list and tools will be discovered later

                    # Filter tools based on blacklists (environment and global)
                    tools = self.mcpserver_service.tools.filter_tools(tools, config_mcpserver_model.tools_blacklist)

                    for tool in tools:
                        tool_name = tool.get("name", "")
                        logger.info(f"🛠️  tool {mcpserver_name} > {tool_name}")
                        # if not tool_name:
                        #    continue

                        # Store tool metadata
                        tool_metadata = {
                            "name": tool_name,
                            "description": tool.get("description", ""),
                            "inputSchema": tool.get("inputSchema", {}),
                            "mcpserver": mcpserver_id,
                            "mcpserver_name": mcpserver_name
                        }

                        self.user_tools[tool_name] = tool_metadata

                except Exception as e:
                    logger.error(f"Error loading tools from mcpserver {mcpserver_id}: {e}")
                    continue

            logger.info("-------------------------")
            logger.info(f"👤 Summary: user {username} has {len(self.user_tools)} tools")
            return self.user_tools

        except Exception as e:
            logger.error(f"Error loading tools for user {username}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to load tools: {str(e)}") from e

    def _get_field_type(self, type_str: str) -> Type:
        """
        Convert JSON Schema type to Python type.

        Args:
            type_str: JSON Schema type string

        Returns:
            Corresponding Python type
        """
        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": List[Any],
            "object": Dict[str, Any]
        }

        return type_mapping.get(type_str, Any)

    # This is main function used by router path
    async def get_user_openapi_schema(self, username: str) -> Dict[str, Any]:
        """
        Generate a streamlined OpenAPI schema for user-specific tools.

        Args:
            username: Username to filter tools for a specific user

        Returns:
            OpenAPI schema dictionary for user-specific tools
        """
        # Load tools for user if not already loaded or if they need to be refreshed
        if not self.user_tools:
            await self.load_tools(username)

        # Create a minimal schema that doesn't rely on components.schemas
        user_tools_schema = {
            "openapi": "3.0.0",
            "info": {
                "title": f"Private '{username}' MCP API Tools",
                "description": f"API for invoking MCP tools for user {username}",
                "version": APP_VERSION
            },
            "components": {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                        "description": "Enter your API key with the format: Bearer YOUR_API_KEY"
                    }
                }
            },
            "security": [{"bearerAuth": []}],
            "paths": {}
        }

        # Add each tool endpoint to the schema
        for tool_name, tool_metadata in self.user_tools.items():
            mcpserver_name = tool_metadata.get("mcpserver_name", "")
            description = tool_metadata.get("description", f"Tool: {tool_name}")
            input_schema = tool_metadata.get("inputSchema", {})

            # Create the path entry
            path = f"/api/v1/user/tool/{mcpserver_name}/{tool_name}"

            # Create the operation object
            operation = {
                "summary": f"Invoke {tool_name} from {mcpserver_name}",
                "description": description,
                "operationId": f"user_tool_{tool_name.replace('-', '_')}",
                "security": [{"bearerAuth": []}],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "additionalProperties": True
                                }
                            }
                        }
                    }
                }
            }

            # Add request body schema directly from input schema
            if input_schema:
                param_schema = {
                    "type": "object",
                    "title": f"{tool_name}Params"
                }

                # Add properties
                if "properties" in input_schema:
                    param_schema["properties"] = input_schema["properties"]

                # Add required fields
                if "required" in input_schema:
                    param_schema["required"] = input_schema["required"]

                # Add request body
                operation["requestBody"] = {
                    "content": {
                        "application/json": {
                            "schema": param_schema
                        }
                    },
                    "required": True
                }

            # Initialize the path item if it doesn't exist
            if path not in user_tools_schema["paths"]:
                user_tools_schema["paths"][path] = {}

            # Add the POST operation
            user_tools_schema["paths"][path]["post"] = operation

        logger.debug(f"Generated OpenAPI schema with {len(user_tools_schema['paths'])} paths")
        return user_tools_schema


# Create singleton instance
mcpo_user_tools_router = MCPOUserToolsRouter()


async def get_tools_router():
    """Get the initialized tools schema generator."""
    await mcpo_user_tools_router.initialize()
    return mcpo_user_tools_router


# Export the router for inclusion in the main app
# Note: This router doesn't actually have any endpoints, it's just used for OpenAPI schema generation
router = mcpo_user_tools_router.router
