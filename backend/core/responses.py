"""
Standardized API response format.

Every endpoint returns:
{
    "success": bool,
    "status_code": int,
    "message": str,
    "data": any,        # payload on success
    "errors": any,      # validation errors on failure
    "meta": {           # pagination info, only on list endpoints
        "count": int,
        "total_pages": int,
        "current_page": int,
        "page_size": int,
        "next": str | null,
        "previous": str | null
    }
}
"""
from rest_framework.response import Response
from rest_framework import status


def success_response(
    data=None,
    message: str = "Success",
    status_code: int = status.HTTP_200_OK,
    meta: dict = None,
) -> Response:
    payload = {
        "success": True,
        "status_code": status_code,
        "message": message,
        "data": data,
        "errors": None,
    }
    if meta:
        payload["meta"] = meta
    return Response(payload, status=status_code)


def created_response(data=None, message: str = "Created successfully") -> Response:
    return success_response(data=data, message=message, status_code=status.HTTP_201_CREATED)


def error_response(
    message: str = "An error occurred",
    errors=None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> Response:
    return Response(
        {
            "success": False,
            "status_code": status_code,
            "message": message,
            "data": None,
            "errors": errors,
        },
        status=status_code,
    )


def not_found_response(resource: str = "Resource") -> Response:
    return error_response(
        message=f"{resource} not found.",
        status_code=status.HTTP_404_NOT_FOUND,
    )


def forbidden_response(message: str = "You do not have permission to perform this action.") -> Response:
    return error_response(message=message, status_code=status.HTTP_403_FORBIDDEN)
