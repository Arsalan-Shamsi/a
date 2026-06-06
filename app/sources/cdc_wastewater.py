"""CDC NWSS — wastewater viral activity levels for COVID-19, flu A, and RSV.

Wastewater is the hardest signal to game: it measures virus shed into the sewer
by everyone in the area, sick or not, tested or not. That makes it a great fit
for a "trustworthy data" dashboard.

Dataset: "CDC Wastewater Viral Activity Level for SARS-CoV-2, Influenza A and RSV"
Resource id: atcp-73re  (data.cdc.gov)

The number (WVAL) is a normalized "activity level"; CDC sorts it into official
buckets Minimal -> Low -> Moderate -> High -> Very High (see app/trends.py).

Geography: filtered to WASTEWATER_COUNTY (config) when the data carries county
detail; otherwise it falls back to statewide and says so.
"""
from typing import Optional

from ..config import HISTORY_WEEKS, LIVE, STATE_ABBR, WASTEWATER_COUNTY
from ..models import MetricPoint, Provenance, Series
from ..trends import compute_trend, wval_category
from .base import first_present, load_fixture, http_get_json, now_iso, to_float

RESOURCE_ID = "atcp-73re"
LANDING_URL = (
    "https://data.cdc.gov/Public-Health-Surveillance/"
    "CDC-Wastewater-Viral-Activity-Level-for-SARS-CoV-2/atcp-73re"
)
API_URL = f"https://data.cdc.gov/resource/{RESOURCE_ID}.json"
METADATA_URL = "https://data.cdc.gov/api/views/atcp-73re.json"

# --- Field names: documented, but the most uncertain of our sources ----------
# VERIFY (LIVE): confirm the exact column names first with:
#   curl "https://data.cdc.gov/api/views/atcp-73re.json"   (lists columns)
#   curl "https://data.cdc.gov/resource/atcp-73re.json?\$limit=2"
# We try several plausible names for each field so a small naming difference
# won't silently break the dashboard.
F_DATE = ["date_end", "week_end", "date", "data_collection_period_end"]
F_STATE = ["wwtp_jurisdiction", "reporting_jurisdiction", "state", "geography"]
F_PATHOGEN = ["pcr_target", "pathogen"]
F_VALUE = ["wva_level", "activity_level", "wva_level_value", "percentile"]
F_CATEGORY = ["wva_level_category", "activity_level_category", "category"]
F_COUNTY = ["county_names", "county", "counties", "wwtp_county"]


def _normalize_pathogen(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    s = str(raw).lower()
    if "cov" in s:
        return "COVID-19"
    if "flu" in s or "influenza" in s:
        return "Influenza"
    if "rsv" in s:
        return "RSV"
    return None


def _county_match(row: dict, county: str) -> bool:
    value = first_present(row, F_COUNTY)
    return bool(value) and county.lower() in str(value).lower()


def _fetch_raw() -> list[dict]:
    if LIVE:
        # Fetch all rows for the state; we filter to the county in code so a
        # missing/oddly-named county column degrades gracefully instead of erroring.
        params = {
            "$where": f"{F_STATE[0]}='{STATE_ABBR}'",
            "$order": f"{F_DATE[0]} DESC",
            "$limit": 10000,
        }
        return http_get_json(API_URL, params=params, cache_key="cdc_wastewater")
    return load_fixture("cdc_wastewater")


def get_series() -> list[Series]:
    rows = _fetch_raw()

    # Narrow to the configured county if that detail is present; otherwise keep
    # everything and report it as statewide.
    county_rows = [r for r in rows if _county_match(r, WASTEWATER_COUNTY)] if WASTEWATER_COUNTY else []
    use_county = bool(county_rows)
    working_rows = county_rows if use_county else rows

    if use_county:
        geography = f"{WASTEWATER_COUNTY} County, {STATE_ABBR}"
        geography_level = "county"
        notes = "Virus measured in sewage; independent of testing or doctor visits."
    else:
        geography = f"Minnesota ({STATE_ABBR}, statewide)"
        geography_level = "state"
        notes = "Virus measured in sewage; independent of testing or doctor visits."
        if WASTEWATER_COUNTY:
            notes += f" County-level data was not available, so this shows statewide."

    by_virus: dict[str, list[dict]] = {}
    for row in working_rows:
        virus = _normalize_pathogen(first_present(row, F_PATHOGEN))
        if virus is not None:
            by_virus.setdefault(virus, []).append(row)

    out: list[Series] = []
    for virus, vrows in by_virus.items():
        vrows.sort(key=lambda r: first_present(r, F_DATE) or "")
        points, categories = [], []
        for r in vrows:
            value = to_float(first_present(r, F_VALUE))
            points.append(MetricPoint(date=first_present(r, F_DATE), value=value))
            # Prefer CDC's own category label; fall back to deriving it ourselves.
            categories.append(first_present(r, F_CATEGORY) or wval_category(value))
        points, categories = points[-HISTORY_WEEKS:], categories[-HISTORY_WEEKS:]

        values = [p.value for p in points]
        trend, trend_label = compute_trend(values)
        current = next((p for p in reversed(points) if p.value is not None), None)
        current_category = next((c for c in reversed(categories) if c), None)

        out.append(
            Series(
                virus=virus,
                signal="wastewater_wval",
                signal_label="Wastewater activity level",
                unit="WVAL",
                points=points,
                provenance=Provenance(
                    source_short="CDC NWSS",
                    source_name=(
                        "CDC National Wastewater Surveillance System — "
                        "Viral Activity Level"
                    ),
                    source_url=LANDING_URL,
                    geography=geography,
                    geography_level=geography_level,
                    api_url=API_URL if LIVE else None,
                    data_through=points[-1].date if points else None,
                    fetched_at=now_iso(),
                    is_sample=not LIVE,
                    notes=notes,
                ),
                current_value=current.value if current else None,
                current_date=current.date if current else None,
                level_category=current_category,
                trend=trend,
                trend_label=trend_label,
                description="How much of this virus is showing up in local sewage.",
            )
        )
    return out
