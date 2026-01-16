"""
Structured logging configuration for the TinySA Coordinator backend.

Provides custom formatters, request ID context management, and logging setup
utilities for consistent logging throughout the application.
"""

import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional

# Context variable for request ID tracking across async operations
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_request_id() -> Optional[str]:
    """Get the current request ID from context."""
    return request_id_var.get()


def set_request_id(request_id: Optional[str]) -> None:
    """Set the request ID in the current context."""
    request_id_var.set(request_id)


class StructuredFormatter(logging.Formatter):
    """Custom log formatter with structured output.

    Provides consistent log format with:
    - ISO 8601 timestamp with timezone
    - Log level
    - Module/logger name
    - Request ID (when available)
    - Message

    Format: TIMESTAMP | LEVEL | MODULE | [REQUEST_ID] | MESSAGE
    """

    def __init__(
        self,
        include_request_id: bool = True,
        datefmt: Optional[str] = None,
    ) -> None:
        """Initialize the formatter.

        Args:
            include_request_id: Whether to include request ID in log output
            datefmt: Date format string (defaults to ISO 8601)
        """
        super().__init__(datefmt=datefmt)
        self.include_request_id = include_request_id

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with structured output."""
        # Generate ISO 8601 timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        # Get log level with consistent width
        level = record.levelname.ljust(8)

        # Get the module name
        module = record.name

        # Build the base message
        parts = [timestamp, level, module]

        # Add request ID if available and enabled
        if self.include_request_id:
            request_id = get_request_id()
            if request_id:
                parts.append(f"[{request_id}]")
            else:
                parts.append("[-]")

        # Add the actual message
        message = record.getMessage()
        parts.append(message)

        formatted = " | ".join(parts)

        # Add exception info if present
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)

        return formatted


class JSONFormatter(logging.Formatter):
    """JSON log formatter for machine-readable output.

    Useful for log aggregation systems and production deployments.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        import json

        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request ID if available
        request_id = get_request_id()
        if request_id:
            log_data["request_id"] = request_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add any extra fields
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data)


def setup_logging(
    level: str = "INFO",
    json_format: bool = False,
    include_request_id: bool = True,
) -> None:
    """Configure application logging.

    Sets up the root logger and configures formatters for consistent
    logging across all modules.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON formatter instead of structured text
        include_request_id: Include request ID in log output
    """
    # Convert level string to logging constant
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create the appropriate formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = StructuredFormatter(include_request_id=include_request_id)

    # Configure the handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Configure specific loggers

    # Application loggers - use configured level
    for logger_name in ["backend", "uvicorn.access"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)

    # Third-party loggers - reduce noise
    for logger_name in ["uvicorn.error", "sqlalchemy.engine"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)

    # Log startup message
    logging.getLogger("backend.core.logging").info(
        f"Logging configured: level={level}, format={'json' if json_format else 'structured'}"
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.

    Convenience function that ensures loggers are properly namespaced
    under the 'backend' hierarchy.

    Args:
        name: Logger name (will be prefixed with 'backend.' if not already)

    Returns:
        Configured logger instance
    """
    if not name.startswith("backend."):
        name = f"backend.{name}"
    return logging.getLogger(name)
