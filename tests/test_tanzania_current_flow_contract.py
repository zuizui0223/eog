from __future__ import annotations

import math

import pytest

from eog.tanzania_current_flow_contract import (
    PRIMARY_HELDOUT_AREA_WEIGHT,
    SENSITIVITY_HELDOUT_AREA_WEIGHT,
    aggregate_weighted_resistance,
    audit_area_weights,
    audit_focal_identity,
    enumerate_resistance_combinations,
    heldout_area_weight,
    released_area_weight,
)


def _rows(order: list[int], areas: list[float] | None = None):
    areas = areas or [float(index + 2) for index in range(len(order))]
    return [
        {
            "patch_number": patch,
            "name": f"patch-{patch}",
            "Area_ha": area,
        }
        for patch, area in zip(order, areas, strict=True)
    ]


def test_resistance_grid_is_complete_and_deterministic():
    combinations = enumerate_resistance_combinations()
    assert len(combinations) == 512
    assert combinations[0] == {
        "eucalyptus": 1,
        "tea": 1,
        "other_agriculture": 1,
    }
    assert combinations[-1] == {
        "eucalyptus": 128,
        "tea": 128,
        "other_agriculture": 128,
    }
    assert len({tuple(row.values()) for row in combinations}) == 512


def test_implicit_focal_ids_are_not_patch_numbers_when_rows_are_permuted():
    audit = audit_focal_identity(_rows([3, 1, 2]), region="E")
    assert audit["n_identity_matches"] == 0
    assert audit["n_identity_mismatches"] == 3
    assert audit["implicit_identity_matches_patch_number"] is False
    assert [row["implicit_focal_id"] for row in audit["row_to_patch_mapping"]] == [1, 2, 3]
    assert [row["patch_number"] for row in audit["row_to_patch_mapping"]] == [3, 1, 2]


def test_identity_audit_accepts_explicit_patch_order():
    audit = audit_focal_identity(_rows([1, 2, 3]), region="W")
    assert audit["n_identity_matches"] == 3
    assert audit["implicit_identity_matches_patch_number"] is True


def test_released_weight_is_negative_below_one_and_singular_at_one():
    assert released_area_weight(0.5) < 0.0
    assert released_area_weight(10.0) == pytest.approx(1.0)
    with pytest.raises(ValueError, match="undefined"):
        released_area_weight(1.0)


def test_heldout_weights_are_positive_and_monotone_for_sub_hectare_patches():
    areas = [0.17, 0.18, 0.65, 0.72, 1.0, 3.0, 100.0]
    for mode in (PRIMARY_HELDOUT_AREA_WEIGHT, SENSITIVITY_HELDOUT_AREA_WEIGHT):
        weights = [heldout_area_weight(area, mode) for area in areas]
        assert all(math.isfinite(value) and value > 0.0 for value in weights)
        assert all(left > right for left, right in zip(weights, weights[1:]))


def test_area_audit_exposes_literal_problem_without_invalidating_repairs():
    audit = audit_area_weights(_rows([1, 2, 3], [0.5, 1.0, 2.0]), region="E")
    assert audit["released_nonpositive_or_undefined_count"] == 2
    assert audit["released_problem_patch_numbers"] == [1, 2]
    assert audit["heldout_formulas_positive_for_all_nodes"] is True
    assert audit["heldout_formulas_strictly_decrease_with_area"] is True


def test_weighted_resistance_uses_predeclared_positive_rule():
    result = aggregate_weighted_resistance([2.0, 5.0], [0.5, 10.0])
    expected = (
        2.0 * heldout_area_weight(0.5, PRIMARY_HELDOUT_AREA_WEIGHT)
        + 5.0 * heldout_area_weight(10.0, PRIMARY_HELDOUT_AREA_WEIGHT)
    )
    assert result == pytest.approx(expected)
    assert result > 0.0


def test_weighted_resistance_rejects_negative_distance():
    with pytest.raises(ValueError, match="non-negative"):
        aggregate_weighted_resistance([-1.0], [2.0])
