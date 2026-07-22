"""Occurrence-conditioned topology of frozen geographical support fields.

This module analyzes connected components of superlevel sets on a regular grid.
It deliberately does not implement paths, bottlenecks, reachability optimization,
or survey ranking; those belong to EOG's bridge and hypothesis-survey layers.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Iterable, Mapping, Sequence

import numpy as np


COMPONENT_CLASSES = {
    "occurrence_anchored_component",
    "persistent_detached_component",
    "transient_detached_component",
    "low_support_or_unresolved",
}


@dataclass(frozen=True)
class SupportGridMetadata:
    """Regular-grid metadata used for auditable coordinates and cell area."""

    x_origin: float = 0.0
    y_origin: float = 0.0
    x_resolution: float = 1.0
    y_resolution: float = 1.0
    crs: str | None = None

    def validate(self) -> None:
        values = (self.x_origin, self.y_origin, self.x_resolution, self.y_resolution)
        if not all(np.isfinite(value) for value in values):
            raise ValueError("grid metadata values must be finite")
        if self.x_resolution == 0 or self.y_resolution == 0:
            raise ValueError("grid resolution must be non-zero")

    @property
    def cell_area(self) -> float:
        return abs(self.x_resolution * self.y_resolution)


@dataclass(frozen=True)
class SupportTopologyConfig:
    """Frozen topology settings.

    Thresholds are interpreted as superlevel-set cutoffs and are normalized to
    strict descending order. ``neighbourhood`` must be 4 or 8.
    """

    thresholds: tuple[float, ...]
    neighbourhood: int = 4
    minimum_persistence_steps: int = 2
    unresolved_below: float | None = None

    def validated_thresholds(self) -> tuple[float, ...]:
        if self.neighbourhood not in {4, 8}:
            raise ValueError("neighbourhood must be 4 or 8")
        if self.minimum_persistence_steps < 1:
            raise ValueError("minimum_persistence_steps must be at least 1")
        if not self.thresholds:
            raise ValueError("at least one support threshold is required")
        values = tuple(float(value) for value in self.thresholds)
        if not all(np.isfinite(value) for value in values):
            raise ValueError("thresholds must be finite")
        if len(set(values)) != len(values):
            raise ValueError("thresholds must be unique")
        return tuple(sorted(values, reverse=True))


@dataclass(frozen=True)
class OccurrenceAnchor:
    anchor_id: str
    row: int
    column: int


@dataclass(frozen=True)
class SupportComponent:
    component_id: str
    first_threshold: float
    last_identifiable_threshold: float
    threshold_count: int
    persistence: float
    anchor_ids: tuple[str, ...]
    anchor_component_ids: tuple[str, ...]
    merge_into_anchored_threshold: float | None
    member_cell_count: int
    area: float
    maximum_support: float
    mean_support: float
    minimum_support: float
    component_class: str
    birth_cells: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class SupportTopologyResult:
    shape: tuple[int, int]
    thresholds: tuple[float, ...]
    neighbourhood: int
    components: tuple[SupportComponent, ...]
    anchor_assignments: tuple[OccurrenceAnchor, ...]
    masked_cell_count: int
    available_cell_count: int
    fingerprint: str


@dataclass(frozen=True)
class ComponentRecovery:
    detection_id: str
    row: int
    column: int
    recovered: bool
    component_id: str | None
    component_class: str | None


@dataclass
class _Track:
    component_id: str
    birth_index: int
    birth_threshold: float
    birth_cells: frozenset[tuple[int, int]]
    snapshots: list[tuple[int, float, frozenset[tuple[int, int]], tuple[str, ...]]]
    merge_into_anchored_threshold: float | None = None
    merged: bool = False


def assign_occurrence_anchors(
    shape: tuple[int, int],
    occurrence_cells: Mapping[str, tuple[int, int]] | Iterable[OccurrenceAnchor],
    *,
    available_mask: np.ndarray | None = None,
) -> tuple[OccurrenceAnchor, ...]:
    """Validate explicit occurrence-to-cell assignments without silent snapping."""

    if len(shape) != 2 or shape[0] <= 0 or shape[1] <= 0:
        raise ValueError("shape must contain two positive dimensions")
    mask = np.ones(shape, dtype=bool) if available_mask is None else np.asarray(available_mask, dtype=bool)
    if mask.shape != shape:
        raise ValueError("available_mask shape must match support field")
    if isinstance(occurrence_cells, Mapping):
        raw = [OccurrenceAnchor(str(key), int(value[0]), int(value[1])) for key, value in occurrence_cells.items()]
    else:
        raw = [OccurrenceAnchor(str(item.anchor_id), int(item.row), int(item.column)) for item in occurrence_cells]
    seen_ids: set[str] = set()
    seen_cells: set[tuple[int, int]] = set()
    anchors: list[OccurrenceAnchor] = []
    for anchor in raw:
        if not anchor.anchor_id:
            raise ValueError("anchor_id must be non-empty")
        if anchor.anchor_id in seen_ids:
            raise ValueError(f"duplicate anchor_id: {anchor.anchor_id}")
        cell = (anchor.row, anchor.column)
        if cell in seen_cells:
            raise ValueError(f"duplicate occurrence anchor cell: {cell}")
        if not (0 <= anchor.row < shape[0] and 0 <= anchor.column < shape[1]):
            raise ValueError(f"occurrence anchor outside grid: {anchor.anchor_id}")
        if not mask[cell]:
            raise ValueError(f"occurrence anchor lies on a masked cell: {anchor.anchor_id}")
        seen_ids.add(anchor.anchor_id)
        seen_cells.add(cell)
        anchors.append(anchor)
    return tuple(sorted(anchors, key=lambda item: (item.row, item.column, item.anchor_id)))


def _validate_field(
    support: np.ndarray,
    missing_mask: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray]:
    field = np.asarray(support, dtype=float)
    if field.ndim != 2 or field.size == 0:
        raise ValueError("support must be a non-empty 2D numeric array")
    mask = np.zeros(field.shape, dtype=bool) if missing_mask is None else np.asarray(missing_mask, dtype=bool)
    if mask.shape != field.shape:
        raise ValueError("missing_mask shape must match support field")
    available = ~mask
    if not available.any():
        raise ValueError("support field has no available cells")
    if not np.isfinite(field[available]).all():
        raise ValueError("available support values must be finite")
    return field, available


def _neighbours(row: int, column: int, shape: tuple[int, int], neighbourhood: int):
    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if neighbourhood == 8:
        offsets += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for dr, dc in offsets:
        rr, cc = row + dr, column + dc
        if 0 <= rr < shape[0] and 0 <= cc < shape[1]:
            yield rr, cc


def _components(binary: np.ndarray, neighbourhood: int) -> list[frozenset[tuple[int, int]]]:
    visited = np.zeros(binary.shape, dtype=bool)
    result: list[frozenset[tuple[int, int]]] = []
    for row, column in np.argwhere(binary):
        row, column = int(row), int(column)
        if visited[row, column]:
            continue
        stack = [(row, column)]
        visited[row, column] = True
        cells: list[tuple[int, int]] = []
        while stack:
            cell = stack.pop()
            cells.append(cell)
            for neighbour in _neighbours(*cell, binary.shape, neighbourhood):
                if binary[neighbour] and not visited[neighbour]:
                    visited[neighbour] = True
                    stack.append(neighbour)
        result.append(frozenset(cells))
    return sorted(result, key=lambda cells: min(cells))


def _component_id(birth_index: int, cells: frozenset[tuple[int, int]]) -> str:
    seed = min(cells)
    digest = hashlib.sha256(json.dumps(sorted(cells)).encode()).hexdigest()[:8]
    return f"SC{birth_index + 1:03d}_r{seed[0]:04d}c{seed[1]:04d}_{digest}"


def infer_support_topology(
    support: np.ndarray,
    occurrence_cells: Mapping[str, tuple[int, int]] | Iterable[OccurrenceAnchor],
    config: SupportTopologyConfig,
    *,
    missing_mask: np.ndarray | None = None,
    grid: SupportGridMetadata | None = None,
) -> SupportTopologyResult:
    """Infer persistent superlevel-set component lineages on a regular grid."""

    field, available = _validate_field(support, missing_mask)
    thresholds = config.validated_thresholds()
    metadata = grid or SupportGridMetadata()
    metadata.validate()
    anchors = assign_occurrence_anchors(field.shape, occurrence_cells, available_mask=available)
    anchor_by_cell = {(item.row, item.column): item.anchor_id for item in anchors}
    tracks: list[_Track] = []

    for threshold_index, threshold in enumerate(thresholds):
        current = _components(available & (field >= threshold), config.neighbourhood)
        for cells in current:
            anchor_ids = tuple(sorted(anchor_by_cell[cell] for cell in cells if cell in anchor_by_cell))
            overlapping = [track for track in tracks if not track.merged and track.birth_cells.intersection(cells)]
            if not overlapping:
                track = _Track(
                    component_id=_component_id(len(tracks), cells),
                    birth_index=threshold_index,
                    birth_threshold=threshold,
                    birth_cells=cells,
                    snapshots=[],
                )
                tracks.append(track)
                overlapping = [track]
            if len(overlapping) > 1:
                anchored = [track for track in overlapping if any(snapshot[3] for snapshot in track.snapshots)]
                survivor = min(anchored or overlapping, key=lambda item: (item.birth_index, item.component_id))
                for track in overlapping:
                    if track is survivor:
                        continue
                    if track.merge_into_anchored_threshold is None and (
                        anchor_ids or any(any(snapshot[3] for snapshot in other.snapshots) for other in overlapping if other is not track)
                    ):
                        track.merge_into_anchored_threshold = threshold
                    track.merged = True
                overlapping = [survivor]
            track = overlapping[0]
            track.snapshots.append((threshold_index, threshold, cells, anchor_ids))

    components: list[SupportComponent] = []
    span = max(thresholds) - min(thresholds)
    for track in tracks:
        snapshots = track.snapshots
        if not snapshots:
            continue
        first_anchor_ids = snapshots[0][3]
        all_anchor_ids = tuple(sorted({anchor for snapshot in snapshots for anchor in snapshot[3]}))
        last_index, last_threshold, largest_cells, _ = max(
            snapshots, key=lambda item: (len(item[2]), -item[0])
        )
        threshold_count = len(snapshots)
        persistence = (
            1.0 if len(thresholds) == 1 else (track.birth_threshold - snapshots[-1][1]) / span if span > 0 else 1.0
        )
        values = np.asarray([field[cell] for cell in largest_cells], dtype=float)
        unresolved_cutoff = config.unresolved_below
        if first_anchor_ids:
            component_class = "occurrence_anchored_component"
        elif unresolved_cutoff is not None and track.birth_threshold <= unresolved_cutoff:
            component_class = "low_support_or_unresolved"
        elif threshold_count >= config.minimum_persistence_steps:
            component_class = "persistent_detached_component"
        else:
            component_class = "transient_detached_component"
        anchor_component_ids = tuple(
            sorted(
                other.component_id
                for other in tracks
                if other is not track and any(set(snapshot[3]).intersection(all_anchor_ids) for snapshot in other.snapshots)
            )
        )
        components.append(
            SupportComponent(
                component_id=track.component_id,
                first_threshold=track.birth_threshold,
                last_identifiable_threshold=snapshots[-1][1],
                threshold_count=threshold_count,
                persistence=float(persistence),
                anchor_ids=all_anchor_ids,
                anchor_component_ids=anchor_component_ids,
                merge_into_anchored_threshold=track.merge_into_anchored_threshold,
                member_cell_count=len(largest_cells),
                area=len(largest_cells) * metadata.cell_area,
                maximum_support=float(values.max()),
                mean_support=float(values.mean()),
                minimum_support=float(values.min()),
                component_class=component_class,
                birth_cells=tuple(sorted(track.birth_cells)),
            )
        )

    components.sort(key=lambda item: (-item.first_threshold, item.component_id))
    payload = {
        "shape": field.shape,
        "thresholds": thresholds,
        "neighbourhood": config.neighbourhood,
        "minimum_persistence_steps": config.minimum_persistence_steps,
        "unresolved_below": config.unresolved_below,
        "grid": asdict(metadata),
        "mask": available.astype(int).tolist(),
        "support": np.where(available, field, 0.0).tolist(),
        "anchors": [asdict(item) for item in anchors],
        "components": [asdict(item) for item in components],
    }
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return SupportTopologyResult(
        shape=field.shape,
        thresholds=thresholds,
        neighbourhood=config.neighbourhood,
        components=tuple(components),
        anchor_assignments=anchors,
        masked_cell_count=int((~available).sum()),
        available_cell_count=int(available.sum()),
        fingerprint=fingerprint,
    )


def summarize_support_components(result: SupportTopologyResult) -> tuple[dict[str, object], ...]:
    """Return stable, serialization-friendly component summaries."""

    return tuple(asdict(component) for component in result.components)


def evaluate_component_recovery(
    result: SupportTopologyResult,
    detections: Mapping[str, tuple[int, int]],
) -> tuple[ComponentRecovery, ...]:
    """Evaluate held-out detections against birth components without refitting."""

    cell_to_component: dict[tuple[int, int], SupportComponent] = {}
    for component in result.components:
        for cell in component.birth_cells:
            current = cell_to_component.get(cell)
            if current is None or component.first_threshold > current.first_threshold:
                cell_to_component[cell] = component
    rows: list[ComponentRecovery] = []
    for detection_id, cell in sorted(detections.items(), key=lambda item: item[0]):
        row, column = int(cell[0]), int(cell[1])
        if not (0 <= row < result.shape[0] and 0 <= column < result.shape[1]):
            raise ValueError(f"held-out detection outside grid: {detection_id}")
        component = cell_to_component.get((row, column))
        rows.append(
            ComponentRecovery(
                detection_id=str(detection_id),
                row=row,
                column=column,
                recovered=component is not None,
                component_id=None if component is None else component.component_id,
                component_class=None if component is None else component.component_class,
            )
        )
    return tuple(rows)


def evaluate_support_topology_sensitivity(
    support: np.ndarray,
    occurrence_cells: Mapping[str, tuple[int, int]],
    configs: Sequence[SupportTopologyConfig],
    *,
    missing_mask: np.ndarray | None = None,
    grid: SupportGridMetadata | None = None,
) -> tuple[dict[str, object], ...]:
    """Audit class counts across predeclared threshold and neighbourhood settings."""

    rows: list[dict[str, object]] = []
    for index, config in enumerate(configs):
        result = infer_support_topology(
            support,
            occurrence_cells,
            config,
            missing_mask=missing_mask,
            grid=grid,
        )
        counts = {name: 0 for name in sorted(COMPONENT_CLASSES)}
        for component in result.components:
            counts[component.component_class] += 1
        rows.append(
            {
                "scenario_id": f"topology_{index + 1:03d}",
                "thresholds": result.thresholds,
                "neighbourhood": result.neighbourhood,
                "component_count": len(result.components),
                "class_counts": counts,
                "fingerprint": result.fingerprint,
            }
        )
    return tuple(rows)
