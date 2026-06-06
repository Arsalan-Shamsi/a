"""Tests for the transparent trend + level logic."""
from app.trends import compute_trend, wval_category


def test_rising():
    code, _ = compute_trend([1, 1, 1, 2, 2.5, 3])
    assert code == "rising"


def test_falling():
    code, _ = compute_trend([3, 2.5, 2, 1, 0.8, 0.5])
    assert code == "falling"


def test_stable_within_threshold():
    code, _ = compute_trend([1.0, 1.0, 1.02, 0.99, 1.01, 1.0])
    assert code == "stable"


def test_not_enough_data():
    assert compute_trend([1, 2]) == (None, None)


def test_ignores_missing_values():
    # None values should be skipped, not crash.
    code, _ = compute_trend([None, 1, 1, 1, 2, 3, None])
    assert code == "rising"


def test_wval_category_boundaries():
    assert wval_category(1.5) == "Minimal"
    assert wval_category(1.51) == "Low"
    assert wval_category(3.0) == "Low"
    assert wval_category(4.5) == "Moderate"
    assert wval_category(8.0) == "High"
    assert wval_category(8.01) == "Very High"
    assert wval_category(None) is None
