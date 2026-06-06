"""Tests that each source parses its SAMPLE fixture into well-formed series.

These run in SAMPLE mode (the default), so they need no network.
"""
from datetime import date

import pytest

from app.sources import cdc_ili, cdc_nssp, cdc_wastewater
from app.sources.cdc_ili import epiweek_to_saturday

LEVELS = {"Minimal", "Low", "Moderate", "High", "Very High"}


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


def test_nssp_has_three_viruses_statewide_by_default():
    series = cdc_nssp.get_series()
    assert {s.virus for s in series} == {"COVID-19", "Influenza", "RSV"}
    for s in series:
        assert s.signal == "ed_visits_pct"
        assert s.provenance.geography_level == "state"
        _check_series(s)


def test_wastewater_localized_to_hennepin_county():
    series = cdc_wastewater.get_series()
    assert {s.virus for s in series} == {"COVID-19", "Influenza", "RSV"}
    for s in series:
        _check_series(s)
        assert s.level_category in LEVELS
        assert "Hennepin" in s.provenance.geography
        assert s.provenance.geography_level == "county"


def test_wastewater_falls_back_to_statewide_without_county(monkeypatch):
    # Rows with no county field should not crash; they report as statewide.
    rows = [{
        "date_end": "2026-05-30", "wwtp_jurisdiction": "MN",
        "pcr_target": "sars-cov-2", "wva_level": "2.0", "wva_level_category": "Low",
    }]
    monkeypatch.setattr(cdc_wastewater, "_fetch_raw", lambda: rows)
    series = cdc_wastewater.get_series()
    assert series and series[0].provenance.geography_level == "state"
    assert "statewide" in series[0].provenance.notes


def test_ili_is_flu_only_and_statewide():
    series = cdc_ili.get_series()
    assert len(series) == 1
    assert series[0].virus == "Influenza"
    assert series[0].provenance.geography_level == "state"
    _check_series(series[0])


@pytest.mark.parametrize("epiweek", [202601, 202611, 202552, 202440])
def test_epiweek_converts_to_a_saturday(epiweek):
    assert date.fromisoformat(epiweek_to_saturday(epiweek)).weekday() == 5
