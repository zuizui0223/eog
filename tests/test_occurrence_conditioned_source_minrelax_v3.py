"""Source-uncertain MRR v3: frozen-generator exact and negative controls.

The scientific directional G1 result is *not* asserted as a test success.
A refuted direction remains a valid completed synthetic experiment.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

import pytest

from benchmarks.occurrence_conditioned_source_minrelax_v3 import (
    XorShift32, _evaluate_graph, generate_graph, run_protocol,
)

P = Path("validation/occurrence_conditioned_source_minrelax_v3/protocol_v3.json")
SPEC = json.loads(P.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def result():
    return run_protocol(SPEC)


def test_generator_int32_cross_language_reference_stream():
    # Reference generated with separate JS xorshift32 code after protocol freeze.
    gen = XorShift32(20261120 + 10000 * 3)
    assert [gen.draw() for _ in range(5)] == [
        0.9239987379405648,
        0.6310894214548171,
        0.2351110477466136,
        0.3085117936134338,
        0.256090271519497,
    ]


def test_full_protocol_denominators_and_predeclared_status_fields():
    x = result()
    s = x["summary"]
    assert s["rows"] == 1152
    assert s["unique_source_count_density_seed_graphs"] == 288
    assert s["matched_regime_graph_pairs"] == 144
    assert s["primary_paired_graphs"] == 96
    assert len(x["all_synthetic_panels"]) == 1152
    assert len(x["primary_paired_rows"]) == 96
    assert x["pre_score_protocol_commit"] == "32626e5a5726d8f33083163c2e2dfc31b7eb2f46"
    assert x["independent_ecological_replications"] == 0
    assert x["new_EOG_WF_empirical_endpoints"] == 0
    assert x["outcomes"]["G1_cycle_gap_strictly_larger_mean_than_complete"] in {
        "SUPPORTED_WITHIN_FROZEN_SYNTHETIC_GENERATOR", "REFUTED_OR_NOT_SUPPORTED"
    }


def test_all_horizon_and_native_negative_controls():
    s = result()["summary"]
    assert s["terminal_source_core_checks"] == 288
    assert s["horizon_monotonicity_pair_checks"] == 864
    assert s["two_source_equivalent_regime_checks"] == 192
    assert s["native_EOG_v2_cross_checks"] == 24
    assert result()["outcomes"]["G2_horizon_monotonicity"] == "IMPLEMENTATION_CONTRACT_PASSED"
    assert result()["outcomes"]["G3_terminal_source_core_convergence"] == "IMPLEMENTATION_CONTRACT_PASSED"
    assert result()["outcomes"]["G4_two_source_regime_identity"] == "NEGATIVE_CONTROL_PASSED"
    assert result()["outcomes"]["G5_native_EOG_vs_independent_BFS"] == "INDEPENDENT_CHECK_PASSED"


def test_each_panel_preserves_universal_subset_possible_and_valid_horizon():
    x = result()
    for row in x["all_synthetic_panels"]:
        assert 0 <= row["source_robust_worlds"] <= row["possible_worlds"] <= row["worlds"]
        assert row["gap_worlds"] == row["possible_worlds"] - row["source_robust_worlds"]
        assert row["gap_world_fraction"] == pytest.approx(row["gap_worlds"] / row["worlds"])
        assert 1 <= row["horizon_steps"] <= row["n_sources"] + 2
        assert len(row["per_source_compatible_counts"]) == row["n_sources"]
        assert len(row["per_source_frontiers"]) == row["n_sources"]
        if row["horizon_steps"] == row["n_sources"] + 2:
            assert row["gap_worlds"] == 0


def test_regime_pairs_share_exact_optional_graph_and_lattice():
    x = result()
    records = {}
    for row in x["all_synthetic_panels"]:
        key = row["n_sources"], row["density_index"], row["seed_index"], row["horizon_steps"]
        records.setdefault(key, []).append(row)
    assert len(records) == 576
    for pair in records.values():
        assert len(pair) == 2
        a, b = pair
        assert a["optional_edge_digest"] == b["optional_edge_digest"]
        assert a["worlds"] == b["worlds"]
        if a["n_sources"] == 2:
            assert a["gap_worlds"] == b["gap_worlds"]
            assert a["possible_frontier"] == b["possible_frontier"]
            assert a["source_robust_frontier"] == b["source_robust_frontier"]


def test_predeclared_source_generator_anchors_are_never_hard():
    generator = SPEC["generator"]
    edges = generate_graph(
        generator, n_sources=4, density_index=0, seed_index=17,
        regime="unidirectional_cycle_baseline"
    )["candidate_directed_edges"]
    nodes = {f"S{i}" for i in range(4)}
    for row in generator["guaranteed_anchor_outgoing_edges"]:
        assert row in edges
        assert row["hard_unavailable"] is False
    source_core = [r for r in edges if r["source"] in nodes and r["target"] in nodes]
    assert len(source_core) == 4
    assert all(r["geographic_km"] <= 10 and r["barrier_permission"] == 0 for r in source_core)


def test_unevaluable_or_tampered_generator_parameters_are_rejected():
    generator = SPEC["generator"]
    with pytest.raises(ValueError, match="outside frozen roster"):
        generate_graph(generator, 7, 0, 0, "complete_bidirectional_baseline")
    with pytest.raises(ValueError, match="unknown source-core"):
        generate_graph(generator, 3, 0, 0, "unknown")
    with pytest.raises(ValueError, match="random seed outside"):
        generate_graph(generator, 3, 0, 24, "unidirectional_cycle_baseline")
    with pytest.raises(ValueError, match="nonzero"):
        XorShift32(0)


def test_short_horizon_is_not_reinterpreted_as_elapsed_years():
    generator = SPEC["generator"]
    graph = generate_graph(generator, 3, 1, 0, "unidirectional_cycle_baseline")
    check = _evaluate_graph({"universe": graph}, horizons=(1, 2, 3, 5))
    assert 5 in check
    assert check[1]["_possible_set"].issubset(check[2]["_possible_set"])
    assert check[2]["_robust_set"].issubset(check[3]["_robust_set"])
    assert check[5]["_possible_set"] == check[5]["_robust_set"]
