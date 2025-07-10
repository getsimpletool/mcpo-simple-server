"""
Logging middleware for FastAPI
Logs incoming requests and their responses
"""

import logging
import time
from fastapi import FastAPI, Request

# Configure logger
logger = logging.getLogger("api")


class RequestLoggingMiddleware:
    """Middleware to log request information"""

    async def __call__(self, request: Request, call_next):
        """Process the request and log information about it"""
        # Generate a unique request ID
        request_id = str(time.time())

        # Log the request
        logger.info(
            "Request %s: %s %s",
            request_id,
            request.method,
            request.url.path
        )

        # Process the request
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log the response
            logger.info(
                "Response %s: %s completed in %.3fs",
                request_id,
                response.status_code,
                process_time
            )
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "Error %s: %s occurred after %.3fs",
                request_id,
                str(e),
                process_time
            )
            raise


def add_logging_middleware(app: FastAPI) -> None:
    """Add the request logging middleware to the FastAPI application"""
    app.middleware("http")(RequestLoggingMiddleware())
