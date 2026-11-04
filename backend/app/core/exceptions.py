"""
Domain exceptions and the global error envelope.

Every error response has the same shape so the frontend can always show a readable
message::

    {"success": false, "error": "<human readable message>", "detail": <optional>}
"""
import logging
from typing import Any, Optional

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("educore.exceptions")


class AppBaseException(Exception):
    """Root application exception carrying an HTTP status code."""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, detail: Any = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class AuthenticationError(AppBaseException):
    def __init__(self, message: str = "Authentication required. Please log in again."):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(AppBaseException):
    def __init__(self, message: str = "You do not have permission to perform this action."):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)


class NotFoundError(AppBaseException):
    def __init__(self, message: str = "The requested record was not found."):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class ConflictError(AppBaseException):
    def __init__(self, message: str):
        super().__init__(message, status_code=status.HTTP_409_CONFLICT)


class ServiceUnavailableError(AppBaseException):
    def __init__(self, message: str):
        super().__init__(message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


def _envelope(status_code: int, message: str, detail: Optional[Any] = None, headers=None) -> JSONResponse:
    body = {"success": False, "error": message}
    if detail is not None:
        body["detail"] = detail
    return JSONResponse(status_code=status_code, content=body, headers=headers)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


async def app_exception_handler(request: Request, exc: AppBaseException) -> JSONResponse:
    log = logger.warning if exc.status_code < 500 else logger.error
    log("request_id=%s %s %s -> %s %s", _request_id(request), request.method, request.url.path,
        exc.status_code, exc.message)
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return _envelope(exc.status_code, exc.message, exc.detail, headers)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    if exc.status_code == 401 and message == "Not authenticated":
        message = "Authentication required. Please log in."
    return _envelope(exc.status_code, message, None, getattr(exc, "headers", None))


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for err in exc.errors():
        location = [str(part) for part in err.get("loc", ()) if part not in ("body", "query", "path")]
        errors.append({"field": ".".join(location) or None, "message": err.get("msg", "Invalid value")})
    first = errors[0] if errors else {"field": None, "message": "Invalid request"}
    message = f"{first['field']}: {first['message']}" if first["field"] else first["message"]
    return _envelope(422, message, errors)


async def global_catchall_handler(request: Request, exc: Exception) -> JSONResponse:
    # Never leak exception text to clients; the request id ties the response to the log.
    logger.exception("request_id=%s Unhandled error on %s %s", _request_id(request), request.method, request.url.path)
    return _envelope(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "Something went wrong on our side. Please try again.",
        {"request_id": _request_id(request)},
    )
