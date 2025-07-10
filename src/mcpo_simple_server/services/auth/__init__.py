"""
Package/Module: Authentication Service - Secure authentication and authorization system

High Level Concept:
-------------------
The Authentication Service implements a robust, multi-method authentication system for
MCPoSimpleServer, supporting both interactive user sessions and programmatic access.
It provides secure authentication, authorization, and user management with defense-in-depth
security measures.

Architecture:
-------------
- Authentication Methods:
  - JWT-based session tokens with configurable expiration
  - Secure API keys with encrypted username binding
  - Admin bearer token for emergency access
- Security Features:
  - bcrypt password hashing with configurable work factor
  - Additional salt pepper for defense against rainbow tables
  - Encrypted API key storage with timestamp validation
  - Configurable JWT secret and algorithm
- User Management:
  - Flexible user roles and permissions
  - Account status control (enabled/disabled)
  - Environment-specific user configurations

Workflow:
---------
1. Authentication Flow:
   a. Client provides credentials (username/password or API key)
   b. System validates credentials against stored hashes
   c. On success, issues JWT token or validates API key
   d. Token/Key is used for subsequent authenticated requests

2. Authorization Flow:
   a. Incoming requests are authenticated via JWT or API key
   b. User permissions are verified based on role and account status
   c. Access is granted or denied with appropriate HTTP status codes

3. Admin Features:
   - First-time admin setup with secure default credentials
   - Emergency access via ADMIN_PASSWORD environment variable
   - User management capabilities

Usage Example:
--------------
# User Authentication
>>> from mcpo_simple_server.services.auth import authenticate_user, jwt
>>> user = await authenticate_user(username="admin", password="secure_password")
>>> token = jwt.create_access_token(data={"sub": user.username})

# API Key Authentication
>>> from mcpo_simple_server.services.auth import api_key
>>> api_key = api_key.create_api_key("service-account")

# Protected Endpoint
>>> from fastapi import Depends
>>> from .get_current_user import get_current_user
>>> async def protected_route(user = Depends(get_current_user)):
...     return {"message": f"Hello, {user.username}"}

Security Notes:
---------------
- All passwords are hashed using bcrypt with a configurable work factor
- API keys include encrypted usernames and timestamps for validation
- JWT tokens use HS256 signing by default (configurable)
- Admin operations require elevated privileges
- Failed authentication attempts are logged for security monitoring
- Default admin credentials are only used during initial setup
"""

# Import submodules for easier access

from . import api_key
from .api_key import get_username_from_api_key
from . import authenticate_user
from .authenticate_user import verify_password, get_password_hash
from . import jwt
from .jwt import verify_jwt_token
from .get_authenticated_by_api_key import get_authenticated_by_api_key
from .get_authenticated_by_jwt_token import get_authenticated_by_jwt_token
from .get_authenticated_user import get_authenticated_user
from .get_current_user import get_current_user
from .get_current_admin_user import get_current_admin_user
from .get_number_of_users import get_number_of_users


# Export key modules for easier imports
__all__ = [
    "api_key",
    "get_username_from_api_key",
    "authenticate_user",
    "verify_password",
    "get_password_hash",
    "jwt",
    "verify_jwt_token",
    "get_authenticated_by_api_key",
    "get_authenticated_by_jwt_token",
    "get_authenticated_user",
    "get_current_admin_user",
    "get_current_user",
    "get_number_of_users"
]
