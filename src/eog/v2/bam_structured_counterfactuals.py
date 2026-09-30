"""Structured ecological counterfactuals over finite BAM survivor fibers.

The transformations in this module are synthetic validation operators frozen in
validation/bam_structured_counterfactuals_v1/protocol_v1.json.  They are not calibrated
real-species climate, interaction, or restoration scenarios.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal, Sequence

import numpy as np

from .bam_ecological_expansion_margin import (
    BM_BITS,
    EcologicalCoordinates,
    ExpandedBAMVariant,
    _all_mask,
    _associate_mask,
    _dilate,
    _erode,
    build_expanded_ecological_lattice,
    declared_world_coordinates,
)
from .known_truth_bam import BAMWorld, movement_state
from .known_truth_bam_generality import GeneralitySystem


Transformation = Literal["climate_shift", "biotic_stress", "barrier_restoration"]


@dataclass(frozen=True)
class StructuredCounterfactualOutcome:
    transformation: Transformation
    current_G: int
    counterfactual_G: int
    binary_decision: bool


def _source_id(system: GeneralitySystem) -> str:
    return f"r{system.landscape.height // 2}c0"


def _source_environment(system: GeneralitySystem) -> tuple[float, float]:
    source = _source_id(system)
    i = system.landscape.node_ids.index(source)
    return system.landscape.environment[i]


def _abiotic_radius(level: int) -> tuple[float, float]:
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
    if level not in radii:
        raise ValueError("A level outside frozen structured-counterfactual lattice")
    return radii[level]


def _shifted_abiotic_mask(
    system: GeneralitySystem,
    A_level: int,
    *,
    temperature_delta: float = 0.08,
    moisture_delta: float = -0.04,
) -> int:
    source_env = _source_environment(system)
    center = np.asarray((source_env[0] + 0.22, source_env[1]), dtype=float)
    radius = np.asarray(_abiotic_radius(A_level), dtype=float)
    environment = np.asarray(system.landscape.environment, dtype=float).copy()
    environment[:, 0] += float(temperature_delta)
    environment[:, 1] += float(moisture_delta)
    scaled = (environment - center) / radius
    keep = np.sum(scaled * scaled, axis=1) <= 1.0 + 1e-12
    mask = 0
    for i, value in enumerate(keep):
        if bool(value):
            mask |= 1 << i
    return mask


def _biotic_mask_after_stress(
    system: GeneralitySystem,
    coords: EcologicalCoordinates,
) -> int:
    n = len(system.landscape.node_ids)
    all_nodes = _all_mask(n)
    partner_current = _associate_mask(
        system,
        system.biotic_state.partner_mask,
        coords.partner_range_level,
    )
    antagonist_current = _associate_mask(
        system,
        system.biotic_state.antagonist_mask,
        coords.antagonist_range_level,
    )
    partner_stressed = _erode(system, partner_current)
    antagonist_stressed = _dilate(system, antagonist_current)

    mask = all_nodes
    if coords.partner_required:
        mask &= partner_stressed
    if coords.antagonist_excluded:
        mask &= all_nodes & ~antagonist_stressed
    return mask


def _movement_state_for_coords(
    system: GeneralitySystem,
    coords: EcologicalCoordinates,
    *,
    force_barrier_permeable: bool | None = None,
):
    radii = {0: 1.01, 1: 2.01, 2: 3.01}
    short = max(3, system.landscape.width // 3)
    long = system.landscape.width + system.landscape.height
    horizons = {0: short, 1: long, 2: long + system.landscape.width}
    if coords.dispersal_radius_level not in radii:
        raise ValueError("unknown dispersal radius level")
    if coords.horizon_level not in horizons:
        raise ValueError("unknown horizon level")
    permeable = (
        bool(coords.barrier_permeable)
        if force_barrier_permeable is None
        else bool(force_barrier_permeable)
    )
    return movement_state(
        system.landscape,
        source_id=_source_id(system),
        step_radius=radii[coords.dispersal_radius_level],
        barrier_permeable=permeable,
        horizon=horizons[coords.horizon_level],
    )


def expanded_variant_bam_state_key(
    system: GeneralitySystem,
    variant: ExpandedBAMVariant,
) -> tuple[object, ...]:
    movement = _movement_state_for_coords(system, variant.coordinates)
    if movement.accessible_mask != variant.movement_mask:
        raise RuntimeError("expanded-variant movement-mask reconstruction mismatch")
    return (
        int(variant.abiotic_mask),
        int(variant.biotic_mask),
        int(variant.movement_mask),
        tuple(movement.first_arrival_steps),
    )


def parameter_key_from_declared_world(
    system: GeneralitySystem,
    world: BAMWorld,
) -> EcologicalCoordinates:
    return declared_world_coordinates(system, world)


def _counterfactual_from_masks(
    system: GeneralitySystem,
    *,
    coords: EcologicalCoordinates,
    A: int,
    B: int,
    M: int,
    transformation: Transformation,
) -> StructuredCounterfactualOutcome:
    current_G = int(A & B & M)
    if transformation == "climate_shift":
        A_cf = _shifted_abiotic_mask(system, coords.A_level)
        G_cf = int(A_cf & B & M)
        binary = G_cf.bit_count() < current_G.bit_count()
    elif transformation == "biotic_stress":
        B_cf = _biotic_mask_after_stress(system, coords)
        G_cf = int(A & B_cf & M)
        if G_cf & ~current_G:
            raise RuntimeError("biotic stress unexpectedly added occupied nodes")
        binary = G_cf != current_G
    elif transformation == "barrier_restoration":
        M_cf = _movement_state_for_coords(
            system,
            coords,
            force_barrier_permeable=True,
        ).accessible_mask
        if M & ~M_cf:
            raise RuntimeError("barrier restoration unexpectedly reduced accessibility")
        G_cf = int(A & B & M_cf)
        binary = bool(G_cf & ~current_G)
    else:
        raise ValueError("unknown structured transformation")
    return StructuredCounterfactualOutcome(
        transformation=transformation,
        current_G=current_G,
        counterfactual_G=G_cf,
        binary_decision=bool(binary),
    )


def declared_world_counterfactual(
    system: GeneralitySystem,
    world: BAMWorld,
    transformation: Transformation,
) -> StructuredCounterfactualOutcome:
    coords = declared_world_coordinates(system, world)
    return _counterfactual_from_masks(
        system,
        coords=coords,
        A=int(world.abiotic_mask),
        B=int(world.biotic_mask),
        M=int(world.movement_mask),
        transformation=transformation,
    )


def expanded_variant_counterfactual(
    system: GeneralitySystem,
    variant: ExpandedBAMVariant,
    transformation: Transformation,
) -> StructuredCounterfactualOutcome:
    return _counterfactual_from_masks(
        system,
        coords=variant.coordinates,
        A=int(variant.abiotic_mask),
        B=int(variant.biotic_mask),
        M=int(variant.movement_mask),
        transformation=transformation,
    )


def exact_parameter_identity_identified(ids: Sequence[str]) -> bool:
    return len(set(ids)) == 1


def target_identified(values: Sequence[object]) -> bool:
    values = tuple(values)
    if not values:
        raise ValueError("target values must be non-empty")
    return len(set(values)) == 1


def build_structured_counterfactual_lattice(
    system: GeneralitySystem,
) -> tuple[ExpandedBAMVariant, ...]:
    return build_expanded_ecological_lattice(system)
