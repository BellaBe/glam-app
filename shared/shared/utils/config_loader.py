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
        env_file = current / ".env"
        if env_file.exists():
            load_dotenv(env_file, override=False)
