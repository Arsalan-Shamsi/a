"""Central configuration for the local illness dashboard.

Anything you might want to change — your area, the SAMPLE/LIVE switch, the exact
field names CDC uses — lives here, so you only ever edit one file.
"""
import os
from pathlib import Path

# --- What area this dashboard covers -----------------------------------------
LOCATION_LABEL = "Eden Prairie / Hennepin County, Minnesota"

# CDC's feeds come at different geographic resolutions, so we configure each.
# These defaults are safe and known to work; localize the LIVE data by following
# the README section "Localizing to your area" once you know the exact labels.
STATE_NAME = "Minnesota"   # CDC NSSP statewide `geography` value
STATE_ABBR = "MN"          # CDC wastewater 2-letter jurisdiction code

# CDC NSSP emergency-department visits can be narrowed to a sub-state Health
# Service Area (HSA). None = whole state. To localize, set this to your area's
# EXACT HSA string (discover it live — see the README); for us that's the Twin
# Cities / Minneapolis HSA that contains Hennepin County.
NSSP_HSA = None

# CDC wastewater can be narrowed to sites serving a county (matched within the
# `county_names` field). None = statewide. "Hennepin" targets your county; if the
# live data has no county detail, the app falls back to statewide automatically.
WASTEWATER_COUNTY = "Hennepin"

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
