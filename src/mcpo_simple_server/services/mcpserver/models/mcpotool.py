from typing import Any
from pydantic import BaseModel


class MCPoTool(BaseModel):
    name: str
    description: str | None = None
    inputSchema: dict[str, Any]
    mcpserver_id: str

    class Config:
        extra = "allow"
