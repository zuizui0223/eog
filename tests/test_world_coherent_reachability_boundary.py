"""Regression tests for the finite-world no-splicing counterexamples."""
import runpy

import pytest


def _run():
    namespace = runpy.run_path("benchmarks/world_coherent_reachability_boundary.py")
    return namespace["run_world_coherent_reachability_boundary"]()


def test_static_worlds_do_not_gain_target_by_unioning_disjoint_edges():
    result = _run()["static"]
    assert result["compatible_world_ids"] == ["world_ab", "world_bc"]
    assert result["target_status"] == "robustly_unreachable"
    assert "C" in result["robustly_unreachable_ids"]
    assert result["target_support_by_world"] == {
        "world_ab": 0.0, "world_bc": 0.0
    }
    assert result["illicit_pooled_target_possible"]
    assert result["illicit_pooled_target_support"]["illicit_pooled_graph"] == pytest.approx(0.25)


def test_real_world_expansion_rescues_target_without_rewriting_previous_worlds():
    result = _run()["static"]["genuine_expansion"]
    assert result["added_world_ids"] == ["world_abc"]
    assert result["new_target_status"] == "contingent"
    assert result["lost_excluded_ids"] == ["C"]
    assert result["monotonicity_holds"] is True


def test_per_interval_union_can_create_impossible_temporal_trajectory():
    result = _run()["temporal"]
    assert result["time_labels"] == ["t0", "t1", "t2"]
    assert result["target_status_at_final_time"] == "robustly_unreachable"
    assert result["target_exact_time_mass_by_world"] == {
        "world_early_ab": 0.0, "world_late_bc": 0.0
    }
    assert result["possible_edges_by_interval"] == [
        [["A", "B"]],
        [["B", "C"]],
    ]
    assert result["illicit_pooled_target_possible"] is True
    assert result["illicit_pooled_target_exact_time_mass"] == pytest.approx(0.25)


def test_world_order_does_not_change_frozen_known_truth_result():
    result = _run()
    assert result["static"]["fingerprint_order_invariant"]
    assert result["temporal"]["fingerprint_order_invariant"]
    assert result["checks"]["both_world_order_invariant"]


def test_claim_is_strictly_a_new_synthetic_method_guardrail():
    result = _run()
    assert result["schema_version"] == 1
    assert result["checks"]["pooling_manufactures_static_false_reachability"]
    assert result["checks"]["pooling_manufactures_temporal_false_reachability"]
    assert result["checks"]["no_existing_frozen_endpoint_modified"]
    assert "not biological impossibility" in result["claim_boundary"]
