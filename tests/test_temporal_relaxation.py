import pytest

from eog.v2.reachability import (
    DynamicReachabilityEdge,
    TemporalRelaxationDeclaration,
    TemporalWorld,
    build_dynamic_transition_operator,
    minimum_temporal_relaxation_frontier,
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
                geographic_support=float(geographic),
                environmental_support=float(environmental),
                barrier_support=float(barrier),
            )
            for source, target, geographic, environmental, barrier in edges
        ],
        loss_support=1.0,
    )


def _empty(node_ids):
    return build_dynamic_transition_operator(node_ids, (), loss_support=1.0)


def _worlds_and_declarations():
    nodes = ("A", "B", "C", "D")
    time = ("t0", "t1", "t2", "t3")

    slow_baseline = TemporalWorld(
        "slow_baseline",
        time,
        (
            _operator(nodes, (("A", "D", 1.0, 1.0, 1.0),)),
            _operator(nodes, (("D", "B", 1.0, 1.0, 1.0),)),
            _operator(nodes, (("B", "C", 1.0, 1.0, 1.0),)),
        ),
        ("A",),
    )
    fast_geo = TemporalWorld(
        "fast_geo",
        time,
        (
            _operator(nodes, (("A", "C", 0.4, 1.0, 1.0),)),
            _empty(nodes),
            _empty(nodes),
        ),
        ("A",),
    )
    fast_env = TemporalWorld(
        "fast_env",
        time,
        (
            _operator(nodes, (("A", "B", 1.0, 0.6, 1.0),)),
            _operator(nodes, (("B", "C", 1.0, 0.6, 1.0),)),
            _empty(nodes),
        ),
        ("A",),
    )
    fast_barrier = TemporalWorld(
        "fast_barrier",
        time,
        (
            _operator(nodes, (("A", "D", 1.0, 1.0, 0.6),)),
            _operator(nodes, (("D", "C", 1.0, 1.0, 0.6),)),
            _empty(nodes),
        ),
        ("A",),
    )
    dominated = TemporalWorld(
        "dominated",
        time,
        (
            _operator(nodes, (("A", "C", 0.4, 0.6, 0.6),)),
            _empty(nodes),
            _empty(nodes),
        ),
        ("A",),
    )

    worlds = (slow_baseline, fast_geo, fast_env, fast_barrier, dominated)
    declarations = (
        TemporalRelaxationDeclaration("slow_baseline", 0.0, 0.0, 0.0),
        TemporalRelaxationDeclaration("fast_geo", 1.0, 0.0, 0.0),
        TemporalRelaxationDeclaration("fast_env", 0.0, 1.0, 0.0),
        TemporalRelaxationDeclaration("fast_barrier", 0.0, 0.0, 1.0),
        TemporalRelaxationDeclaration("dominated", 1.0, 1.0, 1.0),
    )
    return worlds, declarations


def test_earlier_positive_timing_changes_the_minimum_relaxation_frontier():
    worlds, declarations = _worlds_and_declarations()

    late = reconstruct_temporal_worlds(worlds, (("C", "t3"),))
    late_frontier = minimum_temporal_relaxation_frontier(late, declarations)
    assert {point.world_id for point in late_frontier.points} == {"slow_baseline"}

    early = reconstruct_temporal_worlds(worlds, (("C", "t2"),))
    early_frontier = minimum_temporal_relaxation_frontier(early, declarations)
    assert "slow_baseline" not in early.compatible_world_ids
    assert {point.world_id for point in early_frontier.points} == {
        "fast_geo",
        "fast_env",
        "fast_barrier",
    }
    assert "dominated" in early.compatible_world_ids
    assert "dominated" not in {point.world_id for point in early_frontier.points}
    assert early_frontier.coverage_certificate == (
        "complete_relaxation_declaration_over_frozen_temporal_world_universe"
    )


def test_temporal_frontier_preserves_geographic_environmental_and_barrier_axes():
    worlds, declarations = _worlds_and_declarations()
    reconstruction = reconstruct_temporal_worlds(worlds, (("C", "t2"),))
    frontier = minimum_temporal_relaxation_frontier(reconstruction, declarations)
    by_id = {point.world_id: point for point in frontier.points}

    assert by_id["fast_geo"].geographic_relaxation == pytest.approx(1.0)
    assert by_id["fast_geo"].environmental_relaxation == pytest.approx(0.0)
    assert by_id["fast_geo"].barrier_relaxation == pytest.approx(0.0)

    assert by_id["fast_env"].geographic_relaxation == pytest.approx(0.0)
    assert by_id["fast_env"].environmental_relaxation == pytest.approx(1.0)
    assert by_id["fast_env"].barrier_relaxation == pytest.approx(0.0)

    assert by_id["fast_barrier"].geographic_relaxation == pytest.approx(0.0)
    assert by_id["fast_barrier"].environmental_relaxation == pytest.approx(0.0)
    assert by_id["fast_barrier"].barrier_relaxation == pytest.approx(1.0)


def test_relaxation_declaration_order_does_not_change_the_frontier_or_fingerprint():
    worlds, declarations = _worlds_and_declarations()
    reconstruction = reconstruct_temporal_worlds(worlds, (("C", "t2"),))

    first = minimum_temporal_relaxation_frontier(reconstruction, declarations)
    second = minimum_temporal_relaxation_frontier(
        reconstruction, tuple(reversed(declarations))
    )
    assert first == second


def test_relaxation_declarations_must_cover_the_complete_frozen_temporal_universe():
    worlds, declarations = _worlds_and_declarations()
    reconstruction = reconstruct_temporal_worlds(worlds, (("C", "t2"),))

    with pytest.raises(ValueError, match="exactly cover"):
        minimum_temporal_relaxation_frontier(reconstruction, declarations[:-1])

    with pytest.raises(ValueError, match="exactly cover"):
        minimum_temporal_relaxation_frontier(
            reconstruction,
            declarations
            + (TemporalRelaxationDeclaration("not_in_world_universe", 0.0, 0.0, 0.0),),
        )


def test_relaxation_declarations_reject_invalid_axes_and_duplicate_worlds():
    with pytest.raises(ValueError, match="finite and non-negative"):
        TemporalRelaxationDeclaration("bad", geographic_relaxation=-1.0)

    worlds, declarations = _worlds_and_declarations()
    reconstruction = reconstruct_temporal_worlds(worlds, (("C", "t2"),))
    duplicate = declarations + (TemporalRelaxationDeclaration("fast_geo", 2.0, 0.0, 0.0),)
    with pytest.raises(ValueError, match="unique world IDs"):
        minimum_temporal_relaxation_frontier(reconstruction, duplicate)


def test_no_compatible_temporal_world_produces_an_empty_frontier_not_a_fake_rescue():
    worlds, declarations = _worlds_and_declarations()
    reconstruction = reconstruct_temporal_worlds(worlds, (("C", "t0"),))
    assert reconstruction.compatible_world_ids == ()

    frontier = minimum_temporal_relaxation_frontier(reconstruction, declarations)
    assert frontier.points == ()
    assert frontier.compatible_world_ids == ()
