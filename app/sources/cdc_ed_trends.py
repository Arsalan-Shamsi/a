"""CDC NSSP — the LOCAL emergency-department visit trend for your county's area.

Companion to cdc_nssp.py. The state dataset gives a numeric percentage but no
sub-state detail; THIS dataset gives CDC's official rising/falling *direction*
for each county's Health Service Area (HSA) — the most local emergency-department
signal CDC publishes. It carries no percentage, only a direction, so we present
it as a labelled "local direction" rather than a number.

Dataset: "NSSP Emergency Department Visit Trajectories by State and Sub State Regions"
Resource id: rdmq-nq56  (data.cdc.gov)
"""
from typing import Optional

from ..config import LIVE, LOCAL_COUNTY
from ..models import Provenance, Series
from .base import load_fixture, http_get_json, now_iso

RESOURCE_ID = "rdmq-nq56"
LANDING_URL = (
    "https://data.cdc.gov/Public-Health-Surveillance/"
    "NSSP-Emergency-Department-Visit-Trajectories-by-St/rdmq-nq56/about_data"
)
API_URL = f"https://data.cdc.gov/resource/{RESOURCE_ID}.json"

# Field names confirmed from a live sample of the dataset.
F_DATE = "week_end"
F_COUNTY = "county"
F_HSA = "hsa"
# Each virus has its own trend column:
TREND_FIELD = {
    "COVID-19": "ed_trends_covid",
    "Influenza": "ed_trends_influenza",
    "RSV": "ed_trends_rsv",
}


def _map_trend(raw: Optional[str]):
    """CDC's words -> our (code, label). Unknown/unavailable -> (None, label)."""
    s = (raw or "").strip().lower()
    if "increas" in s:
        return "rising", "Rising"
    if "decreas" in s:
        return "falling", "Falling"
    if "stable" in s or "no change" in s:
        return "stable", "Holding steady"
    return None, "Not reported locally"  # "Data Unavailable", "Sparse", blank


def _fetch_raw() -> list[dict]:
    if LIVE:
        params = {
            "$where": f"{F_COUNTY}='{LOCAL_COUNTY}'",
            "$order": f"{F_DATE} DESC",
            "$limit": 50,
        }
        return http_get_json(API_URL, params=params, cache_key="cdc_ed_trends")
    return load_fixture("cdc_ed_trends")


def get_series() -> list[Series]:
    rows = _fetch_raw()
    if not rows:
        return []
    rows.sort(key=lambda r: r.get(F_DATE, ""))
    latest = rows[-1]
    # Read the HSA name straight from the data, so the label is always truthful.
    hsa = latest.get(F_HSA) or f"{LOCAL_COUNTY} County area"
    week = (latest.get(F_DATE) or "")[:10]  # trim any time portion

    out: list[Series] = []
    for virus, field in TREND_FIELD.items():
        trend, label = _map_trend(latest.get(field))
        out.append(
            Series(
                virus=virus,
                signal="ed_local_trend",
                signal_label="ER visits — local direction (CDC)",
                unit="",
                points=[],  # trend-only: there is no numeric series here
                provenance=Provenance(
                    source_short="CDC NSSP (local)",
                    source_name=(
                        "CDC NSSP — Emergency Department Visit Trajectories "
                        "by Sub-State Region (HSA)"
                    ),
                    source_url=LANDING_URL,
                    geography=hsa,
                    geography_level="substate",
                    api_url=API_URL if LIVE else None,
                    data_through=week or None,
                    fetched_at=now_iso(),
                    is_sample=not LIVE,
                    notes=(
                        "CDC's official trend for the Health Service Area that "
                        f"includes {LOCAL_COUNTY} County. Direction only — no number."
                    ),
                ),
                current_value=None,
                current_date=week or None,
                trend=trend,
                trend_label=label,
                description="Whether local ER visits for this illness are rising or falling.",
            )
        )
    return out
