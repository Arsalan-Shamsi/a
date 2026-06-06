"""Trend and level helpers.

Kept deliberately simple and transparent: a person should be able to read this
file and know exactly how we decided something was "rising" or "Moderate".
"""
from typing import Optional


def compute_trend(values: list[Optional[float]], rel_threshold: float = 0.15):
    """Compare the most recent 3 weeks against the previous 3 weeks.

    We use a *relative* threshold (default 15%) so small wiggles don't get
    reported as a real change. Returns ``(code, label)`` where code is
    ``"rising"``, ``"falling"``, ``"stable"`` — or ``(None, None)`` if we don't
    have enough data to say.
    """
    clean = [v for v in values if v is not None]
    if len(clean) < 4:
        return None, None
    recent = clean[-3:]
    prior = clean[-6:-3] if len(clean) >= 6 else clean[:-3]
    if not prior:
        return None, None
    recent_avg = sum(recent) / len(recent)
    prior_avg = sum(prior) / len(prior)
    if prior_avg == 0:
        return ("rising", "Rising") if recent_avg > 0 else ("stable", "Holding steady")
    change = (recent_avg - prior_avg) / prior_avg
    if change >= rel_threshold:
        return "rising", "Rising"
    if change <= -rel_threshold:
        return "falling", "Falling"
    return "stable", "Holding steady"


# Official CDC "Wastewater Viral Activity Level" (WVAL) category thresholds.
# Source: CDC Wastewater Monitoring — Data and Methods.
# https://www.cdc.gov/wastewater/about/data-methods.html
WVAL_THRESHOLDS = [
    (1.5, "Minimal"),
    (3.0, "Low"),
    (4.5, "Moderate"),
    (8.0, "High"),
]


def wval_category(value: Optional[float]) -> Optional[str]:
    """Map a numeric wastewater activity level to CDC's official bucket."""
    if value is None:
        return None
    for ceiling, label in WVAL_THRESHOLDS:
        if value <= ceiling:
            return label
    return "Very High"
