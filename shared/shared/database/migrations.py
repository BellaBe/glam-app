# glam-app/shared/database/migrations.py
import os
from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
import logging

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages Alembic migrations for a microservice"""
    
    def __init__(
        self,
        service_name: str,
        alembic_ini_path: str,
        migrations_path: str,
        database_url: str
    ):
        self.service_name = service_name
        self.alembic_ini_path = Path(alembic_ini_path)
        self.migrations_path = Path(migrations_path)
        self.database_url = database_url
        
        # Verify paths exist
        if not self.alembic_ini_path.exists():
            raise FileNotFoundError(f"Alembic config not found: {alembic_ini_path}")
        
        # Create migrations directory if it doesn't exist
        self.migrations_path.mkdir(parents=True, exist_ok=True)
    
    def get_alembic_config(self) -> Config:
        """Get Alembic configuration"""
        config = Config(str(self.alembic_ini_path))
        config.set_main_option("sqlalchemy.url", self.database_url)
        config.set_main_option("script_location", str(self.migrations_path))
        return config
    
    def init_alembic(self):
        """Initialize Alembic for the service (run once)"""
        config = self.get_alembic_config()
        command.init(config, str(self.migrations_path))
        logger.info(f"Initialized Alembic for {self.service_name}")
    
    def create_migration(self, message: str):
        """Create a new migration"""
        config = self.get_alembic_config()
        command.revision(config, message=message, autogenerate=True)
        logger.info(f"Created migration: {message}")
    
    def upgrade(self, revision: str = "head"):
        """Apply migrations up to a specific revision"""
        config = self.get_alembic_config()
        command.upgrade(config, revision)
        logger.info(f"Upgraded database to {revision}")
    
    def downgrade(self, revision: str):
        """Downgrade to a specific revision"""
        config = self.get_alembic_config()
        command.downgrade(config, revision)
        logger.info(f"Downgraded database to {revision}")
    
    def get_current_revision(self) -> str:
        """Get the current migration revision"""
        config = self.get_alembic_config()
        # This would require more implementation
        return "Not implemented"
    
    async def ensure_schema_exists(self, engine: AsyncEngine, schema_name: str):
        """Ensure a database schema exists (PostgreSQL specific)"""
        async with engine.connect() as conn:
            await conn.execute(
                text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
            )
            await conn.commit()
        logger.info(f"Ensured schema exists: {schema_name}")


def create_alembic_env_template(service_name: str, base_module: str) -> str:
    """Generate env.py template for a service"""
    return f'''"""Alembic environment script for {service_name}"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import your service's Base metadata
from {base_module} import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={{"paramstyle": "named"}},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''