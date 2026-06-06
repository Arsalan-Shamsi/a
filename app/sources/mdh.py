"""Minnesota Department of Health (MDH) — the local, sub-state layer.

MDH publishes Minnesota-specific respiratory data (including the 7-county Twin
Cities metro, which *contains Hennepin County and Eden Prairie*). Its data lives
in CSV files attached to dashboards rather than a clean API, so wiring it up
robustly is a planned next step. For v1 we surface MDH as trustworthy *reference
links* a person can open to check the local picture themselves.

These pages were identified during source research; open them to confirm.
"""
from ..models import Provenance


def reference_sources() -> list[Provenance]:
    """MDH pages shown in the 'Sources & methods' section (not auto-pulled yet)."""
    ref = lambda name, url, notes: Provenance(  # noqa: E731 - tiny local helper
        source_short="MN Dept. of Health",
        source_name=name,
        source_url=url,
        geography="Minnesota (incl. 7-county Twin Cities metro / Hennepin)",
        geography_level="substate",
        role="reference",
        access="Public; published as CSV behind dashboards (planned for a later version)",
        is_sample=False,
        notes=notes,
    )
    return [
        ref(
            "MDH — Viral Respiratory Illness in Minnesota (data hub)",
            "https://www.health.state.mn.us/diseases/respiratory/stats/index.html",
            "Statewide hub for flu, COVID-19, and RSV surveillance.",
        ),
        ref(
            "MDH — Respiratory illness hospitalizations (RESP-NET)",
            "https://www.health.state.mn.us/diseases/respiratory/stats/hosp.html",
            "Hospitalization rates; covers the 7-county metro including Hennepin.",
        ),
        ref(
            "MDH — Wastewater monitoring in Minnesota",
            "https://www.health.state.mn.us/diseases/wastewater/stats/index.html",
            "COVID-19, influenza A/B, and RSV across ~29 Minnesota sites.",
        ),
        ref(
            "MDH — Respiratory illness in K-12 schools",
            "https://www.health.state.mn.us/diseases/respiratory/stats/setting.html",
            "Weekly school outbreak reports — a relatable local signal.",
        ),
    ]
