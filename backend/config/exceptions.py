"""
Custom DRF exception handler.
All errors return the standard envelope:
{
    "success": false,
    "status_code": <int>,
    "message": "<human-readable summary>",
    "data": null,
    "errors": <detail>
}
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import (
    ValidationError,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    NotFound,
    MethodNotAllowed,
    Throttled,
)

logger = logging.getLogger("config.exceptions")

_STATUS_MESSAGES = {
    400: "Bad request. Please check the submitted data.",
    401: "Authentication required. Please log in.",
    403: "You do not have permission to perform this action.",
    404: "The requested resource was not found.",
    405: "Method not allowed.",
    429: "Too many requests. Please slow down.",
    500: "An unexpected error occurred. Please try again later.",
}


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        request = context.get("request")
        logger.exception(
            "Unhandled exception on %s",
            request.path if request else "unknown",
            exc_info=exc,
        )
        return Response(
            {
                "success": False,
                "status_code": 500,
                "message": _STATUS_MESSAGES[500],
                "data": None,
                "errors": None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    code = response.status_code

    if isinstance(exc, ValidationError):
        message = "Validation failed. Please correct the errors below."
        errors = response.data
    elif isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        message = "Authentication required. Please log in."
        errors = None
    elif isinstance(exc, PermissionDenied):
        message = "You do not have permission to perform this action."
        errors = None
    elif isinstance(exc, NotFound):
        message = "The requested resource was not found."
        errors = None
    elif isinstance(exc, MethodNotAllowed):
        message = f"HTTP method not allowed on this endpoint."
        errors = None
    elif isinstance(exc, Throttled):
        wait = getattr(exc, "wait", None)
        message = f"Rate limit exceeded. Try again in {int(wait)}s." if wait else "Rate limit exceeded."
        errors = None
    else:
        message = _STATUS_MESSAGES.get(code, "An error occurred.")
        errors = None

    response.data = {
        "success": False,
        "status_code": code,
        "message": message,
        "data": None,
        "errors": errors,
    }
    return response
