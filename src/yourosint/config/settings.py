"""Application settings management using Pydantic Settings."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """System-wide configuration with environment variable overrides."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core
    ENVIRONMENT: str = Field(default="development")
    LOG_LEVEL: str = Field(default="INFO")
    DEBUG: bool = Field(default=False)
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/yourosint",
        description="Async database connection URL",
    )
    SQLITE_FALLBACK: bool = Field(
        default=True,
        description="Fallback to SQLite when PostgreSQL is unavailable",
    )
    REDIS_URL: str | None = Field(default=None)

    # Privacy & Blind Index (HMAC-SHA256)
    BLIND_INDEX_KEY: str = Field(
        default="dev-insecure-blind-index-key-change-in-prod-v1",
        description="HMAC secret key for blind index generation",
    )
    BLIND_INDEX_KEY_VERSION: str = Field(default="v1")
    OBJECT_HASH_SALT: str = Field(default="dev-salt-change-in-prod")

    # Telegram Credentials
    TELEGRAM_API_ID: int = Field(default=0)
    TELEGRAM_API_HASH: str = Field(default="")
    TELEGRAM_BOT_TOKEN: str | None = Field(default=None)
    TELEGRAM_SESSION_DIR: Path = Field(default=Path("sessions"))

    # Proxy
    PROXY_ADDR: str | None = Field(default=None)
    PROXY_PORT: int | None = Field(default=None)
    PROXY_SECRET: str | None = Field(default=None)

    # Ingestion & Rate Limiting
    PARSER_BASE_DELAY: float = Field(default=0.8)
    PARSER_MAX_DELAY: float = Field(default=5.0)
    PARSER_RPM_LIMIT: int = Field(default=100)
    PARSER_BATCH_SIZE: int = Field(default=100)

    # Threat Intelligence & OSINT APIs
    VIRUSTOTAL_API_KEY: str | None = Field(default=None)
    ABUSEIPDB_API_KEY: str | None = Field(default=None)
    WHOIS_API_KEY: str | None = Field(default=None)


def get_settings() -> Settings:
    """Singleton getter for application configuration."""
    return Settings()
