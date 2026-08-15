"""Axis-preserving minimum relaxation for time-constrained finite EOG worlds.

This module answers one deliberately narrow inverse question that is not covered by the
static relaxation frontier: once time-stamped positive occurrences have filtered a
frozen temporal-world universe, which declared geographic, environmental, and barrier
relaxations are Pareto-minimal among the temporal worlds that still satisfy the
observations?

Relaxation coordinates are declared separately from :class:`TemporalWorld` so adding
this diagnostic does not rewrite temporal-world fingerprints or imply that relaxation
metadata are intrinsic movement parameters. The declaration must cover the complete
frozen temporal-world universe, including worlds that become incompatible, which keeps
axis assignment auditable rather than attaching coordinates only after seeing which
worlds survive.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Sequence

from .temporal_reconstruction import TemporalWorldReconstruction
from .world_reconstruction import RelaxationPoint


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
    if not math.isfinite(result) or result < 0.0:
        raise ValueError(f"{label} must be finite and non-negative")
    return result


@dataclass(frozen=True)
class TemporalRelaxationDeclaration:
    """Declared relaxation coordinates for one already-frozen temporal world.

    The three ecological axes remain separate. ``analytical_variant`` is an identity
    label, not an additional numeric weight and not part of Pareto dominance.
    """

    world_id: str
    geographic_relaxation: float = 0.0
    environmental_relaxation: float = 0.0
    barrier_relaxation: float = 0.0
    analytical_variant: str = "reference"

    def __post_init__(self) -> None:
        world_id = str(self.world_id).strip()
        if not world_id:
            raise ValueError("world_id must be non-empty")
        object.__setattr__(self, "world_id", world_id)
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


@dataclass(frozen=True)
class TemporalRelaxationFrontier:
    """Pareto-minimal relaxation explanations after temporal reconstruction."""

    points: tuple[RelaxationPoint, ...]
    compatible_world_ids: tuple[str, ...]
    declared_world_ids: tuple[str, ...]
    reconstruction_fingerprint: str
    coverage_certificate: str
    fingerprint: str


def minimum_temporal_relaxation_frontier(
    reconstruction: TemporalWorldReconstruction,
    declarations: Sequence[TemporalRelaxationDeclaration],
) -> TemporalRelaxationFrontier:
    """Return non-dominated relaxations among temporally compatible worlds.

    The declaration must cover the complete frozen world universe recorded by
    ``reconstruction``. This function does not infer the coordinates, fit weights, or
    scalarize IBD/geographic, IBE/environmental, and barrier relaxation into one score.
    A world can be removed by temporal evidence before Pareto dominance is evaluated,
    so earlier occurrence timing can legitimately change the minimum required
    relaxation frontier.
    """

    declared = tuple(declarations)
    if not declared:
        raise ValueError("at least one temporal relaxation declaration is required")
    ids = tuple(row.world_id for row in declared)
    if len(set(ids)) != len(ids):
        raise ValueError("temporal relaxation declarations must have unique world IDs")

    frozen_world_ids = tuple(world_id for world_id, _ in reconstruction.world_fingerprints)
    frozen_set = set(frozen_world_ids)
    declared_set = set(ids)
    if declared_set != frozen_set:
        missing = sorted(frozen_set.difference(declared_set))
        extra = sorted(declared_set.difference(frozen_set))
        raise ValueError(
            "temporal relaxation declarations must exactly cover the frozen world universe; "
            f"missing={missing}, extra={extra}"
        )

    by_id = {row.world_id: row for row in declared}
    ordered_declarations = tuple(by_id[world_id] for world_id in frozen_world_ids)
    points = [
        RelaxationPoint(
            world_id=world_id,
            geographic_relaxation=by_id[world_id].geographic_relaxation,
            environmental_relaxation=by_id[world_id].environmental_relaxation,
            barrier_relaxation=by_id[world_id].barrier_relaxation,
            analytical_variant=by_id[world_id].analytical_variant,
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
    certificate = "complete_relaxation_declaration_over_frozen_temporal_world_universe"
    payload = {
        "reconstruction_fingerprint": reconstruction.fingerprint,
        "declarations": [
            {
                "world_id": row.world_id,
                "geographic_relaxation": row.geographic_relaxation,
                "environmental_relaxation": row.environmental_relaxation,
                "barrier_relaxation": row.barrier_relaxation,
                "analytical_variant": row.analytical_variant,
            }
            for row in ordered_declarations
        ],
        "frontier": [
            {
                "world_id": row.world_id,
                "geographic_relaxation": row.geographic_relaxation,
                "environmental_relaxation": row.environmental_relaxation,
                "barrier_relaxation": row.barrier_relaxation,
                "analytical_variant": row.analytical_variant,
            }
            for row in frontier
        ],
        "coverage_certificate": certificate,
    }
    return TemporalRelaxationFrontier(
        points=tuple(frontier),
        compatible_world_ids=reconstruction.compatible_world_ids,
        declared_world_ids=frozen_world_ids,
        reconstruction_fingerprint=reconstruction.fingerprint,
        coverage_certificate=certificate,
        fingerprint=_canonical_sha256(payload),
    )
