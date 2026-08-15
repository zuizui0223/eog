import runpy

import pytest


def _benchmark():
    namespace = runpy.run_path("benchmarks/keitt_critical_distance_boundary.py")
    return namespace["run_keitt_critical_distance_boundary"]()


def test_keitt_boundary_records_the_primary_literature_reference():
    boundary = _benchmark()["literature_boundary"]
    assert boundary["method"] == "Keitt-style patch-distance threshold / percolation connectivity"
    assert boundary["reference"] == "Keitt, Urban & Milne 1997, Conservation Ecology 1(1):4"
    assert boundary["doi"] == "10.5751/ES-00015-010104"


def test_stepping_stone_critical_distance_is_six_not_direct_distance_ten():
    baseline = _benchmark()["keitt_style_baseline"]
    assert baseline["critical_distance"] == pytest.approx(6.0)
    assert baseline["direct_A_C_distance"] == pytest.approx(10.0)
    assert baseline["stepping_stone_reduces_required_threshold"] is True
    assert baseline["edges_present_at_critical_distance"] == [
        ["A", "B", 4.0],
        ["B", "C", 6.0],
    ]


def test_eog_one_dimensional_geographic_basin_merge_matches_critical_distance():
    eog = _benchmark()["eog_one_dimensional_family"]
    assert eog["levels"] == [0.0, 4.0, 6.0, 10.0]
    assert eog["first_possible_level"] == pytest.approx(6.0)
    assert eog["first_robust_level"] == pytest.approx(6.0)
    assert eog["possible_but_variant_dependent"] is False
    assert eog["coverage_certificate"] == "exhaustive_declared_monotone_family_and_variants"


def test_one_dimensional_water_level_is_explicitly_removed_from_novelty_claim():
    boundary = _benchmark()["negative_boundary"]
    assert boundary["critical_thresholds_match"] is True
    assert boundary["do_not_claim_1d_geographic_water_level_as_unique"] is True
    assert boundary["do_not_claim_stepping_stone_critical_distance_as_unique"] is True
    assert "multi-axis geographic/environmental/barrier Pareto relaxation" in boundary[
        "remaining_layers_to_validate"
    ]
