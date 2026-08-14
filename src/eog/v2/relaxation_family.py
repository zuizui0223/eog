"""Basin-merge diagnostics for an explicitly declared one-dimensional relaxation family.

A scalar water level is meaningful here only because the caller declares a monotone
one-dimensional family *before* inference.  This module does not manufacture lambda by
weighting geographic/IBD, environmental/IBE and barrier axes.  Those component axes
remain recorded in each :class:`FiniteWorld` and must vary monotonically along the
declared family.

Multiple analytical variants may be represented at every level.  The first level at
which at least one variant can jointly realize all declared occurrence groups is the
``first_possible_level``.  The first level at which every declared analytical variant
can do so is the ``first_robust_level``.  Both claims are restricted to the enumerated
family and its declared variants.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

import numpy as np

from .world_reconstruction import FiniteWorld, reconstruct_compatible_worlds


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _finite_level(value: float) -> float:
    level = float(value)
    if not np.isfinite(level):
        raise ValueError("relaxation levels must be finite")
    return level


@dataclass(frozen=True)
class MonotoneRelaxationFamily:
    """Frozen one-dimensional family with a complete analytical-variant grid."""

    family_id: str
    levels: tuple[float, ...]
    analytical_variants: tuple[str, ...]
    worlds_by_level: tuple[tuple[FiniteWorld, ...], ...]
    fingerprint: str

    def worlds_at(self, level: float) -> tuple[FiniteWorld, ...]:
        """Return worlds at one declared level in canonical variant order."""

        target = float(level)
        for candidate, worlds in zip(self.levels, self.worlds_by_level, strict=True):
            if candidate == target:
                return worlds
        raise KeyError(f"relaxation level {level!r} is not declared")


@dataclass(frozen=True)
class BasinMergeLevel:
    level: float
    compatible_variants: tuple[str, ...]
    incompatible_variants: tuple[str, ...]
    possible: bool
    robust: bool


@dataclass(frozen=True)
class BasinMergeResult:
    """First possible and robust joint-realization levels for occurrence basins."""

    family_id: str
    basin_groups: tuple[tuple[str, tuple[str, ...]], ...]
    level_results: tuple[BasinMergeLevel, ...]
    first_possible_level: float | None
    first_robust_level: float | None
    possible_but_variant_dependent: bool
    never_possible: bool
    never_robust: bool
    max_steps: int
    support_tolerance: float
    family_fingerprint: str
    coverage_certificate: str
    fingerprint: str


def _validate_monotone_variant(worlds: Sequence[FiniteWorld], levels: Sequence[float]) -> None:
    """Require relaxation to add/strengthen support without silently changing the source contract."""

    first = worlds[0]
    for world in worlds[1:]:
        if world.operator.node_ids != first.operator.node_ids:
            raise ValueError("all worlds in a relaxation family must share node IDs and order")
        if world.source_ids != first.source_ids or world.source_weights != first.source_weights:
            raise ValueError("sources and source weights must remain fixed within an analytical variant")
        if not np.array_equal(world.operator.loss_support, first.operator.loss_support):
            raise ValueError("loss_support must remain fixed within an analytical variant")

    for lower_level, upper_level, lower, upper in zip(
        levels[:-1], levels[1:], worlds[:-1], worlds[1:], strict=True
    ):
        if upper_level <= lower_level:
            raise ValueError("relaxation levels must be strictly increasing")
        if np.any(upper.operator.raw_support + 1e-15 < lower.operator.raw_support):
            raise ValueError(
                "raw transition support must be elementwise non-decreasing along a relaxation family"
            )
        if upper.geographic_relaxation + 1e-15 < lower.geographic_relaxation:
            raise ValueError("geographic relaxation must be non-decreasing with lambda")
        if upper.environmental_relaxation + 1e-15 < lower.environmental_relaxation:
            raise ValueError("environmental relaxation must be non-decreasing with lambda")
        if upper.barrier_relaxation + 1e-15 < lower.barrier_relaxation:
            raise ValueError("barrier relaxation must be non-decreasing with lambda")


def build_monotone_relaxation_family(
    family_id: str,
    level_worlds: Mapping[float, Mapping[str, FiniteWorld]],
) -> MonotoneRelaxationFamily:
    """Freeze a complete level x analytical-variant grid.

    ``level_worlds`` is explicit on purpose.  Every declared analytical variant must
    occur exactly once at every level.  A world must carry the same
    ``analytical_variant`` label as the mapping key.  The function validates that raw
    transition support and declared relaxation coordinates do not become more
    restrictive as lambda increases.
    """

    declared_family_id = str(family_id).strip()
    if not declared_family_id:
        raise ValueError("family_id must be non-empty")
    if len(level_worlds) < 2:
        raise ValueError("a relaxation family requires at least two declared levels")

    canonical_levels = tuple(sorted(_finite_level(value) for value in level_worlds))
    if len(set(canonical_levels)) != len(canonical_levels):
        raise ValueError("relaxation levels must be unique")

    first_mapping = level_worlds[canonical_levels[0]]
    if not first_mapping:
        raise ValueError("each relaxation level must contain at least one analytical variant")
    variants = tuple(sorted(str(value).strip() for value in first_mapping))
    if any(not value for value in variants) or len(set(variants)) != len(variants):
        raise ValueError("analytical variant IDs must be unique and non-empty")
    variant_set = set(variants)

    rows: list[tuple[FiniteWorld, ...]] = []
    for level in canonical_levels:
        mapping = level_worlds[level]
        normalized_keys = {str(value).strip() for value in mapping}
        if normalized_keys != variant_set:
            raise ValueError("every relaxation level must contain the same analytical variants")
        by_variant = {str(key).strip(): world for key, world in mapping.items()}
        worlds = tuple(by_variant[variant] for variant in variants)
        for variant, world in zip(variants, worlds, strict=True):
            if world.analytical_variant != variant:
                raise ValueError(
                    f"world {world.world_id!r} analytical_variant does not match mapping key {variant!r}"
                )
        rows.append(worlds)

    first_nodes = rows[0][0].operator.node_ids
    if any(world.operator.node_ids != first_nodes for worlds in rows for world in worlds):
        raise ValueError("all worlds in the family must share one node universe")

    for variant_index, _variant in enumerate(variants):
        _validate_monotone_variant(
            tuple(worlds[variant_index] for worlds in rows),
            canonical_levels,
        )

    payload = {
        "family_id": declared_family_id,
        "levels": list(canonical_levels),
        "analytical_variants": list(variants),
        "worlds_by_level": [
            [
                {
                    "world_id": world.world_id,
                    "world_fingerprint": world.fingerprint,
                }
                for world in worlds
            ]
            for worlds in rows
        ],
        "contract": "complete_monotone_one_dimensional_relaxation_family",
    }
    return MonotoneRelaxationFamily(
        family_id=declared_family_id,
        levels=canonical_levels,
        analytical_variants=variants,
        worlds_by_level=tuple(rows),
        fingerprint=_canonical_sha256(payload),
    )


def _canonical_basin_groups(
    node_ids: tuple[str, ...],
    basin_groups: Mapping[str, Sequence[str]],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if len(basin_groups) < 2:
        raise ValueError("basin merge requires at least two occurrence groups")
    node_set = set(node_ids)
    seen_nodes: set[str] = set()
    rows: list[tuple[str, tuple[str, ...]]] = []
    for raw_group_id, raw_occurrences in basin_groups.items():
        group_id = str(raw_group_id).strip()
        if not group_id:
            raise ValueError("basin group IDs must be non-empty")
        requested = tuple(str(value).strip() for value in raw_occurrences)
        if not requested or any(not value for value in requested) or len(set(requested)) != len(requested):
            raise ValueError("each basin group must contain unique non-empty occurrence IDs")
        missing = set(requested).difference(node_set)
        if missing:
            raise ValueError(f"basin group {group_id!r} contains unknown nodes: {sorted(missing)}")
        overlap = set(requested).intersection(seen_nodes)
        if overlap:
            raise ValueError(f"basin groups must be disjoint; repeated nodes: {sorted(overlap)}")
        seen_nodes.update(requested)
        requested_set = set(requested)
        ordered = tuple(node_id for node_id in node_ids if node_id in requested_set)
        rows.append((group_id, ordered))
    if len({group_id for group_id, _ in rows}) != len(rows):
        raise ValueError("basin group IDs must be unique")
    return tuple(sorted(rows, key=lambda row: row[0]))


def infer_basin_merge(
    family: MonotoneRelaxationFamily,
    basin_groups: Mapping[str, Sequence[str]],
    *,
    max_steps: int,
    support_floor: float = 1e-12,
    support_tolerance: float = 1e-15,
) -> BasinMergeResult:
    """Find the first possible and first robust joint-realization levels.

    All occurrence anchors from all declared groups are jointly evaluated under every
    analytical variant at each lambda.  ``possible`` means at least one variant at that
    level can realize the full union.  ``robust`` means every declared variant can.

    These are finite-family structural claims.  They do not identify the historical
    crossing event and do not imply that lambda is a biological time or distance.
    """

    if isinstance(max_steps, bool) or not isinstance(max_steps, (int, np.integer)) or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")
    tolerance = float(support_tolerance)
    if not np.isfinite(tolerance) or tolerance < 0.0:
        raise ValueError("support_tolerance must be finite and non-negative")

    node_ids = family.worlds_by_level[0][0].operator.node_ids
    groups = _canonical_basin_groups(node_ids, basin_groups)
    occurrence_ids = tuple(
        node_id
        for node_id in node_ids
        if any(node_id in set(group_occurrences) for _, group_occurrences in groups)
    )

    level_results: list[BasinMergeLevel] = []
    for level, worlds in zip(family.levels, family.worlds_by_level, strict=True):
        reconstruction = reconstruct_compatible_worlds(
            worlds,
            occurrence_ids,
            max_steps=max_steps,
            support_floor=support_floor,
            support_tolerance=tolerance,
        )
        compatibility_by_world = {
            result.world_id: result.compatible for result in reconstruction.world_results
        }
        compatibility_by_variant = {
            world.analytical_variant: compatibility_by_world[world.world_id] for world in worlds
        }
        compatible_variants = tuple(
            variant for variant in family.analytical_variants if compatibility_by_variant[variant]
        )
        incompatible_variants = tuple(
            variant for variant in family.analytical_variants if not compatibility_by_variant[variant]
        )
        level_results.append(
            BasinMergeLevel(
                level=level,
                compatible_variants=compatible_variants,
                incompatible_variants=incompatible_variants,
                possible=bool(compatible_variants),
                robust=not incompatible_variants,
            )
        )

    possible_levels = [row.level for row in level_results if row.possible]
    robust_levels = [row.level for row in level_results if row.robust]
    first_possible = possible_levels[0] if possible_levels else None
    first_robust = robust_levels[0] if robust_levels else None

    # Monotonic-family validation means support should not disappear at higher lambda.
    # Keep this explicit so future operator changes cannot silently break the contract.
    possible_flags = [row.possible for row in level_results]
    robust_flags = [row.robust for row in level_results]
    if any(previous and not current for previous, current in zip(possible_flags[:-1], possible_flags[1:])):
        raise RuntimeError("possible basin merge became impossible at a higher relaxation level")
    if any(previous and not current for previous, current in zip(robust_flags[:-1], robust_flags[1:])):
        raise RuntimeError("robust basin merge became non-robust at a higher relaxation level")

    certificate = "exhaustive_declared_monotone_family_and_variants"
    payload = {
        "family_fingerprint": family.fingerprint,
        "basin_groups": [[group_id, list(nodes)] for group_id, nodes in groups],
        "level_results": [
            {
                "level": row.level,
                "compatible_variants": list(row.compatible_variants),
                "incompatible_variants": list(row.incompatible_variants),
                "possible": row.possible,
                "robust": row.robust,
            }
            for row in level_results
        ],
        "first_possible_level": first_possible,
        "first_robust_level": first_robust,
        "max_steps": int(max_steps),
        "support_floor": float(support_floor),
        "support_tolerance": tolerance,
        "coverage_certificate": certificate,
    }
    return BasinMergeResult(
        family_id=family.family_id,
        basin_groups=groups,
        level_results=tuple(level_results),
        first_possible_level=first_possible,
        first_robust_level=first_robust,
        possible_but_variant_dependent=(
            first_possible is not None
            and (first_robust is None or first_possible < first_robust)
        ),
        never_possible=first_possible is None,
        never_robust=first_robust is None,
        max_steps=int(max_steps),
        support_tolerance=tolerance,
        family_fingerprint=family.fingerprint,
        coverage_certificate=certificate,
        fingerprint=_canonical_sha256(payload),
    )
