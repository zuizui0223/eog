"""Prospectively structured ecological expansion margins for finite BAM worlds.

This module builds a finite parameter-neighbourhood around the frozen deterministic
BAM generality systems.  It is deliberately not a fitted ecological model.  The
expanded levels were preregistered in
validation/bam_ecological_expansion_margin_v1/protocol_v1.json before scoring.

Only expanded worlds that reproduce the exact current distribution G of an E1 survivor
fiber are eligible as counterexamples.
"""
from __future__ import annotations

from dataclasses import dataclass
import itertools
import math
import re
from typing import Iterable, Sequence

from .known_truth_bam import BAMWorld, abiotic_mask, movement_state
from .known_truth_bam_generality import GeneralitySystem


BM_BITS = {
    "none": (0, 0),
    "obligate_partner": (1, 0),
    "antagonist_exclusion": (0, 1),
    "partner_and_antagonist": (1, 1),
}


@dataclass(frozen=True, order=True)
class EcologicalCoordinates:
    A_level: int
    partner_required: int
    antagonist_excluded: int
    partner_range_level: int
    antagonist_range_level: int
    dispersal_radius_level: int
    barrier_permeable: int
    horizon_level: int


@dataclass(frozen=True)
class ExpandedBAMVariant:
    variant_id: str
    coordinates: EcologicalCoordinates
    abiotic_mask: int
    biotic_mask: int
    movement_mask: int
    occupied_mask: int

    def release_expands(self, axis: str) -> bool:
        G = int(self.occupied_mask)
        if axis == "A":
            released = int(self.biotic_mask & self.movement_mask)
        elif axis == "B":
            released = int(self.abiotic_mask & self.movement_mask)
        elif axis == "M":
            released = int(self.abiotic_mask & self.biotic_mask)
        else:
            raise ValueError("axis must be A, B or M")
        return bool(released & ~G)


@dataclass(frozen=True)
class EcologicalFlipMargin:
    axis: str
    survivor_ids: tuple[str, ...]
    current_decision: bool | None
    identified_in_declared_universe: bool
    minimum_distance: int | None
    nearest_variant_ids: tuple[str, ...]
    nearest_changed_dimensions: tuple[str, ...]
    eligible_same_G_expanded_worlds: int
    opposite_decision_expanded_worlds: int


def _all_mask(n: int) -> int:
    return (1 << n) - 1


def _source_id(system: GeneralitySystem) -> str:
    return f"r{system.landscape.height // 2}c0"


def _source_environment(system: GeneralitySystem) -> tuple[float, float]:
    source = _source_id(system)
    i = system.landscape.node_ids.index(source)
    return system.landscape.environment[i]


def _in_grid_neighbours(system: GeneralitySystem, i: int) -> tuple[int, ...]:
    width = system.landscape.width
    height = system.landscape.height
    row, col = divmod(i, width)
    out = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        rr, cc = row + dr, col + dc
        if 0 <= rr < height and 0 <= cc < width:
            out.append(rr * width + cc)
    return tuple(out)


def _dilate(system: GeneralitySystem, mask: int) -> int:
    out = int(mask)
    for i in range(len(system.landscape.node_ids)):
        bit = 1 << i
        if not (mask & bit):
            continue
        for j in _in_grid_neighbours(system, i):
            out |= 1 << j
    return out


def _erode(system: GeneralitySystem, mask: int) -> int:
    out = 0
    for i in range(len(system.landscape.node_ids)):
        bit = 1 << i
        if not (mask & bit):
            continue
        neighbours = _in_grid_neighbours(system, i)
        if all(mask & (1 << j) for j in neighbours):
            out |= bit
    return out


def _associate_mask(system: GeneralitySystem, base: int, level: int) -> int:
    if level == -1:
        return _erode(system, base)
    if level == 0:
        return int(base)
    if level == 1:
        return _dilate(system, base)
    raise ValueError("associate range level must be -1, 0 or 1")


def _A_masks(system: GeneralitySystem) -> dict[int, int]:
    source_env = _source_environment(system)
    center = (source_env[0] + 0.22, source_env[1])
    narrow = (0.36, 0.28)
    broad = (0.62, 0.46)
    delta = (broad[0] - narrow[0], broad[1] - narrow[1])
    radii = {
        -1: (
            max(0.05, narrow[0] - delta[0]),
            max(0.05, narrow[1] - delta[1]),
        ),
        0: narrow,
        1: broad,
        2: (broad[0] + delta[0], broad[1] + delta[1]),
    }
    return {
        level: abiotic_mask(system.landscape, center=center, radius=radius)
        for level, radius in radii.items()
    }


