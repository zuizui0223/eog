"""Species turnover and emergent community connectivity.

This module supports a prospective NEON metacommunity test. It separates:
- community-level one-step world survival;
- the best single-species survival;
- strict worlds that survive only after species are pooled;
- target nodes supported only by different-species neighbours;
- a spatial null that permutes complete local assemblage rows among the already-positive
  guild nodes while preserving species frequencies, local richness values, and within-node
  species co-occurrence vectors.

No biological response is accessed by this module.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Mapping, Sequence

import numpy as np


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _adjacency(values: np.ndarray, n: int, world_id: str) -> np.ndarray:
    matrix = np.asarray(values, dtype=bool)
    if matrix.shape != (n, n):
        raise ValueError(f"world {world_id!r} adjacency must have shape {(n, n)}")
    if not np.array_equal(matrix, matrix.T):
        raise ValueError("metacommunity connectivity v1 requires undirected worlds")
    matrix = matrix.copy()
    np.fill_diagonal(matrix, False)
    return matrix


def _incidence(values: np.ndarray) -> np.ndarray:
    matrix = np.asarray(values, dtype=bool)
    if matrix.ndim != 2 or matrix.shape[0] < 2 or matrix.shape[1] < 1:
        raise ValueError("incidence must be node x species with at least two nodes")
    return matrix


def one_step_survives(adjacency: np.ndarray, positive_mask: np.ndarray) -> bool:
    graph = np.asarray(adjacency, dtype=bool)
    mask = np.asarray(positive_mask, dtype=bool)
    if graph.ndim != 2 or graph.shape[0] != graph.shape[1]:
        raise ValueError("adjacency must be square")
    if mask.shape != (graph.shape[0],):
        raise ValueError("positive_mask length must equal node count")
    indices = np.flatnonzero(mask)
    if indices.size < 2:
        return False
    induced = graph[np.ix_(indices, indices)]
    return bool(np.all(np.sum(induced, axis=1) >= 1))


def _neighbor_lists(adjacency: np.ndarray) -> tuple[np.ndarray, ...]:
    graph = np.asarray(adjacency, dtype=bool)
    return tuple(np.flatnonzero(graph[index, :]) for index in range(graph.shape[0]))


def _one_step_survives_neighbors(
    neighbours: tuple[np.ndarray, ...],
    positive_mask: np.ndarray,
) -> bool:
    mask = np.asarray(positive_mask, dtype=bool)
    indices = np.flatnonzero(mask)
    if indices.size < 2:
        return False
    for index in indices:
        peer_indices = neighbours[int(index)]
        if peer_indices.size == 0 or not bool(np.any(mask[peer_indices])):
            return False
    return True


@dataclass(frozen=True)
class MetacommunityConnectivityResult:
    world_ids: tuple[str, ...]
    species_ids: tuple[str, ...]
    guild_positive_node_count: int
    species_with_two_positive_nodes: tuple[str, ...]
    community_world_survival: tuple[bool, ...]
    community_survival_fraction: float
    species_survival_fractions: tuple[tuple[str, float], ...]
    max_species_survival_fraction: float
    best_species_ids: tuple[str, ...]
    emergent_connectivity_gain: float
    strict_emergent_world_fraction: float
    cross_species_rescue_fraction: float
    dominance_coverage: float
    fingerprint: str


def calculate_metacommunity_connectivity(
    world_adjacencies: Mapping[str, np.ndarray],
    incidence: np.ndarray,
    *,
    species_ids: Sequence[str],
) -> MetacommunityConnectivityResult:
    """Calculate community versus species continuity under canonical one-step worlds."""

    matrix = _incidence(incidence)
    n_nodes, n_species = matrix.shape
    species = tuple(str(value).strip() for value in species_ids)
    if len(species) != n_species or any(not value for value in species):
        raise ValueError("species_ids must match incidence columns and be non-empty")
    if len(set(species)) != len(species):
        raise ValueError("species_ids must be unique")
    if not world_adjacencies:
        raise ValueError("at least one canonical world is required")

    worlds = tuple(sorted(str(value).strip() for value in world_adjacencies))
    if any(not value for value in worlds) or len(set(worlds)) != len(worlds):
        raise ValueError("world IDs must be unique non-empty strings")
    graphs = {
        world_id: _adjacency(world_adjacencies[world_id], n_nodes, world_id)
        for world_id in worlds
    }

    guild_mask = np.any(matrix, axis=1)
    guild_count = int(np.sum(guild_mask))
    if guild_count < 2:
        raise ValueError("guild must occupy at least two nodes")

    species_counts = np.sum(matrix, axis=0).astype(int)
    eligible_indices = np.flatnonzero(species_counts >= 2)
    if eligible_indices.size == 0:
        raise ValueError("at least one species must occupy at least two nodes")
    eligible_species = tuple(species[index] for index in eligible_indices)

    community_survival = tuple(
        one_step_survives(graphs[world_id], guild_mask)
        for world_id in worlds
    )
    community_fraction = float(np.mean(community_survival))

    per_species_world: dict[str, tuple[bool, ...]] = {}
    species_fractions: list[tuple[str, float]] = []
    for index in eligible_indices:
        sid = species[int(index)]
        mask = matrix[:, int(index)]
        survival = tuple(
            one_step_survives(graphs[world_id], mask)
            for world_id in worlds
        )
        per_species_world[sid] = survival
        species_fractions.append((sid, float(np.mean(survival))))

    max_species_fraction = max(value for _, value in species_fractions)
    best_species = tuple(
        sid for sid, value in species_fractions
        if math.isclose(value, max_species_fraction, rel_tol=0.0, abs_tol=1e-15)
    )
    emergent_gain = community_fraction - max_species_fraction

    strict_count = 0
    for world_index, guild_survives in enumerate(community_survival):
        if not guild_survives:
            continue
        if not any(
            survival[world_index]
            for survival in per_species_world.values()
        ):
            strict_count += 1
    strict_fraction = strict_count / len(worlds)

    rescue_numerator = 0
    rescue_denominator = 0
    guild_indices = np.flatnonzero(guild_mask)
    for world_id, guild_survives in zip(worlds, community_survival, strict=True):
        if not guild_survives:
            continue
        graph = graphs[world_id]
        for target in guild_indices:
            neighbours = guild_indices[
                graph[int(target), guild_indices]
            ]
            if neighbours.size == 0:
                raise AssertionError("surviving guild world has unsupported target")
            rescue_denominator += 1
            target_species = matrix[int(target), :]
            shares_species = np.any(
                matrix[neighbours, :] & target_species[None, :],
                axis=1,
            )
            if not bool(np.any(shares_species)):
                rescue_numerator += 1
    rescue_fraction = (
        rescue_numerator / rescue_denominator
        if rescue_denominator
        else 0.0
    )

    dominance = float(np.max(species_counts) / guild_count)

    payload = {
        "world_ids": list(worlds),
        "species_ids": list(species),
        "guild_positive_node_count": guild_count,
        "species_with_two_positive_nodes": list(eligible_species),
        "community_world_survival": list(community_survival),
        "community_survival_fraction": community_fraction,
        "species_survival_fractions": [
            [sid, value] for sid, value in species_fractions
        ],
        "max_species_survival_fraction": max_species_fraction,
        "best_species_ids": list(best_species),
        "emergent_connectivity_gain": emergent_gain,
        "strict_emergent_world_fraction": strict_fraction,
        "cross_species_rescue_fraction": rescue_fraction,
        "dominance_coverage": dominance,
    }
    return MetacommunityConnectivityResult(
        world_ids=worlds,
        species_ids=species,
        guild_positive_node_count=guild_count,
        species_with_two_positive_nodes=eligible_species,
        community_world_survival=community_survival,
        community_survival_fraction=community_fraction,
        species_survival_fractions=tuple(species_fractions),
        max_species_survival_fraction=float(max_species_fraction),
        best_species_ids=best_species,
        emergent_connectivity_gain=float(emergent_gain),
        strict_emergent_world_fraction=float(strict_fraction),
        cross_species_rescue_fraction=float(rescue_fraction),
        dominance_coverage=dominance,
        fingerprint=_canonical_sha256(payload),
    )


@dataclass(frozen=True)
class AssemblagePermutationResult:
    seed: int
    replicates: int
    observed_gain: float
    null_gains: tuple[float, ...]
    null_median_gain: float
    null_adjusted_gain: float
    upper_tail_p: float
    row_sum_preserved: bool
    column_sum_preserved: bool
    guild_positive_set_preserved: bool
    fingerprint: str


def deterministic_site_seed(programme: str, site_code: str) -> int:
    key = f"{programme}|{site_code}".encode("utf-8")
    return int(hashlib.sha256(key).hexdigest()[:8], 16)


def assemblage_row_permutation_null(
    world_adjacencies: Mapping[str, np.ndarray],
    incidence: np.ndarray,
    *,
    species_ids: Sequence[str],
    replicates: int = 999,
    seed: int,
) -> AssemblagePermutationResult:
    """Permute complete local assemblages among fixed guild-positive nodes."""

    matrix = _incidence(incidence)
    reps = int(replicates)
    if reps <= 0:
        raise ValueError("replicates must be positive")
    observed = calculate_metacommunity_connectivity(
        world_adjacencies,
        matrix,
        species_ids=species_ids,
    )
    world_ids = tuple(sorted(str(value).strip() for value in world_adjacencies))
    graphs = {
        world_id: _adjacency(
            world_adjacencies[world_id],
            matrix.shape[0],
            world_id,
        )
        for world_id in world_ids
    }
    neighbour_lists = {
        world_id: _neighbor_lists(graphs[world_id])
        for world_id in world_ids
    }

    guild_mask = np.any(matrix, axis=1)
    positive_indices = np.flatnonzero(guild_mask)
    positive_rows = matrix[positive_indices, :].copy()
    original_row_sums = np.sort(np.sum(positive_rows, axis=1))
    original_column_sums = np.sum(matrix, axis=0)
    rng = np.random.default_rng(int(seed))

    null_gains: list[float] = []
    row_ok = True
    column_ok = True
    guild_ok = True
    for _ in range(reps):
        permutation = rng.permutation(positive_rows.shape[0])
        permuted = np.zeros_like(matrix, dtype=bool)
        permuted[positive_indices, :] = positive_rows[permutation, :]

        row_ok = row_ok and np.array_equal(
            np.sort(np.sum(permuted[positive_indices, :], axis=1)),
            original_row_sums,
        )
        column_ok = column_ok and np.array_equal(
            np.sum(permuted, axis=0),
            original_column_sums,
        )
        guild_ok = guild_ok and np.array_equal(
            np.any(permuted, axis=1),
            guild_mask,
        )
        species_counts = np.sum(permuted, axis=0).astype(int)
        eligible = np.flatnonzero(species_counts >= 2)
        max_species_fraction = 0.0
        for species_index in eligible:
            species_mask = permuted[:, int(species_index)]
            survival_count = 0
            for world_id in world_ids:
                if _one_step_survives_neighbors(
                    neighbour_lists[world_id],
                    species_mask,
                ):
                    survival_count += 1
            fraction = survival_count / len(world_ids)
            if fraction > max_species_fraction:
                max_species_fraction = fraction
        null_gains.append(
            observed.community_survival_fraction - max_species_fraction
        )

    null_array = np.asarray(null_gains, dtype=float)
    median = float(np.median(null_array))
    adjusted = observed.emergent_connectivity_gain - median
    p = float(
        (1 + int(np.sum(null_array >= observed.emergent_connectivity_gain)))
        / (reps + 1)
    )
    payload = {
        "seed": int(seed),
        "replicates": reps,
        "observed_gain": observed.emergent_connectivity_gain,
        "null_gains": null_array.tolist(),
        "null_median_gain": median,
        "null_adjusted_gain": adjusted,
        "upper_tail_p": p,
        "row_sum_preserved": row_ok,
        "column_sum_preserved": column_ok,
        "guild_positive_set_preserved": guild_ok,
    }
    return AssemblagePermutationResult(
        seed=int(seed),
        replicates=reps,
        observed_gain=float(observed.emergent_connectivity_gain),
        null_gains=tuple(float(value) for value in null_array),
        null_median_gain=median,
        null_adjusted_gain=float(adjusted),
        upper_tail_p=p,
        row_sum_preserved=bool(row_ok),
        column_sum_preserved=bool(column_ok),
        guild_positive_set_preserved=bool(guild_ok),
        fingerprint=_canonical_sha256(payload),
    )


@dataclass(frozen=True)
class AggregateEmergenceTest:
    site_count: int
    positive_null_adjusted_site_count: int
    median_observed_gain: float
    median_null_adjusted_gain: float
    one_sided_sign_test_p: float
    confirmatory_estimable: bool
    primary_supported: bool
    fingerprint: str


def aggregate_emergence_test(
    observed_gains: Sequence[float],
    null_adjusted_gains: Sequence[float],
    *,
    minimum_sites: int = 8,
    alpha: float = 0.05,
) -> AggregateEmergenceTest:
    """One-sided exact sign test; zero/tied adjusted effects count as non-positive."""

    observed = np.asarray(tuple(float(v) for v in observed_gains), dtype=float)
    adjusted = np.asarray(tuple(float(v) for v in null_adjusted_gains), dtype=float)
    if observed.size == 0 or observed.shape != adjusted.shape:
        raise ValueError("observed and null-adjusted gains must have equal non-zero length")
    if not np.isfinite(observed).all() or not np.isfinite(adjusted).all():
        raise ValueError("gains must be finite")
    n = int(observed.size)
    positives = int(np.sum(adjusted > 0.0))
    p = float(
        sum(
            math.comb(n, k) * (0.5 ** n)
            for k in range(positives, n + 1)
        )
    )
    median_observed = float(np.median(observed))
    median_adjusted = float(np.median(adjusted))
    estimable = n >= int(minimum_sites)
    supported = bool(
        estimable
        and median_observed > 0.0
        and p < float(alpha)
    )
    payload = {
        "site_count": n,
        "positive_null_adjusted_site_count": positives,
        "median_observed_gain": median_observed,
        "median_null_adjusted_gain": median_adjusted,
        "one_sided_sign_test_p": p,
        "minimum_sites": int(minimum_sites),
        "alpha": float(alpha),
        "confirmatory_estimable": estimable,
        "primary_supported": supported,
    }
    return AggregateEmergenceTest(
        site_count=n,
        positive_null_adjusted_site_count=positives,
        median_observed_gain=median_observed,
        median_null_adjusted_gain=median_adjusted,
        one_sided_sign_test_p=p,
        confirmatory_estimable=estimable,
        primary_supported=supported,
        fingerprint=_canonical_sha256(payload),
    )
