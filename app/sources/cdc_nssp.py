"""CDC NSSP — percent of emergency-department visits for COVID-19, flu, and RSV.

This is the SPINE of the dashboard: weekly, per-virus, and it includes Minnesota.

Dataset: "2023 Respiratory Virus Response - NSSP Emergency Department Visits"
Resource id: vutn-jzwm  (data.cdc.gov, a public Socrata open-data platform)

The numbers mean: of all ER visits in the area that week, what share were for
this illness. Higher = the illness is sending more people to the ER right now.

Geography: defaults to the whole state. Set NSSP_HSA in config.py to narrow to a
sub-state Health Service Area (HSA) once you know its exact name.
"""
from ..config import HISTORY_WEEKS, LIVE, NSSP_HSA, STATE_NAME
from ..models import MetricPoint, Provenance, Series
from ..trends import compute_trend
from .base import load_fixture, http_get_json, now_iso, to_float

RESOURCE_ID = "vutn-jzwm"
LANDING_URL = (
    "https://data.cdc.gov/Public-Health-Surveillance/"
    "2023-Respiratory-Virus-Response-NSSP-Emergency-Dep/vutn-jzwm/about_data"
)
API_URL = f"https://data.cdc.gov/resource/{RESOURCE_ID}.json"

# --- Field names as documented by CDC ----------------------------------------
# VERIFY (LIVE): if live data looks empty or wrong, confirm these against:
#   curl "https://data.cdc.gov/resource/vutn-jzwm.json?\$limit=1"
F_DATE = "week_end"
F_GEO = "geography"
F_PATHOGEN = "pathogen"
F_VALUE = "percent_visits"

# CDC's pathogen label -> the virus name we use. (CDC also emits "Combined".)
PATHOGEN_MAP = {"COVID-19": "COVID-19", "Influenza": "Influenza", "RSV": "RSV"}


def _geography_filter() -> str:
    """The `geography` value to request: a sub-state HSA if set, else the state."""
    return NSSP_HSA or STATE_NAME


def _fetch_raw() -> list[dict]:
    if LIVE:
        params = {
            "$where": f"{F_GEO}='{_geography_filter()}'",
            "$order": f"{F_DATE} DESC",
            "$limit": 5000,
        }
        return http_get_json(API_URL, params=params, cache_key="cdc_nssp")
    return load_fixture("cdc_nssp")


def get_series() -> list[Series]:
    rows = _fetch_raw()

    by_virus: dict[str, list[dict]] = {}
    for row in rows:
        virus = PATHOGEN_MAP.get(row.get(F_PATHOGEN))
        if virus is not None:
            by_virus.setdefault(virus, []).append(row)

    out: list[Series] = []
    for virus, vrows in by_virus.items():
        vrows.sort(key=lambda r: r.get(F_DATE, ""))
        # Label the geography with whatever the data actually carries — truthful
        # in both SAMPLE and LIVE mode.
        geo_value = vrows[0].get(F_GEO) or _geography_filter()
        is_statewide = geo_value == STATE_NAME
        points = [
            MetricPoint(date=r.get(F_DATE), value=to_float(r.get(F_VALUE)))
            for r in vrows
        ][-HISTORY_WEEKS:]
        values = [p.value for p in points]
        trend, trend_label = compute_trend(values)
        current = next((p for p in reversed(points) if p.value is not None), None)

        out.append(
            Series(
                virus=virus,
                signal="ed_visits_pct",
                signal_label="% of ER visits",
                unit="%",
                points=points,
                provenance=Provenance(
                    source_short="CDC NSSP",
                    source_name=(
                        "CDC National Syndromic Surveillance Program — "
                        "Emergency Department Visits"
                    ),
                    source_url=LANDING_URL,
                    geography=(
                        f"{STATE_NAME} (statewide)" if is_statewide
                        else f"{geo_value} (sub-state area)"
                    ),
                    geography_level="state" if is_statewide else "substate",
                    api_url=API_URL if LIVE else None,
                    data_through=points[-1].date if points else None,
                    fetched_at=now_iso(),
                    is_sample=not LIVE,
                    notes="Based on ~80% of US emergency departments reporting.",
                ),
                current_value=current.value if current else None,
                current_date=current.date if current else None,
                trend=trend,
                trend_label=trend_label,
                description="Share of local ER visits that were for this illness.",
            )
        )
    return out
