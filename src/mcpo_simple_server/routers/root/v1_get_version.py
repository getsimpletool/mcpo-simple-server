"""
Package/Module: Root Endpoint - Version check
"""

from . import router
from mcpo_simple_server import __version__
from pydantic import BaseModel


class VersionResponse(BaseModel):
    version: str


@router.get("/api/v1/version", response_model=VersionResponse, include_in_schema=False)
async def handle_version():
    """
    Version check endpoint.
    Returns the version of the server.
    """
    return {"version": __version__}
