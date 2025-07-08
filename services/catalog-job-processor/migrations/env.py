from __future__ import annotations

import os
from logging.config import fileConfig
from typing import Any

from alembic import context
from sqlalchemy import engine_from_config, pool

# ---------------------------------------------------- config boilerplate
config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

# ---------------------------------------------------- models import
from src.models import Base  # pylint: disable=wrong-import-position
target_metadata = Base.metadata

# ---------------------------------------------------- URL via env
db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise RuntimeError("Set DATABASE_URL (export or .env) before running Alembic")
config.set_main_option("sqlalchemy.url", db_url)

# ---------------------------------------------------- offline / online
def _run_offline() -> None:
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="public",
    )
    with context.begin_transaction():
        context.run_migrations()

def _run_online() -> None:
    connectable = engine_from_config(  # type: ignore[arg-type]
        config.get_section(config.config_ini_section) or {},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            version_table_schema="public",
        )
        with context.begin_transaction():
            context.run_migrations()

_run_offline() if context.is_offline_mode() else _run_online()
