"""
Token data model for JWT claims.

This module defines the Pydantic model used for JWT token claims, including both
standard JWT claims and application-specific claims.
"""

from pydantic import BaseModel, Field
from typing import Optional

__all__ = ['TokenData']


class TokenData(BaseModel):
    """Standard JWT claims along with application-specific claims.

    Combines standard JWT claims (iss, sub, aud, exp, nbf, iat, jti) with
    application-specific claims (username, admin).
    """
    # Application-specific mandatory claims
    username: str = Field(
        ...,
        description="Username of the authenticated user",
        examples=["admin", "user123"]
    )
    admin: bool = Field(
        False,
        description="Whether the user has administrative privileges",
        examples=[True, False]
    )

    # Standard JWT claims (optional)
    iss: Optional[str] = Field(
        None,
        description="Issuer of the JWT - identifies the principal that issued the token",
        examples=["mcpo-simple-server"]
    )
    sub: Optional[str] = Field(
        None,
        description="Subject of the JWT - typically contains the user identifier and usually matches username",
        examples=["admin", "user123"]
    )
    aud: Optional[str] = Field(
        None,
        description="Audience for which the JWT is intended - identifies the recipients that the JWT is intended for",
        examples=["mcpo-client", "https://api.mcposerver.com"]
    )
    exp: Optional[int] = Field(
        None,
        description="Expiration time (Unix timestamp) - after which the JWT must not be accepted for processing",
        examples=[1716676800]
    )
    nbf: Optional[int] = Field(
        None,
        description="Not Before time (Unix timestamp) - before which the JWT must not be accepted for processing",
        examples=[1685577600]
    )
    iat: Optional[int] = Field(
        None,
        description="Issued At time (Unix timestamp) - when the JWT was issued",
        examples=[1685577600]
    )
    jti: Optional[str] = Field(
        None,
        description="JWT ID - unique identifier for this token, used to prevent the JWT from being replayed",
        examples=["f9d76d5a-2d5f-4f52-ba1b-3e5bd4c84399"]
    )
