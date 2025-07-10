"""
Authentication handlers for the user router.
Includes login and password management endpoints.
"""
from . import router
from typing import TYPE_CHECKING
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status, Body, Request
from loguru import logger
from mcpo_simple_server.services.auth import get_current_user, get_password_hash, verify_password
from mcpo_simple_server.config import ADMIN_PASSWORD
if TYPE_CHECKING:
    from mcpo_simple_server.services.config import ConfigService
    from mcpo_simple_server.services.auth.models import AuthUserModel


class PasswordUpdateInput(BaseModel):
    """Model for updating password for both users and admins (no length validation)."""
    current_password: str
    new_password: str


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def update_my_password(
    request: Request,
    password_update: PasswordUpdateInput = Body(...),
    current_user: 'AuthUserModel' = Depends(get_current_user)
):
    """
    Updates the password for the currently authenticated user.
    """
    config_service: 'ConfigService' = request.app.state.config_service

    # Get the current user data
    user_data = await config_service.user_config.get_config(current_user.username)
    if not user_data:
        logger.error(f"Failed to retrieve user '{current_user.username}' for password update.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update password")

    # Recovery admin mode
    if current_user.username == "admin" and ADMIN_PASSWORD and password_update.current_password == ADMIN_PASSWORD:
        new_hashed_password = get_password_hash(password_update.new_password)
        user_data.hashed_password = new_hashed_password
        await config_service.user_config.save_config(user_data)
        await config_service.user_config.refresh_users_cache(current_user.username)
        logger.info(f"Password updated for user '{current_user.username}'")
        return

    # Verify current password
    if not verify_password(password_update.current_password, user_data.hashed_password):
        logger.warning(f"Invalid current password provided for user '{current_user.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid current password",
        )

    # Manual password length validation for non-admin users
    if not user_data.group == "admins" and len(password_update.new_password) < 8:
        logger.warning(f"Password too short for user '{current_user.username}' (admin bypasses length check)")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="New password must be at least 8 characters long."
        )

    # Hash new password
    new_hashed_password = get_password_hash(password_update.new_password)
    user_data.hashed_password = new_hashed_password
    # Save updated user data
    await config_service.user_config.save_config(user_data)
    # Refresh only this user's cache
    await config_service.user_config.refresh_users_cache(current_user.username)
    logger.info(f"Password updated for user '{current_user.username}'")
    return
