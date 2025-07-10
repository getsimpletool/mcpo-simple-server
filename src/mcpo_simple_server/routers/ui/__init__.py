"""
Package/Module: User Router - Authentication and user management endpoints

High Level Concept:
-------------------
The User Router provides endpoints for user authentication, profile management,
and API key handling within the MCPoSimpleServer application. It organizes these
functionalities into separate handler files for better maintainability and separation
of concerns. The router follows RESTful conventions and implements proper security
practices, including JWT-based authentication and role-based access control.

Architecture:
-------------
- Authentication: JWT-based auth with username/password login
- User Management: Profile, password, and configuration handling
- API Key Management: Generation and revocation of API keys
- Environment Variables: User-specific environment configuration
- Configuration: User-specific application settings

Endpoints:
----------
* /api/v1/user/auth/* - Authentication operations
  - POST /api/v1/user/login - User login with username and password
  - GET /api/v1/user/me - Get current authenticated user information
  - PUT /api/v1/user/password - Update user password

* /api/v1/user/api-keys/* - API key management
  - POST /api/v1/user/api-keys - Create a new API key
  - DELETE /api/v1/user/api-keys - Delete an existing API key

* /api/v1/user/env/* - Environment variable management
  - GET /api/v1/user/env - Get all user environment variables
  - PUT /api/v1/user/env - Update multiple environment variables
  - PUT /api/v1/user/env/{key} - Update a specific environment variable
  - DELETE /api/v1/user/env - Delete all environment variables
  - DELETE /api/v1/user/env/{key} - Delete a specific environment variable

* /api/v1/user/config - User configuration
  - GET /api/v1/user/config - Get combined user and global configuration

Security Model:
--------------
- Authentication: JWT tokens with configurable expiration
- Authorization: Role-based access control (users/admins)
- Password Security: BCrypt hashing with proper salt rounds
- Sensitive Data: Hashed passwords are never returned in API responses
- API Keys: Generated once and shown only on creation

Configuration Management:
------------------------
- User-specific settings override global configurations
- Environment variables support per-user customization
- Secure storage of sensitive information
- Proper validation of all inputs

Error Handling:
--------------
- Consistent error responses with appropriate HTTP status codes
- Detailed error messages for client-side handling
- Logging of security-relevant events
- Input validation using Pydantic models
"""

from fastapi import APIRouter

__all__ = ["router"]

# Create the main router
router = APIRouter(
    prefix="/ui",
    tags=["UI"],
    responses={404: {"description": "Not found"}},
)


from . import index  # noqa: F401, E402
