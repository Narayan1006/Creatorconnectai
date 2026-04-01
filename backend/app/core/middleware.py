"""
Optional request logging middleware for /api/* routes.

Logs the HTTP method and path for every request that hits the API prefix.
Wire it up in main.py with::

    from app.core.middleware import APIRequestLoggingMiddleware
    app.add_middleware(APIRequestLoggingMiddleware)
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("api.requests")


class APIRequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs method, path, status code, and duration for all /api/* requests."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path.startswith("/api/"):
            start = time.monotonic()
            response = await call_next(request)
            duration_ms = (time.monotonic() - start) * 1000
            logger.info(
                "%s %s -> %d (%.1f ms)",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
            )
            return response
        return await call_next(request)
