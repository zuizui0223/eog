from __future__ import annotations

import numpy as np
import pytest

from eog.v2.temporal_source_closure import (
    TemporalSourceClosureDeclaration,
    evaluate_temporal_source_closure,
)


def declaration() -> TemporalSourceClosureDeclaration:
    return TemporalSourceClosureDeclaration(
        closure_id="fresh-system-v1",
        source_semantics="response-blind possible sources",
        transition_semantics="same-node persistence plus declared source-to-target adjacency",
    )


def test_same_node_persistence_keeps_closure_open():
    node_ids = ("a", "b", "c")
    initial = np.array([True, False, False], dtype=bool)
    persistence = np.array(
        [
            [True, True, True],
            [False, False, False],
            [False, False, False],
        ],
        dtype=bool,
    )
    target = np.zeros((3, 3), dtype=bool)
    adjacency = np.zeros((3, 3), dtype=bool)

    result = evaluate_temporal_source_closure(
        declaration(), node_ids, initial, persistence, target, adjacency
    )

    assert result.passed is True
    assert result.status == "temporal_source_closure_pass"
    assert result.possible_source_counts == (1, 1, 1, 1)
    assert result.first_empty_transition_zero_based is None
    assert result.final_possible_node_ids == ("a",)


def test_declared_transition_chain_can_move_source_between_nodes():
    node_ids = ("a", "b", "c")
    initial = np.array([True, False, False], dtype=bool)
    persistence = np.zeros((3, 2), dtype=bool)
    target = np.array(
        [
            [False, False],
            [True, False],
            [False, True],
        ],
        dtype=bool,
    )
    adjacency = np.array(
        [
            [False, True, False],
            [False, False, True],
            [False, False, False],
        ],
        dtype=bool,
    )

    result = evaluate_temporal_source_closure(
        declaration(), node_ids, initial, persistence, target, adjacency
    )

    assert result.passed is True
    assert result.possible_source_counts == (1, 1, 1)
    assert result.final_possible_node_ids == ("c",)
    assert result.transitions[0].transition_target_count == 1
    assert result.transitions[1].transition_target_count == 1


def test_empty_possible_source_set_is_hard_stop_and_stays_empty():
    node_ids = ("a", "b")
    initial = np.array([True, False], dtype=bool)
    persistence = np.zeros((2, 3), dtype=bool)
    target = np.zeros((2, 3), dtype=bool)
    adjacency = np.ones((2, 2), dtype=bool)

    result = evaluate_temporal_source_closure(
        declaration(), node_ids, initial, persistence, target, adjacency
    )

    assert result.passed is False
    assert result.status == "stop_temporal_source_closure_gap"
    assert result.first_empty_transition_zero_based == 0
    assert result.possible_source_counts == (1, 0, 0, 0)
    assert result.final_possible_node_ids == ()
    assert "before outcome access" in result.reason


def test_target_eligibility_is_required_even_when_adjacent():
    node_ids = ("source", "target")
    initial = np.array([True, False], dtype=bool)
    persistence = np.zeros((2, 1), dtype=bool)
    target = np.zeros((2, 1), dtype=bool)
    adjacency = np.array([[False, True], [False, False]], dtype=bool)

    result = evaluate_temporal_source_closure(
        declaration(), node_ids, initial, persistence, target, adjacency
    )

    assert result.status == "stop_temporal_source_closure_gap"
    assert result.transitions[0].transition_target_count == 0


def test_adjacency_is_source_row_target_column_and_can_be_directed():
    node_ids = ("a", "b")
    persistence = np.zeros((2, 1), dtype=bool)
    target = np.ones((2, 1), dtype=bool)
    adjacency = np.array([[False, True], [False, False]], dtype=bool)

    forward = evaluate_temporal_source_closure(
        declaration(),
        node_ids,
        np.array([True, False], dtype=bool),
        persistence,
        target,
        adjacency,
    )
    reverse = evaluate_temporal_source_closure(
        declaration(),
        node_ids,
        np.array([False, True], dtype=bool),
        persistence,
        target,
        adjacency,
    )

    assert forward.passed is True
    assert forward.final_possible_node_ids == ("b",)
    assert reverse.passed is False


