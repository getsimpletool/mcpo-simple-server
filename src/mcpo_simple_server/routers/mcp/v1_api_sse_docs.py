"""
Defines the OpenAPI path definitions for MCP SSE (Server-Sent Events) endpoints.

This is used to manually add documentation for routes handled by mounted ASGI applications,
which are not automatically included in FastAPI's OpenAPI schema.
"""

SSE_OPENAPI_PATHS = {
    "/api/v1/sse": {
        "get": {
            "tags": ["MCP-SSE"],
            "summary": "MCP SSE Connection (GET)",
            "description": (
                "Establishes a Server-Sent Events (SSE) connection for MCP communication. "
                "Clients should connect to this endpoint using a GET request. "
                "The actual SSE handling is managed by a mounted ASGI application."
            ),
            "responses": {
                "200": {
                    "description": "SSE stream successfully established.",
                    "content": {"text/event-stream": {"schema": {"type": "string"}}},
                },
                "405": {"description": "Method Not Allowed (if not GET)"},
            },
        }
    },
    "/api/v1/sse/messages/": {
        "post": {
            "tags": ["MCP-SSE"],
            "summary": "MCP SSE Message (POST)",
            "description": (
                "Receives MCP messages from clients over an established SSE connection. "
                "Clients should POST messages to this endpoint. "
                "The actual message handling is managed by a mounted ASGI application."
            ),
            # Example for request body, can be expanded based on actual MCP message structure
            # "requestBody": {
            #     "content": {
            #         "application/json": {
            #             "schema": {"type": "object", "properties": {"message": {"type": "string"}}}
            #         }
            #     },
            #     "required": True
            # },
            "responses": {
                "200": {"description": "Message received (actual response may vary based on message content)."},
                "400": {"description": "Bad request (e.g., malformed MCP message)."},
            },
        }
    },
}

__all__ = ["SSE_OPENAPI_PATHS"]
