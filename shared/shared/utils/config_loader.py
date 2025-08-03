# shared/config/loader.py
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Iterable
import os
import yaml
from dotenv import dotenv_values

# repo root
_REPO_ROOT = Path(__file__).resolve()
while _REPO_ROOT.name != "glam-app":
    if _REPO_ROOT.parent == _REPO_ROOT:
        raise RuntimeError("Unable to locate glam-app root directory")
    _REPO_ROOT = _REPO_ROOT.parent

_CONFIG_DIR = _REPO_ROOT / "config"
_SHARED_CONFIG = _CONFIG_DIR / "shared.yml"
_SVC_CFG_DIR = _CONFIG_DIR / "services"
_SERVICES_DIR = _REPO_ROOT / "services"

def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open() as f:
        return yaml.safe_load(f) or {}

def _deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out = a.copy()
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out

def _load_service_dotenv(service: str) -> None:
    """Load services/{service}/.env for local runs only. Never override existing env."""
    if os.path.exists("/.dockerenv") or os.getenv("DISABLE_DOTENV") == "1":
        return
    p = _SERVICES_DIR / service / ".env"
    if not p.is_file():
        return
    for k, v in (dotenv_values(p) or {}).items():
        if v is not None and k not in os.environ:
            os.environ[k] = v

def merged_config(
    service: str,
    *,
    passthrough_env: Iterable[str] = ("DATABASE_URL",),
) -> Dict[str, Any]:
    """shared.yml < service.yml, plus selected raw env keys (no prefixes)."""
    _load_service_dotenv(service)

    cfg = _deep_merge(
        _load_yaml(_SHARED_CONFIG),
        _load_yaml(_SVC_CFG_DIR / f"{service}.yml"),
    )

    for k in passthrough_env:
        if k in os.environ and k not in cfg:
            cfg[k] = os.environ[k]
    return cfg

def flatten_config(data: dict, parent_key: str = "", sep: str = ".") -> dict:
    items: list[tuple[str, Any]] = []
    for k, v in data.items():
        nk = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_config(v, nk, sep=sep).items())
        else:
            items.append((nk, v))
    return dict(items)
