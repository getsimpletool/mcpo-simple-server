import os
import uuid
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError
from mcpo_simple_server.services.auth.models import TokenData
from mcpo_simple_server.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES
# Load environment variables from .env file
load_dotenv()


# --- Password Hashing ---
# Use bcrypt for password hashing
bcrypt.__about__ = bcrypt   # type: ignore - workaround for (trapped) error reading bcrypt version
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_jwt_token(claims: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token with standard JWT claims.

    Args:
        claims: Dictionary containing the claims to include in the token
               Required keys: 'sub' (subject/username), 'admin' (boolean)
        expires_delta: Optional timedelta for token expiration

    Returns:
        JWT token string
    """
    # Copy the claims to avoid modifying the original
    jwt_claims = claims.copy()

    # Ensure required fields are present
    if "sub" not in jwt_claims:
        if "username" in jwt_claims:
            # If username is provided but sub is not, use username as sub
            jwt_claims["sub"] = jwt_claims["username"]
        else:
            raise ValueError("Either 'sub' or 'username' must be provided in claims")

    # Make sure username is set (if not already)
    if "username" not in jwt_claims and "sub" in jwt_claims:
        jwt_claims["username"] = jwt_claims["sub"]

    # Check for admin claim
    if "admin" not in jwt_claims:
        raise ValueError("'admin' claim must be provided")

    # Add standard JWT claims
    current_time = datetime.now(timezone.utc)

    # Set expiration time
    if expires_delta:
        expire = current_time + expires_delta
    else:
        expire = current_time + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    # Add standard JWT timestamps
    jwt_claims.update({
        "iss": os.getenv("JWT_ISSUER", "mcpo-simple-server"),  # Issuer
        "iat": int(current_time.timestamp()),  # Issued at time
        "exp": int(expire.timestamp()),  # Expiration time
        "nbf": int(current_time.timestamp()),  # Not valid before
        "jti": str(uuid.uuid4())  # JWT ID (unique identifier)
    })

    # If aud (audience) is specified in env, add it
    if audience := os.getenv("JWT_AUDIENCE"):
        jwt_claims["aud"] = audience

    # Encode and return the JWT
    encoded_jwt = jwt.encode(jwt_claims, str(JWT_SECRET_KEY), algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_jwt_token(token: str) -> Optional[TokenData]:
    """Verifies a JWT token and returns the payload as TokenData if valid.

    Args:
        token: JWT token string to verify

    Returns:
        TokenData object containing the claims from the token if valid,
        None otherwise
    """
    try:
        # Decode the token with validation
        payload = jwt.decode(token, str(JWT_SECRET_KEY), algorithms=[JWT_ALGORITHM])

        # Extract required claims
        username = payload.get("username") or payload.get("sub")
        admin = payload.get("admin")

        # Check required claims
        if username is None:
            return None
        if admin is None:
            admin = False

        # Build TokenData with all available standard JWT claims
        token_data_dict = {
            "username": username,
            "admin": admin,
            "sub": payload.get("sub"),
            "iss": payload.get("iss"),
            "aud": payload.get("aud"),
            "exp": payload.get("exp"),
            "nbf": payload.get("nbf"),
            "iat": payload.get("iat"),
            "jti": payload.get("jti")
        }

        # Validate payload against the Pydantic model
        token_data = TokenData(**token_data_dict)
        return token_data

    except (JWTError, ValidationError):
        # In a real application, you'd want to log this error
        # logger.error(f"Token verification failed")
        return None
