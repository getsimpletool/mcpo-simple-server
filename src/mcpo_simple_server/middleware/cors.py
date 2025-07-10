"""
CORS middleware for FastAPI
Handles Cross-Origin Resource Sharing (CORS) headers

This module configures CORS settings for the FastAPI application.
Settings can be controlled via environment variables defined in config.py.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcpo_simple_server.config import (
    CORS_ALLOW_ORIGINS,
    CORS_ALLOW_METHODS,
    CORS_ALLOW_HEADERS,
    CORS_ALLOW_CREDENTIALS,
)


def add_cors_middleware(
    app: FastAPI,
    allow_origins=None,
    allow_credentials=None,
    allow_methods=None,
    allow_headers=None,
) -> None:
    """
    Add CORS middleware to the FastAPI application

    Args:
        app: FastAPI application instance
        allow_origins: List of origins that should be permitted to make cross-origin requests
                      (defaults to CORS_ALLOW_ORIGINS from config)
        allow_credentials: Indicate that cookies should be supported for cross-origin requests
                          (defaults to CORS_ALLOW_CREDENTIALS from config)
        allow_methods: List of HTTP methods that should be allowed for cross-origin requests
                      (defaults to CORS_ALLOW_METHODS from config)
        allow_headers: List of HTTP request headers that should be supported for cross-origin requests
                      (defaults to CORS_ALLOW_HEADERS from config)
    """
    # Use environment-based config if parameters are not provided
    if allow_origins is None:
        allow_origins = CORS_ALLOW_ORIGINS

    if allow_methods is None:
        allow_methods = CORS_ALLOW_METHODS

    if allow_headers is None:
        allow_headers = CORS_ALLOW_HEADERS

    if allow_credentials is None:
        allow_credentials = CORS_ALLOW_CREDENTIALS

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
    )
