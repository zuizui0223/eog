"""Frozen scientific regression tests for source-uncertain MRR v2.

Protocol first: validation/occurrence_conditioned_source_minrelax_v2/protocol_v2.json.
Tests use the source input and verify exact counts, alternative-source
semantics, source/horizon dependence, antichain join and honest fail closed.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from benchmarks.occurrence_conditioned_source_minrelax_v2 import (
    _pareto_min,
    run_source_universe,
    run_protocol,
)

PROTOCOL = Path("validation/occurrence_conditioned_source_minrelax_v2/protocol_v2.json")
SPEC = json.loads(PROTOCOL.read_text(encoding="utf-8"))


def _as_set(values):
    return {tuple(v) for v in values}


def test_predeclared_h1_three_sources_produce_incomparable_rescues():
    result = run_protocol(SPEC)["H1"]
    fixed = SPEC["prespecified_fixture_checks"]["H1"]
    assert result["worlds_per_source"] == fixed["breakpoint_worlds"] == 8
    assert result["source_world_pairs"] == fixed["source_world_pairs"] == 24
    assert result["compatible_world_counts_by_source"] == {
        "from_A": 4, "from_B": 4, "from_C": 4
    }
    for name, expected in fixed["source_frontiers"].items():
        assert _as_set(result["source_frontiers"][name]) == _as_set(expected)
    assert result["possible_compatible_world_count"] == fixed["possible_compatible"] == 7
    assert result["source_robust_compatible_world_count"] == fixed["source_robust_compatible"] == 1
    assert _as_set(result["possible_frontier"]) == _as_set(fixed["possible_frontier"])
    assert _as_set(result["source_robust_frontier"]) == _as_set(fixed["source_robust_frontier"])
    assert result["naive_source_frontier_intersection"] == []
    assert result["source_robust_frontier"] != result["naive_source_frontier_intersection"]
    assert result["independent_bfs_and_antichain_join_both_verified"]


def test_horizon_2_removes_source_identity_penalty_in_this_fixture():
    result = run_protocol(SPEC)["H2"]
    fixed = SPEC["prespecified_fixture_checks"]["H2"]
    assert result["worlds_per_source"] == fixed["breakpoint_worlds"] == 8
    assert result["source_world_pairs"] == fixed["source_world_pairs"] == 24
    assert set(result["compatible_world_counts_by_source"].values()) == {7}
    assert result["possible_compatible_world_count"] == fixed["possible_compatible"] == 7
    assert result["source_robust_compatible_world_count"] == fixed["source_robust_compatible"] == 7
    assert _as_set(result["source_robust_frontier"]) == _as_set(fixed["source_robust_frontier"])
    assert result["source_robust_frontier"] == result["possible_frontier"]
    assert result["horizon_steps_not_years"] == 2


def test_hard_unavailable_can_eliminate_all_source_robust_rescues():
    result = run_protocol(SPEC)["hard_edge_boundary"]
    expected = SPEC["prespecified_fixture_checks"]["hard_edge_boundary"]
    assert result["compatible_world_counts_by_source"]["from_C"] == 0
    assert result["source_robust_compatible_world_count"] == 0
    assert result["source_robust_frontier"] == expected["source_robust_frontier"] == []
    assert _as_set(result["possible_frontier"]) == _as_set(expected["possible_frontier"])
    assert result["status"] == "no_source_robust_world_within_declared_source_and_graph_universe"
    assert "biological impossibility" in result["claim_boundary"]


def test_more_alternative_sources_cannot_create_more_universal_feasibility():
    cases = []
    for n in (1, 2, 3):
        clone = deepcopy(SPEC)
        clone["universe"]["alternative_singleton_sources"] = (
            clone["universe"]["alternative_singleton_sources"][:n]
        )
        cases.append(run_source_universe(clone, horizon=1))
    assert [r["possible_compatible_world_count"] for r in cases] == [4, 6, 7]
    assert [r["source_robust_compatible_world_count"] for r in cases] == [4, 2, 1]
    assert _as_set(cases[0]["source_robust_frontier"]) == {(0, 1, 0)}
    assert _as_set(cases[1]["source_robust_frontier"]) == {(5, 1, 0)}
    assert _as_set(cases[2]["source_robust_frontier"]) == {(5, 1, 1)}


def test_frozen_source_order_and_edge_order_do_not_change_science_result():
    standard = run_source_universe(SPEC, horizon=1)
    reversed_order = run_source_universe(
        SPEC, horizon=1,
        source_order=("from_C", "from_A", "from_B"),
        reverse_edges=True,
    )
    assert reversed_order == standard
    assert len(standard["native_reconstruction_fingerprint_by_source"]) == 3


def test_parieto_antichain_join_is_not_naive_frontier_intersection():
    assert _pareto_min([(5, 1, 1), (5, 1, 1), (5, 2, 1)]) == ((5, 1, 1),)
    assert _pareto_min([(0, 1, 0), (5, 0, 0), (0, 0, 1)]) == (
        (0, 0, 1), (0, 1, 0), (5, 0, 0)
    )
    assert run_source_universe(SPEC, horizon=1)["naive_source_frontier_intersection"] == []


def test_invalid_source_or_horizon_or_breakpoint_budget_fails_closed():
    with pytest.raises(ValueError, match="horizon"):
        run_source_universe(SPEC, horizon=0)
    with pytest.raises(ValueError, match="max_worlds"):
        run_source_universe(SPEC, horizon=1, max_worlds=4)
    with pytest.raises(ValueError, match="not in the frozen graph"):
        run_source_universe(SPEC, horizon=1, make_hard_unavailable=("T", "C"))
    with pytest.raises(ValueError, match="source order"):
        run_source_universe(SPEC, horizon=1, source_order=("from_A", "from_B"))
    clone = deepcopy(SPEC)
    clone["universe"]["alternative_singleton_sources"][0]["source_ids"] = ["T", "X"]
    with pytest.raises(ValueError, match="singleton observed positives"):
        run_source_universe(clone, horizon=1)


def test_existing_eog_wf_closure_not_reopened():
    result = run_protocol(SPEC)
    assert result["new_eog_wf_endpoints"] == 0
    assert result["H1"]["frozen_source_hypotheses_are_not_natal_origin_observations"]
    assert result["H2"]["frozen_source_hypotheses_are_not_natal_origin_observations"]
