"""Tests that each source parses its SAMPLE fixture into well-formed series.

These run in SAMPLE mode (the default), so they need no network.
"""
from datetime import date

import pytest

from app.sources import cdc_ili, cdc_nssp, cdc_wastewater
from app.sources.cdc_ili import epiweek_to_saturday


def _check_series(s):
    assert s.points, f"{s.virus}/{s.signal} has no points"
    assert s.current_value is not None
    # dates are ISO YYYY-MM-DD and parseable
    date.fromisoformat(s.current_date)
    # provenance is complete and clearly marked as sample
    p = s.provenance
    assert p.is_sample is True
    assert p.source_url.startswith("http")
    assert p.data_through == s.points[-1].date


def test_nssp_has_three_viruses():
    series = cdc_nssp.get_series()
    assert {s.virus for s in series} == {"COVID-19", "Influenza", "RSV"}
    for s in series:
        assert s.signal == "ed_visits_pct"
        _check_series(s)


def test_wastewater_has_three_viruses_with_categories():
    series = cdc_wastewater.get_series()
    assert {s.virus for s in series} == {"COVID-19", "Influenza", "RSV"}
    for s in series:
        _check_series(s)
        assert s.level_category in {"Minimal", "Low", "Moderate", "High", "Very High"}


def test_ili_is_flu_only():
    series = cdc_ili.get_series()
    assert len(series) == 1
    assert series[0].virus == "Influenza"
    _check_series(series[0])


@pytest.mark.parametrize("epiweek", [202601, 202611, 202552, 202440])
def test_epiweek_converts_to_a_saturday(epiweek):
    assert date.fromisoformat(epiweek_to_saturday(epiweek)).weekday() == 5
