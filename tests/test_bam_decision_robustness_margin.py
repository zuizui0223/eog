from itertools import product

from eog.v2.bam_decision_robustness_margin import (
    brute_force_single_state_completion_flip_margin,
    complete_same_g_release_outcomes,
    release_decision_from_masks,
    single_state_completion_flip_margin,
    survivor_fiber_completion_margin,
)
from eog.v2.known_truth_bam import BAMWorld


def test_complete_same_g_closure_contains_both_release_outcomes_when_G_is_proper():
    for node_count in (1, 2, 3):
        limit = 1 << node_count
        full = limit - 1
        for G in range(limit):
            for axis in ("A", "B", "M"):
                outcomes = complete_same_g_release_outcomes(
                    G, axis=axis, node_count=node_count
                )
                assert outcomes == (frozenset({False}) if G == full else frozenset({False, True}))


def test_closed_form_flip_margin_matches_exhaustive_search_for_all_three_node_states():
    node_count = 3
    limit = 1 << node_count
    for A, B, M in product(range(limit), repeat=3):
        for axis in ("A", "B", "M"):
            exact = single_state_completion_flip_margin(
                A, B, M, axis=axis, node_count=node_count
            )
            brute = brute_force_single_state_completion_flip_margin(
                A, B, M, axis=axis, node_count=node_count
            )
            assert exact == brute


def _world(world_id, A, B, M):
    nodes = ("a", "b")
    return BAMWorld(
        world_id=world_id,
        node_ids=nodes,
        abiotic_mask=A,
        biotic_mask=B,
        movement_mask=M,
        occupied_mask=A & B & M,
        first_arrival_steps=(0, 1),
        abiotic_label=world_id,
        biotic_mode="none",
        movement_label=world_id,
        fingerprint=world_id,
    )


def test_fiber_margin_is_zero_when_declared_survivors_already_disagree():
    # Both worlds have G={a}; release A expands only in w1.
    w1 = _world("w1", 0b01, 0b11, 0b11)
    w2 = _world("w2", 0b11, 0b01, 0b11)
    result = survivor_fiber_completion_margin((w1, w2), ("w1", "w2"), axis="A")
    assert result.identified_in_declared_universe is False
    assert result.completion_flip_margin == 0
    assert result.full_completion_outcomes == frozenset({False, True})


def test_fiber_margin_is_minimum_over_declared_survivors():
    # Both survivors have G={a} and release A=True.
    # w1 has one extra released node; w2 also has one, so fiber margin=1.
    w1 = _world("w1", 0b01, 0b11, 0b11)
    w2 = _world("w2", 0b01, 0b11, 0b11)
    result = survivor_fiber_completion_margin((w1, w2), ("w1", "w2"), axis="A")
    assert result.identified_in_declared_universe is True
    assert result.current_decision is True
    assert result.completion_flip_margin == 1


def test_false_to_true_margin_can_require_three_local_axis_edits():
    # Outside-G node b is locally A=1,B=0,M=0 for release A.
    # To create release-A expansion while preserving G, it must become A=0,B=1,M=1.
    A, B, M = 0b11, 0b01, 0b01
    assert release_decision_from_masks(A, B, M, axis="A", node_count=2) is False
    assert single_state_completion_flip_margin(
        A, B, M, axis="A", node_count=2
    ) == 3
