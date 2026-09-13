from __future__ import annotations

import math

import numpy as np
import pytest
import sklearn
from sklearn.metrics import log_loss

from eog.v2.excluded_world_information import binary_log_loss
from eog.v2.predictive_complementarity import (
    PairedOuterUnitScore,
    PredictiveComplementarityDeclaration,
    evaluate_predictive_complementarity,
)


FROZEN_SCIKIT_LEARN_VERSION = "1.5.2"


def _manual_binary_log_loss(y: np.ndarray, p: np.ndarray) -> float:
    return float(
        np.mean(
            [
                -(int(outcome) * math.log(float(probability))
                  + (1 - int(outcome)) * math.log(1.0 - float(probability)))
                for outcome, probability in zip(y, p, strict=True)
            ]
        )
    )


def test_frozen_endpoint_scoring_runtime_uses_declared_sklearn_version():
    assert sklearn.__version__ == FROZEN_SCIKIT_LEARN_VERSION


def test_binary_log_loss_matches_known_bernoulli_fixture_and_sklearn():
    y = np.asarray([0, 1, 1, 0], dtype=int)
    p = np.asarray([0.1, 0.8, 0.25, 0.6], dtype=float)

    manual = _manual_binary_log_loss(y, p)
    sklearn_score = float(log_loss(y, p, labels=[0, 1]))
    rowwise_score = float(np.mean([binary_log_loss(int(a), float(b)) for a, b in zip(y, p, strict=True)]))

    assert manual == pytest.approx(0.6577722899915204, abs=1e-15)
    assert sklearn_score == pytest.approx(manual, abs=1e-15)
    assert rowwise_score == pytest.approx(manual, abs=1e-15)


def test_probability_boundaries_are_clipped_to_finite_loss():
    perfect_zero = binary_log_loss(0, 0.0)
    perfect_one = binary_log_loss(1, 1.0)
    impossible_zero = binary_log_loss(1, 0.0)
    impossible_one = binary_log_loss(0, 1.0)

    assert perfect_zero >= 0.0
    assert perfect_one >= 0.0
    assert math.isfinite(impossible_zero)
    assert math.isfinite(impossible_one)
    assert impossible_zero > 30.0
    assert impossible_one > 30.0


def test_raw_probability_scores_flow_into_frozen_paired_decision_without_sign_flip():
    y_a = np.asarray([0, 1, 1, 0], dtype=int)
    baseline_a = np.asarray([0.20, 0.70, 0.45, 0.30], dtype=float)
    augmented_a = np.asarray([0.10, 0.80, 0.60, 0.20], dtype=float)

    y_b = np.asarray([0, 0, 1, 1], dtype=int)
    baseline_b = np.asarray([0.35, 0.25, 0.55, 0.65], dtype=float)
    augmented_b = np.asarray([0.25, 0.20, 0.65, 0.75], dtype=float)

    paired_scores = [
        PairedOuterUnitScore(
            "outer-a",
            float(log_loss(y_a, baseline_a, labels=[0, 1])),
            float(log_loss(y_a, augmented_a, labels=[0, 1])),
        ),
        PairedOuterUnitScore(
            "outer-b",
            float(log_loss(y_b, baseline_b, labels=[0, 1])),
            float(log_loss(y_b, augmented_b, labels=[0, 1])),
        ),
    ]

    declaration = PredictiveComplementarityDeclaration(
        metric_name="binary_log_loss",
        lower_is_better=True,
        expected_outer_unit_count=2,
        favorable_min_augmented_wins=2,
        adverse_min_baseline_wins=2,
        learner_fit_fingerprint="rf-frozen-runtime",
        response_endpoint_fingerprint="numeric-regression-fixture",
        split_fingerprint="two-fixed-outer-units",
        external_feature_fingerprint="baseline-fixture",
        eog_feature_fingerprint="layer-b-fixture",
    )
    result = evaluate_predictive_complementarity(declaration, paired_scores)

    expected_baseline_macro = float(np.mean([score.baseline_score for score in paired_scores]))
    expected_augmented_macro = float(np.mean([score.augmented_score for score in paired_scores]))

    assert result.baseline_macro_score == pytest.approx(expected_baseline_macro, abs=1e-15)
    assert result.augmented_macro_score == pytest.approx(expected_augmented_macro, abs=1e-15)
    assert result.augmented_minus_baseline == pytest.approx(
        expected_augmented_macro - expected_baseline_macro,
        abs=1e-15,
    )
    assert result.augmented_better_outer_units == 2
    assert result.baseline_better_outer_units == 0
    assert result.status == "favorable_complementary_added_value"
