"""
Package/Module: Entrypoint /

"""
from fastapi import responses
from mcpo_simple_server.config import APP_NAME
from . import router


import os


@router.get("/", include_in_schema=False, response_class=responses.HTMLResponse)
async def root():
    """
    Root endpoint.
    Returns a simple HTML page with links to API documentation.
    """

    # Get the base directory of the package
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # Create the absolute path to index.html in assets/html directory
    index_path = os.path.join(base_dir, "assets", "html", "index.html")

    # Open index.html using the absolute path
    with open(index_path, "r", encoding="utf-8") as f:
        index = f.read()

    return index
