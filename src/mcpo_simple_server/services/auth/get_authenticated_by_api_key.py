from typing import Optional
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger

from mcpo_simple_server.services.auth import get_username_from_api_key
from mcpo_simple_server.services.auth.models import AuthUserModel
from mcpo_simple_server.services import get_config_service

bearer_scheme = HTTPBearer(auto_error=False, scheme_name="Authorization")


async def get_authenticated_by_api_key(auth: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)) -> Optional[AuthUserModel]:

    if auth is None:
        logger.debug("No API key provided in request.")
        return None

    api_key = auth.credentials

    config_service = get_config_service()

    try:
        username_from_api_key = get_username_from_api_key(api_key)
        config_user_data = await config_service.user_config.get_config(username_from_api_key)
    except Exception as e:
        logger.error(f"Error getting users for API key authentication: {str(e)}")
        return None

    if config_user_data is None:
        logger.warning("API key authentication failed. Invalid API key.")
        return None

    logger.info(f"API key authentication successful for user '{config_user_data.username}'")
    return AuthUserModel(**config_user_data.model_dump())
