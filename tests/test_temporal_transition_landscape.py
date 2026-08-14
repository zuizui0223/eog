import numpy as np
import pytest

from eog.v2.reachability import (
    DynamicReachabilityEdge,
    TemporalWorld,
    build_dynamic_transition_operator,
    summarize_temporal_transition_landscape,
)


def _operator(node_ids, edges):
    index = {node_id: i for i, node_id in enumerate(node_ids)}
    declared = [
        DynamicReachabilityEdge(
            source=index[source],
            target=index[target],
            geographic_support=float(support),
        )
        for source, target, support in edges
    ]
    return build_dynamic_transition_operator(node_ids, declared, loss_support=1.0)


def test_transition_landscape_distinguishes_robust_contingent_and_inactive_edges():
    nodes = ("A", "B", "C")
    world_a = TemporalWorld(
        "a",
        ("t0", "t1", "t2"),
        (
            _operator(nodes, (("A", "B", 1.0),)),
            _operator(nodes, (("B", "C", 1.0),)),
        ),
        ("A",),
    )
    world_b = TemporalWorld(
        "b",
        ("t0", "t1", "t2"),
        (
            _operator(nodes, (("A", "B", 0.2), ("A", "C", 0.4))),
            _operator(nodes, (("B", "C", 0.3),)),
        ),
        ("A",),
    )

    result = summarize_temporal_transition_landscape((world_b, world_a))

    assert result.world_ids == ("a", "b")
    assert result.robust_edges_by_interval[0] == (("A", "B"),)
    assert result.contingent_edges_by_interval[0] == (("A", "C"),)
    assert ("B", "C") in result.inactive_edges_by_interval[0]
    assert result.robust_edges_by_interval[1] == (("B", "C"),)
    assert result.contingent_edges_by_interval[1] == ()
    assert result.coverage_certificate == "exhaustive_declared_temporal_transition_world_set"


def test_transition_landscape_reports_possible_and_robust_openings_and_closures():
    nodes = ("A", "B", "C")
    world_a = TemporalWorld(
        "a",
        ("t0", "t1", "t2", "t3"),
        (
            _operator(nodes, (("A", "B", 1.0),)),
            _operator(nodes, (("B", "C", 1.0),)),
            _operator(nodes, ()),
        ),
        ("A",),
    )
    world_b = TemporalWorld(
        "b",
        ("t0", "t1", "t2", "t3"),
        (
            _operator(nodes, (("A", "B", 1.0), ("A", "C", 0.2))),
            _operator(nodes, (("B", "C", 0.4), ("A", "C", 0.2))),
            _operator(nodes, (("A", "C", 0.2),)),
        ),
        ("A",),
    )

    result = summarize_temporal_transition_landscape((world_a, world_b))

    assert result.possible_openings_by_interval[0] == ()
    assert result.robust_openings_by_interval[0] == ()
    assert result.possible_openings_by_interval[1] == (("B", "C"),)
    assert result.robust_openings_by_interval[1] == (("B", "C"),)
    assert ("A", "B") in result.possible_closures_by_interval[1]
    assert ("A", "B") in result.robust_closures_by_interval[1]

    # B->C disappears from every declared world at the final interval, while A->C
    # remains only a world-dependent possible channel throughout.
    assert result.possible_closures_by_interval[2] == (("B", "C"),)
    assert result.robust_closures_by_interval[2] == (("B", "C"),)
    assert result.contingent_edges_by_interval[2] == (("A", "C"),)


def test_low_positive_support_is_not_relabelled_as_impossible():
    nodes = ("A", "B")
    tiny = 1e-10
    world_a = TemporalWorld(
        "a",
        ("t0", "t1"),
        (_operator(nodes, (("A", "B", tiny),)),),
        ("A",),
    )
    world_b = TemporalWorld(
        "b",
        ("t0", "t1"),
        (_operator(nodes, (("A", "B", 1.0),)),),
        ("A",),
    )

    permissive = summarize_temporal_transition_landscape(
        (world_a, world_b), support_tolerance=1e-12
    )
    strict = summarize_temporal_transition_landscape(
        (world_a, world_b), support_tolerance=1e-8
    )

    assert permissive.robust_edges_by_interval[0] == (("A", "B"),)
    assert strict.contingent_edges_by_interval[0] == (("A", "B"),)
    assert permissive.support_lower_by_interval[0][0, 1] == pytest.approx(tiny)
    assert np.all(
        permissive.support_lower_by_interval[0] <= permissive.support_upper_by_interval[0]
    )


def test_transition_landscape_rejects_incomparable_temporal_worlds():
    nodes = ("A", "B")
    ab = _operator(nodes, (("A", "B", 1.0),))
    first = TemporalWorld("first", ("t0", "t1"), (ab,), ("A",))
    different_labels = TemporalWorld("labels", ("start", "end"), (ab,), ("A",))

    with pytest.raises(ValueError, match="same ordered time labels"):
        summarize_temporal_transition_landscape((first, different_labels))

    with pytest.raises(ValueError, match="finite and non-negative"):
        summarize_temporal_transition_landscape((first,), support_tolerance=-1.0)
