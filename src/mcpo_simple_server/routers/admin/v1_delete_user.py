"""
Admin User Router

This module provides functionality for managing users.
"""
from loguru import logger
from fastapi import Depends, HTTPException, status
from mcpo_simple_server.services.config import get_config_service
from mcpo_simple_server.services.config.models import UserConfigPublicModel
from mcpo_simple_server.services.auth import get_current_admin_user
from mcpo_simple_server.routers.admin import router


@router.delete("/user/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_user(
    username: str,
    admin_user: UserConfigPublicModel = Depends(get_current_admin_user)
):
    """
    Deletes a user by username. Requires admin privileges.
    """
    logger.info(f"Admin '{admin_user.username}' attempting to delete user '{username}'.")

    config_service = get_config_service()
    # Prevent admin from deleting themselves
    if username == admin_user.username:
        logger.warning(f"Admin '{admin_user.username}' attempted to delete themselves.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins cannot delete their own account."
        )

    user_to_delete = await config_service.user_config.get_config(username)
    if not user_to_delete:
        logger.warning(f"Attempted to delete non-existent user '{username}'.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found."
        )

    success = await config_service.user_config.delete_config(username)
    if not success:
        # This could be a race condition or file save error
        logger.error(f"Failed to delete user '{username}' from config file.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not delete user '{username}'."
        )

    logger.info(f"User '{username}' deleted successfully by admin '{admin_user.username}'.")
    return None  # 204 No Content
