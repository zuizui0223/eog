import numpy as np
import pytest

from eog.tanzania_scoring import (
    PROBABILITY_EPSILON,
    bernoulli_log_loss,
    brier_score,
    paired_score_summary,
    species_mean_differences,
)


def test_log_loss_prefers_better_probabilities():
    y = np.array([0, 1, 0, 1], dtype=float)
    worse = np.array([0.4, 0.6, 0.4, 0.6])
    better = np.array([0.1, 0.9, 0.2, 0.8])
    assert bernoulli_log_loss(y, better).mean() < bernoulli_log_loss(y, worse).mean()
    assert brier_score(y, better).mean() < brier_score(y, worse).mean()


def test_paired_summary_uses_exact_valid_intersection():
    y = np.array([0, 1, 0, 1], dtype=float)
    ref = np.array([0.3, 0.7, 0.3, 0.7])
    cand = np.array([0.2, 0.8, 0.2, 0.8])
    summary = paired_score_summary(
        y,
        ref,
        cand,
        reference_valid=np.array([True, True, False, True]),
        candidate_valid=np.array([True, False, True, True]),
    )
    assert summary.n_matched == 2
    assert summary.mean_log_loss_difference < 0
    assert summary.mean_brier_difference < 0


def test_probability_endpoints_are_numerically_clipped_not_rejected():
    y = np.array([0, 1], dtype=float)
    p = np.array([0, 1], dtype=float)
    loss = bernoulli_log_loss(y, p, epsilon=PROBABILITY_EPSILON)
    assert np.all(np.isfinite(loss))
    assert np.all(loss >= 0)


def test_invalid_probability_or_binary_truth_fails():
    with pytest.raises(ValueError):
        bernoulli_log_loss([0, 2], [0.1, 0.9])
    with pytest.raises(ValueError):
        bernoulli_log_loss([0, 1], [-0.1, 1.1])


def test_species_means_preserve_species_as_cluster_unit():
    species = ["a", "a", "b", "b"]
    diff = np.array([-0.2, -0.4, 0.1, 0.3])
    means = species_mean_differences(species, diff)
    assert means["a"] == pytest.approx(-0.3)
    assert means["b"] == pytest.approx(0.2)
