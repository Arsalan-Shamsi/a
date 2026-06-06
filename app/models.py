"""Plain-data models for the dashboard.

These are deliberately simple ``@dataclass`` objects (no framework magic) so that
every number which reaches the screen carries its own provenance and is easy to
test. ``Provenance`` is the heart of the project's "trustworthy data" goal.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class Provenance:
    """Where a single number came from — shown next to it on screen."""

    source_short: str            # e.g. "CDC NSSP"
    source_name: str             # full human-readable name
    source_url: str              # a page a person can open to check it
    geography: str               # e.g. "Minnesota (statewide)"
    geography_level: str         # "national" | "state" | "substate" | "county"
    role: str = "data"           # "data" (we pull it) or "reference" (link only)
    access: str = "Public data, no account or API key required"
    api_url: Optional[str] = None        # the machine endpoint used (None in SAMPLE mode)
    data_through: Optional[str] = None   # the latest date the data covers (ISO)
    fetched_at: Optional[str] = None     # when we fetched it (ISO)
    is_sample: bool = True               # True when this is bundled SAMPLE data
    notes: Optional[str] = None          # caveats in plain English


@dataclass
class MetricPoint:
    """One weekly data point."""

    date: Optional[str]          # ISO week-ending date
    value: Optional[float]       # None means "no data that week"


@dataclass
class Series:
    """A single signal for a single virus (e.g. RSV's % of ER visits over time)."""

    virus: str                   # "COVID-19" | "Influenza" | "RSV"
    signal: str                  # machine id, e.g. "ed_visits_pct"
    signal_label: str            # human label, e.g. "% of ER visits"
    unit: str                    # e.g. "%"
    points: list[MetricPoint]
    provenance: Provenance
    current_value: Optional[float] = None
    current_date: Optional[str] = None
    level_category: Optional[str] = None   # only set when an OFFICIAL banding exists
    trend: Optional[str] = None            # "rising" | "falling" | "stable"
    trend_label: Optional[str] = None
    description: Optional[str] = None       # one-line plain-English meaning

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class VirusBlock:
    """All the signals we have for one virus — becomes one card on screen."""

    virus: str
    series: list[Series] = field(default_factory=list)


@dataclass
class Dashboard:
    """The whole payload the frontend renders."""

    location: str
    generated_at: str
    is_sample: bool
    viruses: list[VirusBlock]
    sources: list[Provenance]
    disclaimers: list[str]

    def to_dict(self) -> dict:
        return asdict(self)
