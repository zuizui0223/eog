import numpy as np
import pytest

from eog.tanzania_scoring import (
    PROBABILITY_EPSILON,
    bernoulli_log_loss,
    brier_score,
    paired_score_summary,
    paired_species_cluster_inference,
    species_cluster_inference,
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
    ref = np.array([0.3, 0.7, np.nan, 0.7])
    cand = np.array([0.2, np.nan, 0.2, 0.8])
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


def test_invalid_nonfinite_difference_is_ignored_by_explicit_mask():
    means = species_mean_differences(
        ["a", "b"],
        np.array([-0.2, np.nan]),
        valid=np.array([True, False]),
    )
    assert set(means) == {"a"}
    assert means["a"] == pytest.approx(-0.2)


def test_cluster_inference_equal_weights_species_not_observations():
    summary = species_cluster_inference(
        ["a", "b", "b", "b"],
        np.array([-1.0, 1.0, 1.0, 1.0]),
        bootstrap_replicates=500,
        bootstrap_seed=7,
        sign_flip_replicates=1_000,
        sign_flip_seed=11,
    )
    assert summary.n_matched == 4
    assert summary.n_species == 2
    assert summary.micro_mean_difference == pytest.approx(0.5)
    assert summary.macro_mean_species_difference == pytest.approx(0.0)
    assert summary.sign_flip_p_value == pytest.approx(1.0)


def test_cluster_inference_is_reproducible_for_frozen_seeds():
    kwargs = dict(
        bootstrap_replicates=500,
        bootstrap_seed=17,
        sign_flip_replicates=1_000,
        sign_flip_seed=19,
    )
    first = species_cluster_inference(
        ["a", "a", "b", "b", "c", "c"],
        np.array([-0.4, -0.2, 0.1, 0.3, -0.1, -0.2]),
        **kwargs,
    )
    second = species_cluster_inference(
        ["a", "a", "b", "b", "c", "c"],
        np.array([-0.4, -0.2, 0.1, 0.3, -0.1, -0.2]),
        **kwargs,
    )
    assert first == second


def test_paired_cluster_inference_uses_candidate_minus_reference_direction():
    y = np.array([0, 1, 0, 1], dtype=float)
    species = ["a", "a", "b", "b"]
    reference = np.array([0.4, 0.6, 0.4, 0.6])
    candidate = np.array([0.1, 0.9, 0.2, 0.8])
    summary = paired_species_cluster_inference(
        y,
        species,
        reference,
        candidate,
        bootstrap_replicates=500,
        bootstrap_seed=23,
        sign_flip_replicates=1_000,
        sign_flip_seed=29,
    )
    assert summary.n_matched == 4
    assert summary.n_species == 2
    assert summary.macro_mean_species_difference < 0
    assert summary.micro_mean_difference < 0


def test_cluster_inference_requires_at_least_two_species():
    with pytest.raises(ValueError, match="at least two species"):
        species_cluster_inference(
            ["a", "a"],
            np.array([-0.1, -0.2]),
            bootstrap_replicates=10,
            sign_flip_replicates=10,
        )
