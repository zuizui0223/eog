"""Exact finite-world reconstruction for the EOG development mainline.

This module does not fit a new movement model. It treats already-declared transition
operators as a finite admissible world universe and reuses EOG's existing first-passage
and occurrence-compatibility operators to ask which worlds remain compatible with an
observed positive occurrence configuration.

Because the declared world universe is finite and exhaustively enumerated, exclusion
claims can carry an explicit finite-universe certificate. They are never promoted to
universal ecological impossibility outside that declared universe. Unobserved nodes are
not treated as absences and compatible worlds are not collapsed into one historical
answer.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal, Sequence

import numpy as np

from ..dynamic_island_reachability import (
    DynamicReachabilityResult,
    DynamicTransitionOperator,
    propagate_dynamic_reachability,
    summarize_first_passage,
)
from .occurrence_constraints import (
    OccurrenceRuleCompatibility,
    evaluate_occurrence_rule_compatibility,
)


WorldNodeStatus = Literal["reachable_in_all", "contingent", "robustly_unreachable"]
CandidateStatus = Literal["discriminating", "non_discriminating", "unsupported_by_universe"]


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _finite_nonnegative(value: float, label: str) -> float:
    result = float(value)
    if not np.isfinite(result) or result < 0.0:
        raise ValueError(f"{label} must be finite and non-negative")
    return result


@dataclass(frozen=True)
class FiniteWorld:
    """One declared distribution-forming world in a finite admissible universe.

    Relaxation axes are separate declared monotone coordinates. They are not fitted
    biological constants and are not combined into an opaque weighted distance.
    """

    world_id: str
    operator: DynamicTransitionOperator
    source_ids: tuple[str, ...]
    source_weights: tuple[float, ...] | None = None
    geographic_relaxation: float = 0.0
    environmental_relaxation: float = 0.0
    barrier_relaxation: float = 0.0
    analytical_variant: str = "reference"

    def __post_init__(self) -> None:
        world_id = str(self.world_id).strip()
        if not world_id:
            raise ValueError("world_id must be non-empty")
        object.__setattr__(self, "world_id", world_id)

        declared_sources = tuple(str(value).strip() for value in self.source_ids)
        if (
            not declared_sources
            or any(not value for value in declared_sources)
            or len(set(declared_sources)) != len(declared_sources)
        ):
            raise ValueError("source_ids must contain unique non-empty node IDs")
        missing = set(declared_sources).difference(self.operator.node_ids)
        if missing:
            raise ValueError(f"source_ids are outside the operator node universe: {sorted(missing)}")

        if self.source_weights is None:
            declared_weights = np.full(
                len(declared_sources), 1.0 / len(declared_sources), dtype=float
            )
        else:
            declared_weights = np.asarray(self.source_weights, dtype=float)
            if declared_weights.shape != (len(declared_sources),):
                raise ValueError("source_weights must contain one value per declared source")
            if (
                not np.isfinite(declared_weights).all()
                or np.any(declared_weights < 0.0)
                or float(np.sum(declared_weights)) <= 0.0
            ):
                raise ValueError("source_weights must be finite, non-negative, and sum to > 0")
            declared_weights = declared_weights / np.sum(declared_weights)

        weight_by_source = dict(zip(declared_sources, declared_weights, strict=True))
        source_set = set(declared_sources)
        ordered_sources = tuple(
            node_id for node_id in self.operator.node_ids if node_id in source_set
        )
        ordered_weights = tuple(float(weight_by_source[node_id]) for node_id in ordered_sources)
        object.__setattr__(self, "source_ids", ordered_sources)
        object.__setattr__(self, "source_weights", ordered_weights)

        object.__setattr__(
            self,
            "geographic_relaxation",
            _finite_nonnegative(self.geographic_relaxation, "geographic_relaxation"),
        )
        object.__setattr__(
            self,
            "environmental_relaxation",
            _finite_nonnegative(self.environmental_relaxation, "environmental_relaxation"),
        )
        object.__setattr__(
            self,
            "barrier_relaxation",
            _finite_nonnegative(self.barrier_relaxation, "barrier_relaxation"),
        )
        variant = str(self.analytical_variant).strip()
        if not variant:
            raise ValueError("analytical_variant must be non-empty")
        object.__setattr__(self, "analytical_variant", variant)

    @property
    def source_weight_mapping(self) -> dict[str, float]:
        return dict(zip(self.source_ids, self.source_weights, strict=True))

    @property
    def fingerprint(self) -> str:
        return _canonical_sha256(
            {
                "world_id": self.world_id,
                "operator_fingerprint": self.operator.fingerprint,
                "source_ids": list(self.source_ids),
                "source_weights": list(self.source_weights),
                "geographic_relaxation": self.geographic_relaxation,
                "environmental_relaxation": self.environmental_relaxation,
                "barrier_relaxation": self.barrier_relaxation,
                "analytical_variant": self.analytical_variant,
            }
        )


@dataclass(frozen=True)
class WorldReachableConfiguration:
    """Positive-support forward envelope for one world, not realised occupancy."""

    world_id: str
    node_ids: tuple[str, ...]
    reachable_ids: tuple[str, ...]
    unreachable_ids: tuple[str, ...]
    first_passage_support: tuple[float, ...]
    max_steps: int
    support_tolerance: float
    world_fingerprint: str
    fingerprint: str


@dataclass(frozen=True)
class WorldCompatibility:
    world_id: str
    compatible: bool
    occurrence_result: OccurrenceRuleCompatibility
    world_fingerprint: str


@dataclass(frozen=True)
class FiniteWorldReconstruction:
    """Exact inverse image ``W(O)`` inside one frozen finite world universe."""

    occurrence_ids: tuple[str, ...]
    world_results: tuple[WorldCompatibility, ...]
    compatible_world_ids: tuple[str, ...]
    incompatible_world_ids: tuple[str, ...]
    world_fingerprints: tuple[tuple[str, str], ...]
    compatible_fraction: float
    identifiable: bool
    max_steps: int
    support_floor: float
    support_tolerance: float
    coverage_certificate: str
    fingerprint: str


@dataclass(frozen=True)
class WorldFlowMember:
    world_id: str
    result: DynamicReachabilityResult
    first_passage_support: np.ndarray
    world_fingerprint: str


@dataclass(frozen=True)
class WorldNodeEnvelope:
    node_id: str
    support_by_world: tuple[tuple[str, float], ...]
    lower_support: float
    upper_support: float
    status: WorldNodeStatus

    @property
    def possible(self) -> bool:
        """Whether at least one compatible world reaches this node."""

        return self.status != "robustly_unreachable"

    @property
    def robust(self) -> bool:
        """Whether every compatible world reaches this node."""

        return self.status == "reachable_in_all"

    @property
    def unresolved(self) -> bool:
        """Whether reachability depends on which compatible world is used."""

        return self.status == "contingent"

    @property
    def robustly_unreachable(self) -> bool:
        """Whether no world in the exhaustive compatible set reaches this node."""

        return self.status == "robustly_unreachable"


@dataclass(frozen=True)
class FiniteWorldFlowSet:
    """World-indexed flow set that retains the world-to-flow association."""

    node_ids: tuple[str, ...]
    members: tuple[WorldFlowMember, ...]
    node_envelopes: tuple[WorldNodeEnvelope, ...]
    mass_lower_envelope: np.ndarray
    mass_upper_envelope: np.ndarray
    robustly_unreachable_ids: tuple[str, ...]
    contingent_ids: tuple[str, ...]
    reachable_in_all_ids: tuple[str, ...]
    max_steps: int
    support_tolerance: float
    coverage_certificate: str
    reconstruction_fingerprint: str
    fingerprint: str

    @property
    def world_ids(self) -> tuple[str, ...]:
        return tuple(member.world_id for member in self.members)

    @property
    def world_fingerprints(self) -> tuple[tuple[str, str], ...]:
        return tuple((member.world_id, member.world_fingerprint) for member in self.members)

    @property
    def possible_ids(self) -> tuple[str, ...]:
        """Nodes reached in at least one compatible world (finite-set union)."""

        unreachable = set(self.robustly_unreachable_ids)
        return tuple(node_id for node_id in self.node_ids if node_id not in unreachable)

    @property
    def robust_ids(self) -> tuple[str, ...]:
        """Nodes reached in every compatible world (finite-set intersection)."""

        return self.reachable_in_all_ids

    @property
    def unresolved_ids(self) -> tuple[str, ...]:
        """Possible but non-robust nodes whose reachability is world-dependent."""

        return self.contingent_ids


@dataclass(frozen=True)
class WorldFlowUniverseUpdate:
    """Exact set changes after a fingerprint-preserving world-universe expansion."""

    before_world_ids: tuple[str, ...]
    after_world_ids: tuple[str, ...]
    added_world_ids: tuple[str, ...]
    lost_robust_ids: tuple[str, ...]
    gained_possible_ids: tuple[str, ...]
    lost_robustly_unreachable_ids: tuple[str, ...]
    shared_world_results_identical: bool
    possible_monotonicity_holds: bool
    robust_monotonicity_holds: bool
    exclusion_monotonicity_holds: bool
    monotonicity_holds: bool
    before_fingerprint: str
    after_fingerprint: str
    coverage_certificate: str
    fingerprint: str


@dataclass(frozen=True)
class RelaxationPoint:
    world_id: str
    geographic_relaxation: float
    environmental_relaxation: float
    barrier_relaxation: float
    analytical_variant: str


@dataclass(frozen=True)
class RelaxationFrontier:
    """Non-dominated compatible relaxations with IBD/IBE/barrier axes preserved."""

    points: tuple[RelaxationPoint, ...]
    compatible_world_ids: tuple[str, ...]
    reconstruction_fingerprint: str
    fingerprint: str


@dataclass(frozen=True)
class ReconstructionUpdate:
    before_occurrence_ids: tuple[str, ...]
    after_occurrence_ids: tuple[str, ...]
    retained_world_ids: tuple[str, ...]
    eliminated_world_ids: tuple[str, ...]
    contraction_fraction: float
    became_identifiable: bool
    before_fingerprint: str
    after_fingerprint: str
    fingerprint: str


@dataclass(frozen=True)
class PositiveOccurrenceCandidate:
    candidate_id: str
    reachable_world_ids: tuple[str, ...]
    unreachable_world_ids: tuple[str, ...]
    positive_elimination_fraction: float
    split_balance: float
    status: CandidateStatus


@dataclass(frozen=True)
class PositiveOccurrenceSurveyRanking:
    """Positive-occurrence discrimination only; non-detections are not inferred."""

    rows: tuple[PositiveOccurrenceCandidate, ...]
    compatible_world_ids: tuple[str, ...]
    reconstruction_fingerprint: str
    fingerprint: str


def _ordered_worlds(worlds: Sequence[FiniteWorld]) -> tuple[FiniteWorld, ...]:
    declared = tuple(worlds)
    if not declared:
        raise ValueError("at least one finite world is required")
    ids = [world.world_id for world in declared]
    if len(set(ids)) != len(ids):
        raise ValueError("world IDs must be unique")
    ordered = tuple(sorted(declared, key=lambda world: world.world_id))
    node_ids = ordered[0].operator.node_ids
    if any(world.operator.node_ids != node_ids for world in ordered[1:]):
        raise ValueError("all finite worlds must share the same node IDs and order")
    return ordered


def _ordered_occurrences(
    node_ids: tuple[str, ...], occurrence_ids: Sequence[str]
) -> tuple[str, ...]:
    requested = tuple(str(value).strip() for value in occurrence_ids)
    if (
        len(requested) < 2
        or any(not value for value in requested)
        or len(set(requested)) != len(requested)
    ):
        raise ValueError("occurrence_ids must contain at least two unique non-empty node IDs")
    missing = set(requested).difference(node_ids)
    if missing:
        raise ValueError(f"occurrence_ids are outside the world node universe: {sorted(missing)}")
    requested_set = set(requested)
    return tuple(node_id for node_id in node_ids if node_id in requested_set)


def _validate_world_universe(
    reconstruction: FiniteWorldReconstruction,
    ordered_worlds: tuple[FiniteWorld, ...],
) -> None:
    current = tuple((world.world_id, world.fingerprint) for world in ordered_worlds)
    if current != reconstruction.world_fingerprints:
        raise ValueError("world universe or world definitions changed after reconstruction")


def _flow_member_fingerprint(member: WorldFlowMember) -> str:
    return _canonical_sha256(
        {
            "world_id": member.world_id,
            "world_fingerprint": member.world_fingerprint,
            "operator_fingerprint": member.result.operator_fingerprint,
            "mass_by_step": member.result.mass_by_step.tolist(),
            "first_passage_support": member.first_passage_support.tolist(),
        }
    )


def _first_passage_vector(
    world: FiniteWorld,
    *,
    max_steps: int,
    support_tolerance: float,
) -> np.ndarray:
    support = np.zeros(len(world.operator.node_ids), dtype=float)
    source_set = set(world.source_ids)
    for index, node_id in enumerate(world.operator.node_ids):
        if node_id in source_set:
            support[index] = 1.0
            continue
        support[index] = summarize_first_passage(
            world.operator,
            world.source_ids,
            node_id,
            max_steps=max_steps,
            support_tolerance=support_tolerance,
        ).horizon_support
    return support


def _candidate_support(
    world: FiniteWorld,
    candidate_id: str,
    reconstruction: FiniteWorldReconstruction,
) -> float:
    if candidate_id in set(world.source_ids):
        return 1.0
    return float(
        summarize_first_passage(
            world.operator,
            world.source_ids,
            candidate_id,
            max_steps=reconstruction.max_steps,
            support_tolerance=reconstruction.support_tolerance,
        ).horizon_support
    )


def forward_reachable_configuration(
    world: FiniteWorld,
    *,
    max_steps: int,
    support_tolerance: float = 1e-15,
) -> WorldReachableConfiguration:
    """Return the exact positive-support reachability envelope for one world."""

    if isinstance(max_steps, bool) or not isinstance(max_steps, (int, np.integer)) or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")
    tolerance = _finite_nonnegative(support_tolerance, "support_tolerance")
    support = _first_passage_vector(world, max_steps=max_steps, support_tolerance=tolerance)
    reachable = tuple(
        node_id
        for node_id, value in zip(world.operator.node_ids, support, strict=True)
        if value > tolerance
    )
    reachable_set = set(reachable)
    unreachable = tuple(
        node_id for node_id in world.operator.node_ids if node_id not in reachable_set
    )
    payload = {
        "world_fingerprint": world.fingerprint,
        "reachable_ids": list(reachable),
        "unreachable_ids": list(unreachable),
        "first_passage_support": support.tolist(),
        "max_steps": int(max_steps),
        "support_tolerance": tolerance,
    }
    return WorldReachableConfiguration(
        world_id=world.world_id,
        node_ids=world.operator.node_ids,
        reachable_ids=reachable,
        unreachable_ids=unreachable,
        first_passage_support=tuple(float(value) for value in support),
        max_steps=int(max_steps),
        support_tolerance=tolerance,
        world_fingerprint=world.fingerprint,
        fingerprint=_canonical_sha256(payload),
    )


def reconstruct_compatible_worlds(
    worlds: Sequence[FiniteWorld],
    occurrence_ids: Sequence[str],
    *,
    max_steps: int,
    support_floor: float = 1e-12,
    support_tolerance: float = 1e-15,
) -> FiniteWorldReconstruction:
    """Enumerate the exact finite inverse image ``W(O)`` for positive occurrences.

    In this first finite core, each world's declared fixed sources must themselves be
    observed occurrences. A world is compatible when every other observed occurrence
    has positive first-passage support above ``support_tolerance``. Compatible worlds
    remain an unranked set.
    """

    ordered = _ordered_worlds(worlds)
    occurrences = _ordered_occurrences(ordered[0].operator.node_ids, occurrence_ids)
    occurrence_set = set(occurrences)
    for world in ordered:
        if not set(world.source_ids).issubset(occurrence_set):
            raise ValueError(
                f"world {world.world_id!r} declares sources outside occurrence_ids; "
                "the first finite reconstruction core requires observed fixed sources"
            )

    results: list[WorldCompatibility] = []
    for world in ordered:
        occurrence_result = evaluate_occurrence_rule_compatibility(
            world.operator,
            occurrences,
            rule_id=world.world_id,
            max_steps=max_steps,
            fixed_source_ids=world.source_ids,
            support_floor=support_floor,
            support_tolerance=support_tolerance,
        )
        results.append(
            WorldCompatibility(
                world_id=world.world_id,
                compatible=not occurrence_result.unsupported_occurrence_ids,
                occurrence_result=occurrence_result,
                world_fingerprint=world.fingerprint,
            )
        )

    compatible = tuple(result.world_id for result in results if result.compatible)
    incompatible = tuple(result.world_id for result in results if not result.compatible)
    certificate = "exhaustive_finite_world_enumeration"
    payload = {
        "occurrence_ids": list(occurrences),
        "world_results": [
            {
                "world_id": result.world_id,
                "world_fingerprint": result.world_fingerprint,
                "occurrence_fingerprint": result.occurrence_result.fingerprint,
                "compatible": result.compatible,
            }
            for result in results
        ],
        "max_steps": int(max_steps),
        "support_floor": float(support_floor),
        "support_tolerance": float(support_tolerance),
        "coverage_certificate": certificate,
    }
    return FiniteWorldReconstruction(
        occurrence_ids=occurrences,
        world_results=tuple(results),
        compatible_world_ids=compatible,
        incompatible_world_ids=incompatible,
        world_fingerprints=tuple((world.world_id, world.fingerprint) for world in ordered),
        compatible_fraction=float(len(compatible) / len(ordered)),
        identifiable=len(compatible) == 1,
        max_steps=int(max_steps),
        support_floor=float(support_floor),
        support_tolerance=float(support_tolerance),
        coverage_certificate=certificate,
        fingerprint=_canonical_sha256(payload),
    )


def build_world_flow_set(
    reconstruction: FiniteWorldReconstruction,
    worlds: Sequence[FiniteWorld],
) -> FiniteWorldFlowSet:
    """Propagate and retain one flow trajectory per compatible finite world."""

    ordered = _ordered_worlds(worlds)
    _validate_world_universe(reconstruction, ordered)
    if not reconstruction.compatible_world_ids:
        raise ValueError("cannot build a flow set when no world is compatible")

    world_by_id = {world.world_id: world for world in ordered}
    members: list[WorldFlowMember] = []
    for world_id in reconstruction.compatible_world_ids:
        world = world_by_id[world_id]
        result = propagate_dynamic_reachability(
            world.operator,
            world.source_weight_mapping,
            max_steps=reconstruction.max_steps,
        )
        members.append(
            WorldFlowMember(
                world_id=world_id,
                result=result,
                first_passage_support=_first_passage_vector(
                    world,
                    max_steps=reconstruction.max_steps,
                    support_tolerance=reconstruction.support_tolerance,
                ),
                world_fingerprint=world.fingerprint,
            )
        )

    mass_stack = np.stack([member.result.mass_by_step for member in members], axis=0)
    mass_lower = np.min(mass_stack, axis=0)
    mass_upper = np.max(mass_stack, axis=0)

    envelopes: list[WorldNodeEnvelope] = []
    for node_index, node_id in enumerate(ordered[0].operator.node_ids):
        supports = tuple(
            (member.world_id, float(member.first_passage_support[node_index]))
            for member in members
        )
        values = np.asarray([value for _, value in supports], dtype=float)
        positive = values > reconstruction.support_tolerance
        if not np.any(positive):
            status: WorldNodeStatus = "robustly_unreachable"
        elif np.all(positive):
            status = "reachable_in_all"
        else:
            status = "contingent"
        envelopes.append(
            WorldNodeEnvelope(
                node_id=node_id,
                support_by_world=supports,
                lower_support=float(np.min(values)),
                upper_support=float(np.max(values)),
                status=status,
            )
        )

    robust = tuple(row.node_id for row in envelopes if row.status == "robustly_unreachable")
    contingent = tuple(row.node_id for row in envelopes if row.status == "contingent")
    universal = tuple(row.node_id for row in envelopes if row.status == "reachable_in_all")
    certificate = "exhaustive_finite_compatible_world_set"
    payload = {
        "reconstruction_fingerprint": reconstruction.fingerprint,
        "members": [
            {
                "world_id": member.world_id,
                "world_fingerprint": member.world_fingerprint,
                "operator_fingerprint": member.result.operator_fingerprint,
                "mass_by_step": member.result.mass_by_step.tolist(),
                "first_passage_support": member.first_passage_support.tolist(),
            }
            for member in members
        ],
        "node_envelopes": [
            {
                "node_id": row.node_id,
                "support_by_world": list(row.support_by_world),
                "status": row.status,
            }
            for row in envelopes
        ],
        "possible_ids": [
            row.node_id for row in envelopes if row.status != "robustly_unreachable"
        ],
        "robust_ids": [row.node_id for row in envelopes if row.status == "reachable_in_all"],
        "unresolved_ids": [row.node_id for row in envelopes if row.status == "contingent"],
        "robustly_unreachable_ids": list(robust),
        "support_tolerance": reconstruction.support_tolerance,
        "coverage_certificate": certificate,
    }
    return FiniteWorldFlowSet(
        node_ids=ordered[0].operator.node_ids,
        members=tuple(members),
        node_envelopes=tuple(envelopes),
        mass_lower_envelope=mass_lower,
        mass_upper_envelope=mass_upper,
        robustly_unreachable_ids=robust,
        contingent_ids=contingent,
        reachable_in_all_ids=universal,
        max_steps=reconstruction.max_steps,
        support_tolerance=reconstruction.support_tolerance,
        coverage_certificate=certificate,
        reconstruction_fingerprint=reconstruction.fingerprint,
        fingerprint=_canonical_sha256(payload),
    )


def compare_world_flow_universes(
    before: FiniteWorldFlowSet,
    after: FiniteWorldFlowSet,
) -> WorldFlowUniverseUpdate:
    """Audit exact reachability monotonicity for nested compatible-world sets.

    The shared worlds must retain identical definitions and results. Adding worlds may
    expand possible reachability, contract robust reachability, and contract the set
    that is unreachable in every compatible world. ``unresolved`` is deliberately not
    monotone: a node may enter or leave disagreement as worlds are added.
    """

    if before.node_ids != after.node_ids:
        raise ValueError("world flow sets must share identical node IDs and order")
    if before.max_steps != after.max_steps:
        raise ValueError("world flow sets must share max_steps")
    if before.support_tolerance != after.support_tolerance:
        raise ValueError("world flow sets must share support_tolerance")

    before_members = {
        member.world_id: _flow_member_fingerprint(member) for member in before.members
    }
    after_members = {
        member.world_id: _flow_member_fingerprint(member) for member in after.members
    }
    if not set(before_members).issubset(after_members):
        raise ValueError("before compatible-world universe must be a subset of after")
    shared_identical = all(
        after_members[world_id] == fingerprint
        for world_id, fingerprint in before_members.items()
    )
    if not shared_identical:
        raise ValueError("shared world IDs must preserve identical fingerprints and results")

    before_possible = set(before.possible_ids)
    after_possible = set(after.possible_ids)
    before_robust = set(before.robust_ids)
    after_robust = set(after.robust_ids)
    before_unreachable = set(before.robustly_unreachable_ids)
    after_unreachable = set(after.robustly_unreachable_ids)

    possible_ok = before_possible.issubset(after_possible)
    robust_ok = after_robust.issubset(before_robust)
    exclusion_ok = after_unreachable.issubset(before_unreachable)
    if not (possible_ok and robust_ok and exclusion_ok):
        raise RuntimeError("world-universe expansion violated exact reachability monotonicity")

    added_world_ids = tuple(
        world_id for world_id in after.world_ids if world_id not in before_members
    )
    lost_robust_ids = tuple(
        node_id for node_id in before.node_ids if node_id in before_robust - after_robust
    )
    gained_possible_ids = tuple(
        node_id for node_id in before.node_ids if node_id in after_possible - before_possible
    )
    lost_unreachable_ids = tuple(
        node_id
        for node_id in before.node_ids
        if node_id in before_unreachable - after_unreachable
    )
    certificate = "exact_nested_finite_compatible_world_sets"
    payload = {
        "before_fingerprint": before.fingerprint,
        "after_fingerprint": after.fingerprint,
        "added_world_ids": list(added_world_ids),
        "lost_robust_ids": list(lost_robust_ids),
        "gained_possible_ids": list(gained_possible_ids),
        "lost_robustly_unreachable_ids": list(lost_unreachable_ids),
        "coverage_certificate": certificate,
    }
    return WorldFlowUniverseUpdate(
        before_world_ids=before.world_ids,
        after_world_ids=after.world_ids,
        added_world_ids=added_world_ids,
        lost_robust_ids=lost_robust_ids,
        gained_possible_ids=gained_possible_ids,
        lost_robustly_unreachable_ids=lost_unreachable_ids,
        shared_world_results_identical=shared_identical,
        possible_monotonicity_holds=possible_ok,
        robust_monotonicity_holds=robust_ok,
        exclusion_monotonicity_holds=exclusion_ok,
        monotonicity_holds=(
            shared_identical and possible_ok and robust_ok and exclusion_ok
        ),
        before_fingerprint=before.fingerprint,
        after_fingerprint=after.fingerprint,
        coverage_certificate=certificate,
        fingerprint=_canonical_sha256(payload),
    )


def minimum_relaxation_frontier(
    reconstruction: FiniteWorldReconstruction,
    worlds: Sequence[FiniteWorld],
) -> RelaxationFrontier:
    """Return non-dominated compatible relaxations without collapsing IBD and IBE.

    A scalar 'water level' is deliberately not manufactured here. If a one-dimensional
    relaxation sequence is scientifically justified, callers should declare that family
    explicitly before projecting this axis-preserving frontier onto it.
    """

    ordered = _ordered_worlds(worlds)
    _validate_world_universe(reconstruction, ordered)
    world_by_id = {world.world_id: world for world in ordered}
    points = [
        RelaxationPoint(
            world_id=world_id,
            geographic_relaxation=world_by_id[world_id].geographic_relaxation,
            environmental_relaxation=world_by_id[world_id].environmental_relaxation,
            barrier_relaxation=world_by_id[world_id].barrier_relaxation,
            analytical_variant=world_by_id[world_id].analytical_variant,
        )
        for world_id in reconstruction.compatible_world_ids
    ]

    frontier: list[RelaxationPoint] = []
    for point in points:
        dominated = False
        for other in points:
            if other.world_id == point.world_id:
                continue
            no_worse = (
                other.geographic_relaxation <= point.geographic_relaxation
                and other.environmental_relaxation <= point.environmental_relaxation
                and other.barrier_relaxation <= point.barrier_relaxation
            )
            strictly_better = (
                other.geographic_relaxation < point.geographic_relaxation
                or other.environmental_relaxation < point.environmental_relaxation
                or other.barrier_relaxation < point.barrier_relaxation
            )
            if no_worse and strictly_better:
                dominated = True
                break
        if not dominated:
            frontier.append(point)

    frontier.sort(
        key=lambda row: (
            row.geographic_relaxation,
            row.environmental_relaxation,
            row.barrier_relaxation,
            row.world_id,
        )
    )
    payload = {
        "reconstruction_fingerprint": reconstruction.fingerprint,
        "points": [
            {
                "world_id": row.world_id,
                "geographic_relaxation": row.geographic_relaxation,
                "environmental_relaxation": row.environmental_relaxation,
                "barrier_relaxation": row.barrier_relaxation,
                "analytical_variant": row.analytical_variant,
            }
            for row in frontier
        ],
    }
    return RelaxationFrontier(
        points=tuple(frontier),
        compatible_world_ids=reconstruction.compatible_world_ids,
        reconstruction_fingerprint=reconstruction.fingerprint,
        fingerprint=_canonical_sha256(payload),
    )


def compare_reconstructions(
    before: FiniteWorldReconstruction,
    after: FiniteWorldReconstruction,
) -> ReconstructionUpdate:
    """Quantify compatible-world contraction after added positive occurrence evidence."""

    if before.world_fingerprints != after.world_fingerprints:
        raise ValueError("reconstructions must use the same frozen world universe")
    if (
        before.max_steps != after.max_steps
        or before.support_floor != after.support_floor
        or before.support_tolerance != after.support_tolerance
    ):
        raise ValueError("reconstructions must use the same reachability contract")
    if not set(before.occurrence_ids).issubset(after.occurrence_ids):
        raise ValueError("after occurrence set must contain the before occurrence set")

    before_set = set(before.compatible_world_ids)
    after_set = set(after.compatible_world_ids)
    newly_compatible = after_set.difference(before_set)
    if newly_compatible:
        raise RuntimeError("adding positive occurrence constraints cannot create newly compatible worlds")
    retained = tuple(world_id for world_id in before.compatible_world_ids if world_id in after_set)
    eliminated = tuple(world_id for world_id in before.compatible_world_ids if world_id not in after_set)
    contraction = 0.0 if not before_set else float(len(eliminated) / len(before_set))
    payload = {
        "before": before.fingerprint,
        "after": after.fingerprint,
        "retained": list(retained),
        "eliminated": list(eliminated),
        "contraction_fraction": contraction,
    }
    return ReconstructionUpdate(
        before_occurrence_ids=before.occurrence_ids,
        after_occurrence_ids=after.occurrence_ids,
        retained_world_ids=retained,
        eliminated_world_ids=eliminated,
        contraction_fraction=contraction,
        became_identifiable=(not before.identifiable and after.identifiable),
        before_fingerprint=before.fingerprint,
        after_fingerprint=after.fingerprint,
        fingerprint=_canonical_sha256(payload),
    )


def rank_positive_occurrence_candidates(
    reconstruction: FiniteWorldReconstruction,
    worlds: Sequence[FiniteWorld],
    candidate_ids: Sequence[str],
) -> PositiveOccurrenceSurveyRanking:
    """Rank nodes by how a *positive occurrence* would split compatible worlds.

    This is not expected information gain and it does not score non-detections. A node
    unreachable in every compatible world is ``unsupported_by_universe``: observing it
    would challenge the declared finite universe rather than select one of its members.
    """

    ordered = _ordered_worlds(worlds)
    _validate_world_universe(reconstruction, ordered)
    if not reconstruction.compatible_world_ids:
        raise ValueError("candidate discrimination requires at least one compatible world")

    candidates = tuple(str(value).strip() for value in candidate_ids)
    if (
        not candidates
        or any(not value for value in candidates)
        or len(set(candidates)) != len(candidates)
    ):
        raise ValueError("candidate_ids must contain unique non-empty node IDs")
    node_set = set(ordered[0].operator.node_ids)
    missing = set(candidates).difference(node_set)
    if missing:
        raise ValueError(f"candidate_ids are outside the world node universe: {sorted(missing)}")
    overlap = set(candidates).intersection(reconstruction.occurrence_ids)
    if overlap:
        raise ValueError(f"candidate_ids already contain observed occurrences: {sorted(overlap)}")

    world_by_id = {world.world_id: world for world in ordered}
    rows: list[PositiveOccurrenceCandidate] = []
    total = len(reconstruction.compatible_world_ids)
    for candidate_id in candidates:
        reachable: list[str] = []
        unreachable: list[str] = []
        for world_id in reconstruction.compatible_world_ids:
            support = _candidate_support(world_by_id[world_id], candidate_id, reconstruction)
            if support > reconstruction.support_tolerance:
                reachable.append(world_id)
            else:
                unreachable.append(world_id)

        if not reachable:
            status: CandidateStatus = "unsupported_by_universe"
        elif not unreachable:
            status = "non_discriminating"
        else:
            status = "discriminating"
        rows.append(
            PositiveOccurrenceCandidate(
                candidate_id=candidate_id,
                reachable_world_ids=tuple(reachable),
                unreachable_world_ids=tuple(unreachable),
                positive_elimination_fraction=float(len(unreachable) / total),
                split_balance=float(min(len(reachable), len(unreachable)) / total),
                status=status,
            )
        )

    priority = {"discriminating": 0, "unsupported_by_universe": 1, "non_discriminating": 2}
    rows.sort(
        key=lambda row: (
            priority[row.status],
            -row.positive_elimination_fraction,
            -row.split_balance,
            row.candidate_id,
        )
    )
    payload = {
        "reconstruction_fingerprint": reconstruction.fingerprint,
        "rows": [
            {
                "candidate_id": row.candidate_id,
                "reachable_world_ids": list(row.reachable_world_ids),
                "unreachable_world_ids": list(row.unreachable_world_ids),
                "positive_elimination_fraction": row.positive_elimination_fraction,
                "split_balance": row.split_balance,
                "status": row.status,
            }
            for row in rows
        ],
    }
    return PositiveOccurrenceSurveyRanking(
        rows=tuple(rows),
        compatible_world_ids=reconstruction.compatible_world_ids,
        reconstruction_fingerprint=reconstruction.fingerprint,
        fingerprint=_canonical_sha256(payload),
    )
