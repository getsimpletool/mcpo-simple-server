import bcrypt
from typing import Optional
from dotenv import load_dotenv
from loguru import logger
from passlib.context import CryptContext
from typing import TYPE_CHECKING
from mcpo_simple_server.config import SALT_PEPPER
from mcpo_simple_server.services import get_config_service
from mcpo_simple_server.services.auth.models import AuthUserModel
if TYPE_CHECKING:
    from mcpo_simple_server.services.config.models import UserConfigModel

# Load environment variables from .env file
load_dotenv()

# --- Password Hashing ---
# Use bcrypt for password hashing
bcrypt.__about__ = bcrypt   # type: ignore - workaround for (trapped) error reading bcrypt version
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password, incorporating the SALT pepper."""
    # Combine password and pepper before verification
    password_with_pepper = plain_password + SALT_PEPPER
    try:
        return pwd_context.verify(password_with_pepper, hashed_password)
    except Exception:  # Broad exception for passlib errors
        return False


def get_password_hash(password: str) -> str:
    """Hashes a password using bcrypt, incorporating the SALT pepper."""
    # Combine password and pepper before hashing
    password_with_pepper = password + SALT_PEPPER
    return pwd_context.hash(password_with_pepper)


async def authenticate_user(username: str, password: str) -> Optional[AuthUserModel]:
    """
    Authenticate a user with username and password using the global CONFIG_SERVICE.

    Args:
        username: Username to authenticate
        password: Plain password to verify

    Returns:
        UserInDB model if authentication is successful, None otherwise
    """
    try:
        # Get config service from dependencies
        config_service = get_config_service()
        logger.debug(f"Authenticating user '{username}'")

        # Get user data from the user_config module
        user_data: Optional[UserConfigModel] = await config_service.user_config.get_config(username)
        if not user_data:
            logger.debug(f"User '{username}' not found")
            return None

        # Verify the password
        if not verify_password(password, user_data.hashed_password):
            logger.debug(f"Password for user '{username}' does not match")
            return None

        return AuthUserModel(**user_data.model_dump())
    except Exception:
        # If any error occurs during authentication, return None
        logger.error(f"Error during authentication for user '{username}'")
        return None
