"""
Application configuration using Pydantic BaseSettings.

Configuration values can be set via environment variables or .env file.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    cors_origins: List[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
    ]

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
