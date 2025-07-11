from fastapi import Request
from fastapi.responses import HTMLResponse
from . import router

from mcpo_simple_server.template import templates

# HTML endpoints


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request):
    return templates.TemplateResponse("index.j2", {"request": request})
