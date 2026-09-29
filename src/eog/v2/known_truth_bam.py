"""Known-truth BAM (Abiotic-Biotic-Movement) simulation for EOG.

The focal species' realised occupied state is generated as

    G0 = A ∩ B ∩ M

where A is abiotic suitability, B is explicit biotic permissibility derived from
independently generated partner/antagonist distributions, and M is source-conditioned
movement accessibility.  The three layers are stored separately and never collapsed
into a weighted score.

This module is synthetic methods validation.  It does not infer real biological
interactions or movement from occurrence data.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import hashlib
import json
import math
from typing import Iterable, Literal, Sequence

import numpy as np

from .known_truth_biogeography import VirtualLandscape, make_gradient_landscape


BMode = Literal[
    "none",
    "obligate_partner",
    "antagonist_exclusion",
    "partner_and_antagonist",
]


def _sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _ids_to_mask(node_ids: Sequence[str], ids: Iterable[str]) -> int:
    index = {node_id: i for i, node_id in enumerate(node_ids)}
    mask = 0
    for node_id in ids:
        if node_id not in index:
            raise ValueError(f"unknown node id: {node_id}")
        mask |= 1 << index[node_id]
    return mask


def _mask_to_ids(node_ids: Sequence[str], mask: int) -> tuple[str, ...]:
    return tuple(
        node_id
        for i, node_id in enumerate(node_ids)
        if mask & (1 << i)
    )


def _all_mask(n: int) -> int:
    return (1 << n) - 1


def _is_subset(left: int, right: int) -> bool:
    return left & ~right == 0


@dataclass(frozen=True)
class MovementState:
    accessible_mask: int
    first_arrival_steps: tuple[int | None, ...]
    fingerprint: str


@dataclass(frozen=True)
class AuxiliaryBioticState:
    partner_mask: int
    antagonist_mask: int
    fingerprint: str


@dataclass(frozen=True)
class BAMWorld:
    world_id: str
    node_ids: tuple[str, ...]
    abiotic_mask: int
    biotic_mask: int
    movement_mask: int
    occupied_mask: int
    first_arrival_steps: tuple[int | None, ...]
    abiotic_label: str
    biotic_mode: BMode
    movement_label: str
    fingerprint: str

    @property
    def abiotic_ids(self) -> tuple[str, ...]:
        return _mask_to_ids(self.node_ids, self.abiotic_mask)

    @property
    def biotic_ids(self) -> tuple[str, ...]:
        return _mask_to_ids(self.node_ids, self.biotic_mask)

    @property
    def movement_ids(self) -> tuple[str, ...]:
        return _mask_to_ids(self.node_ids, self.movement_mask)

    @property
    def occupied_ids(self) -> tuple[str, ...]:
        return _mask_to_ids(self.node_ids, self.occupied_mask)


@dataclass(frozen=True)
class BAMCompatibility:
    compatible_world_ids: tuple[str, ...]
    eliminated_world_ids: tuple[str, ...]
    evidence_level: str
    fingerprint: str


def make_bam_landscape() -> VirtualLandscape:
    """Canonical 7 x 3 landscape with an environmental bottleneck and hard barrier."""

    return make_gradient_landscape(
        width=7,
        height=3,
        spike_col=3,
        spike_amount=0.45,
        barrier_col=4,
        barrier_gap_rows=(1,),
    )


def abiotic_mask(
    landscape: VirtualLandscape,
    *,
    center: tuple[float, float],
    radius: tuple[float, float],
) -> int:
    env = np.asarray(landscape.environment, dtype=float)
    center_arr = np.asarray(center, dtype=float)
    radius_arr = np.asarray(radius, dtype=float)
    if np.any(radius_arr <= 0.0):
        raise ValueError("abiotic niche radii must be positive")
    scaled = (env - center_arr) / radius_arr
    keep = np.sum(scaled * scaled, axis=1) <= 1.0 + 1e-12
    mask = 0
    for i, value in enumerate(keep):
        if bool(value):
            mask |= 1 << i
    return mask


def _crosses_barrier(
    landscape: VirtualLandscape,
    i: int,
    j: int,
) -> bool:
    if landscape.barrier_col is None:
        return False
    x1, y1 = landscape.coordinates[i]
    x2, y2 = landscape.coordinates[j]
    if not (min(x1, x2) < landscape.barrier_col <= max(x1, x2)):
        return False
    # A same-row crossing through an explicit gap is permitted.
    if int(round(y1)) == int(round(y2)):
        row = int(round(y1))
        if row in set(landscape.barrier_gap_rows):
            return False
    return True


def movement_state(
    landscape: VirtualLandscape,
    *,
    source_id: str,
    step_radius: float,
    barrier_permeable: bool,
    horizon: int,
) -> MovementState:
    """Construct M independently of A and B using source-conditioned BFS."""

    if source_id not in landscape.node_ids:
        raise ValueError("source_id outside landscape")
    if step_radius <= 0.0 or not math.isfinite(step_radius):
        raise ValueError("step_radius must be finite and positive")
    if horizon < 0:
        raise ValueError("horizon must be non-negative")

    n = len(landscape.node_ids)
    coords = np.asarray(landscape.coordinates, dtype=float)
    neighbours: list[list[int]] = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            distance = float(np.linalg.norm(coords[i] - coords[j]))
            if distance > step_radius + 1e-12:
                continue
            if not barrier_permeable and _crosses_barrier(landscape, i, j):
                continue
            neighbours[i].append(j)
            neighbours[j].append(i)

    source = landscape.node_ids.index(source_id)
    arrival: list[int | None] = [None] * n
    arrival[source] = 0
    queue: deque[int] = deque([source])
    while queue:
        i = queue.popleft()
        step = arrival[i]
        assert step is not None
        if step >= horizon:
            continue
        for j in neighbours[i]:
            if arrival[j] is None:
                arrival[j] = step + 1
                queue.append(j)

    mask = 0
    for i, step in enumerate(arrival):
        if step is not None and step <= horizon:
            mask |= 1 << i
    payload = {
        "node_ids": landscape.node_ids,
        "source_id": source_id,
        "step_radius": step_radius,
        "barrier_permeable": barrier_permeable,
        "horizon": horizon,
        "accessible_mask": mask,
        "first_arrival_steps": arrival,
    }
    return MovementState(
        accessible_mask=mask,
        first_arrival_steps=tuple(arrival),
        fingerprint=_sha256(payload),
    )


def _auxiliary_species_mask(
    landscape: VirtualLandscape,
    *,
    source_id: str,
    niche_center: tuple[float, float],
    niche_radius: tuple[float, float],
    step_radius: float,
    barrier_permeable: bool,
    horizon: int,
) -> int:
    a = abiotic_mask(
        landscape,
        center=niche_center,
        radius=niche_radius,
    )
    m = movement_state(
        landscape,
        source_id=source_id,
        step_radius=step_radius,
        barrier_permeable=barrier_permeable,
        horizon=horizon,
    ).accessible_mask
    return a & m


def generate_biotic_state(landscape: VirtualLandscape) -> AuxiliaryBioticState:
    """Generate independent partner and antagonist distributions.

    The auxiliary species have their own A and M processes and do not depend on the
    focal species.  Their realised states are then used to construct the focal B set.
    """

    partner = _auxiliary_species_mask(
        landscape,
        source_id="r1c0",
        niche_center=(0.42, 0.55),
        niche_radius=(0.55, 0.35),
        step_radius=1.01,
        barrier_permeable=True,
        horizon=8,
    )
    antagonist = _auxiliary_species_mask(
        landscape,
        source_id="r1c6",
        niche_center=(0.68, 0.55),
        niche_radius=(0.48, 0.35),
        step_radius=1.01,
        barrier_permeable=True,
        horizon=8,
    )
    return AuxiliaryBioticState(
        partner_mask=partner,
        antagonist_mask=antagonist,
        fingerprint=_sha256(
            {
                "partner_mask": partner,
                "antagonist_mask": antagonist,
            }
        ),
    )


def biotic_mask(
    node_count: int,
    state: AuxiliaryBioticState,
    mode: BMode,
) -> int:
    all_nodes = _all_mask(node_count)
    if mode == "none":
        return all_nodes
    if mode == "obligate_partner":
        return state.partner_mask
    if mode == "antagonist_exclusion":
        return all_nodes & ~state.antagonist_mask
    if mode == "partner_and_antagonist":
        return state.partner_mask & ~state.antagonist_mask
    raise ValueError(f"unsupported B mode: {mode}")


def build_bam_world(
    landscape: VirtualLandscape,
    *,
    world_id: str,
    abiotic_label: str,
    niche_center: tuple[float, float],
    niche_radius: tuple[float, float],
    biotic_state: AuxiliaryBioticState,
    biotic_mode: BMode,
    movement_label: str,
    source_id: str,
    step_radius: float,
    barrier_permeable: bool,
    horizon: int,
) -> BAMWorld:
    a = abiotic_mask(
        landscape,
        center=niche_center,
        radius=niche_radius,
    )
    b = biotic_mask(len(landscape.node_ids), biotic_state, biotic_mode)
    m_state = movement_state(
        landscape,
        source_id=source_id,
        step_radius=step_radius,
        barrier_permeable=barrier_permeable,
        horizon=horizon,
    )
    g = a & b & m_state.accessible_mask
    payload = {
        "world_id": world_id,
        "abiotic_mask": a,
        "biotic_mask": b,
        "movement_mask": m_state.accessible_mask,
        "occupied_mask": g,
        "first_arrival_steps": m_state.first_arrival_steps,
        "abiotic_label": abiotic_label,
        "biotic_mode": biotic_mode,
        "movement_label": movement_label,
        "biotic_state_fingerprint": biotic_state.fingerprint,
        "movement_fingerprint": m_state.fingerprint,
    }
    return BAMWorld(
        world_id=world_id,
        node_ids=landscape.node_ids,
        abiotic_mask=a,
        biotic_mask=b,
        movement_mask=m_state.accessible_mask,
        occupied_mask=g,
        first_arrival_steps=m_state.first_arrival_steps,
        abiotic_label=abiotic_label,
        biotic_mode=biotic_mode,
        movement_label=movement_label,
        fingerprint=_sha256(payload),
    )


def _positive_mask(worlds: Sequence[BAMWorld], positive_ids: Sequence[str]) -> int:
    if not worlds:
        raise ValueError("worlds must be non-empty")
    return _ids_to_mask(worlds[0].node_ids, positive_ids)


def compatible_positive_only(
    worlds: Sequence[BAMWorld],
    positive_ids: Sequence[str],
) -> BAMCompatibility:
    positives = _positive_mask(worlds, positive_ids)
    compatible = tuple(
        world.world_id
        for world in worlds
        if _is_subset(positives, world.occupied_mask)
    )
    eliminated = tuple(
        world.world_id
        for world in worlds
        if world.world_id not in set(compatible)
    )
    return BAMCompatibility(
        compatible_world_ids=compatible,
        eliminated_world_ids=eliminated,
        evidence_level="positive_only",
        fingerprint=_sha256(
            {
                "positives": positives,
                "compatible": compatible,
                "evidence_level": "positive_only",
            }
        ),
    )


def compatible_with_perfect_negatives(
    worlds: Sequence[BAMWorld],
    positive_ids: Sequence[str],
    negative_ids: Sequence[str],
) -> BAMCompatibility:
    positives = _positive_mask(worlds, positive_ids)
    negatives = _ids_to_mask(worlds[0].node_ids, negative_ids)
    if positives & negatives:
        raise ValueError("positive and negative evidence overlap")
    compatible = tuple(
        world.world_id
        for world in worlds
        if _is_subset(positives, world.occupied_mask)
        and (negatives & world.occupied_mask) == 0
    )
    eliminated = tuple(
        world.world_id
        for world in worlds
        if world.world_id not in set(compatible)
    )
    return BAMCompatibility(
        compatible_world_ids=compatible,
        eliminated_world_ids=eliminated,
        evidence_level="positive_plus_perfect_negative",
        fingerprint=_sha256(
            {
                "positives": positives,
                "negatives": negatives,
                "compatible": compatible,
                "evidence_level": "positive_plus_perfect_negative",
            }
        ),
    )


def compatible_with_temporal_arrivals(
    worlds: Sequence[BAMWorld],
    positive_ids: Sequence[str],
    negative_ids: Sequence[str],
    observed_arrival_steps: dict[str, int],
) -> BAMCompatibility:
    base = compatible_with_perfect_negatives(worlds, positive_ids, negative_ids)
    compatible_set = set(base.compatible_world_ids)
    node_index = {node_id: i for i, node_id in enumerate(worlds[0].node_ids)}
    compatible: list[str] = []
    for world in worlds:
        if world.world_id not in compatible_set:
            continue
        ok = True
        for node_id, observed_step in observed_arrival_steps.items():
            if node_id not in node_index:
                raise ValueError(f"unknown temporal node: {node_id}")
            predicted = world.first_arrival_steps[node_index[node_id]]
            if predicted != observed_step:
                ok = False
                break
        if ok:
            compatible.append(world.world_id)
    compatible_tuple = tuple(compatible)
    eliminated = tuple(
        world.world_id
        for world in worlds
        if world.world_id not in set(compatible_tuple)
    )
    return BAMCompatibility(
        compatible_world_ids=compatible_tuple,
        eliminated_world_ids=eliminated,
        evidence_level="positive_negative_temporal",
        fingerprint=_sha256(
            {
                "base": base.fingerprint,
                "observed_arrival_steps": observed_arrival_steps,
                "compatible": compatible_tuple,
                "evidence_level": "positive_negative_temporal",
            }
        ),
    )


def axis_witnesses(
    truth: BAMWorld,
    false_world: BAMWorld,
) -> dict[str, tuple[str, ...]]:
    """Return truth-positive nodes excluded by each false BAM axis."""

    if truth.node_ids != false_world.node_ids:
        raise ValueError("BAM worlds must share node universe")
    truth_positive = truth.occupied_mask
    rows = {
        "A": truth_positive & ~false_world.abiotic_mask,
        "B": truth_positive & ~false_world.biotic_mask,
        "M": truth_positive & ~false_world.movement_mask,
    }
    return {
        key: _mask_to_ids(truth.node_ids, mask)
        for key, mask in rows.items()
    }


def _bam_world_grid(
    landscape: VirtualLandscape,
    biotic_state: AuxiliaryBioticState,
) -> tuple[BAMWorld, ...]:
    worlds: list[BAMWorld] = []
    a_specs = (
        ("A_narrow", (0.57, 0.55), (0.42, 0.35)),
        ("A_broad", (0.57, 0.55), (1.30, 0.70)),
    )
    b_modes: tuple[BMode, ...] = (
        "none",
        "obligate_partner",
        "antagonist_exclusion",
        "partner_and_antagonist",
    )
    m_specs = (
        ("M_short_closed_h3", 1.01, False, 3),
        ("M_short_open_h8", 1.01, True, 8),
        ("M_long_closed_h3", 2.01, False, 3),
        ("M_long_open_h8", 2.01, True, 8),
    )
    for a_label, center, radius in a_specs:
        for b_mode in b_modes:
            for m_label, step_radius, barrier_permeable, horizon in m_specs:
                world_id = f"{a_label}|B_{b_mode}|{m_label}"
                worlds.append(
                    build_bam_world(
                        landscape,
                        world_id=world_id,
                        abiotic_label=a_label,
                        niche_center=center,
                        niche_radius=radius,
                        biotic_state=biotic_state,
                        biotic_mode=b_mode,
                        movement_label=m_label,
                        source_id="r1c0",
                        step_radius=step_radius,
                        barrier_permeable=barrier_permeable,
                        horizon=horizon,
                    )
                )
    return tuple(sorted(worlds, key=lambda world: world.world_id))


def run_bam_factorial_v2() -> dict[str, object]:
    """Run the frozen BAM v2 factorial and evidence ladder."""

    landscape = make_bam_landscape()
    biotic_state = generate_biotic_state(landscape)
    worlds = _bam_world_grid(landscape, biotic_state)
    node_set = set(landscape.node_ids)

    eligible = 0
    truth_retention_failures = 0
    h2_axis_mismatches = 0
    h3_equivalence_violations = 0
    h4_superset_violations = 0
    h5_negative_rescue_failures = 0
    h6_temporal_rescue_failures = 0

    positive_unique = 0
    negative_unique = 0
    temporal_unique = 0
    exact_g_equivalence_sizes: list[int] = []
    positive_superset_survivors = 0
    negative_rescuable_supersets = 0
    negative_rescued_supersets = 0
    temporal_rescuable = 0
    temporal_rescued = 0
    axis_counts = {
        "A_only": 0,
        "B_only": 0,
        "M_only": 0,
        "AB": 0,
        "AM": 0,
        "BM": 0,
        "ABM": 0,
    }
    case_rows: list[dict[str, object]] = []

    for truth in worlds:
        positives = truth.occupied_ids
        if len(positives) < 2 or "r1c0" not in positives:
            continue
        eligible += 1
        positive_result = compatible_positive_only(worlds, positives)
        if truth.world_id not in positive_result.compatible_world_ids:
            truth_retention_failures += 1
        if positive_result.compatible_world_ids == (truth.world_id,):
            positive_unique += 1

        g_equiv = tuple(
            world.world_id
            for world in worlds
            if world.occupied_mask == truth.occupied_mask
        )
        exact_g_equivalence_sizes.append(len(g_equiv))
        if not set(g_equiv).issubset(positive_result.compatible_world_ids):
            h3_equivalence_violations += 1

        # H2/H4 audit against every false world.
        for false_world in worlds:
            if false_world.world_id == truth.world_id:
                continue
            witnesses = axis_witnesses(truth, false_world)
            union = set(witnesses["A"]) | set(witnesses["B"]) | set(witnesses["M"])
            eliminated = false_world.world_id not in positive_result.compatible_world_ids
            if eliminated != bool(union):
                h2_axis_mismatches += 1
            axes = tuple(axis for axis in ("A", "B", "M") if witnesses[axis])
            if axes:
                axis_counts["".join(axes)] += 1
            if _is_subset(truth.occupied_mask, false_world.occupied_mask):
                if eliminated:
                    h4_superset_violations += 1
                else:
                    positive_superset_survivors += 1

        negative_ids = tuple(
            node_id for node_id in landscape.node_ids if node_id not in set(positives)
        )
        negative_result = compatible_with_perfect_negatives(
            worlds,
            positives,
            negative_ids,
        )
        if negative_result.compatible_world_ids == (truth.world_id,):
            negative_unique += 1

        for false_world in worlds:
            if false_world.world_id == truth.world_id:
                continue
            if not _is_subset(truth.occupied_mask, false_world.occupied_mask):
                continue
            extra = false_world.occupied_mask & ~truth.occupied_mask
            if extra:
                negative_rescuable_supersets += 1
                if false_world.world_id not in negative_result.compatible_world_ids:
                    negative_rescued_supersets += 1
                else:
                    h5_negative_rescue_failures += 1

        # Temporal evidence is defined only for occupied truth nodes and is evaluated
        # after full perfect presence/absence, so it targets residual equal-G BAM worlds.
        observed_arrivals = {
            node_id: truth.first_arrival_steps[i]
            for i, node_id in enumerate(truth.node_ids)
            if node_id in set(positives)
            and truth.first_arrival_steps[i] is not None
        }
        temporal_result = compatible_with_temporal_arrivals(
            worlds,
            positives,
            negative_ids,
            {key: int(value) for key, value in observed_arrivals.items()},
        )
        if temporal_result.compatible_world_ids == (truth.world_id,):
            temporal_unique += 1

        residual_equal_g = tuple(
            world for world in worlds
            if world.world_id != truth.world_id
            and world.occupied_mask == truth.occupied_mask
        )
        for false_world in residual_equal_g:
            differs = any(
                false_world.first_arrival_steps[i] != truth.first_arrival_steps[i]
                for i, node_id in enumerate(truth.node_ids)
                if node_id in set(positives)
            )
            if differs:
                temporal_rescuable += 1
                if false_world.world_id not in temporal_result.compatible_world_ids:
                    temporal_rescued += 1
                else:
                    h6_temporal_rescue_failures += 1

        case_rows.append(
            {
                "truth_world_id": truth.world_id,
                "occupied_count": len(positives),
                "positive_compatible_count": len(positive_result.compatible_world_ids),
                "perfect_negative_compatible_count": len(negative_result.compatible_world_ids),
                "temporal_compatible_count": len(temporal_result.compatible_world_ids),
                "exact_G_equivalence_size": len(g_equiv),
            }
        )

    verdicts = {
        "BAM_H1_truth_retention": (
            "SUPPORTED" if truth_retention_failures == 0 else "REFUTED"
        ),
        "BAM_H2_axis_witness_attribution": (
            "SUPPORTED" if h2_axis_mismatches == 0 else "REFUTED"
        ),
        "BAM_H3_intersection_nonidentifiability": (
            "SUPPORTED" if h3_equivalence_violations == 0 else "REFUTED"
        ),
        "BAM_H4_positive_superset_ceiling": (
            "SUPPORTED" if h4_superset_violations == 0 else "REFUTED"
        ),
        "BAM_H5_perfect_negative_rescue": (
            "SUPPORTED"
            if negative_rescuable_supersets > 0 and h5_negative_rescue_failures == 0
            else "NOT_TESTED" if negative_rescuable_supersets == 0 else "REFUTED"
        ),
        "BAM_H6_temporal_M_rescue": (
            "SUPPORTED"
            if temporal_rescuable > 0 and h6_temporal_rescue_failures == 0
            else "NOT_TESTED" if temporal_rescuable == 0 else "REFUTED"
        ),
    }
    result: dict[str, object] = {
        "schema": "eog.known_truth_bam.factorial_result.v2",
        "eligible_truth_worlds": eligible,
        "candidate_world_count": len(worlds),
        "truth_retention_failures": truth_retention_failures,
        "axis_witness_mismatches": h2_axis_mismatches,
        "equivalence_violations": h3_equivalence_violations,
        "positive_superset_violations": h4_superset_violations,
        "negative_rescue_failures": h5_negative_rescue_failures,
        "temporal_rescue_failures": h6_temporal_rescue_failures,
        "fraction_truth_unique_positive_only": 0.0 if eligible == 0 else positive_unique / eligible,
        "fraction_truth_unique_with_negatives": 0.0 if eligible == 0 else negative_unique / eligible,
        "fraction_truth_unique_with_temporal_evidence": 0.0 if eligible == 0 else temporal_unique / eligible,
        "positive_superset_survivors": positive_superset_survivors,
        "negative_rescuable_supersets": negative_rescuable_supersets,
        "negative_rescued_supersets": negative_rescued_supersets,
        "negative_rescue_fraction": (
            0.0 if negative_rescuable_supersets == 0
            else negative_rescued_supersets / negative_rescuable_supersets
        ),
        "temporal_rescuable_equal_G_worlds": temporal_rescuable,
        "temporal_rescued_equal_G_worlds": temporal_rescued,
        "temporal_M_rescue_fraction": (
            0.0 if temporal_rescuable == 0 else temporal_rescued / temporal_rescuable
        ),
        "axis_witness_counts": axis_counts,
        "exact_G_equivalence_class_sizes": exact_g_equivalence_sizes,
        "verdicts": verdicts,
        "cases": case_rows,
        "partner_ids": _mask_to_ids(landscape.node_ids, biotic_state.partner_mask),
        "antagonist_ids": _mask_to_ids(landscape.node_ids, biotic_state.antagonist_mask),
    }
    result["fingerprint"] = _sha256(result)
    return result
