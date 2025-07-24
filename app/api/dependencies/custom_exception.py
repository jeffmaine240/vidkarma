from typing import Callable, Optional, Dict, Any
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.api.dependencies.response import error_response
from app.core.config import Config


class BaseAppException(Exception):
    """Custom base exception for our app"""
    def __init__(self, message: Optional[str] = None, errors: Optional[Dict[str, Any]] = None):
        self.message = message or f"An error occurred in {Config.APP_NAME}"
        self.errors = errors or {}
        super().__init__(self.message)

class GoogleOAuthConfigError(BaseAppException):
    """Exception for Google OAuth configuration errors."""
    def __init__(self, message: str = "Google OAuth configuration error", errors: Optional[Dict[str, Any]] = None):
        super().__init__(message, errors)
        
class UserAlreadyExistsError(BaseAppException):
    """Exception raised when trying to create a user that already exists."""
    def __init__(self, message: str = "User already exists", errors: Optional[Dict[str, Any]] = None):
        super().__init__(message, errors)
        

class InvalidCredentialsError(BaseAppException):
    """Exception raised for invalid user credentials."""
    def __init__(self, message: str = "Invalid credentials provided", errors: Optional[Dict[str, Any]] = None):
        super().__init__(message, errors)
        
class InvalidTokenError(BaseAppException):
    """Exception raised for invalid or expired tokens."""
    def __init__(self, message: str = "Invalid or expired token", errors: Optional[Dict[str, Any]] = None):
        super().__init__(message, errors)
        
class GoogleInitiationError(BaseAppException):
    """Exception raised for failed Google Initiation tokens."""
    def __init__(self, message: str = "Google Initiation failed", errors: Optional[Dict[str, Any]] = None):
        super().__init__(message, errors)

class ServerError(BaseAppException):
    """Exception raised for server failure."""
    def __init__(self, message: str = "Server Error", errors: Optional[Dict[str, Any]] = None):
        super().__init__(message, errors)


class OauthError(BaseAppException):
    """Exception raised for failed Google Initiation tokens."""
    def __init__(self, message: str = "Authentication failed", errors: Optional[Dict[str, Any]] = None):
        super().__init__(message, errors)
 
        
def create_rate_limit_exception_handler(
    status_code: int,
    default_message: str
) -> Callable[[Request, Exception], JSONResponse]:
    async def exception_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        message = getattr(exc, "message", default_message)
        errors = getattr(exc, "errors", {})
        return error_response(
            status_code=status_code,
            message=message,
            errors=errors,
        )
    return exception_handler

def create_exception_handler(
    status_code: int,
    default_message: str
) -> Callable[[Request, Exception], JSONResponse]:
    async def exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
        message = getattr(exc, "message", default_message)
        errors = getattr(exc, "errors", {})
        return error_response(
            status_code=status_code,
            message=message,
            errors=errors,
        )
    return exception_handler
