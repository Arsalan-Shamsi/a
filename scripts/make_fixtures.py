"""Generate realistic SAMPLE fixtures shaped like the real API responses.

Run from the repo root:   .venv/bin/python scripts/make_fixtures.py

The point of these files is that the app runs and looks right with no network.
They are clearly labelled as SAMPLE in the UI. The shapes here mirror what the
live CDC (Socrata) and Delphi Epidata APIs return, so the same parser handles
both. The story we model: a late-spring week in Minnesota — flu and RSV fading
after winter, COVID drifting slightly up.
"""
import json
import random
from datetime import date, timedelta
from pathlib import Path

# Make the app importable when run from the repo root.
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.sources.cdc_ili import epiweek_to_saturday  # noqa: E402
from app.trends import wval_category                  # noqa: E402

FIXTURES = Path(__file__).resolve().parent.parent / "data" / "fixtures"
WEEKS = 12
rng = random.Random(42)  # deterministic, so fixtures are reproducible


def recent_saturdays(n: int, on_or_before: date) -> list[date]:
    """The n most recent week-ending Saturdays, oldest first."""
    d = on_or_before
    while d.weekday() != 5:  # 5 == Saturday
        d -= timedelta(days=1)
    return [d - timedelta(weeks=i) for i in range(n - 1, -1, -1)]


def ramp(start: float, end: float, i: int, n: int, jitter: float) -> float:
    """A point on a line from start->end with a little deterministic noise."""
    base = start + (end - start) * (i / (n - 1))
    noisy = base * (1 + rng.uniform(-jitter, jitter))
    return max(0.0, round(noisy, 2))


def saturday_to_epiweek(d: date) -> int:
    """Inverse of epiweek_to_saturday, by searching nearby epiweeks."""
    for y in (d.year, d.year - 1, d.year + 1):
        for wk in range(1, 54):
            if epiweek_to_saturday(y * 100 + wk) == d.isoformat():
                return y * 100 + wk
    raise ValueError(f"no epiweek for {d}")


# Latest complete week sits about a week before "today" (2026-06-06).
saturdays = recent_saturdays(WEEKS, on_or_before=date(2026, 5, 30))

# --- CDC NSSP: % of ER visits (Socrata returns numbers as strings) -----------
nssp_curves = {
    "COVID-19": (0.38, 0.90, 0.05),   # a summer uptick (clearly rising)
    "Influenza": (2.60, 0.34, 0.08),  # fading after winter
    "RSV": (0.70, 0.12, 0.10),        # fading after winter
}
nssp_rows = []
for pathogen, (start, end, jit) in nssp_curves.items():
    for i, sat in enumerate(saturdays):
        nssp_rows.append({
            "week_end": sat.isoformat(),
            "geography": "Minnesota",
            "pathogen": pathogen,
            "percent_visits": f"{ramp(start, end, i, WEEKS, jit):.2f}",
        })

# --- CDC NWSS: wastewater viral activity level (with CDC's category label) ----
ww_curves = {
    "sars-cov-2": (1.6, 4.1, 0.05),   # rising, into "Moderate"
    "influenza a": (3.1, 1.1, 0.07),  # falls to "Minimal"
    "rsv": (1.5, 0.7, 0.10),
}
ww_rows = []
for target, (start, end, jit) in ww_curves.items():
    for i, sat in enumerate(saturdays):
        level = ramp(start, end, i, WEEKS, jit)
        ww_rows.append({
            "date_end": sat.isoformat(),
            "wwtp_jurisdiction": "MN",
            "county_names": "Hennepin County",  # so the county filter has a match
            "pcr_target": target,
            "wva_level": f"{level:.2f}",
            "wva_level_category": wval_category(level),
        })

# --- CDC FluView / ILINet via Delphi Epidata (returns numbers + epiweeks) -----
ili_rows = []
latest_ew = saturday_to_epiweek(saturdays[-1])
for i, sat in enumerate(saturdays):
    wili = ramp(3.0, 1.0, i, WEEKS, 0.07)
    ili_rows.append({
        "region": "mn",
        "epiweek": saturday_to_epiweek(sat),
        "num_ili": int(wili * 220),
        "num_patients": 22000,
        "num_providers": 40,
        "wili": wili,
        "ili": round(wili * 0.96, 2),
        "release_date": date(2026, 6, 6).isoformat(),
        "issue": latest_ew,
        "lag": 0,
    })
ili_payload = {"result": 1, "epidata": ili_rows, "message": "success"}

# --- CDC NSSP sub-state trends (rdmq-nq56): local DIRECTION for the county -----
# Each county row carries its Health Service Area name + a trend word per virus.
# We emit the last few weeks; the app uses the most recent. Story matches the
# curves above: COVID rising, flu and RSV falling.
ed_trend_rows = []
for sat in saturdays[-4:]:
    ed_trend_rows.append({
        "week_end": sat.isoformat() + "T00:00:00.000",
        "geography": "Minnesota",
        "county": "Hennepin",
        "ed_trends_covid": "Increasing",
        "ed_trends_influenza": "Decreasing",
        "ed_trends_rsv": "Decreasing",
        "hsa": "Hennepin (Minneapolis), MN",
        "hsa_counties": "Anoka, Carver, Hennepin, Scott",
        "hsa_nci_id": "999",
        "fips": "27053",
        "trend_source": "HSA",
        "buildnumber": date(2026, 6, 6).isoformat(),
    })

FIXTURES.mkdir(parents=True, exist_ok=True)
(FIXTURES / "cdc_nssp.json").write_text(json.dumps(nssp_rows, indent=2))
(FIXTURES / "cdc_wastewater.json").write_text(json.dumps(ww_rows, indent=2))
(FIXTURES / "cdc_ili.json").write_text(json.dumps(ili_payload, indent=2))
(FIXTURES / "cdc_ed_trends.json").write_text(json.dumps(ed_trend_rows, indent=2))

print(f"Wrote fixtures for {WEEKS} weeks ending {saturdays[-1].isoformat()}:")
print(f"  cdc_nssp.json        {len(nssp_rows)} rows")
print(f"  cdc_wastewater.json  {len(ww_rows)} rows")
print(f"  cdc_ili.json         {len(ili_rows)} weeks")
print(f"  cdc_ed_trends.json   {len(ed_trend_rows)} rows (local HSA direction)")
