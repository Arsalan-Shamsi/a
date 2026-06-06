"""Shared plumbing for data sources: load a SAMPLE fixture or fetch LIVE data."""
import json
from datetime import datetime, timezone
from typing import Optional

from .. import cache
from ..config import FIXTURES_DIR, HTTP_TIMEOUT_SECONDS, SOCRATA_APP_TOKEN


def now_iso() -> str:
    """Current UTC time, e.g. 2026-06-06T14:00:00Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def to_float(value) -> Optional[float]:
    """Socrata returns numbers as strings; turn them into floats safely."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def first_present(row: dict, candidates: list[str]):
    """Return the first candidate key that exists in ``row`` (with a value).

    We use this for sources whose exact field names we documented but could not
    byte-verify against the live API. It tries each plausible name in turn.
    """
    for key in candidates:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return None


def load_fixture(name: str):
    """Read bundled SAMPLE data from ``data/fixtures/<name>.json``."""
    return json.loads((FIXTURES_DIR / f"{name}.json").read_text())


def http_get_json(url: str, params: Optional[dict] = None, cache_key: Optional[str] = None):
    """Fetch JSON in LIVE mode, with caching.

    ``httpx`` is imported lazily so that SAMPLE mode has zero third-party needs.
    """
    if cache_key:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
    import httpx  # local import: only needed when actually going live

    headers = {"User-Agent": "local-illness-dashboard/0.1 (personal, educational)"}
    if SOCRATA_APP_TOKEN:
        headers["X-App-Token"] = SOCRATA_APP_TOKEN
    resp = httpx.get(url, params=params, headers=headers, timeout=HTTP_TIMEOUT_SECONDS)
    resp.raise_for_status()
    data = resp.json()
    if cache_key:
        cache.put(cache_key, data)
    return data
