"""Pre-frozen source-MRR horizon intervals, SCC bounds and true graph controls.

Tests assert exact arithmetic and study size, not a hard-coded positive G5
scientific result. A nonpositive mean must be retained as non-support.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

import pytest

from benchmarks.occurrence_conditioned_source_minrelax_v4 import (
    COMPLETE, CYCLE, STAR, _broken_source_core_control, analyze_graph,
    run_protocol, source_graph,
)

PROTOCOL = json.loads(Path(
    "validation/occurrence_conditioned_source_minrelax_v4/protocol_v4.json"
).read_text(encoding="utf-8"))
ROOT = json.loads(Path(
    "validation/occurrence_conditioned_source_minrelax_v3/protocol_v3.json"
).read_text(encoding="utf-8"))
GENERATOR = ROOT["generator"]


@lru_cache(maxsize=1)
def _result():
    return run_protocol(PROTOCOL)


def test_predeclared_new_seeds_and_source_core_diameters():
    for n in (3, 4):
        expected = {COMPLETE: 1, STAR: 2, CYCLE: n - 1}
        for name, diameter in expected.items():
            graph = source_graph(GENERATOR, n, 0, 24, name)
            audit = analyze_graph(graph)
            assert audit["source_core_directed_diameter"] == diameter
            assert len(audit["gap_by_horizon"]) == n + 3
            assert audit["gap_by_horizon"][-1]["gap_world_fraction"] == 0
    with pytest.raises(ValueError, match="new seed indices"):
        source_graph(GENERATOR, 3, 0, 23, COMPLETE)
    with pytest.raises(ValueError, match="new seed indices"):
        source_graph(GENERATOR, 4, 0, 40, CYCLE)
    with pytest.raises(ValueError, match="unknown source-core"):
        source_graph(GENERATOR, 3, 0, 24, "unknown")


def test_shortest_hop_interval_exactly_classifies_all_threshold_worlds():
    graph = source_graph(GENERATOR, 4, 1, 24, CYCLE)
    report = analyze_graph(graph)
    for H in range(len(graph["node_ids"])):
        worlds = report["per_threshold_minimum_source_hops"]
        all_possible = sum(
            any(h is not None and h <= H for h in row["source_minimum_hops"].values())
            for row in worlds
        )
        all_robust = sum(
            all(h is not None and h <= H for h in row["source_minimum_hops"].values())
            for row in worlds
        )
        assert all_possible == report["gap_by_horizon"][H]["possible_worlds"]
        assert all_robust == report["gap_by_horizon"][H]["source_robust_worlds"]
        assert all_robust <= all_possible


def test_hop_gap_integrates_to_mean_width_and_is_diameter_bounded():
    for regime in (COMPLETE, STAR, CYCLE):
        for n in (3, 4):
            graph = source_graph(GENERATOR, n, 1, 25, regime)
            r = analyze_graph(graph)
            assert sum(x["gap_world_fraction"] for x in r["gap_by_horizon"][:-1]) == pytest.approx(
                r["ambiguity_area_mean_hops"], abs=1e-12,
            )
            assert r["ambiguity_area_mean_hops"] >= 0
            assert all(
                x["ambiguity_hop_width"] is not None
                and x["ambiguity_hop_width"] <= r["source_core_directed_diameter"]
                for x in r["per_threshold_minimum_source_hops"]
            )
            assert r["gap_by_horizon"][-1]["gap_world_fraction"] == 0


def test_disconnected_core_does_not_falsely_claim_terminal_robustness():
    control = _broken_source_core_control(GENERATOR)
    assert control == {
        "source_core_strongly_connected": False,
        "at_full_relaxation_possible_finite": True,
        "at_full_relaxation_robust_infinite": True,
        "terminal_robust_but_possible": True,
    }
    graph = source_graph(GENERATOR, 3, 0, 24, CYCLE)
    graph["candidate_directed_edges"] = [
        e for e in graph["candidate_directed_edges"]
        if (e["source"], e["target"]) != ("S0", "S1")
    ]
    with pytest.raises(AssertionError, match="strongly connected"):
        analyze_graph(graph)


def test_full_independent_seed_panel_and_native_reconstruction_controls():
    v = _result()
    assert v["summary"]["graphs"] == 192
    assert v["summary"]["paired_graph_triples"] == 64
    assert v["summary"]["native_v2_horizon_checks"] == 36
    assert v["summary"]["diameter_bound_violations"] == 0
    assert v["summary"]["integrated_gap_identity_violations"] == 0
    assert len(v["graph_horizon_summaries"]) == 192
    assert len(v["primary_paired_graphs"]) == 64
    assert v["verdicts"]["G5_cycle_area_greater_than_star"] in {
        "SUPPORTED_WITHIN_PREDECLARED_NEW_SEEDS", "REFUTED_OR_NOT_SUPPORTED"
    }
    assert sum((
        v["summary"]["cycle_minus_star_sign_counts"][key]
        for key in ("positive", "tied", "negative")
    )) == 64
    assert v["independent_ecological_replications"] == 0
    assert v["new_EOG_WF_empirical_endpoints"] == 0
    assert v["pre_score_protocol_amendment_commit"] == (
        "0dca8a6f01c5ec060bbe30cf52edb8bc1b5cbf6e"
    )


def test_pairing_keeps_optional_edges_and_world_budget_identical():
    for n in (3, 4):
        for d in (0, 1):
            for seed in (24, 39):
                graphs = [
                    source_graph(GENERATOR, n, d, seed, name)
                    for name in (COMPLETE, STAR, CYCLE)
                ]
                assert len({x["optional_edge_digest"] for x in graphs}) == 1
                audits = [analyze_graph(x) for x in graphs]
                assert len({x["threshold_world_count"] for x in audits}) == 1
                assert all(
                    row["source_core_directed_diameter"] is not None
                    for row in audits
                )


def test_per_graph_area_does_not_claim_measured_migration():
    v = _result()
    assert v["status"] == "SYNTHETIC_ONLY_NOT_ECOLOGICAL_FIELD_VALIDATION"
    assert v["summary"]["total_threshold_worlds"] > 0
    for row in v["graph_horizon_summaries"]:
        assert row["ambiguity_area_mean_hops"] <= row["diameter"]
        assert row["source_core"] in (COMPLETE, STAR, CYCLE)
        assert 0 <= row["tight_worlds"] <= row["worlds"]
        assert 0 <= row["positive_width_worlds"] <= row["worlds"]
        assert 0 <= row["ambiguity_area_mean_hops"]
