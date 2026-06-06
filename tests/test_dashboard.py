"""Tests for assembling the whole dashboard payload."""
import json

from app.aggregate import build_dashboard


def test_dashboard_shape():
    d = build_dashboard()
    assert d.location
    assert d.is_sample is True
    assert [b.virus for b in d.viruses] == ["COVID-19", "Influenza", "RSV"]
    for block in d.viruses:
        assert block.series, f"{block.virus} should have at least one signal"


def test_every_number_is_sourced_and_dated():
    d = build_dashboard()
    for block in d.viruses:
        for s in block.series:
            assert s.provenance.source_name
            assert s.provenance.source_url.startswith("http")
            assert s.provenance.data_through  # the "as of" date


def test_sources_include_mdh_reference_links():
    d = build_dashboard()
    roles = {p.role for p in d.sources}
    assert "data" in roles and "reference" in roles
    assert any("Health" in p.source_short for p in d.sources)  # the MDH entries


def test_payload_is_json_serializable():
    payload = build_dashboard().to_dict()
    json.dumps(payload)  # raises if anything is not serializable
    assert payload["disclaimers"]
