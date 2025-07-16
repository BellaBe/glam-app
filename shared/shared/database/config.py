# glam-app/shared/database/config.py
from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Any, Dict


class DatabaseConfig(BaseSettings):
    # ── connection ─────────────────────────────────────────────
    DB_HOST: str
    DB_PORT: int = 5432
    DB_PORT_EXTERNAL: int | None = None
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_ENABLED: bool = True

    # ── pool / driver ──────────────────────────────────────────
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_PRE_PING: bool = True
    DB_POOL_RECYCLE: int = 3600
    DB_ASYNC_DRIVER: str = "asyncpg"
    DB_ECHO: bool = False

    # defaults: `.env` at repo root, strict case match
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,          # "CREDIT_DB_HOST" must match exactly
        populate_by_name=True,
    )

    # ── helpers ────────────────────────────────────────────────
    def model_post_init(self, _ctx: Any) -> None:
        if self.DB_PORT is None:
            if self.DB_HOST in {"localhost", "127.0.0.1", "host.docker.internal"}:
                self.DB_PORT = self.DB_PORT_EXTERNAL or 5432
            else:
                self.DB_PORT = 5432

    @property
    def effective_port(self) -> int:
        """Return host-side port when talking to localhost, else the container port."""
        if self.DB_HOST in {"localhost", "127.0.0.1", "host.docker.internal"}:
            return self.DB_PORT_EXTERNAL or self.DB_PORT
        return self.DB_PORT
    
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+{self.DB_ASYNC_DRIVER}://"
            f"{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.effective_port}/{self.DB_NAME}"
        )

    def engine_kwargs(self) -> Dict[str, Any]:
        return dict(
            echo=self.DB_ECHO,
            pool_size=self.DB_POOL_SIZE,
            max_overflow=self.DB_MAX_OVERFLOW,
            pool_pre_ping=self.DB_POOL_PRE_PING,
            pool_recycle=self.DB_POOL_RECYCLE,
        )


def create_database_config(prefix: str) -> DatabaseConfig:
    """Factory that applies the per-service prefix (CREDIT_, NOTIFICATION_, …)."""
    class Prefixed(DatabaseConfig):
        model_config = SettingsConfigDict(
            env_prefix=prefix,         # CREDIT_DB_HOST, etc.
            env_file=".env",
            case_sensitive=True,
            populate_by_name=True,
        )
    return Prefixed() # type: ignore[call-arg]
