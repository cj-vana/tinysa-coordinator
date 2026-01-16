"""
FastAPI middleware for request tracing, logging, and error handling.

Provides:
- Request ID generation and propagation for distributed tracing
- Centralized exception handling with RFC 7807 Problem Details responses
"""

import logging
import time
import uuid
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.core.exceptions import AppException
from backend.core.logging import set_request_id
from backend.core.tinysa import TinySACommandError, TinySAConnectionError, TinySAError

logger = logging.getLogger(__name__)

# Content type for RFC 7807 Problem Details
PROBLEM_CONTENT_TYPE = "application/problem+json"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that generates and tracks request IDs.

    For each incoming request:
    1. Extracts existing X-Request-ID header or generates a new UUID
    2. Sets the request ID in context for logging
    3. Adds X-Request-ID to the response headers
    4. Logs request start and completion with timing
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and add request ID tracking."""
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())[:8]  # Short ID for readability

        # Set request ID in context for logging
        set_request_id(request_id)

        # Store request ID in request state for access in routes
        request.state.request_id = request_id

        # Log request start
        start_time = time.perf_counter()
        logger.info(
            f"Request started: {request.method} {request.url.path}"
        )

        try:
            # Process the request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log request completion
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"status={response.status_code} duration={duration_ms:.2f}ms"
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate duration even on error
            duration_ms = (time.perf_counter() - start_time) * 1000

            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"duration={duration_ms:.2f}ms error={str(e)}"
            )
            raise

        finally:
            # Clear request ID from context
            set_request_id(None)


# ============================================================================
# Exception Handlers (RFC 7807 Problem Details)
# ============================================================================


def create_problem_response(
    status_code: int,
    error_code: str,
    detail: str,
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    """Create an RFC 7807 Problem Details JSON response.

    Args:
        status_code: HTTP status code
        error_code: Machine-readable error code
        detail: Human-readable error description
        extra: Additional fields to include in the response

    Returns:
        JSONResponse with proper content type and structure
    """
    content: dict[str, Any] = {
        "type": f"https://tinysa.local/errors/{error_code}",
        "title": error_code.replace("_", " ").title(),
        "status": status_code,
        "detail": detail,
    }
    if extra:
        content.update(extra)

    return JSONResponse(
        status_code=status_code,
        content=content,
        media_type=PROBLEM_CONTENT_TYPE,
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions.

    Converts AppException instances to RFC 7807 Problem Details responses.
    """
    logger.warning(
        f"Application error: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "path": str(request.url.path),
            "method": request.method,
            "details": exc.details,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_problem_details(),
        media_type=PROBLEM_CONTENT_TYPE,
    )


async def tinysa_error_handler(request: Request, exc: TinySAError) -> JSONResponse:
    """Handle TinySA-specific exceptions.

    Maps TinySA exceptions from the core module to appropriate HTTP responses.
    """
    if isinstance(exc, TinySAConnectionError):
        error_code = "device_connection_failed"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif isinstance(exc, TinySACommandError):
        error_code = "device_command_failed"
        status_code = status.HTTP_502_BAD_GATEWAY
    else:
        error_code = "device_error"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    logger.error(
        f"TinySA error: {error_code} - {str(exc)}",
        extra={
            "error_code": error_code,
            "path": str(request.url.path),
            "method": request.method,
        },
    )

    return create_problem_response(
        status_code=status_code,
        error_code=error_code,
        detail=str(exc),
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle standard HTTP exceptions.

    Converts FastAPI/Starlette HTTPException to RFC 7807 format.
    """
    # Map common status codes to error codes
    error_code_map = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        409: "conflict",
        422: "validation_error",
        429: "too_many_requests",
        500: "internal_server_error",
        502: "bad_gateway",
        503: "service_unavailable",
        504: "gateway_timeout",
    }
    error_code = error_code_map.get(exc.status_code, "http_error")

    # Only log errors for 5xx status codes
    if exc.status_code >= 500:
        logger.error(
            f"HTTP error {exc.status_code}: {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "path": str(request.url.path),
                "method": request.method,
            },
        )
    else:
        logger.info(
            f"HTTP error {exc.status_code}: {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "path": str(request.url.path),
                "method": request.method,
            },
        )

    return create_problem_response(
        status_code=exc.status_code,
        error_code=error_code,
        detail=str(exc.detail) if exc.detail else f"HTTP {exc.status_code} Error",
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors.

    Converts Pydantic validation errors to RFC 7807 format with detailed
    error information for each invalid field.
    """
    errors = []
    for error in exc.errors():
        error_detail = {
            "loc": list(error.get("loc", [])),
            "msg": error.get("msg", "Validation error"),
            "type": error.get("type", "value_error"),
        }
        errors.append(error_detail)

    logger.info(
        f"Validation error on {request.method} {request.url.path}",
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "error_count": len(errors),
        },
    )

    return create_problem_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="validation_error",
        detail="Request validation failed",
        extra={"validation_errors": errors},
    )


async def pydantic_validation_handler(
    request: Request, exc: PydanticValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors that escape the request layer.

    These are typically errors from manual Pydantic model instantiation.
    """
    errors = []
    for error in exc.errors():
        error_detail = {
            "loc": list(error.get("loc", [])),
            "msg": error.get("msg", "Validation error"),
            "type": error.get("type", "value_error"),
        }
        errors.append(error_detail)

    logger.warning(
        f"Pydantic validation error: {len(errors)} errors",
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "error_count": len(errors),
        },
    )

    return create_problem_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="validation_error",
        detail="Data validation failed",
        extra={"validation_errors": errors},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions.

    Catches any unhandled exceptions and returns a generic 500 error.
    The actual exception details are logged but not exposed to the client
    for security reasons.
    """
    logger.exception(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}",
        extra={
            "path": str(request.url.path),
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
    )

    return create_problem_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="internal_server_error",
        detail="An unexpected error occurred. Please try again later.",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI application.

    This function should be called during application startup to set up
    centralized error handling.

    Args:
        app: The FastAPI application instance
    """
    # Custom application exceptions
    app.add_exception_handler(AppException, app_exception_handler)

    # TinySA-specific exceptions from the core module
    app.add_exception_handler(TinySAError, tinysa_error_handler)

    # Standard HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # Request validation errors (from path/query/body validation)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # Pydantic validation errors (from manual model instantiation)
    app.add_exception_handler(PydanticValidationError, pydantic_validation_handler)

    # Generic catch-all for unexpected errors
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered successfully")
