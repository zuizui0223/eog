"""Exact finite row-resolution and fail-closed tests, without field inference."""
import pytest
from benchmarks.wetland_duplicate_bounds_v1 import build_bounds


def _row(sid, site, method, day, pel=0, rana=0):
    return {"surv": sid, "site": site, "method": method, "date": day,
            "Pelobates fuscus": str(pel), "Rana dalmatina": str(rana)}


def _fixture():
    return [
        _row("A:bottletrap:1", "A", "bottletrap", "2024-03-01"),
        _row("A:bottletrap:1", "A", "bottletrap", "2024-03-01", pel=1, rana=1),
        _row("A:visual:1", "A", "visual", "2024-03-01", pel=1, rana=1),
        _row("B:bottletrap:2", "B", "bottletrap", "2024-03-02"),
        _row("B:bottletrap:2", "B", "bottletrap", "2024-03-02", pel=1),
        _row("B:bottletrap:3", "B", "bottletrap", "2024-03-03", pel=1),
    ]


def test_exact_sensitivity_keeps_site_detections_but_not_every_method():
    rows = _fixture()
    result = build_bounds(rows, [{"site": "A"}, {"site": "B"}],
                          ["Pelobates fuscus", "Rana dalmatina"])
    assert result["scenarios"] == 4
    assert result["unique_survey_ids"] == 4
    s = result["grains"]
    assert s["site_species"]["positive_in_some_resolution_only"] == 0
    assert s["site_method_species"]["positive_in_some_resolution_only"] == 2
    assert s["survey_species"]["positive_in_some_resolution_only"] == 3
    assert s["site_species"]["positive_in_all_resolutions"] == 3


def test_invalid_collision_shape_fails_closed():
    rows = _fixture()
    rows[1] = _row("A:bottletrap:1", "A", "bottletrap", "2024-03-01", pel=2)
    rows[0] = _row("A:bottletrap:1", "A", "bottletrap", "2024-03-01", pel=1)
    with pytest.raises(ValueError, match="zero-versus-positive"):
        build_bounds(rows, [{"site": "A"}, {"site": "B"}],
                     ["Pelobates fuscus", "Rana dalmatina"])
