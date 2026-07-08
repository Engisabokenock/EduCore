from fastapi import Request, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("educore.exceptions")

class AppBaseException(Exception):
    """Root Application Exception."""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class AuthenticationError(AppBaseException):
    def __init__(self, message: str = "Invalid credentials or missing authorization"):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)

class AuthorizationError(AppBaseException):
    def __init__(self, message: str = "Insufficient privileges for resource execution"):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)

async def app_exception_handler(request: Request, exc: AppBaseException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.message}
    )

async def global_catchall_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled Runtime Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "error": "Internal System Error occurred."}
    )
