import json
from typing import Union, Dict, Any, List
from mcp.types import CallToolResult, TextContent, ImageContent, EmbeddedResource


def process_tool_response(result: Union[CallToolResult, Dict[str, Any]]) -> List[Any]:
    """Universal response processor for all tool endpoints"""
    response = []
    if isinstance(result, dict):
        result = CallToolResult(**result)
    for content in result.content:
        if isinstance(content, TextContent):
            text = content.text
            if isinstance(text, str):
                try:
                    text = json.loads(text)
                except json.JSONDecodeError:
                    pass
            response.append(text)
        elif isinstance(content, ImageContent):
            image_data = f"data:{content.mimeType};base64,{content.data}"
            response.append(image_data)
        elif isinstance(content, EmbeddedResource):
            # TODO: Handle embedded resources
            response.append("Embedded resource not supported yet.")
    return response
