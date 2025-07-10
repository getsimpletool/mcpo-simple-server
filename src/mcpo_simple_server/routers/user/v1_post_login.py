"""
Authentication handlers for the user router.
Includes login and password management endpoints.
"""
from . import router
from typing import TYPE_CHECKING, Optional
from datetime import timedelta
from fastapi import HTTPException, status, Body, Request
from loguru import logger
from pydantic import BaseModel, Field
from mcpo_simple_server.config import ADMIN_PASSWORD, JWT_ACCESS_TOKEN_EXPIRE_MINUTES
from mcpo_simple_server.services.auth import jwt, authenticate_user
from mcpo_simple_server.services.config.models import UserConfigModel
if TYPE_CHECKING:
    from mcpo_simple_server.services.config import ConfigService


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$", examples=["admin"])
    password: str = Field(..., min_length=1, examples=["MCPOadmin"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
async def login_for_access_token(
        request: Request,
        request_body: LoginRequest = Body(...)):
    """
    Logs in a user and returns an access token.
    Uses username and password provided in the request body.

    Special cases:
    1. First-time login: If no users exist and username is 'admin', the ADMIN_PASSWORD
       environment variable is checked and used to create the first admin account.
    2. Admin recovery: If username is 'admin' and ADMIN_PASSWORD is provided and matches,
       the login is allowed even if the stored password is different.
    """

    config_service: 'ConfigService' = request.app.state.config_service

    # Check if request_body.username exist
    if not request_body.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is required")

    # Check if request_body.password exist
    if not request_body.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is required")

    user_config: Optional[UserConfigModel] = await config_service.user_config.get_config(request_body.username)

    # Special case 1: First-time login with ADMIN_PASSWORD or default admin/MCPOadmin
    if request_body.username == "admin" and not user_config:
        # Case 1a: Using ADMIN_PASSWORD from environment variable
        if ADMIN_PASSWORD and request_body.password == ADMIN_PASSWORD:
            logger.info("Creating first admin account using ADMIN_PASSWORD from environment")
            password_to_use = ADMIN_PASSWORD
        # Case 1b: No ADMIN_PASSWORD set, allow default admin/MCPOadmin
        elif not ADMIN_PASSWORD and request_body.password == "MCPOadmin":
            logger.info("Creating first admin account using default admin/MCPOadmin credentials")
            password_to_use = "MCPOadmin"
        else:
            # Not a special case, continue with normal authentication flow
            logger.debug("Not a special first-time login case, continuing with normal authentication")
            password_to_use = None

        # If we have a password to use, create the admin account
        if password_to_use:
            try:
                user_in_db = UserConfigModel(
                    username="admin",
                    hashed_password=authenticate_user.get_password_hash(password_to_use),
                    group="admins",
                    disabled=False
                )

                # Save the user & refresh the users cache
                await config_service.user_config.save_config(user_in_db)
                await config_service.user_config.refresh_users_cache()

                logger.info("First admin user 'admin' created successfully")

                # Create access token
                access_token = jwt.create_access_jwt_token(
                    claims={"sub": "admin", "admin": True},
                    expires_delta=timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
                )

                return TokenResponse(access_token=access_token, token_type="bearer")
            except Exception as e:
                error_message = str(e)
                logger.error(f"Error creating admin user: {error_message}")

                # Check if it's a validation error (contains 'validation error')
                if "validation error" in error_message.lower():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid input: {error_message}"
                    ) from e
                else:
                    # For other errors, return 500
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to create admin user: {error_message}"
                    ) from e

    # Special case 2: Admin recovery using ADMIN_PASSWORD
    if request_body.username == "admin" and ADMIN_PASSWORD and request_body.password == ADMIN_PASSWORD:
        try:
            # Get the admin user data
            admin_data = await config_service.user_config.get_config(request_body.username)

            if admin_data and admin_data.group == "admins":
                logger.info("Admin login recovery using ADMIN_PASSWORD")

                # Create access token
                access_token = jwt.create_access_jwt_token(
                    claims={"sub": "admin", "admin": True},
                    expires_delta=timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
                )

                return TokenResponse(access_token=access_token, token_type="bearer")
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error during admin recovery: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Admin recovery failed: {error_message}"
            ) from e

    # Standard authentication flow
    user = await authenticate_user.authenticate_user(
        request_body.username,
        request_body.password
    )
    if not user:
        logger.warning(f"Failed login attempt for user '{request_body.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is disabled
    if user.disabled:
        logger.warning(f"Login attempt for disabled user '{request_body.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is admin group
    if user.group == "admins":
        admin_status = True
    else:
        admin_status = False

    # Create access token
    access_token = jwt.create_access_jwt_token(
        claims={"sub": user.username, "admin": admin_status},
        expires_delta=timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    logger.info(f"User '{request_body.username}' logged in successfully")
    return TokenResponse(access_token=access_token, token_type="bearer")
