"""Finite-set identifiability theory for explicit BAM worlds.

This module is independent of the virtual-landscape generator.  It operates only on
finite state objects and the evidence semantics frozen in
validation/bam_identifiability_theory_v1/protocol_v1.json.
"""
from __future__ import annotations

from dataclasses import dataclass
import itertools
from typing import Callable, Iterable, Sequence


@dataclass(frozen=True)
class FiniteBAMState:
    world_id: str
    node_ids: tuple[str, ...]
    A: frozenset[str]
    B: frozenset[str]
    M: frozenset[str]
    tau: tuple[int | None, ...]
    parameter_label: str = ""

    def __post_init__(self) -> None:
        nodes = set(self.node_ids)
        if not self.world_id.strip():
            raise ValueError("world_id must be non-empty")
        if len(nodes) != len(self.node_ids):
            raise ValueError("node_ids must be unique")
        if not self.A <= nodes or not self.B <= nodes or not self.M <= nodes:
            raise ValueError("A/B/M must be subsets of node_ids")
        if len(self.tau) != len(self.node_ids):
            raise ValueError("tau must contain one state per node")

    @property
    def G(self) -> frozenset[str]:
        return self.A & self.B & self.M

    @property
    def bam_state_key(self) -> tuple[object, ...]:
        return (
            tuple(sorted(self.A)),
            tuple(sorted(self.B)),
            tuple(sorted(self.M)),
            self.tau,
        )


def _ordered(worlds: Sequence[FiniteBAMState]) -> tuple[FiniteBAMState, ...]:
    rows = tuple(worlds)
    if not rows:
        raise ValueError("worlds must be non-empty")
    node_ids = rows[0].node_ids
    if any(world.node_ids != node_ids for world in rows):
        raise ValueError("all worlds must share node_ids and order")
    if len({world.world_id for world in rows}) != len(rows):
        raise ValueError("world IDs must be unique")
    return tuple(sorted(rows, key=lambda world: world.world_id))


def survivor_E0(
    worlds: Sequence[FiniteBAMState],
    truth: FiniteBAMState,
) -> tuple[str, ...]:
    """Complete positive occurrence state G* only."""

    ordered = _ordered(worlds)
    return tuple(
        world.world_id
        for world in ordered
        if truth.G <= world.G
    )


def survivor_E1(
    worlds: Sequence[FiniteBAMState],
    truth: FiniteBAMState,
) -> tuple[str, ...]:
    """Complete perfect presence/absence map."""

    ordered = _ordered(worlds)
    return tuple(
        world.world_id
        for world in ordered
        if world.G == truth.G
    )


def survivor_E2(
    worlds: Sequence[FiniteBAMState],
    truth: FiniteBAMState,
) -> tuple[str, ...]:
    """E1 plus exact movement arrival restricted to truth-positive nodes."""

    ordered = _ordered(worlds)
    node_index = {node_id: i for i, node_id in enumerate(truth.node_ids)}
    positive_indices = tuple(node_index[node_id] for node_id in truth.G)
    return tuple(
        world.world_id
        for world in ordered
        if world.G == truth.G
        and all(world.tau[i] == truth.tau[i] for i in positive_indices)
    )


def survivor_E3(
    worlds: Sequence[FiniteBAMState],
    truth: FiniteBAMState,
) -> tuple[str, ...]:
    """E2 plus complete direct A state."""

    ids = set(survivor_E2(worlds, truth))
    ordered = _ordered(worlds)
    return tuple(
        world.world_id
        for world in ordered
        if world.world_id in ids and world.A == truth.A
    )


def survivor_E4(
    worlds: Sequence[FiniteBAMState],
    truth: FiniteBAMState,
) -> tuple[str, ...]:
    """E3 plus complete direct B state."""

    ids = set(survivor_E3(worlds, truth))
    ordered = _ordered(worlds)
    return tuple(
        world.world_id
        for world in ordered
        if world.world_id in ids and world.B == truth.B
    )


def survivor_E5(
    worlds: Sequence[FiniteBAMState],
    truth: FiniteBAMState,
) -> tuple[str, ...]:
    """E4 plus complete direct M accessibility state."""

    ids = set(survivor_E4(worlds, truth))
    ordered = _ordered(worlds)
    return tuple(
        world.world_id
        for world in ordered
        if world.world_id in ids and world.M == truth.M
    )


def survivor_E6(
    worlds: Sequence[FiniteBAMState],
    truth: FiniteBAMState,
) -> tuple[str, ...]:
    """E5 plus complete movement first-arrival state."""

    ids = set(survivor_E5(worlds, truth))
    ordered = _ordered(worlds)
    return tuple(
        world.world_id
        for world in ordered
        if world.world_id in ids and world.tau == truth.tau
    )


def evidence_ladder(
    worlds: Sequence[FiniteBAMState],
    truth: FiniteBAMState,
) -> tuple[tuple[str, ...], ...]:
    return (
        survivor_E0(worlds, truth),
        survivor_E1(worlds, truth),
        survivor_E2(worlds, truth),
        survivor_E3(worlds, truth),
        survivor_E4(worlds, truth),
        survivor_E5(worlds, truth),
        survivor_E6(worlds, truth),
    )


