"""
Authentication handlers for the user router.
Includes login and password management endpoints.
"""
from . import router
from typing import TYPE_CHECKING
from fastapi import Depends, HTTPException, status
from mcpo_simple_server.services.auth import get_authenticated_by_jwt_token
if TYPE_CHECKING:
    from mcpo_simple_server.services.auth.models import AuthUserModel


@router.get("/me")
async def read_users_me(current_user: 'AuthUserModel' = Depends(get_authenticated_by_jwt_token)):
    """
    Returns the details of the currently authenticated user (excluding sensitive info).
    Returns 401 if the user is not authenticated.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user
