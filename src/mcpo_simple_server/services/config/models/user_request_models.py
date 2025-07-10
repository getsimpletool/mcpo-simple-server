"""
User request models.

This module defines the Pydantic models for user creation and API key management.
"""

from pydantic import BaseModel, Field

__all__ = ['UserCreateRequest']


class UserCreateRequest(BaseModel):
    """Model for creating a new user."""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern="^[a-zA-Z0-9_-]+$",
        description="Username (3-50 chars, alphanumeric with _ and -)",
        examples=["admin"]
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Plain text password (min 8 chars)",
        examples=["secure_password123"]
    )
    group: str = Field(
        default="users",
        description="User group (e.g., 'admins', 'users')",
        examples=["admins"]
    )
    disabled: bool = Field(
        default=False,
        description="Whether the user account is disabled",
        examples=[False]
    )
