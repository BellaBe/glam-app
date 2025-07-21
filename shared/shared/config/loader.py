from __future__ import annotations
from pathlib import Path
from typing import Any, Dict

import os
import yaml
from dotenv import load_dotenv


_REPO_ROOT = Path(__file__).resolve()    

while _REPO_ROOT.name != "glam-app":
    if _REPO_ROOT.parent == _REPO_ROOT:
        raise RuntimeError("Unable to locate glam-app root directory")
    _REPO_ROOT = _REPO_ROOT.parent

_CONFIG_DIR = _REPO_ROOT / "config"                     # ./config
_SHARED_CONFIG = _CONFIG_DIR / "shared.yml"            # ./config/shared.yml
_SVC_CFG_DIR = _CONFIG_DIR / "services"                 # ./config/services
_ENV_FILE = _REPO_ROOT / ".env"                         # optional


# Check if files exist
print(f"\nFile existence check:")
print(f"  .env exists: {_ENV_FILE.exists()}")
print(f"  shared.yml exists: {_SHARED_CONFIG.exists()}")
print(f"  config/services/ exists: {_SVC_CFG_DIR.exists()}")

# Load .env once so os.environ is ready (local runs)
if _ENV_FILE.exists():
    load_dotenv(_ENV_FILE)


def _load_yaml_file(path: Path) -> Dict[str, Any]:
    """Load a YAML file and return dict"""
    if not path.is_file():
        return {}
    with path.open() as f:
        return yaml.safe_load(f) or {}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries, override takes precedence"""
    result = base.copy()
    
    for key, value in override.items():
        if (key in result and 
            isinstance(result[key], dict) and 
            isinstance(value, dict)):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def merged_config(service: str, *, env_prefix: str) -> Dict[str, Any]:
    """
    Load configuration in order of precedence:
    1. config/shared.yml              -> baseline shared config
    2. config/services/{service}.yml  -> service-specific config  
    3. Environment variables           -> runtime overrides
    
    YAML                      -> baseline
    (prefixed) env variables  -> override keys in YAML
    RESULT                    -> dict ready for Pydantic
    """
    
    # 1. Load shared configuration (baseline)
    cfg = _load_yaml_file(_SHARED_CONFIG)
    
    # 2. Load service-specific configuration and merge
    service_config_path = _SVC_CFG_DIR / f"{service}.yml"
    if not service_config_path.is_file():
        raise FileNotFoundError(f"Service config not found: {service_config_path}")
    
    service_config = _load_yaml_file(service_config_path)
    cfg = _deep_merge(cfg, service_config)
    
    # 3. Apply environment variable overrides
    prefix = f"{env_prefix.upper()}_"
    for key, val in os.environ.items():
        if key.startswith(prefix):
            yaml_key = key[len(prefix):].lower()
            
            # Handle nested keys with double underscore
            if "__" in yaml_key:
                parts = yaml_key.split("__")
                current = cfg
                
                # Navigate/create nested structure
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # Set the final value
                current[parts[-1]] = val
            else:
                cfg[yaml_key] = val
    
    return cfg

def flatten_config(data: dict, parent_key: str = '', sep: str = '.') -> dict:
    """Flatten nested dict for Pydantic validation_alias to work"""
    items = []
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_config(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)