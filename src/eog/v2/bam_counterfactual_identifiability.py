"""Decision-relevant counterfactual identifiability over finite BAM worlds.

This module extends the exact finite BAM identifiability programme without changing
its frozen results.  It asks whether worlds that remain observationally equivalent
under a complete current distribution also agree under declared counterfactual probes.

The counterfactual probes here are deliberately idealised axis-release probes:
- release A: G_cf = B ∩ M
- release B: G_cf = A ∩ M
- release M: G_cf = A ∩ B

They are mechanism probes, not literal management or climate scenarios.

The evidence planner is truth-relative known-truth validation.  Given the actually
observed value of a direct finite measurement, it computes the exact minimum number of
measurements needed to eliminate every surviving world whose declared *target* differs
from the truth target.  Worlds with a different mechanism but the same target need not
be eliminated.  This is the central distinction between mechanism identification and
decision/forecast sufficiency.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Hashable, Mapping, Sequence

from .bam_identifiability_theory import DiagnosticMeasurement
from .known_truth_bam import BAMWorld


_AXIS_TO_MASK = {
    "A": "abiotic_mask",
    "B": "biotic_mask",
    "M": "movement_mask",
}


def axis_release_outcome(world: BAMWorld, axis: str) -> int:
    """Return the exact occupied mask after removing one BAM constraint."""

    if axis == "A":
        return int(world.biotic_mask & world.movement_mask)
    if axis == "B":
        return int(world.abiotic_mask & world.movement_mask)
    if axis == "M":
        return int(world.abiotic_mask & world.biotic_mask)
    raise ValueError("axis must be A, B or M")


def release_expands_current(world: BAMWorld, axis: str) -> bool:
    """Whether the axis-release probe unlocks any node outside current G."""

    outcome = axis_release_outcome(world, axis)
    return bool(outcome & ~int(world.occupied_mask))


def joint_release_signature(world: BAMWorld) -> tuple[int, int, int]:
    return tuple(axis_release_outcome(world, axis) for axis in ("A", "B", "M"))


def counterfactual_classes(
    survivor_ids: Sequence[str],
    target_by_world: Mapping[str, Hashable],
) -> tuple[tuple[str, ...], ...]:
    """Partition a survivor fiber by a declared counterfactual/decision target."""

    ids = tuple(sorted(set(str(value) for value in survivor_ids)))
    if not ids:
        raise ValueError("survivor_ids must be non-empty")
    missing = set(ids).difference(target_by_world)
    if missing:
        raise ValueError(f"target_by_world missing survivors: {sorted(missing)}")

    groups: dict[Hashable, list[str]] = defaultdict(list)
    for world_id in ids:
        groups[target_by_world[world_id]].append(world_id)
    return tuple(
        sorted(
            (tuple(sorted(group)) for group in groups.values()),
            key=lambda group: (len(group), group),
        )
    )


def target_identified(
    survivor_ids: Sequence[str],
    target_by_world: Mapping[str, Hashable],
) -> bool:
    return len(counterfactual_classes(survivor_ids, target_by_world)) == 1


def truth_relative_direct_measurements(
    worlds: Sequence[BAMWorld],
    truth: BAMWorld,
    survivor_ids: Sequence[str],
    *,
    include_arrival: bool = True,
) -> tuple[DiagnosticMeasurement, ...]:
    """Build exact direct A/B/M/(optional tau) measurements relative to truth."""

    by_id = {world.world_id: world for world in worlds}
    survivors = tuple(sorted(set(str(value) for value in survivor_ids)))
    missing = set(survivors).difference(by_id)
    if missing:
        raise ValueError(f"unknown survivor worlds: {sorted(missing)}")
    if truth.world_id not in by_id:
        raise ValueError("truth world must be declared")
    if any(by_id[world_id].node_ids != truth.node_ids for world_id in survivors):
        raise ValueError("all survivor worlds must share truth node_ids and order")

    rows: list[DiagnosticMeasurement] = []
    for i, node_id in enumerate(truth.node_ids):
        bit = 1 << i
        for axis, attr in _AXIS_TO_MASK.items():
            truth_value = bool(int(getattr(truth, attr)) & bit)
            eliminated = frozenset(
                world_id
                for world_id in survivors
                if bool(int(getattr(by_id[world_id], attr)) & bit) != truth_value
            )
            rows.append(
                DiagnosticMeasurement(
                    measurement_id=f"{axis}:{node_id}",
                    eliminated_world_ids=eliminated,
                )
            )

        if include_arrival:
            truth_tau = truth.first_arrival_steps[i]
            eliminated_tau = frozenset(
                world_id
                for world_id in survivors
                if by_id[world_id].first_arrival_steps[i] != truth_tau
            )
            rows.append(
                DiagnosticMeasurement(
                    measurement_id=f"tau:{node_id}",
                    eliminated_world_ids=eliminated_tau,
                )
            )
    return tuple(rows)


@dataclass(frozen=True)
class TruthTargetMeasurementPlan:
    truth_world_id: str
    survivor_ids: tuple[str, ...]
    truth_target_repr: str
    nuisance_world_ids: tuple[str, ...]
    minimum_measurement_ids: tuple[str, ...] | None
    minimum_size: int | None
    target_already_identified: bool
    evidence_library_sufficient: bool


def exact_minimum_truth_target_measurements(
    survivor_ids: Sequence[str],
    truth_world_id: str,
    target_by_world: Mapping[str, Hashable],
    measurements: Sequence[DiagnosticMeasurement],
) -> TruthTargetMeasurementPlan:
    """Exact minimum truth-relative evidence needed to fix a declared target.

    A nuisance world is any current survivor whose target differs from the truth
    target.  Same-target worlds may survive or be eliminated: the goal is target
    sufficiency, not recovery of every world sharing that target.

    Because every DiagnosticMeasurement is assumed to encode the outcome observed
    under the truth, any measurement that lists the truth as eliminated is rejected.
    The remaining problem is an exact finite minimum set cover over target-discordant
    nuisance worlds.
    """

    survivors = tuple(sorted(set(str(value) for value in survivor_ids)))
    if not survivors:
        raise ValueError("survivor_ids must be non-empty")
    if truth_world_id not in survivors:
        raise ValueError("truth_world_id must be a current survivor")
    missing = set(survivors).difference(target_by_world)
    if missing:
        raise ValueError(f"target_by_world missing survivors: {sorted(missing)}")

    truth_target = target_by_world[truth_world_id]
    nuisance = tuple(
        world_id
        for world_id in survivors
        if target_by_world[world_id] != truth_target
    )
    if not nuisance:
        return TruthTargetMeasurementPlan(
            truth_world_id=truth_world_id,
            survivor_ids=survivors,
            truth_target_repr=repr(truth_target),
            nuisance_world_ids=(),
            minimum_measurement_ids=(),
            minimum_size=0,
            target_already_identified=True,
            evidence_library_sufficient=True,
        )

    nuisance_index = {world_id: i for i, world_id in enumerate(nuisance)}
    full_mask = (1 << len(nuisance)) - 1

    # Equal coverage masks are interchangeable for minimum cardinality.  Retain the
    # lexicographically first ID to make the exact answer deterministic.
    coverage_to_id: dict[int, str] = {}
    for measurement in measurements:
        if truth_world_id in measurement.eliminated_world_ids:
            raise ValueError(
                f"measurement {measurement.measurement_id!r} eliminates the truth"
            )
        mask = 0
        for world_id in measurement.eliminated_world_ids:
            if world_id in nuisance_index:
                mask |= 1 << nuisance_index[world_id]
        if not mask:
            continue
        incumbent = coverage_to_id.get(mask)
        if incumbent is None or measurement.measurement_id < incumbent:
            coverage_to_id[mask] = measurement.measurement_id

    rows = tuple(sorted((measurement_id, mask) for mask, measurement_id in coverage_to_id.items()))
    coverable = 0
    for _, mask in rows:
        coverable |= mask
    if coverable != full_mask:
        return TruthTargetMeasurementPlan(
            truth_world_id=truth_world_id,
            survivor_ids=survivors,
            truth_target_repr=repr(truth_target),
            nuisance_world_ids=nuisance,
            minimum_measurement_ids=None,
            minimum_size=None,
            target_already_identified=False,
            evidence_library_sufficient=False,
        )

    # Exact 0/1 set-cover dynamic programme.  State is the nuisance-coverage bit mask.
    best: dict[int, tuple[str, ...]] = {0: ()}
    for measurement_id, measurement_mask in rows:
        updates: dict[int, tuple[str, ...]] = {}
        for mask, chosen in tuple(best.items()):
            updated = mask | measurement_mask
            candidate = tuple(sorted((*chosen, measurement_id)))
            incumbent = best.get(updated)
            pending = updates.get(updated)
            reference = incumbent
            if pending is not None and (
                reference is None
                or (len(pending), pending) < (len(reference), reference)
            ):
                reference = pending
            if reference is None or (len(candidate), candidate) < (
                len(reference),
                reference,
            ):
                updates[updated] = candidate
        for mask, candidate in updates.items():
            incumbent = best.get(mask)
            if incumbent is None or (len(candidate), candidate) < (
                len(incumbent),
                incumbent,
            ):
                best[mask] = candidate

    solution = best.get(full_mask)
    return TruthTargetMeasurementPlan(
        truth_world_id=truth_world_id,
        survivor_ids=survivors,
        truth_target_repr=repr(truth_target),
        nuisance_world_ids=nuisance,
        minimum_measurement_ids=solution,
        minimum_size=None if solution is None else len(solution),
        target_already_identified=False,
        evidence_library_sufficient=solution is not None,
    )
