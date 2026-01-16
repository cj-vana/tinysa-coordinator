"""Rate limiting configuration for the TinySA Frequency Scanner API.

Provides rate limiting using slowapi for REST endpoints and
connection limits for WebSocket connections.

Configuration is done via environment variables:
- RATE_LIMIT_ENABLED: Enable/disable rate limiting (default: true)
- RATE_LIMIT_DEFAULT: Default rate limit (default: "100/minute")
- RATE_LIMIT_DEVICE: Rate limit for device endpoints (default: "30/minute")
- RATE_LIMIT_HISTORY: Rate limit for history endpoints (default: "60/minute")
- RATE_LIMIT_EXPORT: Rate limit for export endpoints (default: "20/minute")
- WEBSOCKET_MAX_CONNECTIONS: Maximum concurrent WebSocket connections (default: 10)
"""

from __future__ import annotations

import logging
import os

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)


def get_real_client_ip(request: Request) -> str:
    """Extract the real client IP address from the request.

    Checks X-Forwarded-For and X-Real-IP headers for proxied requests,
    falls back to the direct client IP.

    Args:
        request: The FastAPI request object

    Returns:
        The client's IP address as a string
    """
    # Check X-Forwarded-For header (common for proxies/load balancers)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain (original client)
        return forwarded_for.split(",")[0].strip()

    # Check X-Real-IP header (nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct connection IP
    return get_remote_address(request)


class RateLimitConfig:
    """Configuration for rate limiting across the application."""

    def __init__(self) -> None:
        """Initialize rate limit configuration from environment variables."""
        self.enabled = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"

        # Rate limits for different endpoint categories
        self.default_limit = os.environ.get("RATE_LIMIT_DEFAULT", "100/minute")
        self.device_limit = os.environ.get("RATE_LIMIT_DEVICE", "30/minute")
        self.history_limit = os.environ.get("RATE_LIMIT_HISTORY", "60/minute")
        self.export_limit = os.environ.get("RATE_LIMIT_EXPORT", "20/minute")
        self.preset_limit = os.environ.get("RATE_LIMIT_PRESET", "60/minute")

        # WebSocket connection limit
        self.websocket_max_connections = int(os.environ.get("WEBSOCKET_MAX_CONNECTIONS", "10"))

        logger.info(
            f"Rate limiting {'enabled' if self.enabled else 'disabled'}: "
            f"default={self.default_limit}, device={self.device_limit}, "
            f"history={self.history_limit}, export={self.export_limit}, "
            f"websocket_max={self.websocket_max_connections}"
        )


# Global configuration instance
_config: RateLimitConfig | None = None


def get_rate_limit_config() -> RateLimitConfig:
    """Get the rate limit configuration singleton.

    Returns:
        The global RateLimitConfig instance
    """
    global _config
    if _config is None:
        _config = RateLimitConfig()
    return _config


# Create the limiter instance
# Uses in-memory storage by default (suitable for single-instance deployments)
limiter = Limiter(
    key_func=get_real_client_ip,
    default_limits=["100/minute"],
    enabled=True,  # Actual enable/disable is handled per-route
)


def get_limiter() -> Limiter:
    """Get the slowapi limiter instance.

    Returns:
        The configured Limiter instance
    """
    return limiter
