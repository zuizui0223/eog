import inspect

import numpy as np
import pytest

from eog.v2.world_scale_ladder import (
    StructuralScaleLadderDeclaration,
    build_structural_scale_ladder,
    compose_intersection_worlds,
    structural_scale_adjacencies,
)


def _line_distance(values):
    x = np.asarray(values, dtype=float)
    return np.abs(x[:, None] - x[None, :])


def test_scale_ladder_uses_minimal_thresholds_for_declared_component_regimes():
    # Two tight triplets separated by a large gap. Local site-spacing summaries would
    # remain at distance 1, but a spanning structural regime must cross the gap.
    node_ids = tuple("abcdef")
    distance = _line_distance([0, 1, 2, 20, 21, 22])
    declaration = StructuralScaleLadderDeclaration(
        axis_id="geo",
        target_largest_component_fractions=(0.5, 1.0),
    )

    ladder = build_structural_scale_ladder(node_ids, distance, declaration)

    assert ladder.thresholds == pytest.approx((1.0, 18.0))
    assert ladder.levels[0].achieved_largest_component_fraction == pytest.approx(0.5)
    assert ladder.levels[1].achieved_largest_component_fraction == pytest.approx(1.0)
    assert ladder.levels[0].weak_component_count == 2
    assert ladder.levels[1].weak_component_count == 1

    # Minimality: immediately below the spanning threshold the two triplets remain split.
    below = distance <= (ladder.thresholds[1] - 1e-9)
    np.fill_diagonal(below, False)
    assert not np.any(below[:3, 3:])


def test_scale_ladder_edges_are_nested_and_targets_are_monotone():
    node_ids = tuple(str(i) for i in range(8))
    distance = _line_distance([0, 1, 2, 3, 10, 11, 12, 30])
    declaration = StructuralScaleLadderDeclaration(
        axis_id="geo",
        target_largest_component_fractions=(0.25, 0.5, 0.75, 1.0),
    )
    ladder = build_structural_scale_ladder(node_ids, distance, declaration)
    worlds = structural_scale_adjacencies(ladder, distance)

    assert list(ladder.thresholds) == sorted(ladder.thresholds)
    matrices = [worlds[level_id] for level_id in ladder.level_ids]
    for earlier, later in zip(matrices, matrices[1:]):
        assert np.all(~earlier | later)


def test_ladder_thresholds_do_not_depend_on_node_order():
    ids = np.asarray(["a", "b", "c", "d", "e", "f"])
    distance = _line_distance([0, 1, 2, 20, 21, 22])
    declaration = StructuralScaleLadderDeclaration(
        axis_id="geo",
        target_largest_component_fractions=(0.5, 1.0),
    )
    original = build_structural_scale_ladder(ids, distance, declaration)

    order = np.asarray([3, 0, 5, 2, 1, 4])
    permuted = build_structural_scale_ladder(
        ids[order], distance[np.ix_(order, order)], declaration
    )

    assert permuted.thresholds == pytest.approx(original.thresholds)
    assert [row.achieved_largest_component_fraction for row in permuted.levels] == pytest.approx(
        [row.achieved_largest_component_fraction for row in original.levels]
    )


def test_tied_distances_are_admitted_together_before_target_evaluation():
    # Equilateral triangle: all three edges arrive at the same threshold.
    distance = np.asarray(
        [
            [0.0, 1.0, 1.0],
            [1.0, 0.0, 1.0],
            [1.0, 1.0, 0.0],
        ]
    )
    declaration = StructuralScaleLadderDeclaration(
        axis_id="geo",
        target_largest_component_fractions=(2 / 3, 1.0),
    )
    ladder = build_structural_scale_ladder(("a", "b", "c"), distance, declaration)

    assert ladder.thresholds == pytest.approx((1.0, 1.0))
    assert all(row.achieved_largest_component_fraction == pytest.approx(1.0) for row in ladder.levels)


def test_near_ties_outside_absolute_threshold_tolerance_are_not_union_only_edges():
    # Regression for geodesic regular grids: rtol-based np.isclose previously grouped
    # the first two edges at threshold 10.0 because 5e-12 is tiny relative to 10 km,
    # while adjacency reconstruction admitted only <= 10.0 + 1e-12.  The union-find
    # scan could therefore claim 3/4 connectivity at an adjacency with only 2/4.
    distance = np.asarray(
        [
            [0.0, 10.0, 30.0, 60.0],
            [10.0, 0.0, 10.0 + 5e-12, 40.0],
            [30.0, 10.0 + 5e-12, 0.0, 50.0],
            [60.0, 40.0, 50.0, 0.0],
        ]
    )
    declaration = StructuralScaleLadderDeclaration(
        axis_id="geo",
        target_largest_component_fractions=(0.75,),
    )

    ladder = build_structural_scale_ladder(("a", "b", "c", "d"), distance, declaration)
    worlds = structural_scale_adjacencies(ladder, distance)

    assert ladder.thresholds[0] == pytest.approx(10.0 + 5e-12, abs=1e-13)
    assert ladder.levels[0].achieved_largest_component_fraction == pytest.approx(0.75)
    adjacency = worlds[ladder.level_ids[0]]
    assert adjacency[0, 1]
    assert adjacency[1, 2]
    assert not adjacency[0, 2]


def test_structural_scale_api_has_no_response_or_occurrence_argument():
    signature = inspect.signature(build_structural_scale_ladder)
    forbidden = {"response", "responses", "species", "occurrence", "occurrences", "y"}
    assert forbidden.isdisjoint(signature.parameters)


def test_distance_matrix_is_frozen_by_node_order_and_values():
    distance = _line_distance([0, 1, 2, 10])
    declaration = StructuralScaleLadderDeclaration(
        axis_id="geo", target_largest_component_fractions=(0.5, 1.0)
    )
    ladder = build_structural_scale_ladder(("a", "b", "c", "d"), distance, declaration)

    changed = distance.copy()
    changed[0, 1] = changed[1, 0] = 2.0
    with pytest.raises(ValueError, match="differs from the frozen ladder"):
        structural_scale_adjacencies(ladder, changed)


def test_intersection_composition_retains_primary_only_worlds():
    primary = {
        "local": np.asarray([[0, 1, 0], [1, 0, 0], [0, 0, 0]], dtype=bool),
        "spanning": np.asarray([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=bool),
    }
    secondary = {
        "strict": np.asarray([[0, 1, 0], [1, 0, 0], [0, 0, 0]], dtype=bool)
    }

    worlds = compose_intersection_worlds(primary, secondary, include_primary_only=True)

    assert set(worlds) == {
        "primary::local",
        "primary::spanning",
        "primary::local|secondary::strict",
        "primary::spanning|secondary::strict",
    }
    assert np.array_equal(worlds["primary::spanning"], primary["spanning"])
    assert not worlds["primary::spanning|secondary::strict"][1, 2]


def test_declaration_rejects_implicit_or_unsorted_scale_targets():
    with pytest.raises(ValueError, match="at least one"):
        StructuralScaleLadderDeclaration(axis_id="geo", target_largest_component_fractions=())
    with pytest.raises(ValueError, match="strictly increasing"):
        StructuralScaleLadderDeclaration(
            axis_id="geo", target_largest_component_fractions=(0.75, 0.5)
        )
    with pytest.raises(ValueError, match="strictly increasing"):
        StructuralScaleLadderDeclaration(
            axis_id="geo", target_largest_component_fractions=(0.5, 0.5)
        )
