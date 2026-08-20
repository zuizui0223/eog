from __future__ import annotations

import math

import pytest

from eog.v2.predictive_complementarity import (
    PairedOuterUnitScore,
    PredictiveComplementarityDeclaration,
    evaluate_predictive_complementarity,
)


def declaration(*, lower_is_better: bool = True, n: int = 3):
    return PredictiveComplementarityDeclaration(
        metric_name="log_loss" if lower_is_better else "auc",
        lower_is_better=lower_is_better,
        expected_outer_unit_count=n,
        favorable_min_augmented_wins=2,
        adverse_min_baseline_wins=2,
        learner_fit_fingerprint="learner-v1",
        response_endpoint_fingerprint="endpoint-v1",
        split_fingerprint="split-v1",
        external_feature_fingerprint="external-v1",
        eog_feature_fingerprint="symmetric-world-support-summary-v1",
    )


def test_lower_is_better_favorable_requires_macro_and_outer_wins():
    result = evaluate_predictive_complementarity(
        declaration(),
        [
            PairedOuterUnitScore("y1", 0.30, 0.28),
            PairedOuterUnitScore("y2", 0.20, 0.18),
            PairedOuterUnitScore("y3", 0.25, 0.26),
        ],
    )
    assert result.status == "favorable_complementary_added_value"
    assert result.augmented_better_outer_units == 2
    assert result.baseline_better_outer_units == 1
    assert result.augmented_minus_baseline < 0


def test_lower_is_better_adverse_is_preserved():
    result = evaluate_predictive_complementarity(
        declaration(),
        [
            PairedOuterUnitScore("y1", 0.20, 0.23),
            PairedOuterUnitScore("y2", 0.25, 0.26),
            PairedOuterUnitScore("y3", 0.40, 0.39),
        ],
    )
    assert result.status == "adverse_complementary_added_value"
    assert result.baseline_better_outer_units == 2
    assert result.augmented_minus_baseline > 0


def test_conflicting_macro_and_direction_is_not_forced_to_win():
    result = evaluate_predictive_complementarity(
        declaration(),
        [
            PairedOuterUnitScore("y1", 0.50, 0.10),
            PairedOuterUnitScore("y2", 0.20, 0.21),
            PairedOuterUnitScore("y3", 0.20, 0.21),
        ],
    )
    assert result.augmented_minus_baseline < 0
    assert result.augmented_better_outer_units == 1
    assert result.status == "no_confirmed_complementary_added_value"


def test_higher_is_better_reverses_score_direction_only():
    result = evaluate_predictive_complementarity(
        declaration(lower_is_better=False),
        [
            PairedOuterUnitScore("fold1", 0.70, 0.73),
            PairedOuterUnitScore("fold2", 0.75, 0.76),
            PairedOuterUnitScore("fold3", 0.80, 0.79),
        ],
    )
    assert result.status == "favorable_complementary_added_value"
    assert result.augmented_minus_baseline > 0


def test_outer_unit_order_does_not_change_result_or_fingerprint():
    rows = [
        PairedOuterUnitScore("b", 0.3, 0.2),
        PairedOuterUnitScore("a", 0.2, 0.1),
        PairedOuterUnitScore("c", 0.4, 0.5),
    ]
    first = evaluate_predictive_complementarity(declaration(), rows)
    second = evaluate_predictive_complementarity(declaration(), list(reversed(rows)))
    assert first == second


def test_tie_tolerance_is_explicit_and_conservative():
    result = evaluate_predictive_complementarity(
        declaration(),
        [
            PairedOuterUnitScore("a", 0.2, 0.1999999),
            PairedOuterUnitScore("b", 0.3, 0.2999999),
            PairedOuterUnitScore("c", 0.4, 0.4),
        ],
        tie_tolerance=1e-5,
    )
    assert result.tied_outer_units == 3
    assert result.status == "no_confirmed_complementary_added_value"