def _B_masks(system: GeneralitySystem) -> dict[tuple[int, int, int, int], int]:
    n = len(system.landscape.node_ids)
    all_nodes = _all_mask(n)
    partner_masks = {
        level: _associate_mask(system, system.biotic_state.partner_mask, level)
        for level in (-1, 0, 1)
    }
    antagonist_masks = {
        level: _associate_mask(system, system.biotic_state.antagonist_mask, level)
        for level in (-1, 0, 1)
    }
    out = {}
    for partner_required, antagonist_excluded, p_level, a_level in itertools.product(
        (0, 1), (0, 1), (-1, 0, 1), (-1, 0, 1)
    ):
        mask = all_nodes
        if partner_required:
            mask &= partner_masks[p_level]
        if antagonist_excluded:
            mask &= all_nodes & ~antagonist_masks[a_level]
        out[(partner_required, antagonist_excluded, p_level, a_level)] = mask
    return out


def _M_masks(system: GeneralitySystem) -> dict[tuple[int, int, int], int]:
    short = max(3, system.landscape.width // 3)
    long = system.landscape.width + system.landscape.height
    radii = {0: 1.01, 1: 2.01, 2: 3.01}
    horizons = {0: short, 1: long, 2: long + system.landscape.width}
    source = _source_id(system)
    out = {}
    for d_level, p_bit, h_level in itertools.product((0, 1, 2), (0, 1), (0, 1, 2)):
        out[(d_level, p_bit, h_level)] = movement_state(
            system.landscape,
            source_id=source,
            step_radius=radii[d_level],
            barrier_permeable=bool(p_bit),
            horizon=horizons[h_level],
        ).accessible_mask
    return out


def build_expanded_ecological_lattice(
    system: GeneralitySystem,
) -> tuple[ExpandedBAMVariant, ...]:
    A_masks = _A_masks(system)
    B_masks = _B_masks(system)
    M_masks = _M_masks(system)
    rows = []
    for (
        A_level,
        partner_required,
        antagonist_excluded,
        partner_range_level,
        antagonist_range_level,
        d_level,
        p_bit,
        h_level,
    ) in itertools.product(
        (-1, 0, 1, 2),
        (0, 1),
        (0, 1),
        (-1, 0, 1),
        (-1, 0, 1),
        (0, 1, 2),
        (0, 1),
        (0, 1, 2),
    ):
        coords = EcologicalCoordinates(
            A_level=A_level,
            partner_required=partner_required,
            antagonist_excluded=antagonist_excluded,
            partner_range_level=partner_range_level,
            antagonist_range_level=antagonist_range_level,
            dispersal_radius_level=d_level,
            barrier_permeable=p_bit,
            horizon_level=h_level,
        )
        A = A_masks[A_level]
        B = B_masks[
            (
                partner_required,
                antagonist_excluded,
                partner_range_level,
                antagonist_range_level,
            )
        ]
        M = M_masks[(d_level, p_bit, h_level)]
        variant_id = (
            f"A{A_level}|Bpr{partner_required}ae{antagonist_excluded}"
            f"_ps{partner_range_level}_as{antagonist_range_level}"
            f"|Md{d_level}p{p_bit}h{h_level}"
        )
        rows.append(
            ExpandedBAMVariant(
                variant_id=variant_id,
                coordinates=coords,
                abiotic_mask=A,
                biotic_mask=B,
                movement_mask=M,
                occupied_mask=A & B & M,
            )
        )
    return tuple(rows)


_MOVEMENT_RE = re.compile(r"^D(?P<D>[0-9.]+)_P(?P<P>[01])_H(?P<H>[0-9]+)$")


def declared_world_coordinates(
    system: GeneralitySystem,
    world: BAMWorld,
) -> EcologicalCoordinates:
    if world.abiotic_label == "A_narrow":
        A_level = 0
    elif world.abiotic_label == "A_broad":
        A_level = 1
    else:
        raise ValueError(f"unknown declared A label: {world.abiotic_label}")

    try:
        partner_required, antagonist_excluded = BM_BITS[world.biotic_mode]
    except KeyError as exc:
        raise ValueError(f"unknown declared B mode: {world.biotic_mode}") from exc

    match = _MOVEMENT_RE.match(world.movement_label)
    if match is None:
        raise ValueError(f"cannot parse movement label: {world.movement_label}")
    D = float(match.group("D"))
    P = int(match.group("P"))
    H = int(match.group("H"))
    if math.isclose(D, 1.01):
        d_level = 0
    elif math.isclose(D, 2.01):
        d_level = 1
    else:
        raise ValueError(f"unknown declared dispersal radius: {D}")

    short = max(3, system.landscape.width // 3)
    long = system.landscape.width + system.landscape.height
    if H == short:
        h_level = 0
    elif H == long:
        h_level = 1
    else:
        raise ValueError(f"unknown declared horizon: {H}")

    return EcologicalCoordinates(
        A_level=A_level,
        partner_required=partner_required,
        antagonist_excluded=antagonist_excluded,
        partner_range_level=0,
        antagonist_range_level=0,
        dispersal_radius_level=d_level,
        barrier_permeable=P,
        horizon_level=h_level,
    )


_COORD_FIELDS = (
    "A_level",
    "partner_required",
    "antagonist_excluded",
    "partner_range_level",
    "antagonist_range_level",
    "dispersal_radius_level",
    "barrier_permeable",
    "horizon_level",
)


def ecological_coordinate_distance(
    left: EcologicalCoordinates,
    right: EcologicalCoordinates,
) -> int:
    return sum(abs(int(getattr(left, field)) - int(getattr(right, field))) for field in _COORD_FIELDS)


def changed_dimensions(
    left: EcologicalCoordinates,
    right: EcologicalCoordinates,
) -> tuple[str, ...]:
    return tuple(
        field
        for field in _COORD_FIELDS
        if getattr(left, field) != getattr(right, field)
    )


def _nearest_declared_survivor(
    candidate: ExpandedBAMVariant,
    survivor_coords: Sequence[tuple[str, EcologicalCoordinates]],
) -> tuple[int, tuple[str, ...], tuple[str, ...]]:
    best = None
    ids = []
    dims = set()
    for world_id, coords in survivor_coords:
        distance = ecological_coordinate_distance(coords, candidate.coordinates)
        if best is None or distance < best:
            best = distance
            ids = [world_id]
            dims = set(changed_dimensions(coords, candidate.coordinates))
        elif distance == best:
            ids.append(world_id)
            dims.update(changed_dimensions(coords, candidate.coordinates))
    assert best is not None
    return int(best), tuple(sorted(ids)), tuple(sorted(dims))


def ecological_flip_margin(
    system: GeneralitySystem,
    survivor_ids: Sequence[str],
    expanded_lattice: Sequence[ExpandedBAMVariant],
    *,
    axis: str,
) -> EcologicalFlipMargin:
    by_id = {world.world_id: world for world in system.worlds}
    ids = tuple(sorted(set(str(value) for value in survivor_ids)))
    if not ids:
        raise ValueError("survivor_ids must be non-empty")
    missing = set(ids).difference(by_id)
    if missing:
        raise ValueError(f"unknown survivor worlds: {sorted(missing)}")
    survivors = tuple(by_id[world_id] for world_id in ids)
    G = int(survivors[0].occupied_mask)
    if any(int(world.occupied_mask) != G for world in survivors):
        raise ValueError("ecological margin requires a same-G E1 survivor fiber")

    decisions = set()
    for world in survivors:
        if axis == "A":
            released = world.biotic_mask & world.movement_mask
        elif axis == "B":
            released = world.abiotic_mask & world.movement_mask
        elif axis == "M":
            released = world.abiotic_mask & world.biotic_mask
        else:
            raise ValueError("axis must be A, B or M")
        decisions.add(bool(released & ~G))

    same_G = tuple(row for row in expanded_lattice if int(row.occupied_mask) == G)
    if len(decisions) != 1:
        return EcologicalFlipMargin(
            axis=axis,
            survivor_ids=ids,
            current_decision=None,
            identified_in_declared_universe=False,
            minimum_distance=0,
            nearest_variant_ids=(),
            nearest_changed_dimensions=(),
            eligible_same_G_expanded_worlds=len(same_G),
            opposite_decision_expanded_worlds=0,
        )

    current = next(iter(decisions))
    opposite = tuple(row for row in same_G if row.release_expands(axis) != current)
    if not opposite:
        return EcologicalFlipMargin(
            axis=axis,
            survivor_ids=ids,
            current_decision=current,
            identified_in_declared_universe=True,
            minimum_distance=None,
            nearest_variant_ids=(),
            nearest_changed_dimensions=(),
            eligible_same_G_expanded_worlds=len(same_G),
            opposite_decision_expanded_worlds=0,
        )

    survivor_coords = tuple(
        (world.world_id, declared_world_coordinates(system, world))
        for world in survivors
    )
    scored = []
    for candidate in opposite:
        distance, _, dims = _nearest_declared_survivor(candidate, survivor_coords)
        scored.append((distance, candidate.variant_id, dims))
    best = min(row[0] for row in scored)
    best_rows = tuple(row for row in scored if row[0] == best)
    return EcologicalFlipMargin(
        axis=axis,
        survivor_ids=ids,
        current_decision=current,
        identified_in_declared_universe=True,
        minimum_distance=best,
        nearest_variant_ids=tuple(sorted(row[1] for row in best_rows)),
        nearest_changed_dimensions=tuple(
            sorted({dim for _, _, dims in best_rows for dim in dims})
        ),
        eligible_same_G_expanded_worlds=len(same_G),
        opposite_decision_expanded_worlds=len(opposite),
    )


def declared_world_is_embedded_exactly(
    system: GeneralitySystem,
    world: BAMWorld,
    expanded_lattice: Sequence[ExpandedBAMVariant],
) -> bool:
    coords = declared_world_coordinates(system, world)
    matches = tuple(row for row in expanded_lattice if row.coordinates == coords)
    return (
        len(matches) == 1
        and matches[0].abiotic_mask == world.abiotic_mask
        and matches[0].biotic_mask == world.biotic_mask
        and matches[0].movement_mask == world.movement_mask
        and matches[0].occupied_mask == world.occupied_mask
    )
