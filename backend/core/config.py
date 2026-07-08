"""
DefenSync System Configuration.
"""

from __future__ import annotations

import json
from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ==========================================================================
    # Application
    # ==========================================================================

    APP_NAME: str = "DefenSync - Behavioral Log Intelligence System"
    APP_DESCRIPTION: str = (
        "Multi-server behavioral log intelligence and security event analysis platform"
    )

    API_VERSION: str = "v1"
    API_PREFIX: str = "/api/v1"

    DEBUG: bool = False

    ENVIRONMENT: str = "development"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ==========================================================================
    # Database
    # ==========================================================================

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "defensync_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"

    @property
    def DATABASE_URL(self) -> str:
        """Return SQLAlchemy PostgreSQL connection URL."""
        return (
            f"postgresql+psycopg://"
            f"{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # ==========================================================================
    # JWT Security
    # ==========================================================================

    SECRET_KEY: SecretStr

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ==========================================================================
    # Default Admin Bootstrap
    # ==========================================================================

    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_EMAIL: str = "admin@defensync.local"
    DEFAULT_ADMIN_PASSWORD: SecretStr = SecretStr("Admin@123")

    # ==========================================================================
    # CORS
    # ==========================================================================

    ALLOWED_ORIGINS: str = "http://localhost:5173"
    @property
    def cors_origins(self) -> list[str]:
        """
        Return allowed CORS origins as a list.
        Accepts either a comma-separated string or a JSON list.
        """
        value = self.ALLOWED_ORIGINS
        if value.startswith("["):
            return json.loads(value)
        return [origin.strip() for origin in value.split(",") if origin.strip()]

    # ==========================================================================
    # Logging
    # ==========================================================================

    LOG_LEVEL: str = "INFO"

    # ==========================================================================
    # Background Scheduler (multi-server collection)
    # ==========================================================================

    SCHEDULER_ENABLED: bool = False
    COLLECTION_INTERVAL_MINUTES: int = 15
    COLLECTION_TAIL_LINES: int = 500

    # ==========================================================================
    # Server Health Monitoring
    # ==========================================================================

    HEALTH_CHECK_ENABLED: bool = True
    HEALTH_CHECK_INTERVAL_SECONDS: int = 30
    HEALTH_CHECK_TIMEOUT_SECONDS: float = 3.0
    HEALTH_CHECK_MAX_WORKERS: int = 20
    HEALTH_RECENT_WINDOW_SECONDS: int = 300

    # ==========================================================================
    # Pydantic Settings Configuration
    # ==========================================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    Using lru_cache ensures the configuration is loaded only once
    during the application's lifetime.
    """
    return Settings()