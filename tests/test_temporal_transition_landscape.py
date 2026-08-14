import numpy as np
import pytest

from eog.v2.reachability import (
    DynamicReachabilityEdge,
    TemporalWorld,
    build_dynamic_transition_operator,
    compare_temporal_transition_universes,
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


def test_expanding_world_universe_weakens_robustness_and_expands_possibility():
    nodes = ("A", "B", "C")
    baseline = TemporalWorld(
        "baseline",
        ("t0", "t1"),
        (_operator(nodes, (("A", "B", 1.0),)),),
        ("A",),
    )
    alternative = TemporalWorld(
        "alternative",
        ("t0", "t1"),
        (_operator(nodes, (("A", "C", 1.0),)),),
        ("A",),
    )

    before = summarize_temporal_transition_landscape((baseline,))
    after = summarize_temporal_transition_landscape((baseline, alternative))
    update = compare_temporal_transition_universes(before, after)

    assert update.added_world_ids == ("alternative",)
    assert update.lost_robust_edges_by_interval[0] == (("A", "B"),)
    assert update.gained_possible_edges_by_interval[0] == (("A", "C"),)
    assert update.lost_inactive_edges_by_interval[0] == (("A", "C"),)
    assert update.robust_monotonicity_holds
    assert update.possible_monotonicity_holds
    assert update.exclusion_monotonicity_holds
    assert update.coverage_certificate == "exact_nested_temporal_transition_world_universes"


def test_nested_universe_comparison_requires_identical_shared_worlds_and_tolerance():
    nodes = ("A", "B")
    baseline = TemporalWorld(
        "baseline",
        ("t0", "t1"),
        (_operator(nodes, (("A", "B", 1.0),)),),
        ("A",),
    )
    changed_baseline = TemporalWorld(
        "baseline",
        ("t0", "t1"),
        (_operator(nodes, ()),),
        ("A",),
    )

    before = summarize_temporal_transition_landscape((baseline,))
    changed = summarize_temporal_transition_landscape((changed_baseline,))
    with pytest.raises(ValueError, match="identical fingerprints"):
        compare_temporal_transition_universes(before, changed)

    different_tolerance = summarize_temporal_transition_landscape(
        (baseline,), support_tolerance=1e-10
    )
    with pytest.raises(ValueError, match="support_tolerance"):
        compare_temporal_transition_universes(before, different_tolerance)


def test_transition_landscape_rejects_incomparable_temporal_worlds():
    nodes = ("A", "B")
    ab = _operator(nodes, (("A", "B", 1.0),))
    first = TemporalWorld("first", ("t0", "t1"), (ab,), ("A",))
    different_labels = TemporalWorld("labels", ("start", "end"), (ab,), ("A",))

    with pytest.raises(ValueError, match="same ordered time labels"):
        summarize_temporal_transition_landscape((first, different_labels))

    with pytest.raises(ValueError, match="finite and non-negative"):
        summarize_temporal_transition_landscape((first,), support_tolerance=-1.0)
