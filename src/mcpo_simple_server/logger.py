import sys
import os
from loguru import logger
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Configure loguru
# Temporarily set default log level to DEBUG to see debug messages
log_level = os.getenv("LOG_LEVEL", "INFO").upper()

# Remove default handler
logger.remove()
# Strip non-ascii characters from log messages


def _strip_non_ascii(record):
    record["message"] = record["message"].encode("ascii", "ignore").decode("ascii")


logger = logger.patch(_strip_non_ascii)
# Customize level colors
logger.level("INFO", color="<green>")
logger.level("DEBUG", color="<cyan>")
logger.level("WARNING", color="<yellow>")
logger.level("ERROR", color="<red>")
logger.level("CRITICAL", color="<red><bold>")

# Define format strings for different log levels
INFO_FORMAT = "<level>{level.name}</level>:     {message}"
DEBUG_FORMAT = "<level>{level.name}</level>:    {message}"
ERROR_FORMAT = "<level>{level.name}</level>:    [<level>!!</level>] {message}"
CRITICAL_FORMAT = "<level>{level.name}</level>: [<level>!!!</level>] {message}"
WARNING_FORMAT = "<level>{level.name}</level>:  [<level>!</level>] {message}"
DEFAULT_FORMAT = "<level>{level.name}</level>: {message}"

def custom_formatter(record):
    level_name = record["level"].name
    if level_name == "INFO":
        return INFO_FORMAT + "\n"
    elif level_name == "DEBUG":
        return DEBUG_FORMAT + "\n"
    elif level_name == "ERROR":
        return ERROR_FORMAT + "\n"
    elif level_name == "CRITICAL":
        return CRITICAL_FORMAT + "\n"
    elif level_name == "WARNING":
        return WARNING_FORMAT + "\n"
    else:
        return DEFAULT_FORMAT + "\n"

# Add a single handler that respects the log_level environment variable and uses custom formatting
logger.add(sys.stderr, level=log_level, format=custom_formatter, colorize=True)


logger.info(f"Log level (env LOG_LEVEL): {log_level}")
