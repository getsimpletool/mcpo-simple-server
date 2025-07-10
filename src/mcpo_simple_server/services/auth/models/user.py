from pydantic import BaseModel, Field
from typing import Dict, Any


class AuthUserModel(BaseModel):
    """User-specific configuration model."""
    username: str = Field(..., min_length=3, max_length=50)
    group: str = Field(default="user", pattern=r"^(users|admins)$")
    disabled: bool = Field(default=False)
    preferences: Dict[str, Any] = Field(default_factory=dict)
