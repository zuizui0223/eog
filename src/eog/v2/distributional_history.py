"""Occurrence-to-occurrence relation summaries over compatible EOG worlds.

This is a synthesis layer over finite-world reconstruction and dynamic first-passage
operators. It introduces no new ecological transition rule.

For every ordered pair of observed occurrences, it asks whether the target is reachable
from the source in all, some, or none of the compatible worlds, and whether earliest
positive propagation depth is fixed or varies across worlds.

These are assumption-conditioned structural possibilities, not claims of observed
migration, ancestry, a unique colonisation route, calibrated time, or historical truth.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal, Sequence

import numpy as np

from ..dynamic_island_reachability import summarize_first_passage
from .world_reconstruction import FiniteWorld, FiniteWorldReconstruction


OccurrenceRelationStatus = Literal[
    "reachable_in_all",
    "contingent",
    "robustly_unreachable",
]
ArrivalDepthStatus = Literal["fixed", "variable", "partial", "undefined"]


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class OccurrencePairRelation:
    source_id: str
    target_id: str
    support_by_world: tuple[tuple[str, float], ...]
    first_arrival_step_by_world: tuple[tuple[str, int | None], ...]
    lower_support: float
    upper_support: float
    supporting_world_count: int
    compatible_world_count: int
    reachability_status: OccurrenceRelationStatus
    arrival_depth_status: ArrivalDepthStatus
    possible_first_arrival_steps: tuple[int, ...]
    fixed_first_arrival_step: int | None

    @property
    def robust_reachable(self) -> bool:
        return self.reachability_status == "reachable_in_all"

    @property
    def contingent(self) -> bool:
        return self.reachability_status == "contingent"

    @property
    def robustly_unreachable(self) -> bool:
        return self.reachability_status == "robustly_unreachable"

    @property
    def arrival_depth_unresolved(self) -> bool:
        return self.arrival_depth_status in {"variable", "partial"}


@dataclass(frozen=True)
class OccurrenceRelationGraph:
    occurrence_ids: tuple[str, ...]
    relations: tuple[OccurrencePairRelation, ...]
    compatible_world_ids: tuple[str, ...]
    robust_relation_count: int
    contingent_relation_count: int
    robustly_unreachable_relation_count: int
    arrival_depth_unresolved_relation_count: int
    max_steps: int
    support_tolerance: float
    coverage_certificate: str
    reconstruction_fingerprint: str
    fingerprint: str

    def relation(self, source_id: str, target_id: str) -> OccurrencePairRelation:
        source = str(source_id)
        target = str(target_id)
        matches = tuple(
            row
            for row in self.relations
            if row.source_id == source and row.target_id == target
        )
        if len(matches) != 1:
            raise KeyError(f"no unique occurrence relation {source!r}->{target!r}")
        return matches[0]


def _ordered_worlds(
    reconstruction: FiniteWorldReconstruction,
    worlds: Sequence[FiniteWorld],
) -> tuple[FiniteWorld, ...]:
    declared = tuple(sorted(tuple(worlds), key=lambda world: world.world_id))
    if not declared:
        raise ValueError("at least one finite world is required")
    if len({world.world_id for world in declared}) != len(declared):
        raise ValueError("world IDs must be unique")
    node_ids = declared[0].operator.node_ids
    if any(world.operator.node_ids != node_ids for world in declared[1:]):
        raise ValueError("all worlds must share node IDs and order")
    fingerprints = tuple((world.world_id, world.fingerprint) for world in declared)
    if fingerprints != reconstruction.world_fingerprints:
        raise ValueError(
            "world universe or world definitions changed after reconstruction"
        )
    return declared


def _ordered_occurrences(
    reconstruction: FiniteWorldReconstruction,
    node_ids: tuple[str, ...],
    occurrence_ids: Sequence[str] | None,
) -> tuple[str, ...]:
    if occurrence_ids is None:
        requested = reconstruction.occurrence_ids
    else:
        requested = tuple(str(value).strip() for value in occurrence_ids)
        if (
            len(requested) < 2
            or any(not value for value in requested)
            or len(set(requested)) != len(requested)
        ):
            raise ValueError(
                "occurrence_ids must contain at least two unique non-empty IDs"
            )
        if not set(requested).issubset(reconstruction.occurrence_ids):
            raise ValueError(
                "occurrence relation graph may only use occurrences already "
                "conditioned into the reconstruction"
            )
    requested_set = set(requested)
    return tuple(node_id for node_id in node_ids if node_id in requested_set)


def summarize_occurrence_relations(
    reconstruction: FiniteWorldReconstruction,
    worlds: Sequence[FiniteWorld],
    *,
    occurrence_ids: Sequence[str] | None = None,
) -> OccurrenceRelationGraph:
    """Summarize directed occurrence relations across all compatible worlds."""

    ordered = _ordered_worlds(reconstruction, worlds)
    if not reconstruction.compatible_world_ids:
        raise ValueError(
            "cannot summarize occurrence relations when no world is compatible"
        )
    occurrences = _ordered_occurrences(
        reconstruction,
        ordered[0].operator.node_ids,
        occurrence_ids,
    )
    world_by_id = {world.world_id: world for world in ordered}

    rows: list[OccurrencePairRelation] = []
    for source_id in occurrences:
        for target_id in occurrences:
            if source_id == target_id:
                continue

            supports: list[tuple[str, float]] = []
            arrivals: list[tuple[str, int | None]] = []
            for world_id in reconstruction.compatible_world_ids:
                world = world_by_id[world_id]
                summary = summarize_first_passage(
                    world.operator,
                    (source_id,),
                    target_id,
                    max_steps=reconstruction.max_steps,
                    support_tolerance=reconstruction.support_tolerance,
                )
                supports.append((world_id, float(summary.horizon_support)))
                arrivals.append(
                    (
                        world_id,
                        None
                        if summary.first_positive_step is None
                        else int(summary.first_positive_step),
                    )
                )

            values = np.asarray([value for _, value in supports], dtype=float)
            positive = values > reconstruction.support_tolerance
            supporting_count = int(np.sum(positive))
            world_count = len(supports)

            if supporting_count == 0:
                relation_status: OccurrenceRelationStatus = "robustly_unreachable"
            elif supporting_count == world_count:
                relation_status = "reachable_in_all"
            else:
                relation_status = "contingent"

            positive_steps = tuple(
                sorted(
                    {
                        int(step)
                        for (_, step), is_positive in zip(
                            arrivals,
                            positive,
                            strict=True,
                        )
                        if is_positive and step is not None
                    }
                )
            )
            if supporting_count == 0:
                arrival_status: ArrivalDepthStatus = "undefined"
                fixed_step = None
            elif supporting_count < world_count:
                arrival_status = "partial"
                fixed_step = None
            elif len(positive_steps) == 1:
                arrival_status = "fixed"
                fixed_step = positive_steps[0]
            else:
                arrival_status = "variable"
                fixed_step = None

            rows.append(
                OccurrencePairRelation(
                    source_id=source_id,
                    target_id=target_id,
                    support_by_world=tuple(supports),
                    first_arrival_step_by_world=tuple(arrivals),
                    lower_support=float(np.min(values)),
                    upper_support=float(np.max(values)),
                    supporting_world_count=supporting_count,
                    compatible_world_count=world_count,
                    reachability_status=relation_status,
                    arrival_depth_status=arrival_status,
                    possible_first_arrival_steps=positive_steps,
                    fixed_first_arrival_step=fixed_step,
                )
            )

    certificate = "exhaustive_compatible_world_occurrence_pair_first_passage"
    payload = {
        "occurrence_ids": list(occurrences),
        "compatible_world_ids": list(reconstruction.compatible_world_ids),
        "relations": [
            {
                "source_id": row.source_id,
                "target_id": row.target_id,
                "support_by_world": [list(item) for item in row.support_by_world],
                "first_arrival_step_by_world": [
                    [world_id, step]
                    for world_id, step in row.first_arrival_step_by_world
                ],
                "reachability_status": row.reachability_status,
                "arrival_depth_status": row.arrival_depth_status,
                "possible_first_arrival_steps": list(
                    row.possible_first_arrival_steps
                ),
            }
            for row in rows
        ],
        "max_steps": reconstruction.max_steps,
        "support_tolerance": reconstruction.support_tolerance,
        "coverage_certificate": certificate,
        "reconstruction_fingerprint": reconstruction.fingerprint,
    }
    return OccurrenceRelationGraph(
        occurrence_ids=occurrences,
        relations=tuple(rows),
        compatible_world_ids=reconstruction.compatible_world_ids,
        robust_relation_count=sum(
            row.reachability_status == "reachable_in_all" for row in rows
        ),
        contingent_relation_count=sum(
            row.reachability_status == "contingent" for row in rows
        ),
        robustly_unreachable_relation_count=sum(
            row.reachability_status == "robustly_unreachable" for row in rows
        ),
        arrival_depth_unresolved_relation_count=sum(
            row.arrival_depth_unresolved for row in rows
        ),
        max_steps=reconstruction.max_steps,
        support_tolerance=reconstruction.support_tolerance,
        coverage_certificate=certificate,
        reconstruction_fingerprint=reconstruction.fingerprint,
        fingerprint=_canonical_sha256(payload),
    )
