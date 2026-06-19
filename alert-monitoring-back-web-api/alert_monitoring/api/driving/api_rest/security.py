import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

_EXCLUDED_PATHS = {
    "/docs",
    "/openapi.json",
    "/redoc",
    "/health-check/health",
    "/health-check/info",
}


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Validates X-Api-Key header when API_KEY env var is set.

    When API_KEY is not configured the middleware is a no-op, allowing
    local development without credentials.
    """

    def __init__(self, app, api_key: str | None = None) -> None:
        super().__init__(app)
        self._api_key = api_key

    async def dispatch(self, request: Request, call_next):
        if not self._api_key or request.url.path in _EXCLUDED_PATHS:
            return await call_next(request)
        key = request.headers.get("X-Api-Key")
        if key != self._api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized"},
            )
        return await call_next(request)
