"""Paired learner-seed evaluation contract for prospective Layer-B tests.

The same declared seed must be used for the baseline and augmented arms. Multiple seeds
are required by default so the primary comparison is not a single realization of learner
randomness while a placebo is summarized over repeated seeds.

This module is score-agnostic: callers provide one baseline and one augmented scoring
callback. It does not fit models or touch endpoint data by itself.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Callable, Sequence

import numpy as np


ScoreFunction = Callable[[int], float]


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class PairedSeedResult:
    seeds: tuple[int, ...]
    baseline_scores: tuple[float, ...]
    augmented_scores: tuple[float, ...]
    paired_deltas: tuple[float, ...]
    mean_baseline: float
    mean_augmented: float
    mean_delta: float
    median_delta: float
    augmented_win_fraction: float
    fingerprint: str


def evaluate_paired_seed_scores(
    *,
    seeds: Sequence[int],
    baseline_score: ScoreFunction,
    augmented_score: ScoreFunction,
    require_multiple: bool = True,
) -> PairedSeedResult:
    """Evaluate baseline and augmented arms under the identical seed sequence."""

    seed_tuple = tuple(int(seed) for seed in seeds)
    if not seed_tuple:
        raise ValueError("at least one learner seed is required")
    if len(set(seed_tuple)) != len(seed_tuple):
        raise ValueError("learner seeds must be unique")
    if require_multiple and len(seed_tuple) < 2:
        raise ValueError("prospective primary evaluation requires multiple learner seeds")

    baseline: list[float] = []
    augmented: list[float] = []
    for seed in seed_tuple:
        base = float(baseline_score(seed))
        aug = float(augmented_score(seed))
        if not np.isfinite(base) or not np.isfinite(aug):
            raise ValueError("all paired scores must be finite")
        baseline.append(base)
        augmented.append(aug)

    baseline_arr = np.asarray(baseline, dtype=float)
    augmented_arr = np.asarray(augmented, dtype=float)
    deltas = augmented_arr - baseline_arr

    payload = {
        "seeds": list(seed_tuple),
        "baseline_scores": baseline_arr.tolist(),
        "augmented_scores": augmented_arr.tolist(),
        "paired_deltas": deltas.tolist(),
    }
    return PairedSeedResult(
        seeds=seed_tuple,
        baseline_scores=tuple(float(value) for value in baseline_arr),
        augmented_scores=tuple(float(value) for value in augmented_arr),
        paired_deltas=tuple(float(value) for value in deltas),
        mean_baseline=float(np.mean(baseline_arr)),
        mean_augmented=float(np.mean(augmented_arr)),
        mean_delta=float(np.mean(deltas)),
        median_delta=float(np.median(deltas)),
        augmented_win_fraction=float(np.mean(deltas < 0.0)),
        fingerprint=_canonical_sha256(payload),
    )
