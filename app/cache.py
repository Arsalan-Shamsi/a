"""A tiny on-disk cache.

In LIVE mode we save each API response to ``data/cache`` and reuse it for a few
hours. That keeps us from hammering CDC's servers and means the dashboard still
loads if a source is briefly unavailable. SAMPLE mode never touches this.
"""
import json
import time
from pathlib import Path

from .config import CACHE_DIR, CACHE_TTL_SECONDS


def _path(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"


def get(key: str):
    """Return cached data if it exists and is still fresh, else None."""
    p = _path(key)
    if not p.exists():
        return None
    if time.time() - p.stat().st_mtime > CACHE_TTL_SECONDS:
        return None
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def put(key: str, value) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _path(key).write_text(json.dumps(value))
