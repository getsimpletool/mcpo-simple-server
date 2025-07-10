"""
Package/Module: Root Endpoint - Health check
"""

from . import router
from pydantic import BaseModel
from datetime import datetime
from mcpo_simple_server.config import BOOT_TIME


class HealthResponse(BaseModel):
    status: str
    uptime: datetime


@router.get("/api/v1/health", response_model=HealthResponse, include_in_schema=False)
async def handle_health():
    """
    Health check endpoint.
    Returns a simple status message indicating the server is operational.
    """
    return {"status": "ok", "uptime": (datetime.now() - BOOT_TIME).total_seconds()}
