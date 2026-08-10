"""Leakage-safe scoring primitives for the Tanzania external benchmark.

These functions are intentionally outcome-agnostic utilities. They implement
the pre-outcome scoring contract using only already-frozen held-out labels and
probabilities. They do not fit models, choose folds, tune thresholds, or build
EOG graphs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

PROBABILITY_EPSILON = 1e-15
SPECIES_BOOTSTRAP_REPLICATES = 10_000
SPECIES_BOOTSTRAP_SEED = 20260810
SPECIES_SIGN_FLIP_REPLICATES = 100_000
SPECIES_SIGN_FLIP_SEED = 20260810
SPECIES_BOOTSTRAP_QUANTILES = (0.025, 0.975)


@dataclass(frozen=True)
class PairedScoreSummary:
    n_matched: int
    mean_log_loss_reference: float
    mean_log_loss_candidate: float
    mean_log_loss_difference: float
    mean_brier_reference: float
    mean_brier_candidate: float
    mean_brier_difference: float


@dataclass(frozen=True)
class SpeciesClusterInference:
    """Frozen species-clustered summary for one paired method contrast.

    Differences are candidate minus reference. Negative values therefore mean
    the candidate has lower (better) held-out loss.
    """

    n_matched: int
    n_species: int
    micro_mean_difference: float
    macro_mean_species_difference: float
    bootstrap_ci_lower: float
    bootstrap_ci_upper: float
    bootstrap_replicates: int
    bootstrap_seed: int
    sign_flip_p_value: float
    sign_flip_replicates: int
    sign_flip_seed: int


def _validated_binary(y: Sequence[float] | np.ndarray) -> np.ndarray:
    arr = np.asarray(y, dtype=float)
    if arr.ndim != 1:
        raise ValueError("y must be one-dimensional")
    if not np.all(np.isfinite(arr)):
        raise ValueError("y contains non-finite values")
    if not np.all(np.isin(arr, [0.0, 1.0])):
        raise ValueError("y must contain only 0/1 values")
    return arr


def _probability_array(p: Sequence[float] | np.ndarray) -> np.ndarray:
    arr = np.asarray(p, dtype=float)
    if arr.ndim != 1:
        raise ValueError("probabilities must be one-dimensional")
    return arr


def _validate_probability_values(values: np.ndarray, label: str) -> None:
    if not np.all(np.isfinite(values)):
        raise ValueError(f"{label} contains non-finite valid values")
    if np.any((values < 0.0) | (values > 1.0)):
        raise ValueError(f"{label} valid values must lie in [0, 1]")


def _validated_probability(p: Sequence[float] | np.ndarray) -> np.ndarray:
    arr = _probability_array(p)
    _validate_probability_values(arr, "probabilities")
    return arr


def _validated_mask(
    value: Sequence[bool] | np.ndarray | None,
    *,
    size: int,
    label: str,
) -> np.ndarray:
    if value is None:
        return np.ones(size, dtype=bool)
    mask = np.asarray(value, dtype=bool)
    if mask.shape != (size,):
        raise ValueError(f"{label} must be a one-dimensional mask matching y")
    return mask


def _validated_replicates(value: int, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a positive integer")
    result = int(value)
    if result != value or result <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return result


def _paired_inputs(
    y: Sequence[float] | np.ndarray,
    reference_probability: Sequence[float] | np.ndarray,
    candidate_probability: Sequence[float] | np.ndarray,
    reference_valid: Sequence[bool] | np.ndarray | None,
    candidate_valid: Sequence[bool] | np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    yy = _validated_binary(y)
    ref = _probability_array(reference_probability)
    cand = _probability_array(candidate_probability)
    if not (yy.shape == ref.shape == cand.shape):
        raise ValueError("y/reference/candidate arrays must have identical shape")
    ref_valid = _validated_mask(reference_valid, size=yy.size, label="reference_valid")
    cand_valid = _validated_mask(candidate_valid, size=yy.size, label="candidate_valid")
    _validate_probability_values(ref[ref_valid], "reference probabilities")
    _validate_probability_values(cand[cand_valid], "candidate probabilities")
    matched = ref_valid & cand_valid
    if not np.any(matched):
        raise ValueError("no matched valid held-out predictions")
    return yy, ref, cand, matched


def bernoulli_log_loss(
    y: Sequence[float] | np.ndarray,
    probability: Sequence[float] | np.ndarray,
    *,
    epsilon: float = PROBABILITY_EPSILON,
) -> np.ndarray:
    """Return per-observation Bernoulli negative log likelihood.

    ``epsilon`` exists only for numerical stability and must be shared by every
    method in a benchmark comparison.
    """
    yy = _validated_binary(y)
    pp = _validated_probability(probability)
    if yy.shape != pp.shape:
        raise ValueError("y and probability must have identical shape")
    if not (0.0 < epsilon < 0.5):
        raise ValueError("epsilon must lie strictly between 0 and 0.5")
    clipped = np.clip(pp, epsilon, 1.0 - epsilon)
    return -(yy * np.log(clipped) + (1.0 - yy) * np.log(1.0 - clipped))


def brier_score(
    y: Sequence[float] | np.ndarray,
    probability: Sequence[float] | np.ndarray,
) -> np.ndarray:
    """Return per-observation Brier score."""
    yy = _validated_binary(y)
    pp = _validated_probability(probability)
    if yy.shape != pp.shape:
        raise ValueError("y and probability must have identical shape")
    return np.square(pp - yy)


def paired_score_summary(
    y: Sequence[float] | np.ndarray,
    reference_probability: Sequence[float] | np.ndarray,
    candidate_probability: Sequence[float] | np.ndarray,
    *,
    reference_valid: Sequence[bool] | np.ndarray | None = None,
    candidate_valid: Sequence[bool] | np.ndarray | None = None,
    epsilon: float = PROBABILITY_EPSILON,
) -> PairedScoreSummary:
    """Compare two methods on their exact intersection of valid predictions."""
    yy, ref, cand, matched = _paired_inputs(
        y,
        reference_probability,
        candidate_probability,
        reference_valid,
        candidate_valid,
    )
    y_m = yy[matched]
    ref_m = ref[matched]
    cand_m = cand[matched]
    ref_ll = bernoulli_log_loss(y_m, ref_m, epsilon=epsilon)
    cand_ll = bernoulli_log_loss(y_m, cand_m, epsilon=epsilon)
    ref_br = brier_score(y_m, ref_m)
    cand_br = brier_score(y_m, cand_m)

    return PairedScoreSummary(
        n_matched=int(matched.sum()),
        mean_log_loss_reference=float(np.mean(ref_ll)),
        mean_log_loss_candidate=float(np.mean(cand_ll)),
        mean_log_loss_difference=float(np.mean(cand_ll - ref_ll)),
        mean_brier_reference=float(np.mean(ref_br)),
        mean_brier_candidate=float(np.mean(cand_br)),
        mean_brier_difference=float(np.mean(cand_br - ref_br)),
    )


def species_mean_differences(
    species_ids: Iterable[str],
    per_observation_difference: Sequence[float] | np.ndarray,
    valid: Sequence[bool] | np.ndarray | None = None,
) -> dict[str, float]:
    """Aggregate matched score differences at species level."""
    species = np.asarray([str(x).strip() for x in species_ids], dtype=object)
    diff = np.asarray(per_observation_difference, dtype=float)
    if species.ndim != 1 or diff.ndim != 1 or species.shape != diff.shape:
        raise ValueError("species_ids and differences must be aligned 1-D arrays")
    mask = _validated_mask(valid, size=diff.size, label="valid")
    if not np.all(np.isfinite(diff[mask])):
        raise ValueError("valid differences contain non-finite values")
    if np.any(species[mask] == ""):
        raise ValueError("valid species IDs must be nonblank")

    out: dict[str, float] = {}
    for name in sorted(set(species[mask].tolist())):
        selected = mask & (species == name)
        out[name] = float(np.mean(diff[selected]))
    return out


def _sign_flip_p_value(
    species_means: np.ndarray,
    *,
    replicates: int,
    seed: int,
) -> float:
    observed = abs(float(np.mean(species_means)))
    rng = np.random.default_rng(seed)
    extreme = 0
    completed = 0
    chunk_size = 10_000
    while completed < replicates:
        current = min(chunk_size, replicates - completed)
        signs = rng.integers(
            0,
            2,
            size=(current, species_means.size),
            dtype=np.int8,
        )
        signs = signs * 2 - 1
        permuted = np.mean(signs * species_means, axis=1)
        extreme += int(np.count_nonzero(np.abs(permuted) >= observed))
        completed += current
    return float((extreme + 1) / (replicates + 1))


def species_cluster_inference(
    species_ids: Iterable[str],
    per_observation_difference: Sequence[float] | np.ndarray,
    valid: Sequence[bool] | np.ndarray | None = None,
    *,
    bootstrap_replicates: int = SPECIES_BOOTSTRAP_REPLICATES,
    bootstrap_seed: int = SPECIES_BOOTSTRAP_SEED,
    sign_flip_replicates: int = SPECIES_SIGN_FLIP_REPLICATES,
    sign_flip_seed: int = SPECIES_SIGN_FLIP_SEED,
) -> SpeciesClusterInference:
    """Summarize a paired contrast with species as the replication unit.

    The inferential point estimate is the equal-weight mean of per-species mean
    differences. The observation-weighted mean is retained as a descriptive
    diagnostic. Species are resampled as intact clusters for the percentile
    interval; sites are not independently resampled.
    """
    species = np.asarray([str(x).strip() for x in species_ids], dtype=object)
    diff = np.asarray(per_observation_difference, dtype=float)
    if species.ndim != 1 or diff.ndim != 1 or species.shape != diff.shape:
        raise ValueError("species_ids and differences must be aligned 1-D arrays")
    mask = _validated_mask(valid, size=diff.size, label="valid")
    if not np.any(mask):
        raise ValueError("no valid matched observations for clustered inference")
    if not np.all(np.isfinite(diff[mask])):
        raise ValueError("valid differences contain non-finite values")
    if np.any(species[mask] == ""):
        raise ValueError("valid species IDs must be nonblank")

    by_species = species_mean_differences(species, diff, mask)
    if len(by_species) < 2:
        raise ValueError("clustered inference requires at least two species")
    species_means = np.asarray(list(by_species.values()), dtype=float)

    n_bootstrap = _validated_replicates(
        bootstrap_replicates,
        "bootstrap_replicates",
    )
    n_sign_flip = _validated_replicates(
        sign_flip_replicates,
        "sign_flip_replicates",
    )
    rng = np.random.default_rng(int(bootstrap_seed))
    indices = rng.integers(
        0,
        species_means.size,
        size=(n_bootstrap, species_means.size),
    )
    bootstrap_means = np.mean(species_means[indices], axis=1)
    lower, upper = np.quantile(
        bootstrap_means,
        SPECIES_BOOTSTRAP_QUANTILES,
        method="linear",
    )

    return SpeciesClusterInference(
        n_matched=int(mask.sum()),
        n_species=int(species_means.size),
        micro_mean_difference=float(np.mean(diff[mask])),
        macro_mean_species_difference=float(np.mean(species_means)),
        bootstrap_ci_lower=float(lower),
        bootstrap_ci_upper=float(upper),
        bootstrap_replicates=n_bootstrap,
        bootstrap_seed=int(bootstrap_seed),
        sign_flip_p_value=_sign_flip_p_value(
            species_means,
            replicates=n_sign_flip,
            seed=int(sign_flip_seed),
        ),
        sign_flip_replicates=n_sign_flip,
        sign_flip_seed=int(sign_flip_seed),
    )


def paired_species_cluster_inference(
    y: Sequence[float] | np.ndarray,
    species_ids: Iterable[str],
    reference_probability: Sequence[float] | np.ndarray,
    candidate_probability: Sequence[float] | np.ndarray,
    *,
    reference_valid: Sequence[bool] | np.ndarray | None = None,
    candidate_valid: Sequence[bool] | np.ndarray | None = None,
    epsilon: float = PROBABILITY_EPSILON,
    bootstrap_replicates: int = SPECIES_BOOTSTRAP_REPLICATES,
    bootstrap_seed: int = SPECIES_BOOTSTRAP_SEED,
    sign_flip_replicates: int = SPECIES_SIGN_FLIP_REPLICATES,
    sign_flip_seed: int = SPECIES_SIGN_FLIP_SEED,
) -> SpeciesClusterInference:
    """Run the frozen clustered inference on a paired probability contrast."""
    species = np.asarray([str(x).strip() for x in species_ids], dtype=object)
    yy, ref, cand, matched = _paired_inputs(
        y,
        reference_probability,
        candidate_probability,
        reference_valid,
        candidate_valid,
    )
    if species.shape != yy.shape:
        raise ValueError("species_ids must align with y and probabilities")
    difference = (
        bernoulli_log_loss(yy[matched], cand[matched], epsilon=epsilon)
        - bernoulli_log_loss(yy[matched], ref[matched], epsilon=epsilon)
    )
    return species_cluster_inference(
        species[matched],
        difference,
        bootstrap_replicates=bootstrap_replicates,
        bootstrap_seed=bootstrap_seed,
        sign_flip_replicates=sign_flip_replicates,
        sign_flip_seed=sign_flip_seed,
    )
