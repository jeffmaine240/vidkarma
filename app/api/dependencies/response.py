import json
from typing import Any, Dict, List, Optional, Union

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def success_response(
    status_code: int,
    message: str = "Request successful",
    data: Optional[Union[Dict[str, Any], List[Any]]] = None,
) -> JSONResponse:
    """
    Standardized success response format.

    Args:
        status_code (int): HTTP status code
        message (str): Human-readable success message
        data (Optional): Optional response payload

    Returns:
        JSONResponse: Standardized success JSON response
    """
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder({
            "status": "success",
            "status_code": status_code,
            "message": message,
            "data": data or {}
        }),
    )


def error_response(
    status_code: int,
    message: str = "An error occurred",
    errors: Optional[Union[str, Dict[str, Any], List[Dict[str, Any]]]] = None,
) -> JSONResponse:
    """
    Standardized error response format.

    Args:
        status_code (int): HTTP error status
        message (str): Error message
        errors (Optional): Error detail (e.g., field issues, exceptions)

    Returns:
        JSONResponse: Standardized error JSON response
    """
    # Try to decode JSON error strings if passed as raw strings
    parsed_errors = errors
    if isinstance(errors, str):
        try:
            parsed_errors = json.loads(errors)
        except json.JSONDecodeError:
            parsed_errors = {"detail": errors}

    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder({
            "status": "error",
            "status_code": status_code,
            "message": message,
            "errors": parsed_errors or {},
        }),
    )
