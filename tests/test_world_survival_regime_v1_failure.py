import numpy as np

from eog.v2.world_adequacy import audit_world_universe_structure


def _symmetric(n, edges):
    adjacency = np.zeros((n, n), dtype=bool)
    for left, right in edges:
        adjacency[left, right] = True
        adjacency[right, left] = True
    return adjacency


def test_n_minus_1_horizon_forces_ratio_one_when_lcc_is_strict_majority():
    # Six of ten nodes form one connected component; the other four are isolated.
    # Under horizon n-1, every node in the size-6 component reaches all six members.
    adjacency = _symmetric(
        10,
        [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)],
    )
    audit = audit_world_universe_structure(
        tuple(f"n{i}" for i in range(10)),
        {"world": adjacency},
        horizon=9,
    )
    row = audit.world_audits[0]

    assert row.largest_weak_component_fraction == 0.6
    assert row.median_horizon_reachable_fraction == 0.6
    assert (
        row.median_horizon_reachable_fraction
        / row.largest_weak_component_fraction
    ) == 1.0


def test_adequacy_ladder_with_majority_lcc_cannot_forecast_all_worlds_fail_under_v1():
    # The theorem is structural: any undirected world with LCC > 0.5 gets v1 ratio 1.
    # Therefore a world family containing even one such world cannot yield a
    # falsified_universe prediction at any v1 cutoff <= 1.
    adjacency = _symmetric(
        8,
        [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6)],
    )
    audit = audit_world_universe_structure(
        tuple(f"n{i}" for i in range(8)),
        {"high_lcc": adjacency},
        horizon=7,
    )
    row = audit.world_audits[0]
    ratio = (
        row.median_horizon_reachable_fraction
        / row.largest_weak_component_fraction
    )

    assert row.largest_weak_component_fraction == 7 / 8
    assert ratio == 1.0
    assert ratio >= 0.5
