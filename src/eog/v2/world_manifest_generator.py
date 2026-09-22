"""Declarative response-blind coordinate world generation for EOG-WF v2.

This module removes the need for dataset-specific Python code that manually constructs
N x N threshold matrices. It does not infer biological dispersal distances.

Two construction modes are supported:

- declared_thresholds: apply prospectively declared metric thresholds exactly.
- structural_lcc_ladder: derive the smallest metric threshold that reaches each
  prospectively declared largest-component target, using world_scale_ladder.py.

Generated geometry worlds may be declaratively replicated across rule/source variants.
Those variants change exact Layer-A world identity but not geometry. One variant may be
marked as the structural representative so duplicate geometry does not inflate the
structural-adequacy denominator.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Mapping, Sequence

import numpy as np

from eog.v2.world_scale_ladder import (
    StructuralScaleLadderDeclaration,
    build_structural_scale_ladder,
    structural_scale_adjacencies,
)


_DISTANCE_TOLERANCE = 1e-12
_METRICS = {"haversine_km", "euclidean"}


def _sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _text(value: object, label: str) -> str:
    result = str(value).strip()
    if not result:
        raise ValueError(f"{label} must be non-empty")
    return result


def _finite_nonnegative(value: object, label: str) -> float:
    result = float(value)
    if not np.isfinite(result) or result < 0.0:
        raise ValueError(f"{label} must be finite and non-negative")
    return result


def _canonical_mapping(value: Mapping[str, object] | None, label: str) -> dict[str, object]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be a mapping")
    # Round-trip rejects NaN/Infinity and detaches mutable caller state.
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    decoded = json.loads(encoded)
    if not isinstance(decoded, dict):
        raise TypeError(f"{label} must encode a JSON object")
    return decoded


def coordinate_distance_matrix(
    node_ids: Sequence[str],
    coordinates: Mapping[str, tuple[float, float]],
    *,
    metric: str,
) -> np.ndarray:
    """Build a deterministic response-independent distance matrix."""

    ids = tuple(_text(value, "node_id") for value in node_ids)
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("node_ids must be non-empty and unique")
    if metric not in _METRICS:
        raise ValueError(f"metric must be one of {sorted(_METRICS)}")
    if set(coordinates) != set(ids):
        raise ValueError("coordinate keys must exactly equal node_ids")

    xy = np.asarray(
        [
            (
                float(coordinates[node_id][0]),
                float(coordinates[node_id][1]),
            )
            for node_id in ids
        ],
        dtype=float,
    )
    if xy.shape != (len(ids), 2) or not np.isfinite(xy).all():
        raise ValueError("coordinates must be finite x/y pairs")

    if metric == "euclidean":
        delta = xy[:, None, :] - xy[None, :, :]
        matrix = np.sqrt(np.sum(delta * delta, axis=2))
    else:
        lon = xy[:, 0]
        lat = xy[:, 1]
        if np.any(lon < -180.0) or np.any(lon > 180.0):
            raise ValueError("haversine longitude must lie in [-180, 180]")
        if np.any(lat < -90.0) or np.any(lat > 90.0):
            raise ValueError("haversine latitude must lie in [-90, 90]")
        radius_km = 6371.0088
        lon_rad = np.radians(lon)
        lat_rad = np.radians(lat)
        dlat = lat_rad[:, None] - lat_rad[None, :]
        dlon = lon_rad[:, None] - lon_rad[None, :]
        a = np.sin(dlat / 2.0) ** 2 + (
            np.cos(lat_rad[:, None])
            * np.cos(lat_rad[None, :])
            * np.sin(dlon / 2.0) ** 2
        )
        a = np.clip(a, 0.0, 1.0)
        matrix = 2.0 * radius_km * np.arcsin(np.sqrt(a))

    matrix = np.asarray(matrix, dtype=float)
    matrix = (matrix + matrix.T) / 2.0
    np.fill_diagonal(matrix, 0.0)
    if not np.isfinite(matrix).all() or np.any(matrix < 0.0):
        raise RuntimeError("generated distance matrix is invalid")
    return matrix


@dataclass(frozen=True)
class GeometryWorld:
    base_world_id: str
    threshold: float
    adjacency: np.ndarray


@dataclass(frozen=True)
class GeneratedWorldFamily:
    node_ids: tuple[str, ...]
    metric: str
    construction_mode: str
    worlds: dict[str, np.ndarray]
    world_semantics: dict[str, object]
    structural_world_ids: tuple[str, ...]
    geometry_thresholds: tuple[float, ...]
    distance_matrix_fingerprint: str
    generator_fingerprint: str
    fingerprint: str


def _distance_fingerprint(
    node_ids: tuple[str, ...],
    metric: str,
    matrix: np.ndarray,
) -> str:
    return _sha256(
        {
            "schema": "eog.coordinate_distance_matrix.v1",
            "node_ids": list(node_ids),
            "metric": metric,
            "distance_matrix": matrix.tolist(),
        }
    )


def _merge_semantics(
    *parts: Mapping[str, object],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for part in parts:
        for key, value in part.items():
            if key in result and result[key] != value:
                raise ValueError(
                    f"world semantics key {key!r} is declared with conflicting values"
                )
            result[key] = value
    return result


def _declared_geometry_worlds(
    matrix: np.ndarray,
    threshold_specs: Sequence[Mapping[str, object]],
) -> tuple[GeometryWorld, ...]:
    values = tuple(threshold_specs)
    if not values:
        raise ValueError("declared_thresholds requires at least one threshold")
    worlds: list[GeometryWorld] = []
    seen_ids: set[str] = set()
    previous = -math.inf
    for index, raw in enumerate(values):
        if not isinstance(raw, Mapping):
            raise TypeError(f"threshold spec {index} must be a mapping")
        world_id = _text(raw.get("world_id"), f"threshold spec {index} world_id")
        if world_id in seen_ids:
            raise ValueError("declared threshold world IDs must be unique")
        seen_ids.add(world_id)
        threshold = _finite_nonnegative(
            raw.get("threshold"),
            f"threshold spec {index} threshold",
        )
        if threshold + _DISTANCE_TOLERANCE < previous:
            raise ValueError("declared thresholds must be non-decreasing")
        previous = threshold
        adjacency = matrix <= threshold + _DISTANCE_TOLERANCE
        np.fill_diagonal(adjacency, False)
        worlds.append(
            GeometryWorld(
                base_world_id=world_id,
                threshold=float(threshold),
                adjacency=np.asarray(adjacency, dtype=bool),
            )
        )
    return tuple(worlds)


def _lcc_geometry_worlds(
    node_ids: tuple[str, ...],
    matrix: np.ndarray,
    *,
    axis_id: str,
    target_lcc_fractions: Sequence[float],
    world_id_prefix: str,
    deduplicate_identical_thresholds: bool,
) -> tuple[GeometryWorld, ...]:
    declaration = StructuralScaleLadderDeclaration(
        axis_id=_text(axis_id, "axis_id"),
        target_largest_component_fractions=tuple(float(v) for v in target_lcc_fractions),
    )
    ladder = build_structural_scale_ladder(node_ids, matrix, declaration)
    adjacencies = structural_scale_adjacencies(ladder, matrix)

    worlds: list[GeometryWorld] = []
    threshold_to_index: dict[float, int] = {}
    for level in ladder.levels:
        threshold = float(level.distance_threshold)
        if deduplicate_identical_thresholds and threshold in threshold_to_index:
            continue
        index = len(worlds) + 1
        threshold_to_index[threshold] = index
        worlds.append(
            GeometryWorld(
                base_world_id=f"{_text(world_id_prefix, 'world_id_prefix')}{index}",
                threshold=threshold,
                adjacency=adjacencies[level.level_id],
            )
        )
    if not worlds:
        raise RuntimeError("structural ladder produced no geometry worlds")
    return tuple(worlds)


def generate_coordinate_world_family(
    node_ids: Sequence[str],
    coordinates: Mapping[str, tuple[float, float]],
    *,
    metric: str,
    construction_mode: str,
    threshold_specs: Sequence[Mapping[str, object]] = (),
    axis_id: str | None = None,
    target_lcc_fractions: Sequence[float] = (),
    world_id_prefix: str = "local_geo",
    deduplicate_identical_thresholds: bool = True,
    threshold_semantics_key: str = "geometry_threshold",
    local_semantics: Mapping[str, object] | None = None,
    variants: Sequence[Mapping[str, object]] = (),
    structural_variant_id: str | None = None,
    include_external_open: bool = False,
    external_open_world_id: str = "external_open",
    external_open_semantics: Mapping[str, object] | None = None,
) -> GeneratedWorldFamily:
    """Generate an exact finite world family from response-independent coordinates."""

    ids = tuple(_text(value, "node_id") for value in node_ids)
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("node_ids must be non-empty and unique")
    matrix = coordinate_distance_matrix(ids, coordinates, metric=metric)
    distance_fp = _distance_fingerprint(ids, metric, matrix)

    if construction_mode == "declared_thresholds":
        geometry_worlds = _declared_geometry_worlds(matrix, threshold_specs)
        construction_payload: dict[str, object] = {
            "threshold_specs": [
                {
                    "world_id": world.base_world_id,
                    "threshold": world.threshold,
                }
                for world in geometry_worlds
            ]
        }
    elif construction_mode == "structural_lcc_ladder":
        if axis_id is None:
            raise ValueError("structural_lcc_ladder requires axis_id")
        geometry_worlds = _lcc_geometry_worlds(
            ids,
            matrix,
            axis_id=axis_id,
            target_lcc_fractions=target_lcc_fractions,
            world_id_prefix=world_id_prefix,
            deduplicate_identical_thresholds=bool(deduplicate_identical_thresholds),
        )
        construction_payload = {
            "axis_id": axis_id,
            "target_lcc_fractions": [float(v) for v in target_lcc_fractions],
            "world_id_prefix": world_id_prefix,
            "deduplicate_identical_thresholds": bool(
                deduplicate_identical_thresholds
            ),
        }
    else:
        raise ValueError(
            "construction_mode must be declared_thresholds or structural_lcc_ladder"
        )

    threshold_key = _text(threshold_semantics_key, "threshold_semantics_key")
    common_local = _canonical_mapping(local_semantics, "local_semantics")

    variant_values = tuple(variants)
    parsed_variants: list[tuple[str, dict[str, object]]] = []
    if variant_values:
        seen_variants: set[str] = set()
        for index, raw in enumerate(variant_values):
            if not isinstance(raw, Mapping):
                raise TypeError(f"variant {index} must be a mapping")
            variant_id = _text(raw.get("variant_id"), f"variant {index} variant_id")
            if variant_id in seen_variants:
                raise ValueError("variant IDs must be unique")
            seen_variants.add(variant_id)
            parsed_variants.append(
                (
                    variant_id,
                    _canonical_mapping(raw.get("semantics"), f"variant {index} semantics"),
                )
            )
        if structural_variant_id is None:
            raise ValueError(
                "structural_variant_id is required when geometry worlds are replicated"
            )
        structural_variant = _text(
            structural_variant_id,
            "structural_variant_id",
        )
        if structural_variant not in seen_variants:
            raise ValueError("structural_variant_id is not one of the declared variants")
    else:
        if structural_variant_id is not None:
            raise ValueError("structural_variant_id requires declared variants")
        structural_variant = None

    worlds: dict[str, np.ndarray] = {}
    semantics: dict[str, object] = {}
    structural_ids: list[str] = []

    for geometry in geometry_worlds:
        geometry_semantics = {
            "kind": "local",
            threshold_key: float(geometry.threshold),
        }
        if not parsed_variants:
            world_id = geometry.base_world_id
            worlds[world_id] = geometry.adjacency.copy()
            semantics[world_id] = _merge_semantics(
                geometry_semantics,
                common_local,
            )
            structural_ids.append(world_id)
            continue

        for variant_id, variant_semantics in parsed_variants:
            world_id = f"{geometry.base_world_id}::{variant_id}"
            worlds[world_id] = geometry.adjacency.copy()
            semantics[world_id] = _merge_semantics(
                geometry_semantics,
                common_local,
                variant_semantics,
            )
            if variant_id == structural_variant:
                structural_ids.append(world_id)

    if include_external_open:
        external_id = _text(external_open_world_id, "external_open_world_id")
        if external_id in worlds:
            raise ValueError("external_open_world_id collides with a local world")
        external = np.ones((len(ids), len(ids)), dtype=bool)
        np.fill_diagonal(external, False)
        worlds[external_id] = external
        supplied_external = _canonical_mapping(
            external_open_semantics,
            "external_open_semantics",
        )
        semantics[external_id] = _merge_semantics(
            {"kind": "external_open"},
            supplied_external,
        )

    generator_payload = {
        "schema": "eog.coordinate_world_generator.v1",
        "node_ids": list(ids),
        "metric": metric,
        "construction_mode": construction_mode,
        "distance_matrix_fingerprint": distance_fp,
        "construction": construction_payload,
        "threshold_semantics_key": threshold_key,
        "local_semantics": common_local,
        "variants": [
            {"variant_id": variant_id, "semantics": value}
            for variant_id, value in parsed_variants
        ],
        "structural_variant_id": structural_variant,
        "include_external_open": bool(include_external_open),
        "external_open_world_id": (
            external_open_world_id if include_external_open else None
        ),
        "external_open_semantics": (
            _canonical_mapping(external_open_semantics, "external_open_semantics")
            if include_external_open
            else None
        ),
    }
    generator_fp = _sha256(generator_payload)
    family_payload = {
        **generator_payload,
        "world_ids": sorted(worlds),
        "world_matrices": {
            world_id: np.asarray(worlds[world_id], dtype=int).tolist()
            for world_id in sorted(worlds)
        },
        "world_semantics": {
            world_id: semantics[world_id] for world_id in sorted(semantics)
        },
        "structural_world_ids": list(structural_ids),
    }
    return GeneratedWorldFamily(
        node_ids=ids,
        metric=metric,
        construction_mode=construction_mode,
        worlds=worlds,
        world_semantics=semantics,
        structural_world_ids=tuple(structural_ids),
        geometry_thresholds=tuple(world.threshold for world in geometry_worlds),
        distance_matrix_fingerprint=distance_fp,
        generator_fingerprint=generator_fp,
        fingerprint=_sha256(family_payload),
    )
