"""
Package/Module: Root Endpoint - Ping check
"""

from . import router
from pydantic import BaseModel


class PingResponse(BaseModel):
    response: str


@router.get("/api/v1/ping", response_model=PingResponse, include_in_schema=False)
async def handle_ping():
    """
    Ping check endpoint.
    Returns a simple "pong" response to verify the server is responsive.
    """
    return {"response": "pong"}
