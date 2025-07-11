from . import router
from loguru import logger
from typing import Optional, TYPE_CHECKING
from fastapi import Body, Depends, HTTPException, status, Request
from mcpo_simple_server.services.config.models import UserConfigPublicModel, UserConfigModel, UserCreateRequest
from mcpo_simple_server.services.auth import get_current_admin_user, get_number_of_users, get_password_hash
if TYPE_CHECKING:
    from mcpo_simple_server.services.config import ConfigService
    from mcpo_simple_server.services.auth.models import AuthUserModel


@router.post("/user", response_model=UserConfigPublicModel, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    request: Request,
    user_in: UserCreateRequest = Body(...),
    current_user: Optional['AuthUserModel'] = Depends(get_current_admin_user)
):
    """
    Creates a new user.
    """
    number_of_users = await get_number_of_users()
    logger.info(f"Attempting to create user '{user_in.username}'. Number of users: {number_of_users}")

    admin_username_for_log = "N/A"  # Default for logging if not required/found

    if number_of_users == 0:
        # If admin is required, current_user MUST exist and be an admins
        if current_user is None:
            # Should be caught by get_authenticated_user raising 401 if no auth provided
            logger.error("Admin required, but no authenticated user found (get_authenticated_user should have raised 401).")
            # Re-raise 401 just in case dependency behaviour changes or auto_error=False is used later
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

        if not current_user.group == "admins":
            logger.warning(f"Admin privileges required to create user, but user '{current_user.username}' is not an admin.")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required.")

        admin_username_for_log = current_user.username
        logger.info(f"Admin '{admin_username_for_log}' creating user '{user_in.username}' with admin status: {user_in.group}.")

        # First user creation
        logger.info(f"Creating first user '{user_in.username}' with admin status: {user_in.group}.")
        admin_username_for_log = "System (Initial Setup)"
        logger.info(f"Admin '{admin_username_for_log}' creating user '{user_in.username}' with admin status: {user_in.group}.")

    config_service: 'ConfigService' = request.app.state.config_service

    # Ensure we have fresh data by refreshing the cache for this specific username
    await config_service.user_config.refresh_users_cache(user_in.username)

    existing_user = await config_service.user_config.get_config(user_in.username)
    if existing_user:
        logger.warning(f"Attempted to create user '{user_in.username}', but username already exists.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered"
        )

    # Create user data with hashed password
    user_data = UserConfigModel(
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        group="users",
        disabled=user_in.disabled,
        api_keys={},
        env={},
        mcpServers={}
    )

    success = await config_service.user_config.save_config(user_data)
    if not success:
        logger.error(f"Failed to create user '{user_in.username}' in config file.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create user."
        )

    data = await config_service.user_config.get_config(user_in.username)
    logger.info(f"User '{user_in.username}' created successfully.")
    return data
