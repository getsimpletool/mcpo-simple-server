from fastapi import HTTPException, status
from loguru import logger
from mcpo_simple_server.services import get_config_service


async def get_number_of_users() -> int:
    """Return the number of users in the system."""
    config_service = get_config_service()

    if not config_service:
        logger.error("Config manager not set in auth dependencies")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error",
        )

    try:
        all_users_dict = await config_service.user_config.get_all_users_configs()
        return len(all_users_dict)
    except Exception as e:
        logger.error(f"Error getting user count: {str(e)} - return 0")
        return 0