def bam_state_equivalence_class(
    worlds: Sequence[FiniteBAMState],
    truth: FiniteBAMState,
) -> tuple[str, ...]:
    ordered = _ordered(worlds)
    key = truth.bam_state_key
    return tuple(world.world_id for world in ordered if world.bam_state_key == key)


def bam_state_identified(
    worlds: Sequence[FiniteBAMState],
    survivor_ids: Sequence[str],
) -> bool:
    ordered = _ordered(worlds)
    by_id = {world.world_id: world for world in ordered}
    ids = tuple(survivor_ids)
    if not ids:
        return False
    keys = {by_id[world_id].bam_state_key for world_id in ids}
    return len(keys) == 1


@dataclass(frozen=True)
class DiagnosticMeasurement:
    measurement_id: str
    eliminated_world_ids: frozenset[str]


def exact_minimum_diagnostic_measurements(
    survivor_ids: Sequence[str],
    target_ids: Sequence[str],
    measurements: Sequence[DiagnosticMeasurement],
) -> tuple[str, ...] | None:
    """Solve the finite minimum hitting-set problem exactly with bit-mask DP.

    The target fiber must be retained.  Each measurement declares which survivor
    worlds it would eliminate given the truth state.  A valid diagnostic design must
    eliminate every non-target survivor and no target survivor.
    """

    survivors = tuple(sorted(set(str(v) for v in survivor_ids)))
    targets = frozenset(str(v) for v in target_ids)
    survivor_set = frozenset(survivors)
    if not targets <= survivor_set:
        raise ValueError("target_ids must be a subset of survivor_ids")

    nuisance = tuple(world_id for world_id in survivors if world_id not in targets)
    if not nuisance:
        return ()

    index = {world_id: i for i, world_id in enumerate(nuisance)}
    full_mask = (1 << len(nuisance)) - 1
    rows: list[tuple[str, int]] = []
    for measurement in measurements:
        if targets & measurement.eliminated_world_ids:
            continue
        mask = 0
        for world_id in measurement.eliminated_world_ids:
            if world_id in index:
                mask |= 1 << index[world_id]
        if mask:
            rows.append((measurement.measurement_id, mask))

    coverable = 0
    for _, mask in rows:
        coverable |= mask
    if coverable != full_mask:
        return None

    best: dict[int, tuple[str, ...]] = {0: ()}
    for measurement_id, measurement_mask in rows:
        for mask, chosen in list(best.items()):
            updated = mask | measurement_mask
            candidate = tuple(sorted((*chosen, measurement_id)))
            incumbent = best.get(updated)
            if incumbent is None or (len(candidate), candidate) < (
                len(incumbent),
                incumbent,
            ):
                best[updated] = candidate
    return best[full_mask]


def brute_force_minimum_diagnostic_measurements(
    survivor_ids: Sequence[str],
    target_ids: Sequence[str],
    measurements: Sequence[DiagnosticMeasurement],
) -> tuple[str, ...] | None:
    """Reference brute-force solver for small test fixtures."""

    survivors = frozenset(str(v) for v in survivor_ids)
    targets = frozenset(str(v) for v in target_ids)
    nuisance = survivors - targets
    valid = tuple(
        measurement
        for measurement in measurements
        if not targets & measurement.eliminated_world_ids
    )
    if not nuisance:
        return ()
    for size in range(1, len(valid) + 1):
        for combo in itertools.combinations(valid, size):
            eliminated: set[str] = set()
            for measurement in combo:
                eliminated.update(measurement.eliminated_world_ids)
            if nuisance <= eliminated:
                return tuple(sorted(row.measurement_id for row in combo))
    return None


def measurements_from_binary_state(
    worlds: Sequence[FiniteBAMState],
    truth: FiniteBAMState,
    survivor_ids: Sequence[str],
    *,
    component: str,
) -> tuple[DiagnosticMeasurement, ...]:
    """Build direct-node measurements for A, B or M."""

    if component not in {"A", "B", "M"}:
        raise ValueError("component must be A, B or M")
    ordered = _ordered(worlds)
    by_id = {world.world_id: world for world in ordered}
    rows: list[DiagnosticMeasurement] = []
    truth_set = getattr(truth, component)

    for node_id in truth.node_ids:
        truth_value = node_id in truth_set
        eliminated = frozenset(
            world_id
            for world_id in survivor_ids
            if ((node_id in getattr(by_id[world_id], component)) != truth_value)
        )
        rows.append(
            DiagnosticMeasurement(
                measurement_id=f"{component}:{node_id}",
                eliminated_world_ids=eliminated,
            )
        )
    return tuple(rows)


def measurements_from_arrival_state(
    worlds: Sequence[FiniteBAMState],
    truth: FiniteBAMState,
    survivor_ids: Sequence[str],
) -> tuple[DiagnosticMeasurement, ...]:
    ordered = _ordered(worlds)
    by_id = {world.world_id: world for world in ordered}
    rows: list[DiagnosticMeasurement] = []
    for i, node_id in enumerate(truth.node_ids):
        truth_value = truth.tau[i]
        eliminated = frozenset(
            world_id
            for world_id in survivor_ids
            if by_id[world_id].tau[i] != truth_value
        )
        rows.append(
            DiagnosticMeasurement(
                measurement_id=f"tau:{node_id}",
                eliminated_world_ids=eliminated,
            )
        )
    return tuple(rows)
