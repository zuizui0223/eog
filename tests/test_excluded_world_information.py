from __future__ import annotations

from dataclasses import replace
import math

import pytest

from eog.v2.excluded_world_information import (
    ExplanatoryHeldoutRow,
    ExplanatoryTrainingRow,
    binary_entropy,
    evaluate_excluded_world_information,
    freeze_excluded_world_information_thresholds,
)


def _training_rows() -> tuple[ExplanatoryTrainingRow, ...]:
    return (
        ExplanatoryTrainingRow("t1", 0.05, 0.00),
        ExplanatoryTrainingRow("t2", 0.25, 0.10),
        ExplanatoryTrainingRow("t3", 0.50, 0.40),
        ExplanatoryTrainingRow("t4", 0.75, 0.80),
    )


def test_thresholds_are_training_only_medians_and_order_invariant():
    forward = freeze_excluded_world_information_thresholds(_training_rows())
    reverse = freeze_excluded_world_information_thresholds(tuple(reversed(_training_rows())))

    assert forward == reverse
    assert forward.training_row_count == 4
    assert forward.local_uncertainty_entropy_threshold == pytest.approx(
        (binary_entropy(0.25) + binary_entropy(0.75)) / 2.0
    )
    assert forward.world_disagreement_support_range_threshold == pytest.approx(0.25)


def test_all_four_frozen_strata_are_retained_and_primary_status_is_immutable():
    thresholds = freeze_excluded_world_information_thresholds(_training_rows())
    rows = (
        ExplanatoryHeldoutRow(
            "h1", 0, 0.05, 0.04, 0.00, 0.00, 0.50, "robustly_supported"
        ),
        ExplanatoryHeldoutRow(
            "h2", 1, 0.10, 0.20, 0.40, 0.20, 0.50, "contingent"
        ),
        ExplanatoryHeldoutRow(
            "h3", 1, 0.50, 0.70, 0.10, 0.05, 0.50, "robustly_supported"
        ),
        ExplanatoryHeldoutRow(
            "h4", 1, 0.50, 0.80, 0.80, 0.30, 0.50, "contingent"
        ),
    )

    result = evaluate_excluded_world_information(
        outer_unit_id="outer-1",
        thresholds=thresholds,
        heldout_rows=rows,
        declared_world_count=6,
        surviving_world_count=3,
    )

    assert {summary.stratum for summary in result.strata} == {
        "low_local_uncertainty_low_world_disagreement",
        "low_local_uncertainty_high_world_disagreement",
        "high_local_uncertainty_low_world_disagreement",
        "high_local_uncertainty_high_world_disagreement",
    }
    assert all(summary.row_count == 1 for summary in result.strata)
    assert result.world_contraction_fraction == pytest.approx(0.5)
    assert result.contingent_row_fraction == pytest.approx(0.5)
    assert result.structurally_informative is True
    assert result.primary_terminal_status_mutable is False
    assert result.augmented_macro_log_loss < result.baseline_macro_log_loss


def test_empty_strata_are_retained_without_response_driven_rebinning():
    thresholds = freeze_excluded_world_information_thresholds(_training_rows())
    row = ExplanatoryHeldoutRow(
        "h1", 0, 0.01, 0.01, 0.00, 0.00, 1.00, "robustly_supported"
    )

    result = evaluate_excluded_world_information(
        outer_unit_id="outer-empty",
        thresholds=thresholds,
        heldout_rows=(row,),
        declared_world_count=4,
        surviving_world_count=4,
    )

    assert sum(summary.row_count == 0 for summary in result.strata) == 3
    assert result.structurally_informative is False
    for summary in result.strata:
        if summary.row_count == 0:
            assert summary.baseline_mean_log_loss is None
            assert summary.augmented_mean_log_loss is None
            assert summary.augmented_minus_baseline_mean_log_loss is None


def test_surviving_world_fraction_must_match_exact_world_counts():
    thresholds = freeze_excluded_world_information_thresholds(_training_rows())
    row = ExplanatoryHeldoutRow(
        "h1", 1, 0.5, 0.6, 0.2, 0.1, 0.75, "contingent"
    )

    with pytest.raises(ValueError, match="inconsistent"):
        evaluate_excluded_world_information(
            outer_unit_id="outer-mismatch",
            thresholds=thresholds,
            heldout_rows=(row,),
            declared_world_count=4,
            surviving_world_count=2,
        )


@pytest.mark.parametrize("probability", [-0.1, 1.1, math.inf])
def test_invalid_probabilities_fail_closed(probability):
    with pytest.raises((TypeError, ValueError)):
        ExplanatoryTrainingRow("bad", probability, 0.1)


def test_duplicate_ids_fail_closed():
    duplicate_training = (
        ExplanatoryTrainingRow("same", 0.1, 0.1),
        ExplanatoryTrainingRow("same", 0.2, 0.2),
    )
    with pytest.raises(ValueError, match="unique"):
        freeze_excluded_world_information_thresholds(duplicate_training)

    thresholds = freeze_excluded_world_information_thresholds(_training_rows())
    heldout = ExplanatoryHeldoutRow(
        "same", 0, 0.1, 0.1, 0.1, 0.1, 1.0, "robustly_supported"
    )
    with pytest.raises(ValueError, match="unique"):
        evaluate_excluded_world_information(
            outer_unit_id="outer-duplicate",
            thresholds=thresholds,
            heldout_rows=(heldout, replace(heldout, outcome=1)),
            declared_world_count=1,
            surviving_world_count=1,
        )
