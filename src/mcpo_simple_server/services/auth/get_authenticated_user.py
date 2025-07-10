from typing import Optional, TYPE_CHECKING
from fastapi import Depends, HTTPException, status
from fastapi import Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger
from mcpo_simple_server.services.auth.models import AuthUserModel
from mcpo_simple_server.services.auth import verify_jwt_token, get_username_from_api_key
from mcpo_simple_server.services.auth.models import TokenData
from mcpo_simple_server.config import ADMIN_BEARER_HACK
if TYPE_CHECKING:
    from mcpo_simple_server.services.config import ConfigService

# Create a single bearer scheme for extracting the token
bearer_scheme = HTTPBearer(auto_error=False, scheme_name="Authorization")


async def get_authenticated_user(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> AuthUserModel:
    """
    Get authenticated user, supporting both JWT tokens and API keys.

    This function first tries to authenticate using JWT token, then falls back to API key.
    It uses a single HTTP bearer scheme to avoid conflicts in the dependency injection system.

    Args:
        request: The FastAPI request object
        auth: The HTTP authorization credentials

    Returns:
        Authenticated user model

    Raises:
        HTTPException: If authentication fails
    """
    if auth is None:
        logger.warning("Tool authentication failed. No authorization header provided.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get the token from the authorization header
    token = auth.credentials
    config_service: ConfigService = request.app.state.config_service

    # Try JWT token authentication first
    try:
        # Check for admin bearer token
        if ADMIN_BEARER_HACK and token == ADMIN_BEARER_HACK:
            logger.info("Tool authentication successful using ADMIN_BEARER_HACK")
            # Return a synthetic admin user
            user_data = await config_service.user_config.get_config(username="admin")
            if user_data is None:
                raise ValueError("Admin user not found in config")
            return AuthUserModel(**user_data.model_dump())

        # Try regular JWT token
        jwt_token_data: Optional[TokenData] = verify_jwt_token(token)
        if jwt_token_data and jwt_token_data.username:
            config_user_data = await config_service.user_config.get_config(username=jwt_token_data.username)
            if config_user_data and not config_user_data.disabled:
                logger.debug(f"Tool JWT authentication successful for user '{config_user_data.username}'")
                return AuthUserModel(**config_user_data.model_dump())
    except Exception as e:
        logger.debug(f"JWT authentication failed, will try API key: {str(e)}")

    # Fall back to API key authentication
    try:
        username_from_api_key = get_username_from_api_key(token)
        config_user_data = await config_service.user_config.get_config(username_from_api_key)

        if config_user_data:
            if config_user_data.disabled:
                logger.warning(f"Tool API key authentication failed. User '{config_user_data.username}' is disabled.")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

            logger.debug(f"Tool API key authentication successful for user '{config_user_data.username}'")
            return AuthUserModel(**config_user_data.model_dump())
    except Exception as e:
        logger.debug(f"API key authentication failed: {str(e)}")

    # If we get here, authentication failed with both methods
    logger.warning("Tool authentication failed. Invalid token or API key.")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
