"""CDC FluView / ILINet — the classic "influenza-like illness" measure.

ILI = the share of outpatient visits that were for fever plus cough/sore throat.
It's the long-running yardstick people mean by "flu activity."

We read it through the Delphi Epidata API (Carnegie Mellon), which mirrors CDC
FluView as a clean, documented, free JSON endpoint — easier and more stable than
CDC's own dashboard export.
Docs: https://cmu-delphi.github.io/delphi-epidata/api/fluview.html
"""
from datetime import date, timedelta
from typing import Optional

from ..config import HISTORY_WEEKS, LIVE
from ..models import MetricPoint, Provenance, Series
from ..trends import compute_trend
from .base import load_fixture, http_get_json, now_iso, to_float

API_URL = "https://api.delphi.cmu.edu/epidata/fluview/"
FLUVIEW_PAGE = "https://www.cdc.gov/fluview/index.html"
REGION = "mn"  # Delphi uses lowercase 2-letter state codes


def _mmwr_week1_start(year: int) -> date:
    """First day (Sunday) of MMWR epiweek 1 for a given year."""
    jan1 = date(year, 1, 1)
    sunday_idx = (jan1.weekday() + 1) % 7          # Mon=0..Sun=6  ->  Sun=0..Sat=6
    sunday = jan1 - timedelta(days=sunday_idx)     # the Sunday on/before Jan 1
    # If Jan 1 falls Sun..Wed, the week containing it is week 1; otherwise week 1
    # is the following week.
    return sunday if sunday_idx <= 3 else sunday + timedelta(days=7)


def epiweek_to_saturday(epiweek: int) -> str:
    """Convert an MMWR epiweek (YYYYWW) to its week-ending Saturday (ISO date)."""
    year, week = divmod(epiweek, 100)
    start = _mmwr_week1_start(year) + timedelta(weeks=week - 1)
    return (start + timedelta(days=6)).isoformat()


def _fetch_raw() -> dict:
    if LIVE:
        # Ask for a generous range and just keep the most recent weeks returned.
        today = date.today()
        params = {
            "regions": REGION,
            "epiweeks": f"{(today.year - 1) * 100 + 30}-{today.year * 100 + 30}",
        }
        return http_get_json(API_URL, params=params, cache_key="cdc_ili")
    return load_fixture("cdc_ili")


def get_series() -> list[Series]:
    raw = _fetch_raw()
    rows = raw.get("epidata", []) if isinstance(raw, dict) else []
    rows = sorted(rows, key=lambda r: r.get("epiweek", 0))

    points = [
        MetricPoint(
            date=epiweek_to_saturday(r["epiweek"]),
            value=to_float(r.get("wili")),  # weighted % ILI
        )
        for r in rows
        if r.get("epiweek")
    ][-HISTORY_WEEKS:]

    if not points:
        return []

    values = [p.value for p in points]
    trend, trend_label = compute_trend(values)
    current = next((p for p in reversed(points) if p.value is not None), None)

    return [
        Series(
            virus="Influenza",
            signal="ili_pct",
            signal_label="% flu-like illness (ILINet)",
            unit="%",
            points=points,
            provenance=Provenance(
                source_short="CDC FluView (ILINet)",
                source_name="CDC Outpatient Influenza-like Illness Surveillance Network",
                source_url=FLUVIEW_PAGE,
                geography="Minnesota (statewide)",
                geography_level="state",
                api_url=API_URL if LIVE else None,
                data_through=points[-1].date if points else None,
                fetched_at=now_iso(),
                is_sample=not LIVE,
                notes="Via the Delphi Epidata API (mirrors CDC FluView). Published at state level only.",
            ),
            current_value=current.value if current else None,
            current_date=current.date if current else None,
            trend=trend,
            trend_label=trend_label,
            description="Share of clinic visits for fever plus cough or sore throat.",
        )
    ]
