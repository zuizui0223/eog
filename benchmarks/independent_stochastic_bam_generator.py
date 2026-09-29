"""Independent stochastic BAM metapopulation generator.

IMPORTANT: this generator intentionally imports no EOG modules.  It is used to create
synthetic partner, antagonist and focal occurrence histories before any EOG finite-world
evaluation is performed.

The generator shares only the preregistered ecological parameter semantics with the
downstream evaluator.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math

import numpy as np


@dataclass(frozen=True)
class IndependentLandscape:
    width: int
    height: int
    node_ids: tuple[str, ...]
    coordinates: np.ndarray
    environment: np.ndarray
    barrier_col: int
    barrier_gap_row: int


@dataclass(frozen=True)
class SpeciesSpec:
    source_id: str
    niche_center: tuple[float, float]
    niche_radius: tuple[float, float]
    step_radius: float
    barrier_permeable: bool
    colonization_beta: float
    persistence_probability: float


@dataclass(frozen=True)
class FocalSpec:
    scenario_id: str
    source_id: str
    abiotic_label: str
    niche_center: tuple[float, float]
    niche_radius: tuple[float, float]
    biotic_mode: str
    movement_label: str
    step_radius: float
    barrier_permeable: bool
    colonization_beta: float
    persistence_probability: float


@dataclass(frozen=True)
class AssociateRealization:
    partner_mask: np.ndarray
    antagonist_mask: np.ndarray
    partner_history: np.ndarray
    antagonist_history: np.ndarray


@dataclass(frozen=True)
class FocalRealization:
    scenario_id: str
    occupancy_history: np.ndarray
    accumulated_occurrence_ids_by_horizon: tuple[tuple[int, tuple[str, ...]], ...]
    final_snapshot_ids: tuple[str, ...]
    structural_reachable_ids: tuple[str, ...]


def seed_from(*parts: object) -> int:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def make_landscape() -> IndependentLandscape:
    width = 12
    height = 8
    node_ids = []
    coords = []
    env = []
    for row in range(height):
        for col in range(width):
            node_ids.append(f"r{row}c{col}")
            coords.append((float(col), float(row)))
            temp = col / (width - 1)
            if col == 5:
                temp += 0.35
            moisture = row / (height - 1)
            env.append((float(temp), float(moisture)))
    return IndependentLandscape(
        width=width,
        height=height,
        node_ids=tuple(node_ids),
        coordinates=np.asarray(coords, dtype=float),
        environment=np.asarray(env, dtype=float),
        barrier_col=7,
        barrier_gap_row=4,
    )


def abiotic_mask(
    landscape: IndependentLandscape,
    center: tuple[float, float],
    radius: tuple[float, float],
) -> np.ndarray:
    c = np.asarray(center, dtype=float)
    r = np.asarray(radius, dtype=float)
    scaled = (landscape.environment - c) / r
    return np.sum(scaled * scaled, axis=1) <= 1.0 + 1e-12


def _crosses_barrier(
    landscape: IndependentLandscape,
    i: int,
    j: int,
) -> bool:
    x1, y1 = landscape.coordinates[i]
    x2, y2 = landscape.coordinates[j]
    if not (min(x1, x2) < landscape.barrier_col <= max(x1, x2)):
        return False
    if int(round(y1)) == int(round(y2)) == landscape.barrier_gap_row:
        return False
    return True


def movement_adjacency(
    landscape: IndependentLandscape,
    *,
    step_radius: float,
    barrier_permeable: bool,
) -> tuple[tuple[int, ...], ...]:
    n = len(landscape.node_ids)
    rows: list[list[int]] = [[] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            distance = float(
                np.linalg.norm(landscape.coordinates[i] - landscape.coordinates[j])
            )
            if distance > step_radius + 1e-12:
                continue
            if not barrier_permeable and _crosses_barrier(landscape, i, j):
                continue
            rows[i].append(j)
    return tuple(tuple(values) for values in rows)


def structural_reachable_mask(
    landscape: IndependentLandscape,
    *,
    source_id: str,
    eligible_mask: np.ndarray,
    step_radius: float,
    barrier_permeable: bool,
) -> np.ndarray:
    index = {node_id: i for i, node_id in enumerate(landscape.node_ids)}
    source = index[source_id]
    if not bool(eligible_mask[source]):
        raise ValueError("source is outside structural eligibility")
    adjacency = movement_adjacency(
        landscape,
        step_radius=step_radius,
        barrier_permeable=barrier_permeable,
    )
    reached = np.zeros(len(landscape.node_ids), dtype=bool)
    reached[source] = True
    queue = [source]
    cursor = 0
    while cursor < len(queue):
        current = queue[cursor]
        cursor += 1
        for target in adjacency[current]:
            if reached[target] or not bool(eligible_mask[target]):
                continue
            reached[target] = True
            queue.append(target)
    return reached


def simulate_species(
    landscape: IndependentLandscape,
    spec: SpeciesSpec,
    *,
    steps: int,
    seed: int,
    extra_eligible_mask: np.ndarray | None = None,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    A = abiotic_mask(landscape, spec.niche_center, spec.niche_radius)
    eligible = A if extra_eligible_mask is None else A & extra_eligible_mask
    index = {node_id: i for i, node_id in enumerate(landscape.node_ids)}
    source = index[spec.source_id]
    if not bool(eligible[source]):
        raise ValueError("species source is not eligible")

    adjacency = movement_adjacency(
        landscape,
        step_radius=spec.step_radius,
        barrier_permeable=spec.barrier_permeable,
    )
    history = np.zeros((steps + 1, len(landscape.node_ids)), dtype=bool)
    history[0, source] = True

    for step in range(1, steps + 1):
        previous = history[step - 1]
        current = np.zeros(len(landscape.node_ids), dtype=bool)
        current[source] = True
        for node in range(len(landscape.node_ids)):
            if node == source or not bool(eligible[node]):
                continue
            if previous[node]:
                current[node] = rng.random() < spec.persistence_probability
                continue
            sources = sum(1 for neighbour in adjacency[node] if previous[neighbour])
            if sources <= 0:
                continue
            probability = 1.0 - (1.0 - spec.colonization_beta) ** sources
            current[node] = rng.random() < probability
        history[step] = current
    return history


def simulate_associates(landscape: IndependentLandscape) -> AssociateRealization:
    partner = SpeciesSpec(
        source_id="r4c0",
        niche_center=(0.42, 0.52),
        niche_radius=(0.48, 0.72),
        step_radius=1.01,
        barrier_permeable=True,
        colonization_beta=0.58,
        persistence_probability=0.94,
    )
    antagonist = SpeciesSpec(
        source_id="r4c11",
        niche_center=(0.78, 0.50),
        niche_radius=(0.34, 0.72),
        step_radius=1.01,
        barrier_permeable=True,
        colonization_beta=0.55,
        persistence_probability=0.94,
    )
    partner_history = simulate_species(
        landscape,
        partner,
        steps=30,
        seed=seed_from("associate", "partner"),
    )
    antagonist_history = simulate_species(
        landscape,
        antagonist,
        steps=30,
        seed=seed_from("associate", "antagonist"),
    )
    return AssociateRealization(
        partner_mask=partner_history[-1].copy(),
        antagonist_mask=antagonist_history[-1].copy(),
        partner_history=partner_history,
        antagonist_history=antagonist_history,
    )


def biotic_mask(
    mode: str,
    *,
    partner_mask: np.ndarray,
    antagonist_mask: np.ndarray,
) -> np.ndarray:
    if mode == "none":
        return np.ones(partner_mask.shape[0], dtype=bool)
    if mode == "obligate_partner":
        return partner_mask.copy()
    if mode == "antagonist_exclusion":
        return ~antagonist_mask
    if mode == "partner_and_antagonist":
        return partner_mask & ~antagonist_mask
    raise ValueError(f"unknown biotic mode: {mode}")


def candidate_parameter_grid() -> tuple[FocalSpec, ...]:
    a_specs = (
        ("A_narrow", (0.42, 0.52), (0.44, 0.74)),
        ("A_broad", (0.50, 0.52), (0.82, 0.90)),
    )
    b_modes = (
        "none",
        "obligate_partner",
        "antagonist_exclusion",
        "partner_and_antagonist",
    )
    m_specs = (
        ("short_closed", 1.01, False),
        ("short_open", 1.01, True),
        ("long_closed", 2.01, False),
        ("long_open", 2.01, True),
    )
    rows = []
    for a_label, center, radius in a_specs:
        for b_mode in b_modes:
            for m_label, step_radius, permeability in m_specs:
                rows.append(
                    FocalSpec(
                        scenario_id=f"{a_label}|B_{b_mode}|M_{m_label}",
                        source_id="r4c0",
                        abiotic_label=a_label,
                        niche_center=center,
                        niche_radius=radius,
                        biotic_mode=b_mode,
                        movement_label=m_label,
                        step_radius=step_radius,
                        barrier_permeable=permeability,
                        colonization_beta=0.48,
                        persistence_probability=0.86,
                    )
                )
    return tuple(rows)


def truth_scenarios() -> dict[str, str]:
    return {
        "A_limited": "A_narrow|B_none|M_long_open",
        "partner_limited": "A_broad|B_obligate_partner|M_long_open",
        "antagonist_limited": "A_broad|B_antagonist_exclusion|M_long_open",
        "distance_limited": "A_broad|B_none|M_short_open",
        "barrier_limited": "A_broad|B_none|M_long_closed",
        "joint_ABM": "A_narrow|B_partner_and_antagonist|M_short_closed",
    }


def simulate_focal(
    landscape: IndependentLandscape,
    associates: AssociateRealization,
    spec: FocalSpec,
    *,
    replicate: int,
    steps: int = 40,
    horizons: tuple[int, ...] = (5, 10, 20, 40),
) -> FocalRealization:
    A = abiotic_mask(landscape, spec.niche_center, spec.niche_radius)
    B = biotic_mask(
        spec.biotic_mode,
        partner_mask=associates.partner_mask,
        antagonist_mask=associates.antagonist_mask,
    )
    eligible = A & B

    species_spec = SpeciesSpec(
        source_id=spec.source_id,
        niche_center=spec.niche_center,
        niche_radius=spec.niche_radius,
        step_radius=spec.step_radius,
        barrier_permeable=spec.barrier_permeable,
        colonization_beta=spec.colonization_beta,
        persistence_probability=spec.persistence_probability,
    )
    history = simulate_species(
        landscape,
        species_spec,
        steps=steps,
        seed=seed_from("focal", spec.scenario_id, replicate),
        extra_eligible_mask=B,
    )
    reachable = structural_reachable_mask(
        landscape,
        source_id=spec.source_id,
        eligible_mask=eligible,
        step_radius=spec.step_radius,
        barrier_permeable=spec.barrier_permeable,
    )

    accumulated_rows = []
    for horizon in horizons:
        ever = np.any(history[: horizon + 1], axis=0)
        ids = tuple(
            node_id
            for node_id, present in zip(landscape.node_ids, ever, strict=True)
            if bool(present)
        )
        accumulated_rows.append((horizon, ids))

    final_ids = tuple(
        node_id
        for node_id, present in zip(
            landscape.node_ids,
            history[steps],
            strict=True,
        )
        if bool(present)
    )
    reachable_ids = tuple(
        node_id
        for node_id, present in zip(
            landscape.node_ids,
            reachable,
            strict=True,
        )
        if bool(present)
    )

    return FocalRealization(
        scenario_id=spec.scenario_id,
        occupancy_history=history,
        accumulated_occurrence_ids_by_horizon=tuple(accumulated_rows),
        final_snapshot_ids=final_ids,
        structural_reachable_ids=reachable_ids,
    )
