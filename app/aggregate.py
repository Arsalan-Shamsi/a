"""Assemble the full dashboard from every source.

This is the only place that knows about all sources at once. It groups signals
by virus and builds the de-duplicated 'Sources & methods' list.
"""
from .config import LIVE, LOCATION_LABEL
from .models import Dashboard, VirusBlock
from .sources import cdc_ed_trends, cdc_ili, cdc_nssp, cdc_wastewater, mdh
from .sources.base import now_iso

VIRUS_ORDER = ["COVID-19", "Influenza", "RSV"]

DISCLAIMERS = [
    "This shows community-level public health surveillance, not individual diagnoses.",
    "It is for general awareness only and is not medical advice.",
    "No personal or health information is collected from anyone who uses this app.",
    "Every number links to its official public source and the date range it covers.",
]


def build_dashboard() -> Dashboard:
    all_series = []
    for module in (cdc_nssp, cdc_ed_trends, cdc_wastewater, cdc_ili):
        all_series.extend(module.get_series())

    blocks = [
        VirusBlock(virus=v, series=[s for s in all_series if s.virus == v])
        for v in VIRUS_ORDER
    ]

    # Build the sources list: each distinct data source once, then MDH references.
    sources, seen = [], set()
    for s in all_series:
        key = (s.provenance.source_short, s.provenance.geography)
        if key not in seen:
            seen.add(key)
            sources.append(s.provenance)
    sources.extend(mdh.reference_sources())

    return Dashboard(
        location=LOCATION_LABEL,
        generated_at=now_iso(),
        is_sample=not LIVE,
        viruses=blocks,
        sources=sources,
        disclaimers=DISCLAIMERS,
    )
