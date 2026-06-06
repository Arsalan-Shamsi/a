"""Central configuration for the local illness dashboard.

Anything you might want to change — your location, the SAMPLE/LIVE switch, the
exact field names CDC uses — lives here, so you only ever edit one file.
"""
import os
from pathlib import Path

# --- What this dashboard is "about" ------------------------------------------
LOCATION_LABEL = "Eden Prairie / Hennepin County, Minnesota"
STATE_NAME = "Minnesota"   # how CDC NSSP labels the state (its `geography` value)
STATE_ABBR = "MN"          # how CDC wastewater labels the state (a 2-letter code)

# --- LIVE vs SAMPLE data -----------------------------------------------------
# By default we serve bundled SAMPLE data, so the app runs anywhere with no
# network at all. On your own machine, set ILLNESS_LIVE=1 to pull real CDC data.
LIVE = os.environ.get("ILLNESS_LIVE", "0") == "1"

# Optional free Socrata app token. NOT required; it just raises rate limits.
SOCRATA_APP_TOKEN = os.environ.get("SOCRATA_APP_TOKEN", "").strip()

# --- Paths -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
FIXTURES_DIR = BASE_DIR / "data" / "fixtures"
CACHE_DIR = BASE_DIR / "data" / "cache"
STATIC_DIR = BASE_DIR / "static"

# --- Behaviour ---------------------------------------------------------------
HISTORY_WEEKS = 12                 # how many recent weeks each trend line shows
CACHE_TTL_SECONDS = int(os.environ.get("ILLNESS_CACHE_TTL", str(12 * 3600)))
HTTP_TIMEOUT_SECONDS = 30
