"""Target-aware evidence design for structured future BAM targets.

The active universe is the preregistered W1 ecological expansion lattice.  For a
current same-G survivor fiber, this module constructs two deliberately distinct
truth-relative evidence libraries:

1. present-state evidence: node-level A/B/M/tau;
2. latent-parameter evidence: the eight frozen W1 ecological coordinates.

The exact target-specific solver eliminates only survivor worlds whose declared future
target differs from the truth target.  Same-target aliases may remain unresolved.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, Mapping, Sequence

from .bam_counterfactual_identifiability import (
    TruthTargetMeasurementPlan,
    exact_minimum_truth_target_measurements,
)
from .bam_ecological_expansion_margin import (
    EcologicalCoordinates,
    ExpandedBAMVariant,
)
from .bam_identifiability_theory import DiagnosticMeasurement
from .bam_structured_counterfactuals import expanded_variant_bam_state_key
from .known_truth_bam_generality import GeneralitySystem


PARAMETER_FIELDS = (
    "A_level",
    "partner_required",
    "antagonist_excluded",
    "partner_range_level",
    "antagonist_range_level",
    "dispersal_radius_level",
    "barrier_permeable",
    "horizon_level",
)


@dataclass(frozen=True)
class FutureTargetEvidencePlan:
    truth_variant_id: str
    survivor_variant_ids: tuple[str, ...]
    target_already_identified: bool
    state_only: TruthTargetMeasurementPlan
    parameter_only: TruthTargetMeasurementPlan
    combined: TruthTargetMeasurementPlan


def _validate_active(
    variants: Sequence[ExpandedBAMVariant],
    survivor_variant_ids: Sequence[str],
    truth_variant_id: str,
) -> tuple[dict[str, ExpandedBAMVariant], tuple[str, ...]]:
    by_id = {row.variant_id: row for row in variants}
    ids = tuple(sorted(set(str(value) for value in survivor_variant_ids)))
    if not ids:
        raise ValueError("survivor_variant_ids must be non-empty")
    missing = set(ids).difference(by_id)
    if missing:
        raise ValueError(f"unknown W1 variants: {sorted(missing)}")
    if truth_variant_id not in ids:
        raise ValueError("truth_variant_id must be a current survivor")
    G = int(by_id[ids[0]].occupied_mask)
    if any(int(by_id[world_id].occupied_mask) != G for world_id in ids):
        raise ValueError("future-target evidence requires a same-G W1 survivor fiber")
    return by_id, ids


def current_state_measurements(
    system: GeneralitySystem,
    variants: Sequence[ExpandedBAMVariant],
    survivor_variant_ids: Sequence[str],
    truth_variant_id: str,
) -> tuple[DiagnosticMeasurement, ...]:
    """Build exact truth-relative A/B/M/tau node measurements."""

    by_id, ids = _validate_active(variants, survivor_variant_ids, truth_variant_id)
    truth = by_id[truth_variant_id]
    node_ids = system.landscape.node_ids

    state_by_id = {
        world_id: expanded_variant_bam_state_key(system, by_id[world_id])
        for world_id in ids
    }
    truth_state = state_by_id[truth_variant_id]
    rows: list[DiagnosticMeasurement] = []

    for component_index, component in enumerate(("A", "B", "M")):
        truth_mask = int(truth_state[component_index])
        for i, node_id in enumerate(node_ids):
            bit = 1 << i
            truth_value = bool(truth_mask & bit)
            eliminated = frozenset(
                world_id
                for world_id in ids
                if bool(int(state_by_id[world_id][component_index]) & bit)
                != truth_value
            )
            rows.append(
                DiagnosticMeasurement(
                    measurement_id=f"state:{component}:{node_id}",
                    eliminated_world_ids=eliminated,
                )
            )

    truth_tau = tuple(truth_state[3])
    for i, node_id in enumerate(node_ids):
        value = truth_tau[i]
        eliminated = frozenset(
            world_id
            for world_id in ids
            if tuple(state_by_id[world_id][3])[i] != value
        )
        rows.append(
            DiagnosticMeasurement(
                measurement_id=f"state:tau:{node_id}",
                eliminated_world_ids=eliminated,
            )
        )

    if any(truth_variant_id in row.eliminated_world_ids for row in rows):
        raise RuntimeError("truth-relative state measurement eliminated truth")
    return tuple(rows)


def parameter_measurements(
    variants: Sequence[ExpandedBAMVariant],
    survivor_variant_ids: Sequence[str],
    truth_variant_id: str,
) -> tuple[DiagnosticMeasurement, ...]:
    """Build exact truth-relative measurements of the eight W1 parameters."""

    by_id, ids = _validate_active(variants, survivor_variant_ids, truth_variant_id)
    truth_coords = by_id[truth_variant_id].coordinates
    rows: list[DiagnosticMeasurement] = []
    for field in PARAMETER_FIELDS:
        truth_value = getattr(truth_coords, field)
        eliminated = frozenset(
            world_id
            for world_id in ids
            if getattr(by_id[world_id].coordinates, field) != truth_value
        )
        rows.append(
            DiagnosticMeasurement(
                measurement_id=f"param:{field}",
                eliminated_world_ids=eliminated,
            )
        )
    if any(truth_variant_id in row.eliminated_world_ids for row in rows):
        raise RuntimeError("truth-relative parameter measurement eliminated truth")
    return tuple(rows)


def exact_future_target_evidence_plan(
    system: GeneralitySystem,
    variants: Sequence[ExpandedBAMVariant],
    survivor_variant_ids: Sequence[str],
    truth_variant_id: str,
    target_by_world: Mapping[str, Hashable],
) -> FutureTargetEvidencePlan:
    """Return exact state-only, parameter-only and combined target designs."""

    _, ids = _validate_active(variants, survivor_variant_ids, truth_variant_id)
    missing = set(ids).difference(target_by_world)
    if missing:
        raise ValueError(f"target_by_world missing active variants: {sorted(missing)}")

    state = current_state_measurements(
        system,
        variants,
        ids,
        truth_variant_id,
    )
    parameter = parameter_measurements(
        variants,
        ids,
        truth_variant_id,
    )
    state_plan = exact_minimum_truth_target_measurements(
        ids,
        truth_variant_id,
        target_by_world,
        state,
    )
    parameter_plan = exact_minimum_truth_target_measurements(
        ids,
        truth_variant_id,
        target_by_world,
        parameter,
    )
    combined_plan = exact_minimum_truth_target_measurements(
        ids,
        truth_variant_id,
        target_by_world,
        (*state, *parameter),
    )
    return FutureTargetEvidencePlan(
        truth_variant_id=truth_variant_id,
        survivor_variant_ids=ids,
        target_already_identified=state_plan.target_already_identified,
        state_only=state_plan,
        parameter_only=parameter_plan,
        combined=combined_plan,
    )


def full_parameter_world_target(
    variants: Sequence[ExpandedBAMVariant],
    survivor_variant_ids: Sequence[str],
) -> dict[str, tuple[int, ...]]:
    """Exact W1 parameter-coordinate target for active worlds."""

    by_id = {row.variant_id: row for row in variants}
    ids = tuple(sorted(set(str(value) for value in survivor_variant_ids)))
    missing = set(ids).difference(by_id)
    if missing:
        raise ValueError(f"unknown W1 variants: {sorted(missing)}")
    return {
        world_id: tuple(int(value) for value in by_id[world_id].coordinates.__dict__.values())
        for world_id in ids
    }


def parameter_target_plan(
    variants: Sequence[ExpandedBAMVariant],
    survivor_variant_ids: Sequence[str],
    truth_variant_id: str,
) -> TruthTargetMeasurementPlan:
    """Minimum parameter-coordinate assays needed to identify the truth W1 world."""

    target = full_parameter_world_target(variants, survivor_variant_ids)
    measurements = parameter_measurements(
        variants,
        survivor_variant_ids,
        truth_variant_id,
    )
    return exact_minimum_truth_target_measurements(
        survivor_variant_ids,
        truth_variant_id,
        target,
        measurements,
    )
