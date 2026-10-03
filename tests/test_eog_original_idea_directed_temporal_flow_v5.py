from benchmarks.run_eog_original_idea_directed_temporal_flow_v5 import (
    _directed_graph,
    _evaluate_row,
    _outlet_corner,
    _potential,
)
from benchmarks.run_eog_original_idea_virtual_worlds_v2 import _generate_base


def _first_eligible():
    for replicate in range(32):
        row = _evaluate_row(replicate, "low", "rook", 0.20)
        if row["eligible"]:
            return row
    raise AssertionError("expected one eligible v5 row")


def test_directed_graph_follows_frozen_flow_potential():
    base = _generate_base(0, "low", "rook")
    outlet = _outlet_corner(0, "low", "rook")
    edges = tuple(base["geo_edges"])
    graph = _directed_graph(base["permissive"], edges, outlet)
    for source, targets in graph.items():
        for target in targets:
            assert _potential(source, outlet) >= _potential(target, outlet)


def test_temporal_evidence_is_never_less_restrictive_than_static():
    row = _first_eligible()
    for key in ("0.10", "0.25", "0.50", "1.00"):
        assert (
            row["coverage"][key]["directed_temporal"]["survivor_world_count"]
            <= row["coverage"][key]["directed_static"]["survivor_world_count"]
        )


def test_truth_retention_and_false_exclusion_invariants():
    row = _first_eligible()
    for key in ("0.10", "0.25", "0.50", "1.00"):
        for regime in (
            "undirected_static",
            "directed_static",
            "directed_temporal",
        ):
            item = row["coverage"][key][regime]
            assert item["truth_world_survives"] is True
            assert item["false_robust_exclusion_count"] == 0