def test_north_anatolia_style_gap_regression():
    # Minimal abstract regression of the empirically discovered response-blind shape:
    # 14 -> 11 -> 46 -> 45 -> 0.  Counts are not outcomes; they represent optimistic
    # possible-source sets under frozen availability + transition constraints.
    n = 171
    node_ids = tuple(f"n{i:03d}" for i in range(n))
    initial = np.zeros(n, dtype=bool)
    initial[:14] = True
    persistence = np.zeros((n, 4), dtype=bool)
    target = np.zeros((n, 4), dtype=bool)
    adjacency = np.zeros((n, n), dtype=bool)

    # t0 -> t1: persist 11 sources.
    persistence[:11, 0] = True

    # t1 -> t2: permit 46 targets from any of the retained eleven sources.
    target[:46, 1] = True
    adjacency[:11, :46] = True

    # t2 -> t3: persist 45.
    persistence[:45, 2] = True

    # t3 -> t4: neither persistence nor eligible transition targets.

    result = evaluate_temporal_source_closure(
        declaration(), node_ids, initial, persistence, target, adjacency
    )

    assert result.possible_source_counts == (14, 11, 46, 45, 0)
    assert result.status == "stop_temporal_source_closure_gap"
    assert result.first_empty_transition_zero_based == 3


def test_union_of_possible_paths_is_kept_without_choosing_one_parent():
    node_ids = ("a", "b", "c", "d")
    initial = np.array([True, True, False, False], dtype=bool)
    persistence = np.zeros((4, 2), dtype=bool)
    target = np.array(
        [
            [False, False],
            [False, False],
            [True, False],
            [True, True],
        ],
        dtype=bool,
    )
    adjacency = np.array(
        [
            [False, False, True, False],
            [False, False, False, True],
            [False, False, False, True],
            [False, False, False, False],
        ],
        dtype=bool,
    )

    result = evaluate_temporal_source_closure(
        declaration(), node_ids, initial, persistence, target, adjacency
    )

    assert result.possible_source_counts == (2, 2, 1)
    assert result.final_possible_node_ids == ("d",)


def test_fingerprints_are_deterministic_and_contract_sensitive():
    node_ids = ("a", "b")
    initial = np.array([True, False], dtype=bool)
    persistence = np.ones((2, 1), dtype=bool)
    target = np.ones((2, 1), dtype=bool)
    adjacency = np.eye(2, dtype=bool)

    first = evaluate_temporal_source_closure(
        declaration(), node_ids, initial, persistence, target, adjacency
    )
    second = evaluate_temporal_source_closure(
        declaration(), node_ids, initial.copy(), persistence.copy(), target.copy(), adjacency.copy()
    )
    changed = evaluate_temporal_source_closure(
        TemporalSourceClosureDeclaration(
            closure_id="fresh-system-v2",
            source_semantics="response-blind possible sources",
            transition_semantics="same-node persistence plus declared source-to-target adjacency",
        ),
        node_ids,
        initial,
        persistence,
        target,
        adjacency,
    )

    assert first.fingerprint == second.fingerprint
    assert first.input_fingerprint == second.input_fingerprint
    assert first.fingerprint != changed.fingerprint


@pytest.mark.parametrize(
    "node_ids",
    [(), ("a", "a"), ("", "b")],
)
def test_invalid_node_ids_fail_closed(node_ids):
    with pytest.raises(ValueError):
        evaluate_temporal_source_closure(
            declaration(),
            node_ids,
            np.array([], dtype=bool),
            np.zeros((0, 1), dtype=bool),
            np.zeros((0, 1), dtype=bool),
            np.zeros((0, 0), dtype=bool),
        )


def test_shapes_and_dtypes_fail_closed():
    ids = ("a", "b")
    with pytest.raises(TypeError, match="boolean dtype"):
        evaluate_temporal_source_closure(
            declaration(),
            ids,
            np.array([1, 0], dtype=int),
            np.ones((2, 1), dtype=bool),
            np.ones((2, 1), dtype=bool),
            np.eye(2, dtype=bool),
        )
    with pytest.raises(ValueError, match="persistence_eligible first dimension"):
        evaluate_temporal_source_closure(
            declaration(),
            ids,
            np.array([True, False], dtype=bool),
            np.ones((3, 1), dtype=bool),
            np.ones((2, 1), dtype=bool),
            np.eye(2, dtype=bool),
        )
    with pytest.raises(ValueError, match="transition_adjacency"):
        evaluate_temporal_source_closure(
            declaration(),
            ids,
            np.array([True, False], dtype=bool),
            np.ones((2, 1), dtype=bool),
            np.ones((2, 1), dtype=bool),
            np.ones((2, 3), dtype=bool),
        )


def test_declaration_and_evaluator_types_fail_closed():
    with pytest.raises(ValueError, match="closure_id"):
        TemporalSourceClosureDeclaration(
            closure_id=" ",
            source_semantics="x",
            transition_semantics="y",
        )
    with pytest.raises(TypeError, match="declaration must be"):
        evaluate_temporal_source_closure(
            "bad",  # type: ignore[arg-type]
            ("a",),
            np.array([True], dtype=bool),
            np.ones((1, 1), dtype=bool),
            np.ones((1, 1), dtype=bool),
            np.ones((1, 1), dtype=bool),
        )
