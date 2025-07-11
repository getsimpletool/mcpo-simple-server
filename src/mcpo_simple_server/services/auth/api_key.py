import base64
import json
import time
from cryptography.fernet import Fernet
from mcpo_simple_server.config import API_KEY_ENCRYPTION_KEY, API_KEY_PREFIX

# Generate a key once and store it in your config
# You can generate it with: Fernet.generate_key()
# Then store it in your config as ENCRYPTION_KEY
_ENCRYPTION_KEY = str(API_KEY_ENCRYPTION_KEY).encode()


def encrypt_data(data: dict) -> str:
    """Encrypt data (as JSON) for API key."""
    f = Fernet(_ENCRYPTION_KEY)
    json_str = json.dumps(data)
    return base64.urlsafe_b64encode(f.encrypt(json_str.encode())).decode()


def decrypt_data(encrypted_data: str) -> dict:
    """Decrypt JSON data from API key."""
    f = Fernet(_ENCRYPTION_KEY)
    json_str = f.decrypt(base64.urlsafe_b64decode(encrypted_data)).decode()
    return json.loads(json_str)


def create_api_key(username: str) -> str:
    """
    Generates a new secure API key (plain text).
    The username and timestamp are encrypted as JSON data and included in the key.

    Args:
        username: The username to include in the API key

    Returns:
        The plain API key
    """
    # Get current Unix timestamp
    timestamp = int(time.time())

    # Create data dictionary with username and timestamp
    data = {
        "username": username,
        "timestamp": timestamp
    }

    # Encrypt the data as JSON
    encrypted_data = encrypt_data(data)

    # Format: {prefix}{encrypted_data}
    plain_key = f"{API_KEY_PREFIX}{encrypted_data}"

    return plain_key


def get_username_from_api_key(api_key: str) -> str:
    """
    Extracts and decrypts the username from an API key.

    Args:
        api_key: The full API key string

    Returns:
        The decrypted username

    Raises:
        ValueError: If the API key format is invalid
    """
    try:
        # Remove the prefix to get the encrypted data
        if api_key.startswith("Bearer "):
            api_key = api_key[7:]
        if not api_key.startswith(API_KEY_PREFIX):
            raise ValueError("Invalid API key format: missing prefix")

        encrypted_data = api_key[len(API_KEY_PREFIX):]
        data = decrypt_data(encrypted_data)

        # Return the username from the decrypted data
        return data["username"]
    except Exception as e:
        raise ValueError(f"Failed to extract username from API key: {str(e)}") from e
