"""
Application configuration using Pydantic BaseSettings.

Configuration values can be set via environment variables or .env file.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Default CORS origins for development
DEFAULT_CORS_ORIGINS: list[str] = [
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:5173",
]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application settings
    app_name: str = "TinySA Frequency Scanner"
    app_version: str = "0.1.0"
    debug: bool = False

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS settings
    # Set via ALLOWED_ORIGINS env var as comma-separated list
    # Example: ALLOWED_ORIGINS="https://myapp.example.com,https://api.example.com"
    # If not set, defaults to localhost origins for development
    cors_origins: list[str] = DEFAULT_CORS_ORIGINS

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """
        Parse CORS origins from comma-separated string or list.

        Also checks ALLOWED_ORIGINS env var for backward compatibility.
        """
        # Check for ALLOWED_ORIGINS env var (backward compatibility)
        allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "")
        if allowed_origins_env:
            return [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

        # Handle standard CORS_ORIGINS value
        if isinstance(v, str):
            if not v.strip():
                return DEFAULT_CORS_ORIGINS
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v if v else DEFAULT_CORS_ORIGINS

    # Database settings
    database_url: str = "sqlite:///./frequency_scanner.db"

    # TinySA serial settings
    serial_port: str = "/dev/cu.usbmodem4001"
    serial_baudrate: int = 115200
    serial_timeout: float = 1.0

    # Scan settings
    default_start_freq: int = 400_000_000  # 400 MHz
    default_stop_freq: int = 700_000_000  # 700 MHz
    default_points: int = 450


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: The application settings singleton.
    """
    return Settings()
