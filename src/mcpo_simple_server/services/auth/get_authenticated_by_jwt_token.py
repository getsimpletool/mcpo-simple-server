from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger
from mcpo_simple_server.config import ADMIN_BEARER_HACK
from mcpo_simple_server.services import get_config_service
from mcpo_simple_server.services.auth import verify_jwt_token
from mcpo_simple_server.services.auth.models import TokenData, AuthUserModel

bearer_scheme = HTTPBearer(auto_error=False, scheme_name="Authorization")


async def get_authenticated_by_jwt_token(auth: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)) -> Optional[AuthUserModel]:
    if auth is None:
        return None

    jwt_token = auth.credentials

    config_service = get_config_service()

    # Check if token matches ADMIN_BEARER_HACK
    if ADMIN_BEARER_HACK and jwt_token == ADMIN_BEARER_HACK:
        logger.info("Authentication successful using ADMIN_BEARER_HACK")
        # Return a synthetic admin user
        user_data = await config_service.user_config.get_config(username="admin")
        if user_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return AuthUserModel(**user_data.model_dump())

    jwt_token_data: Optional[TokenData] = verify_jwt_token(jwt_token)
    if jwt_token_data is None or jwt_token_data.username is None:
        logger.warning(f"Token data: {jwt_token_data}")
        logger.warning("Token verification failed or username missing in token.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    config_user_data = await config_service.user_config.get_config(username=jwt_token_data.username)
    if config_user_data is None:
        logger.warning(f"User '{jwt_token_data.username}' from token not found in config.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if config_user_data.disabled:
        logger.warning(f"Authentication failed. User '{config_user_data.username}' is disabled.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    return AuthUserModel(**config_user_data.model_dump())
