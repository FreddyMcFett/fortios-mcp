"""Application configuration loaded from environment variables."""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

_ENV_FILE = Path(".env")


def _check_env_file_permissions() -> None:
    """Warn if the .env file is world-readable."""
    if not _ENV_FILE.exists():
        return
    try:
        mode = _ENV_FILE.stat().st_mode
        if mode & 0o077:
            logger.warning(
                ".env file permissions are %s — consider chmod 600 to protect secrets.",
                oct(mode & 0o777),
            )
    except OSError:
        pass


class Settings(BaseSettings):
    """Environment-driven configuration for the FortiOS MCP server."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    FORTIOS_HOST: str = Field(default="", description="FortiGate hostname or IP.")
    FORTIOS_PORT: int = Field(default=443, ge=1, le=65535)
    FORTIOS_API_TOKEN: str = Field(default="", description="REST API admin token.")
    FORTIOS_VERIFY_SSL: bool = Field(default=True)
    FORTIOS_TIMEOUT: int = Field(default=30, ge=1, le=300)
    FORTIOS_MAX_RETRIES: int = Field(default=3, ge=0, le=10)
    FORTIOS_DEFAULT_VDOM: str = Field(default="root")
    FORTIOS_ENABLE_WRITES: bool = Field(
        default=False,
        description="If false, all mutating tools refuse to run.",
    )

    MCP_SERVER_MODE: str = Field(default="auto")
    MCP_SERVER_HOST: str = Field(default="0.0.0.0")
    MCP_SERVER_PORT: int = Field(default=8002, ge=1, le=65535)
    MCP_AUTH_TOKEN: str | None = Field(default=None)
    MCP_ALLOWED_HOSTS: list[str] = Field(default_factory=list)

    FORTIOS_TOOL_MODE: str = Field(default="full", description="'full' or 'dynamic'.")

    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: Path | None = Field(default=None)
    LOG_FORMAT: str = Field(
        default="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    @field_validator("MCP_SERVER_MODE")
    @classmethod
    def _valid_mode(cls, v: str) -> str:
        if v not in {"auto", "stdio", "http"}:
            raise ValueError("MCP_SERVER_MODE must be 'auto', 'stdio' or 'http'")
        return v

    @field_validator("FORTIOS_TOOL_MODE")
    @classmethod
    def _valid_tool_mode(cls, v: str) -> str:
        if v not in {"full", "dynamic"}:
            raise ValueError("FORTIOS_TOOL_MODE must be 'full' or 'dynamic'")
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def _valid_log_level(cls, v: str) -> str:
        v = v.upper()
        if v not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("LOG_LEVEL must be a standard level name")
        return v

    @field_validator("MCP_ALLOWED_HOSTS", mode="before")
    @classmethod
    def _split_hosts(cls, v: object) -> object:
        if isinstance(v, str):
            return [h.strip() for h in v.split(",") if h.strip()]
        return v

    def require_credentials(self) -> None:
        """Raise RuntimeError if mandatory connection settings are missing."""
        missing = []
        if not self.FORTIOS_HOST:
            missing.append("FORTIOS_HOST")
        if not self.FORTIOS_API_TOKEN:
            missing.append("FORTIOS_API_TOKEN")
        if missing:
            raise RuntimeError("Missing required environment variables: " + ", ".join(missing))

    def configure_logging(self) -> None:
        """Apply logging configuration globally."""
        level = getattr(logging, self.LOG_LEVEL)
        handlers: list[logging.Handler] = [logging.StreamHandler()]
        if self.LOG_FILE:
            self.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(self.LOG_FILE))
        for h in handlers:
            h.setLevel(level)
            h.setFormatter(logging.Formatter(self.LOG_FORMAT))
        root = logging.getLogger()
        root.handlers.clear()
        root.setLevel(level)
        for h in handlers:
            root.addHandler(h)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)


@lru_cache
def get_settings() -> Settings:
    """Return the cached Settings instance."""
    _check_env_file_permissions()
    return Settings()


def reset_settings_cache() -> None:
    """Clear the cached settings; used in tests."""
    get_settings.cache_clear()
    os.environ.pop("_FORTIOS_MCP_SETTINGS", None)
