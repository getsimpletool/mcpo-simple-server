"""
Authentication models package.

This package contains Pydantic models for authentication services.
"""


from .token_data import TokenData
from .user import AuthUserModel

__all__ = ['TokenData', 'AuthUserModel']
