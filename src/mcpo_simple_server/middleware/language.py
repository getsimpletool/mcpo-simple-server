from typing import Callable

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from mcpo_simple_server import i18n


async def language_processor(request: Request, call_next: Callable) -> Response:
    """Process language settings from request and set appropriate locale.

    This middleware extracts the preferred language from:
    1. Query parameter 'language'
    2. Cookie 'language'
    3. Accept-Language header

    It then sets the locale for the current request and stores it in a cookie.
    """
    # Try to get locale from query params, cookies, or Accept-Language header
    locale = request.query_params.get("language")
    if not locale:
        locale = request.cookies.get("language")
        if not locale:
            accept_language = request.headers.get("Accept-Language")
            if accept_language:
                # Parse the Accept-Language header (e.g., 'en-US,en;q=0.9')
                try:
                    locale = accept_language.split(",")[0].split(";")[0].replace("-", "_")
                except (IndexError, AttributeError):
                    locale = None

    # Get the list of supported locales
    supported_locales = i18n.get_supported_locales()

    # Set the locale if it's supported, otherwise fall back to 'en'
    if locale and locale in supported_locales:
        i18n.set_locale(locale)
    else:
        i18n.set_locale("en")

    # Process the request
    response = await call_next(request)

    # Set the language cookie if we have a valid locale
    current_locale = i18n.get_locale()
    if current_locale:
        response.set_cookie(
            key="language",
            value=current_locale,
            max_age=86400 * 30,  # 30 days
            httponly=True
        )

    return response


def add_language_middleware(app: FastAPI) -> None:
    """Add the language processing middleware to the FastAPI application"""
    app.middleware("http")(language_processor)