def test_declared_outer_unit_count_is_mandatory():
    with pytest.raises(ValueError, match="outer-unit count"):
        evaluate_predictive_complementarity(
            declaration(),
            [
                PairedOuterUnitScore("a", 0.2, 0.1),
                PairedOuterUnitScore("b", 0.3, 0.2),
            ],
        )


def test_duplicate_outer_unit_ids_are_rejected():
    with pytest.raises(ValueError, match="unique"):
        evaluate_predictive_complementarity(
            declaration(),
            [
                PairedOuterUnitScore("a", 0.2, 0.1),
                PairedOuterUnitScore("a", 0.3, 0.2),
                PairedOuterUnitScore("c", 0.4, 0.5),
            ],
        )


def test_nonfinite_scores_and_invalid_thresholds_are_rejected():
    with pytest.raises(ValueError, match="finite"):
        PairedOuterUnitScore("a", math.nan, 0.1)
    with pytest.raises(ValueError, match="cannot exceed"):
        PredictiveComplementarityDeclaration(
            metric_name="log_loss",
            lower_is_better=True,
            expected_outer_unit_count=2,
            favorable_min_augmented_wins=3,
            adverse_min_baseline_wins=1,
            learner_fit_fingerprint="learner",
            response_endpoint_fingerprint="endpoint",
            split_fingerprint="split",
            external_feature_fingerprint="external",
            eog_feature_fingerprint="eog",
        )


def test_contract_types_fail_closed():
    with pytest.raises(TypeError, match="lower_is_better"):
        PredictiveComplementarityDeclaration(
            metric_name="log_loss",
            lower_is_better="yes",  # type: ignore[arg-type]
            expected_outer_unit_count=3,
            favorable_min_augmented_wins=2,
            adverse_min_baseline_wins=2,
            learner_fit_fingerprint="learner",
            response_endpoint_fingerprint="endpoint",
            split_fingerprint="split",
            external_feature_fingerprint="external",
            eog_feature_fingerprint="eog",
        )
    with pytest.raises(ValueError, match="positive integer"):
        PredictiveComplementarityDeclaration(
            metric_name="log_loss",
            lower_is_better=True,
            expected_outer_unit_count=3.5,  # type: ignore[arg-type]
            favorable_min_augmented_wins=2,
            adverse_min_baseline_wins=2,
            learner_fit_fingerprint="learner",
            response_endpoint_fingerprint="endpoint",
            split_fingerprint="split",
            external_feature_fingerprint="external",
            eog_feature_fingerprint="eog",
        )
    with pytest.raises(TypeError, match="outer_unit_id"):
        PairedOuterUnitScore(1, 0.2, 0.1)  # type: ignore[arg-type]


def test_declaration_fingerprint_changes_with_frozen_scientific_choice():
    base = declaration()
    changed = PredictiveComplementarityDeclaration(
        metric_name=base.metric_name,
        lower_is_better=base.lower_is_better,
        expected_outer_unit_count=base.expected_outer_unit_count,
        favorable_min_augmented_wins=base.favorable_min_augmented_wins,
        adverse_min_baseline_wins=base.adverse_min_baseline_wins,
        learner_fit_fingerprint="learner-v2",
        response_endpoint_fingerprint=base.response_endpoint_fingerprint,
        split_fingerprint=base.split_fingerprint,
        external_feature_fingerprint=base.external_feature_fingerprint,
        eog_feature_fingerprint=base.eog_feature_fingerprint,
    )
    assert base.fingerprint != changed.fingerprint


def test_validation_facade_exposes_complementarity_without_root_growth():
    from eog.v2 import validation

    assert validation.PredictiveComplementarityDeclaration is PredictiveComplementarityDeclaration
    assert validation.PairedOuterUnitScore is PairedOuterUnitScore
    assert validation.evaluate_predictive_complementarity is evaluate_predictive_complementarity
