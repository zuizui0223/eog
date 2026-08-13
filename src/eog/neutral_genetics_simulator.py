"""Small neutral drift-migration simulator for prospective EOG-R validation.

This module is validation infrastructure, not a demographic inference engine. It
simulates biallelic locus frequencies under a declared migration-support matrix and
finite-population drift so reachability distances can be checked against known truth
before any empirical genetic dataset is inspected.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class NeutralGeneticSimulationResult:
    allele_frequencies: np.ndarray
    pairwise_fst: np.ndarray
    migration_fraction: np.ndarray
    effective_population_size: np.ndarray
    generations: int
    n_loci: int
    seed: int
    fingerprint: str


def _sha256(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def pairwise_heterozygosity_fst(allele_frequencies: np.ndarray) -> np.ndarray:
    """Return a simple true-frequency heterozygosity FST for every population pair.

    This is a simulation diagnostic computed from latent population allele
    frequencies; it is not a finite-sample estimator such as Weir-Cockerham FST.
    """

    p = np.asarray(allele_frequencies, dtype=float)
    if p.ndim != 2 or p.shape[0] < 2 or p.shape[1] < 2 or not np.isfinite(p).all():
        raise ValueError("allele_frequencies must be a finite population-by-locus matrix")
    if np.any((p < 0.0) | (p > 1.0)):
        raise ValueError("allele frequencies must lie in [0, 1]")
    n = p.shape[0]
    result = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            pi = p[i]
            pj = p[j]
            pbar = 0.5 * (pi + pj)
            ht = float(np.mean(2.0 * pbar * (1.0 - pbar)))
            hs = float(np.mean(pi * (1.0 - pi) + pj * (1.0 - pj)))
            fst = 0.0 if ht <= 0.0 else 1.0 - hs / ht
            result[i, j] = result[j, i] = float(np.clip(fst, 0.0, 1.0))
    return result


def simulate_neutral_drift_migration(
    migration_support: np.ndarray,
    *,
    migration_scale: float,
    effective_population_size: int | Sequence[int],
    generations: int,
    n_loci: int,
    seed: int,
    ancestral_beta: tuple[float, float] = (0.8, 0.8),
) -> NeutralGeneticSimulationResult:
    """Simulate neutral allele-frequency divergence under declared migration truth.

    ``migration_support[i, j]`` is an uncalibrated directed support from donor ``i``
    to recipient ``j``. Multiplication by ``migration_scale`` yields the per-generation
    migrant fraction used by the simulator. Column sums must remain below one so the
    recipient retains a non-negative local fraction.
    """

    support = np.asarray(migration_support, dtype=float)
    if support.ndim != 2 or support.shape[0] != support.shape[1] or support.shape[0] < 2:
        raise ValueError("migration_support must be a square matrix with at least two populations")
    if not np.isfinite(support).all() or np.any(support < 0.0):
        raise ValueError("migration_support must be finite and non-negative")
    if not np.allclose(np.diag(support), 0.0, rtol=0.0, atol=1e-15):
        raise ValueError("migration_support diagonal must be zero")
    if not np.isfinite(migration_scale) or migration_scale < 0.0:
        raise ValueError("migration_scale must be finite and non-negative")
    if isinstance(generations, bool) or not isinstance(generations, (int, np.integer)) or generations < 1:
        raise ValueError("generations must be a positive integer")
    if isinstance(n_loci, bool) or not isinstance(n_loci, (int, np.integer)) or n_loci < 2:
        raise ValueError("n_loci must be an integer >= 2")
    if not isinstance(seed, (int, np.integer)):
        raise ValueError("seed must be an integer")
    alpha, beta = (float(ancestral_beta[0]), float(ancestral_beta[1]))
    if not np.isfinite([alpha, beta]).all() or alpha <= 0.0 or beta <= 0.0:
        raise ValueError("ancestral_beta parameters must be finite and positive")

    n = support.shape[0]
    if np.isscalar(effective_population_size):
        ne = np.full(n, int(effective_population_size), dtype=int)
    else:
        ne = np.asarray(effective_population_size, dtype=int)
        if ne.shape != (n,):
            raise ValueError("effective_population_size must be scalar or one value per population")
    if np.any(ne < 2):
        raise ValueError("effective population sizes must be integers >= 2")

    migration = float(migration_scale) * support
    incoming = np.sum(migration, axis=0)
    if np.any(incoming >= 1.0):
        raise ValueError("migration fractions into each recipient must sum to < 1")

    rng = np.random.default_rng(int(seed))
    ancestral = rng.beta(alpha, beta, int(n_loci))
    frequencies = np.tile(ancestral, (n, 1))
    chromosome_counts = 2 * ne

    for _ in range(int(generations)):
        migrant_contribution = migration.T @ frequencies
        mixed = (1.0 - incoming)[:, None] * frequencies + migrant_contribution
        mixed = np.clip(mixed, 0.0, 1.0)
        draws = np.empty_like(frequencies)
        for population in range(n):
            draws[population] = rng.binomial(
                int(chromosome_counts[population]),
                mixed[population],
            ) / float(chromosome_counts[population])
        frequencies = draws

    fst = pairwise_heterozygosity_fst(frequencies)
    payload = {
        "migration_support": support.tolist(),
        "migration_scale": float(migration_scale),
        "effective_population_size": ne.tolist(),
        "generations": int(generations),
        "n_loci": int(n_loci),
        "seed": int(seed),
        "ancestral_beta": [alpha, beta],
        "pairwise_fst": fst.tolist(),
    }
    return NeutralGeneticSimulationResult(
        allele_frequencies=frequencies,
        pairwise_fst=fst,
        migration_fraction=migration,
        effective_population_size=ne,
        generations=int(generations),
        n_loci=int(n_loci),
        seed=int(seed),
        fingerprint=_sha256(payload),
    )
