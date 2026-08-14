import pytest

from eog.v2.reachability import (
    DynamicReachabilityEdge,
    TemporalWorld,
    build_dynamic_transition_operator,
    compare_temporal_reconstructions,
    reconstruct_temporal_worlds,
)


def _operator(node_ids, edges):
    index = {node_id: i for i, node_id in enumerate(node_ids)}
    return build_dynamic_transition_operator(
        node_ids,
        [
            DynamicReachabilityEdge(
                source=index[source],
                target=index[target],
                geographic_support=float(support),
            )
            for source, target, support in edges
        ],
        loss_support=1.0,
    )


def _empty(node_ids):
    return build_dynamic_transition_operator(node_ids, (), loss_support=1.0)


def _early_and_late_worlds():
    nodes = ("A", "B", "C")
    ab = _operator(nodes, (("A", "B", 1.0),))
    bc = _operator(nodes, (("B", "C", 1.0),))
    empty = _empty(nodes)
    return (
        TemporalWorld("early", ("t0", "t1", "t2", "t3"), (ab, bc, empty), ("A",)),
        TemporalWorld("late", ("t0", "t1", "t2", "t3"), (empty, ab, bc), ("A",)),
    )


def test_late_endpoint_observation_keeps_multiple_temporal_histories_underidentified():
    worlds = _early_and_late_worlds()
    result = reconstruct_temporal_worlds(worlds, (("C", "t3"),))

    assert result.compatible_world_ids == ("early", "late")
    assert result.incompatible_world_ids == ()
    assert result.identifiable is False
    assert result.compatible_fraction == pytest.approx(1.0)
    assert result.coverage_certificate == "exhaustive_declared_temporal_world_set_positive_observations"


def test_earlier_time_stamp_eliminates_a_world_that_reaches_the_same_endpoint_later():
    worlds = _early_and_late_worlds()
    before = reconstruct_temporal_worlds(worlds, (("C", "t3"),))
    after = reconstruct_temporal_worlds(worlds, (("C", "t3"), ("C", "t2")))
    update = compare_temporal_reconstructions(before, after)

    assert after.compatible_world_ids == ("early",)
    assert after.incompatible_world_ids == ("late",)
    assert after.identifiable is True
    assert dict(after.unsupported_observations_by_world)["late"] == (("C", "t2"),)
    assert update.retained_world_ids == ("early",)
    assert update.eliminated_world_ids == ("late",)
    assert update.contraction_fraction == pytest.approx(0.5)
    assert update.became_identifiable is True


def test_positive_observations_are_canonical_and_input_order_does_not_change_fingerprint():
    worlds = _early_and_late_worlds()
    first = reconstruct_temporal_worlds(worlds, (("C", "t3"), ("B", "t1")))
    second = reconstruct_temporal_worlds(worlds, (("B", "t1"), ("C", "t3")))

    assert first.observations == (("B", "t1"), ("C", "t3"))
    assert first == second


def test_reachability_by_time_is_a_necessary_constraint_not_an_exact_time_occupancy_claim():
    nodes = ("A", "B", "C")
    world = TemporalWorld(
        "reach_then_drain",
        ("t0", "t1", "t2"),
        (_operator(nodes, (("A", "B", 1.0),)), _empty(nodes)),
        ("A",),
    )
    result = reconstruct_temporal_worlds((world,), (("B", "t2"),))

    assert result.compatible_world_ids == ("reach_then_drain",)
    assert result.identifiable is True


def test_very_low_positive_support_remains_compatible_above_the_declared_tolerance():
    nodes = ("A", "C")
    rare = TemporalWorld(
        "rare",
        ("t0", "t1"),
        (_operator(nodes, (("A", "C", 1e-8),)),),
        ("A",),
    )

    permissive = reconstruct_temporal_worlds((rare,), (("C", "t1"),), support_tolerance=1e-15)
    strict = reconstruct_temporal_worlds((rare,), (("C", "t1"),), support_tolerance=1e-6)

    assert permissive.compatible_world_ids == ("rare",)
    assert strict.compatible_world_ids == ()
    assert strict.incompatible_world_ids == ("rare",)


def test_unobserved_nodes_are_not_silently_treated_as_absences():
    nodes = ("A", "B", "C", "D")
    world = TemporalWorld(
        "extra_reachable_node",
        ("t0", "t1"),
        (_operator(nodes, (("A", "B", 1.0), ("A", "D", 1.0))),),
        ("A",),
    )
    result = reconstruct_temporal_worlds((world,), (("B", "t1"),))

    assert result.compatible_world_ids == ("extra_reachable_node",)
    assert result.incompatible_world_ids == ()


def test_temporal_observation_contract_rejects_invalid_or_duplicate_rows():
    worlds = _early_and_late_worlds()

    with pytest.raises(ValueError, match="at least one"):
        reconstruct_temporal_worlds(worlds, ())
    with pytest.raises(ValueError, match="unique"):
        reconstruct_temporal_worlds(worlds, (("C", "t3"), ("C", "t3")))
    with pytest.raises(ValueError, match="outside"):
        reconstruct_temporal_worlds(worlds, (("D", "t3"),))
    with pytest.raises(ValueError, match="undeclared"):
        reconstruct_temporal_worlds(worlds, (("C", "t9"),))


def test_temporal_reconstruction_comparison_requires_the_same_world_universe():
    early, late = _early_and_late_worlds()
    before = reconstruct_temporal_worlds((early, late), (("C", "t3"),))
    different_universe = reconstruct_temporal_worlds((early,), (("C", "t3"),))

    with pytest.raises(ValueError, match="same frozen world universe"):
        compare_temporal_reconstructions(before, different_universe)
