
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from loguru import logger
from mcpo_simple_server.services.auth import get_current_user
from mcpo_simple_server.services.auth.models import AuthUserModel

bearer_scheme = HTTPBearer(auto_error=False, scheme_name="Authorization")


async def get_current_admin_user(current_user: AuthUserModel = Depends(get_current_user)) -> AuthUserModel:
    """
    Get the current authenticated user and verify they have admin privileges.
    """
    if current_user.group not in {"admin", "admins"}:
        logger.warning(f"Admin access denied for user '{current_user.username}'.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return current_user
