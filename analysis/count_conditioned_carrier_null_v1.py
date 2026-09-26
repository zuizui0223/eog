from __future__ import annotations

import hashlib
import itertools
import math
import random
from collections.abc import Iterable, Sequence


def world_survives(positive_nodes: set[int], edges: set[tuple[int, int]]) -> bool:
    if len(positive_nodes) < 2:
        return False
    degree = {x: 0 for x in positive_nodes}
    for a, b in edges:
        if a in positive_nodes and b in positive_nodes:
            degree[a] += 1
            degree[b] += 1
    return all(degree[x] > 0 for x in positive_nodes)


def is_carrier(positive_nodes: set[int], worlds: Sequence[set[tuple[int, int]]]) -> bool:
    return bool(worlds) and all(world_survives(positive_nodes, edges) for edges in worlds)


def deterministic_seed(site_code: str, species_name: str) -> int:
    token = f"carrier_prevalence_mechanism_v1|{site_code}|{species_name}".encode()
    return int(hashlib.sha256(token).hexdigest()[:16], 16)


def count_conditioned_carrier_probability(
    candidate_nodes: Sequence[int],
    positive_count: int,
    worlds: Sequence[set[tuple[int, int]]],
    *,
    replicates: int = 999,
    seed: int,
) -> float:
    nodes = tuple(candidate_nodes)
    n = len(nodes)
    k = positive_count
    if k < 2 or k > n:
        return 0.0

    total = math.comb(n, k)
    if total <= replicates:
        trials: Iterable[tuple[int, ...]] = itertools.combinations(nodes, k)
        hits = sum(is_carrier(set(x), worlds) for x in trials)
        return hits / total

    rng = random.Random(seed)
    hits = 0
    for _ in range(replicates):
        draw = set(rng.sample(nodes, k))
        hits += is_carrier(draw, worlds)
    return hits / replicates


def carrier_excess(
    observed_positive_nodes: set[int],
    candidate_nodes: Sequence[int],
    worlds: Sequence[set[tuple[int, int]]],
    *,
    replicates: int,
    seed: int,
) -> tuple[int, float, float]:
    observed = int(is_carrier(observed_positive_nodes, worlds))
    expected = count_conditioned_carrier_probability(
        candidate_nodes,
        len(observed_positive_nodes),
        worlds,
        replicates=replicates,
        seed=seed,
    )
    return observed, expected, observed - expected


def deterministic_grid_seed(site_code: str, species_name: str) -> int:
    token = f"carrier_prevalence_mechanism_v1|grid|{site_code}|{species_name}".encode()
    return int(hashlib.sha256(token).hexdigest()[:16], 16)


def grid_conditioned_carrier_probability(
    candidate_nodes: Sequence[int],
    grid_by_node: dict[int, str],
    observed_positive_nodes: set[int],
    worlds: Sequence[set[tuple[int, int]]],
    *,
    replicates: int = 999,
    seed: int,
) -> float:
    candidates = tuple(candidate_nodes)
    if len(observed_positive_nodes) < 2:
        return 0.0
    if any(node not in grid_by_node for node in candidates):
        raise ValueError("every candidate node must have a grid id")
    if any(node not in set(candidates) for node in observed_positive_nodes):
        raise ValueError("observed positive nodes must be a subset of candidate nodes")

    nodes_by_grid: dict[str, list[int]] = {}
    for node in candidates:
        nodes_by_grid.setdefault(grid_by_node[node], []).append(node)

    counts_by_grid: dict[str, int] = {}
    for node in observed_positive_nodes:
        grid = grid_by_node[node]
        counts_by_grid[grid] = counts_by_grid.get(grid, 0) + 1

    for grid, k in counts_by_grid.items():
        if k > len(nodes_by_grid.get(grid, [])):
            raise ValueError(f"observed grid count exceeds candidates for {grid}")

    total = 1
    for grid, k in counts_by_grid.items():
        total *= math.comb(len(nodes_by_grid[grid]), k)

    used_grids = tuple(sorted(counts_by_grid))
    if total <= replicates:
        combinations_by_grid = [
            tuple(itertools.combinations(nodes_by_grid[grid], counts_by_grid[grid]))
            for grid in used_grids
        ]
        hits = 0
        for parts in itertools.product(*combinations_by_grid):
            draw: set[int] = set()
            for part in parts:
                draw.update(part)
            hits += is_carrier(draw, worlds)
        return hits / total

    rng = random.Random(seed)
    hits = 0
    for _ in range(replicates):
        draw: set[int] = set()
        for grid in used_grids:
            draw.update(rng.sample(nodes_by_grid[grid], counts_by_grid[grid]))
        hits += is_carrier(draw, worlds)
    return hits / replicates


def grid_conditioned_decomposition(
    observed_positive_nodes: set[int],
    candidate_nodes: Sequence[int],
    grid_by_node: dict[int, str],
    worlds: Sequence[set[tuple[int, int]]],
    *,
    replicates: int,
    sitewide_seed: int,
    grid_seed: int,
) -> dict[str, float | int]:
    observed, expected_sitewide, sitewide_excess = carrier_excess(
        observed_positive_nodes,
        candidate_nodes,
        worlds,
        replicates=replicates,
        seed=sitewide_seed,
    )
    expected_grid = grid_conditioned_carrier_probability(
        candidate_nodes,
        grid_by_node,
        observed_positive_nodes,
        worlds,
        replicates=replicates,
        seed=grid_seed,
    )
    between_grid = expected_grid - expected_sitewide
    within_grid = observed - expected_grid
    reconstruction_error = sitewide_excess - (between_grid + within_grid)
    return {
        "observed_carrier": observed,
        "expected_sitewide": expected_sitewide,
        "expected_grid_conditioned": expected_grid,
        "sitewide_excess": sitewide_excess,
        "between_grid_allocation_component": between_grid,
        "within_grid_organization_component": within_grid,
        "reconstruction_error": reconstruction_error,
    }
