"""
Custom exception classes for the TinySA Coordinator application.

Defines domain-specific exceptions that are mapped to appropriate HTTP
error responses via the error handling middleware. All exceptions follow
RFC 7807 Problem Details format conventions.
"""

from typing import Any


class AppException(Exception):
    """Base exception for all application errors.

    Provides a consistent structure for error responses following
    RFC 7807 Problem Details specification.

    Attributes:
        message: Human-readable explanation of the error
        status_code: HTTP status code for the error response
        error_code: Machine-readable error code (e.g., "device_not_connected")
        details: Additional context about the error
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "internal_error",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)

    def to_problem_details(self) -> dict[str, Any]:
        """Convert exception to RFC 7807 Problem Details format.

        Returns:
            Dictionary conforming to RFC 7807 with type, title, status,
            detail, and any additional context.
        """
        response = {
            "type": f"https://tinysa.local/errors/{self.error_code}",
            "title": self.error_code.replace("_", " ").title(),
            "status": self.status_code,
            "detail": self.message,
        }
        if self.details:
            response.update(self.details)
        return response


# ============================================================================
# Device Exceptions (4xx - Client Errors)
# ============================================================================


class DeviceError(AppException):
    """Base exception for device-related errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "device_error",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code, error_code, details)


class DeviceNotConnectedError(DeviceError):
    """Raised when an operation requires a connected device but none is connected."""

    def __init__(
        self,
        message: str = "No TinySA device is connected",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=503,
            error_code="device_not_connected",
            details=details,
        )


class DeviceConnectionError(DeviceError):
    """Raised when connection to the TinySA device fails."""

    def __init__(
        self,
        message: str = "Failed to connect to TinySA device",
        port: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        extra_details = details or {}
        if port:
            extra_details["port"] = port
        super().__init__(
            message=message,
            status_code=400,
            error_code="device_connection_failed",
            details=extra_details,
        )


class DeviceAlreadyConnectedError(DeviceError):
    """Raised when trying to connect to a device when one is already connected."""

    def __init__(
        self,
        message: str = "A device is already connected",
        current_port: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        extra_details = details or {}
        if current_port:
            extra_details["current_port"] = current_port
        super().__init__(
            message=message,
            status_code=409,
            error_code="device_already_connected",
            details=extra_details,
        )


class DeviceCommunicationError(DeviceError):
    """Raised when communication with the device fails after connection."""

    def __init__(
        self,
        message: str = "Communication with TinySA device failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=502,
            error_code="device_communication_error",
            details=details,
        )


# ============================================================================
# Scan Exceptions
# ============================================================================


class ScanError(AppException):
    """Base exception for scan-related errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "scan_error",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code, error_code, details)


class ScanInProgressError(ScanError):
    """Raised when trying to start a scan while one is already running."""

    def __init__(
        self,
        message: str = "A scan is already in progress",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=409,
            error_code="scan_in_progress",
            details=details,
        )


class ScanConfigurationError(ScanError):
    """Raised when scan configuration is invalid."""

    def __init__(
        self,
        message: str = "Invalid scan configuration",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=422,
            error_code="scan_configuration_invalid",
            details=details,
        )


class ScanDataError(ScanError):
    """Raised when there's an issue with scan data."""

    def __init__(
        self,
        message: str = "Error processing scan data",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code="scan_data_error",
            details=details,
        )


# ============================================================================
# Export Exceptions
# ============================================================================


class ExportError(AppException):
    """Base exception for export-related errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "export_error",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code, error_code, details)


class ExportFormatError(ExportError):
    """Raised when an unsupported export format is requested."""

    def __init__(
        self,
        message: str = "Unsupported export format",
        requested_format: str | None = None,
        supported_formats: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        extra_details = details or {}
        if requested_format:
            extra_details["requested_format"] = requested_format
        if supported_formats:
            extra_details["supported_formats"] = supported_formats
        super().__init__(
            message=message,
            status_code=400,
            error_code="export_format_unsupported",
            details=extra_details,
        )


class ExportDataError(ExportError):
    """Raised when scan data cannot be exported."""

    def __init__(
        self,
        message: str = "Cannot export scan data",
        scan_id: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        extra_details = details or {}
        if scan_id is not None:
            extra_details["scan_id"] = scan_id
        super().__init__(
            message=message,
            status_code=400,
            error_code="export_data_error",
            details=extra_details,
        )


# ============================================================================
# Resource Exceptions (404 - Not Found)
# ============================================================================


class ResourceNotFoundError(AppException):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: Any | None = None,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        extra_details = details or {}
        extra_details["resource_type"] = resource_type
        if resource_id is not None:
            extra_details["resource_id"] = resource_id

        if message is None:
            if resource_id is not None:
                message = f"{resource_type} with ID {resource_id} not found"
            else:
                message = f"{resource_type} not found"

        super().__init__(
            message=message,
            status_code=404,
            error_code="resource_not_found",
            details=extra_details,
        )


class ScanNotFoundError(ResourceNotFoundError):
    """Raised when a requested scan is not found."""

    def __init__(
        self,
        scan_id: int,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            resource_type="Scan",
            resource_id=scan_id,
            message=message,
            details=details,
        )


class PresetNotFoundError(ResourceNotFoundError):
    """Raised when a requested preset is not found."""

    def __init__(
        self,
        preset_id: int,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            resource_type="Preset",
            resource_id=preset_id,
            message=message,
            details=details,
        )


# ============================================================================
# Permission Exceptions (403 - Forbidden)
# ============================================================================


class ForbiddenError(AppException):
    """Raised when an operation is forbidden."""

    def __init__(
        self,
        message: str = "Operation not permitted",
        error_code: str = "forbidden",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=403,
            error_code=error_code,
            details=details,
        )


class BuiltinPresetModificationError(ForbiddenError):
    """Raised when trying to modify or delete a built-in preset."""

    def __init__(
        self,
        operation: str = "modify",
        preset_id: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        extra_details = details or {}
        extra_details["operation"] = operation
        if preset_id is not None:
            extra_details["preset_id"] = preset_id

        super().__init__(
            message=f"Built-in presets cannot be {operation}d",
            error_code="builtin_preset_protected",
            details=extra_details,
        )


# ============================================================================
# Validation Exceptions (422 - Unprocessable Entity)
# ============================================================================


class ValidationError(AppException):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        errors: list[dict[str, Any]] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        extra_details = details or {}
        if errors:
            extra_details["validation_errors"] = errors

        super().__init__(
            message=message,
            status_code=422,
            error_code="validation_error",
            details=extra_details,
        )


# ============================================================================
# Database Exceptions
# ============================================================================


class DatabaseError(AppException):
    """Raised when a database operation fails."""

    def __init__(
        self,
        message: str = "Database operation failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code="database_error",
            details=details,
        )
