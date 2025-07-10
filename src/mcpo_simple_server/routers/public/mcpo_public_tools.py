from typing import Dict, List, Any, Type
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import create_model, Field
from loguru import logger
from mcpo_simple_server.services.mcpserver import McpServerService
from mcpo_simple_server.services import get_mcpserver_service
from mcpo_simple_server.config import APP_VERSION
from mcpo_simple_server.utils.tools.process_tool_response import process_tool_response


class MCPOPublicToolsRouter:
    """
    Dynamic router that creates endpoints for each available tool.

    This class creates a FastAPI router with dynamically generated endpoints
    for each tool available in the server. Each tool gets its own dedicated
    endpoint with proper documentation based on the tool's metadata.
    """

    def __init__(self):
        """Initialize the tools router."""
        self.router = APIRouter(
            prefix="/api/v1/public/tool",
            tags=["Public Tools"],
            responses={404: {"description": "Tool not found"}},
        )
        self.tools_metadata = {}
        self.initialized = False
        self._dynamic_route_names = set()  # Track dynamic endpoint names

    async def initialize(self):
        """
        Initialize the router by fetching tools and creating endpoints.

        Args:
            mcpserver_manager: The server manager instance to fetch tools from
        """
        mcpserver_service = get_mcpserver_service()

        # Remove previously added dynamic tool endpoints
        if self._dynamic_route_names:
            new_routes = []
            for route in self.router.routes:
                if getattr(route, 'name', None) not in self._dynamic_route_names:
                    new_routes.append(route)
            self.router.routes = new_routes
            self._dynamic_route_names.clear()
        self.initialized = False

        # Fetch all available tools
        tools = await mcpserver_service.tools.list_all_tools()

        # Store tools metadata for later use
        self.tools_metadata = {tool["name"]: tool for tool in tools}

        # Group tools by server
        tools_by_server = {}
        for tool in tools:
            server_id = tool.get("mcpserver", "unknown")
            # Check if servere have status 'public'
            mcpserver = mcpserver_service.get_mcpserver(server_id)
            if mcpserver is None or mcpserver.mcpserver_type != "public":
                continue
            if server_id not in tools_by_server:
                tools_by_server[server_id] = []
            tools_by_server[server_id].append(tool)

        # Create an endpoint for each tool
        for server_id, server_tools in tools_by_server.items():
            for tool in server_tools:
                self._create_tool_endpoint(server_id, tool)

        self.initialized = True
        logger.info(f"Initialized tools router with {len(tools)} dynamic endpoints across {len(tools_by_server)} servers")

        # Return the router to allow chaining
        return self.router

    def _create_tool_endpoint(self, server_id: str, tool: Dict[str, Any]):
        """
        Create a dedicated endpoint for a specific tool.

        Args:
            server_id: ID of the server containing this tool
            tool: Tool metadata dictionary
        """
        mcpserver_service = get_mcpserver_service()
        tool_name = tool["name"]
        tool_description = tool.get("description", f"Tool: {tool_name}")
        input_schema = tool.get("inputSchema", {})
        mcpserver = mcpserver_service.get_mcpserver(server_id)
        if mcpserver is None:
            logger.error(f"MCP server {server_id} not found")
            return
        mcpserver_name = mcpserver.name

        # Create a dynamic Pydantic model for the tool's input parameters
        # based on the tool's input schema
        param_fields = {}
        properties = input_schema.get("properties", {})
        required_props = input_schema.get("required", [])

        for prop_name, prop_schema in properties.items():
            field_type = self._get_field_type(prop_schema.get("type", "string"))
            is_required = prop_name in required_props

            # Create field with proper type and description
            field_info = Field(
                default=... if is_required else None,
                description=prop_schema.get("description", f"Parameter: {prop_name}")
            )

            param_fields[prop_name] = (field_type, field_info)

        # Create the dynamic model
        param_model = create_model(
            f"{tool_name.capitalize()}Params",
            **param_fields
        )

        # Create the endpoint function
        async def tool_endpoint(
            params: param_model = Body(..., description=f"Parameters for {tool_name}"),     # type: ignore
            server_manager: McpServerService = Depends(get_mcpserver_service)
        ):
            """Invoke the tool with the provided parameters."""
            # Convert Pydantic model to dict if needed
            if hasattr(params, "dict"):
                params_dict = params.dict(exclude_none=True)
            else:
                # If it's already a dict, filter out None values
                params_dict = {k: v for k, v in params.items() if v is not None}

            result = await server_manager.invoke_tool(tool["mcpserver"], tool_name, params_dict)

            if "isError" in result and result["isError"]:
                raise HTTPException(status_code=404, detail=result["result"])

            # Log successful execution
            logger.info(f"Tool {tool_name} executed successfully")

            # Process the tool response
            processed_result = process_tool_response(result.get("result", {}))
            return processed_result

        # Set function name and docstring for better OpenAPI docs
        tool_endpoint.__name__ = f"invoke_{tool_name}"
        tool_endpoint.__doc__ = f"""
        {tool_description}

        This endpoint invokes the '{tool_name}' tool with the provided parameters.
        """

        # Add the endpoint to the router
        # Create a short operationId
        short_operation_id = f"public_tool_{tool_name}"

        self.router.add_api_route(
            f"/{mcpserver_name}/{tool_name}",
            tool_endpoint,
            methods=["POST"],
            response_model=List[Any],
            summary=f"Invoke {tool_name} from {mcpserver_name}",
            description=tool_description,
            operation_id=short_operation_id,  # Use explicit operation_id instead of name
            name=f"invoke_{mcpserver_name}_{tool_name}"
        )
        self._dynamic_route_names.add(f"invoke_{mcpserver_name}_{tool_name}")

        logger.debug(f"Created endpoint for tool: {mcpserver_name}/{tool_name}")

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

    def get_openapi_schema(self, app) -> Dict[str, Any]:
        """
        Generate a streamlined OpenAPI schema containing only the tools endpoints.

        Args:
            app: The FastAPI application instance

        Returns:
            OpenAPI schema dictionary with only tools endpoints and minimal schemas
        """
        # Create a minimal schema that doesn't rely on components.schemas
        tools_schema = {
            "openapi": "3.0.0",
            "info": {
                "title": "MCP API Public Tools",
                "description": "API for invoking MCP public tools",
                "version": APP_VERSION
            },
            "paths": {}
        }

        # Add each tool endpoint to the schema
        mcpserver_service = get_mcpserver_service()
        for tool_name, tool_metadata in self.tools_metadata.items():
            server_id = tool_metadata.get("mcpserver", "unknown")
            mcpserver = mcpserver_service.get_mcpserver(server_id)
            if mcpserver is None or mcpserver.mcpserver_type != "public":
                continue

            mcpserver_name = mcpserver.name
            description = tool_metadata.get("description", f"Tool: {tool_name}")
            input_schema = tool_metadata.get("inputSchema", {})

            # Create the path entry
            path = f"/api/v1/public/tool/{mcpserver_name}/{tool_name}"

            # Create the operation object
            operation = {
                "summary": f"Invoke {tool_name} from {mcpserver_name}",
                "description": description,
                "operationId": f"public_tool_{tool_name.replace('-', '_')}",
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
            if path not in tools_schema["paths"]:
                tools_schema["paths"][path] = {}

            # Add the POST operation
            tools_schema["paths"][path]["post"] = operation

        logger.debug(f"Generated OpenAPI schema with {len(tools_schema['paths'])} paths")
        return tools_schema


# Create a singleton instance
mcpo_public_tools_router = MCPOPublicToolsRouter()


# Dependency to get the initialized tools router
async def get_tools_router() -> MCPOPublicToolsRouter:
    """
    Get the initialized tools router.

    Returns:
        Initialized tools router
    """
    if not mcpo_public_tools_router.initialized:
        await mcpo_public_tools_router.initialize()
    return mcpo_public_tools_router


# Export the router for inclusion in the main app
router = mcpo_public_tools_router.router
