# shared/shared/utils/config_loader.py

import os
from pathlib import Path

from dotenv import load_dotenv


def load_root_env():
    """Load .env from repository root"""
    # Don't load in Docker containers
    if os.path.exists("/.dockerenv"):
        return
    # Find repo root
    current = Path(__file__).resolve()
    while current.name != "glam-app":
        if current.parent == current:
            break
        current = current.parent
    else:
        # Determine which env file to load
        env_name = os.getenv("APP_ENV", "local")
        infrastructure_dir = current / "infrastructure"

        # Load environment-specific file
        env_file = infrastructure_dir / f".env.{env_name}"
        if env_file.exists():
            load_dotenv(env_file, override=False)
            return

        # Fallback to .env.local
        env_file = infrastructure_dir / ".env.local"
        if env_file.exists():
            load_dotenv(env_file, override=False)
