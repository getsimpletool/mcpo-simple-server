"""
Global configuration module for the server.

This module provides central configuration variables used throughout the application.
"""
import os
import sys
import pathlib
from datetime import datetime
from cryptography.fernet import Fernet
from mcpo_simple_server.logger import logger
from mcpo_simple_server.metadata import __version__


# --- Boot ---
BOOT_TIME = datetime.now()

# --- Application ---
LIB_PATH = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
APP_PATH = pathlib.Path(os.getcwd())
APP_VERSION = str(__version__)
APP_NAME = "MCPoSimpleServer"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# --- Config Storage ---
# If the path points to a file (config.json), extract the directory path
CONFIG_STORAGE_TYPE = os.getenv("CONFIG_STORAGE_TYPE", "ddb")
CONFIG_STORAGE_PATH = os.getenv("CONFIG_STORAGE_PATH", str(APP_PATH / "data" / "config"))
if CONFIG_STORAGE_PATH.endswith(".db") or CONFIG_STORAGE_PATH.endswith(".json"):
    CONFIG_STORAGE_PATH = os.path.dirname(CONFIG_STORAGE_PATH)

# --- Tools ---
TOOLS_BLACKLIST = os.getenv("TOOLS_BLACKLIST", "").replace(" ", "").split(",")

# --- Cleanup MCPServers ---
MCPSERVER_CLEANUP_INTERVAL = int(os.getenv("MCPSERVER_CLEANUP_INTERVAL", "5"))
MCPSERVER_CLEANUP_TIMEOUT = int(os.getenv("MCPSERVER_CLEANUP_TIMEOUT", "3600"))
# Create the config directory if it doesn't exist
try:
    if not os.path.exists(CONFIG_STORAGE_PATH):
        os.makedirs(CONFIG_STORAGE_PATH)
        logger.info(f"📁 Config directory created: {CONFIG_STORAGE_PATH}")
except Exception as e:
    logger.error(f"Failed to create config directory at {CONFIG_STORAGE_PATH}: {str(e)}")

# --- Admin Bearer Hack ---
ADMIN_BEARER_HACK = os.getenv("ADMIN_BEARER_HACK")
if ADMIN_BEARER_HACK:
    logger.info("ADMIN_BEARER_HACK environment variable is set. Static admin Bearer token is enabled.")

# --- Password Hashing ---
SALT_PEPPER = os.getenv("SALT", "default_insecure_pepper")  # For MD5 password hashing

# --- JWT ---
EXIT_ON_ERROR = 0
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # Get JWT secret from env
if JWT_SECRET_KEY is None:
    example_keys = [Fernet.generate_key().decode() for _ in range(3)]
    logger.error("JWT_SECRET_KEY environment variable is not set. It is required for JWT authentication.")
    logger.error("Example valid JWT secret keys:\nJWT_SECRET_KEY=" + "\nJWT_SECRET_KEY=".join(example_keys))
    EXIT_ON_ERROR = 1

# --- API Key ---
API_KEY_PREFIX = os.getenv("API_KEY_PREFIX", "st-")  # Prefix for generated API keys
API_KEY_ENCRYPTION_KEY = os.getenv("API_KEY_ENCRYPTION_KEY")
if API_KEY_ENCRYPTION_KEY is None:
    example_keys = [Fernet.generate_key().decode() for _ in range(3)]
    logger.error("API_KEY_ENCRYPTION_KEY environment variable is not set. It is required for API key encryption (Fernet).")
    logger.error("Example valid Fernet keys:\nAPI_KEY_ENCRYPTION_KEY=" + "\nAPI_KEY_ENCRYPTION_KEY=".join(example_keys))
    EXIT_ON_ERROR = 1

if EXIT_ON_ERROR:
    logger.error("-----")
    logger.error("Exiting due to configuration errors.")
    logger.error("Create {APP_PATH}/.env file with the following environment variables:")
    logger.error("JWT_SECRET_KEY")
    logger.error("API_KEY_ENCRYPTION_KEY")
    logger.error("-----")
    sys.exit(1)

# --- CORS Configuration ---
# Parse comma-separated origins into a list, default to ["*"] (allow all)
CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
# Parse comma-separated methods into a list, default to common HTTP methods
CORS_ALLOW_METHODS = os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,DELETE,OPTIONS,PATCH").split(",")
# Parse comma-separated headers into a list, default to ["*"] (allow all)
CORS_ALLOW_HEADERS = os.getenv("CORS_ALLOW_HEADERS", "*").split(",")
# Parse boolean string, default to True
CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "True").lower() in ("true", "1", "t", "yes")
