"""
Public Prompts Router

This module provides functionality for accessing and executing public prompts.
"""
from typing import List
from fastapi import Depends
from mcpo_simple_server.services.prompt_manager import PromptManager
from mcpo_simple_server.services.prompt_manager.models.prompts import PromptInfo
from mcpo_simple_server.routers.public import router
from mcpo_simple_server.services.prompt_manager import get_prompt_manager
from mcpo_simple_server.services.mcpserver import get_mcpserver_service

from loguru import logger

# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------


@router.get("/prompts", response_model=List[PromptInfo])
async def list_public_prompts(
    prompt_manager: PromptManager = Depends(get_prompt_manager)
) -> List[PromptInfo]:
    """
    List all public prompts.

    Returns:
        List of public prompt info objects
    """
    logger.debug("Listing public prompts")
    return await prompt_manager.get_public_prompts()

# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
