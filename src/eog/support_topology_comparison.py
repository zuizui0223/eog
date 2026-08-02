"""Audited held-out comparison for frozen spatial support topology inputs."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Mapping, Sequence

import numpy as np

from .support_topology import SupportTopologyConfig, infer_support_topology


METHODS = (
    "support_only",
    "distance_only",
    "support_plus_distance",
    "single_threshold_detached",
    "multi_threshold_persistent",
)


@dataclass(frozen=True)
class HeldoutCandidate:
    candidate_id: str
    row: int
    column: int
    detected: int


@dataclass(frozen=True)
class SupportTopologyComparisonConfig:
    thresholds: tuple[float, ...]
    single_threshold: float
    minimum_persistence_steps: int = 2
    neighbourhood: int = 4
    support_weight: float = 0.5

    def validate(self) -> None:
        SupportTopologyConfig(
            self.thresholds,
            neighbourhood=self.neighbourhood,
            minimum_persistence_steps=self.minimum_persistence_steps,
        ).validated_thresholds()
        if not np.isfinite(self.single_threshold):
            raise ValueError("single_threshold must be finite")
        if not 0.0 <= self.support_weight <= 1.0:
            raise ValueError("support_weight must be between zero and one")


@dataclass(frozen=True)
class ComparisonMetric:
    roc_auc: float
    brier_score: float


@dataclass(frozen=True)
class SupportTopologyComparisonResult:
    metrics: Mapping[str, ComparisonMetric]
    candidates: tuple[dict[str, object], ...]
    config: SupportTopologyComparisonConfig
    fingerprint: str
    claim_limit: str


def _scale_with_reference(values: np.ndarray, reference_values: np.ndarray) -> np.ndarray:
    """Scale values using a frozen declared-domain reference, not held-out rows."""
    low = float(reference_values.min())
    high = float(reference_values.max())
    if high == low:
        return np.zeros_like(values, dtype=float)
    return np.clip((values - low) / (high - low), 0.0, 1.0)


def _roc_auc(labels: np.ndarray, scores: np.ndarray) -> float:
    positives = scores[labels == 1]
    negatives = scores[labels == 0]
    if not len(positives) or not len(negatives):
        raise ValueError("ROC AUC requires at least one positive and one negative")
    values = [
        1.0 if positive > negative else 0.5 if positive == negative else 0.0
        for positive in positives
        for negative in negatives
    ]
    return float(np.mean(values))


def _neighbours(
    cell: tuple[int, int],
    shape: tuple[int, int],
    neighbourhood: int,
):
    row, column = cell
    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if neighbourhood == 8:
        offsets += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for dr, dc in offsets:
        candidate = (row + dr, column + dc)
        if 0 <= candidate[0] < shape[0] and 0 <= candidate[1] < shape[1]:
            yield candidate


def _member_class_by_cell(
    result,
    field: np.ndarray,
    mask: np.ndarray,
) -> dict[tuple[int, int], str]:
    """Map cells in each component's last identifiable superlevel-set extent.

    ``birth_cells`` define lineage identity, but they are not the full component
    extent reported by ``member_cell_count`` and ``area``. Held-out scoring must
    therefore recover cells that entered the same lineage at later thresholds.
    """
    assignments: dict[tuple[int, int], tuple[float, str]] = {}
    for component in result.components:
        active = (~mask) & (field >= component.last_identifiable_threshold)
        seeds = [cell for cell in component.birth_cells if active[cell]]
        if not seeds:
            continue
        visited = {seeds[0]}
        stack = [seeds[0]]
        while stack:
            cell = stack.pop()
            for neighbour in _neighbours(cell, field.shape, result.neighbourhood):
                if active[neighbour] and neighbour not in visited:
                    visited.add(neighbour)
                    stack.append(neighbour)
        for cell in visited:
            current = assignments.get(cell)
            candidate = (component.first_threshold, component.component_class)
            if current is None or candidate[0] > current[0]:
                assignments[cell] = candidate
    return {cell: value[1] for cell, value in assignments.items()}


def _validate_anchors(
    anchors: Mapping[str, tuple[int, int]],
    shape: tuple[int, int],
    mask: np.ndarray,
) -> tuple[tuple[int, int], ...]:
    if not anchors:
        raise ValueError("at least one historical anchor is required")
    cells: list[tuple[int, int]] = []
    seen_ids: set[str] = set()
    for anchor_id, raw_cell in anchors.items():
        if not anchor_id or anchor_id in seen_ids:
            raise ValueError("anchor IDs must be non-empty and unique")
        if len(raw_cell) != 2:
            raise ValueError(f"anchor must contain row and column: {anchor_id}")
        cell = (int(raw_cell[0]), int(raw_cell[1]))
        if not (0 <= cell[0] < shape[0] and 0 <= cell[1] < shape[1]):
            raise ValueError(f"anchor outside grid: {anchor_id}")
        if mask[cell]:
            raise ValueError(f"anchor lies on masked cell: {anchor_id}")
        seen_ids.add(anchor_id)
        cells.append(cell)
    return tuple(cells)


def _distance_to_nearest_anchor(
    cells: Sequence[tuple[int, int]],
    anchor_cells: Sequence[tuple[int, int]],
) -> np.ndarray:
    return np.asarray(
        [
            min(np.hypot(cell[0] - anchor[0], cell[1] - anchor[1]) for anchor in anchor_cells)
            for cell in cells
        ],
        dtype=float,
    )


def compare_support_topology_heldout(
    support: np.ndarray,
    missing_mask: np.ndarray,
    anchors: Mapping[str, tuple[int, int]],
    candidates: Sequence[HeldoutCandidate],
    config: SupportTopologyComparisonConfig,
) -> SupportTopologyComparisonResult:
    """Compare five frozen scoring rules without fitting held-out labels or rows."""
    config.validate()
    field = np.asarray(support, dtype=float)
    mask = np.asarray(missing_mask, dtype=bool)
    if field.ndim != 2 or mask.shape != field.shape:
        raise ValueError("support and missing_mask must be matching 2D arrays")
    if not np.isfinite(field[~mask]).all():
        raise ValueError("unmasked support values must be finite")
    if not candidates:
        raise ValueError("at least one held-out candidate is required")

    anchor_cells = _validate_anchors(anchors, field.shape, mask)
    anchor_cell_set = set(anchor_cells)

    ids: set[str] = set()
    candidate_cells: set[tuple[int, int]] = set()
    cells: list[tuple[int, int]] = []
    labels: list[int] = []
    for candidate in candidates:
        if not candidate.candidate_id or candidate.candidate_id in ids:
            raise ValueError("candidate IDs must be non-empty and unique")
        if candidate.detected not in {0, 1}:
            raise ValueError("detected must be zero or one")
        cell = (int(candidate.row), int(candidate.column))
        if not (0 <= cell[0] < field.shape[0] and 0 <= cell[1] < field.shape[1]):
            raise ValueError(f"candidate outside grid: {candidate.candidate_id}")
        if mask[cell]:
            raise ValueError(f"candidate lies on masked cell: {candidate.candidate_id}")
        if cell in candidate_cells:
            raise ValueError(f"duplicate held-out candidate cell: {cell}")
        if cell in anchor_cell_set:
            raise ValueError(
                f"held-out candidate overlaps historical anchor cell: {candidate.candidate_id}"
            )
        ids.add(candidate.candidate_id)
        candidate_cells.add(cell)
        cells.append(cell)
        labels.append(candidate.detected)

    labels_array = np.asarray(labels, dtype=int)
    local_support = np.asarray([field[cell] for cell in cells], dtype=float)
    distance = _distance_to_nearest_anchor(cells, anchor_cells)

    available_cells = tuple(tuple(cell) for cell in np.argwhere(~mask))
    support_reference = field[~mask]
    distance_reference = _distance_to_nearest_anchor(available_cells, anchor_cells)
    support_score = _scale_with_reference(local_support, support_reference)
    distance_score = 1.0 - _scale_with_reference(distance, distance_reference)
    combined_score = (
        config.support_weight * support_score
        + (1.0 - config.support_weight) * distance_score
    )

    single = infer_support_topology(
        field,
        anchors,
        SupportTopologyConfig(
            (config.single_threshold,),
            neighbourhood=config.neighbourhood,
            minimum_persistence_steps=1,
        ),
        missing_mask=mask,
    )
    multi = infer_support_topology(
        field,
        anchors,
        SupportTopologyConfig(
            config.thresholds,
            neighbourhood=config.neighbourhood,
            minimum_persistence_steps=config.minimum_persistence_steps,
        ),
        missing_mask=mask,
    )
    single_classes = _member_class_by_cell(single, field, mask)
    multi_classes = _member_class_by_cell(multi, field, mask)
    single_score = np.asarray(
        [float(single_classes.get(cell) == "persistent_detached_component") for cell in cells]
    )
    multi_score = np.asarray(
        [float(multi_classes.get(cell) == "persistent_detached_component") for cell in cells]
    )
    scores = {
        "support_only": support_score,
        "distance_only": distance_score,
        "support_plus_distance": combined_score,
        "single_threshold_detached": single_score,
        "multi_threshold_persistent": multi_score,
    }
    metrics = {
        method: ComparisonMetric(
            roc_auc=_roc_auc(labels_array, values),
            brier_score=float(np.mean((values - labels_array) ** 2)),
        )
        for method, values in scores.items()
    }
    rows = tuple(
        {
            "candidate_id": candidate.candidate_id,
            "row": candidate.row,
            "column": candidate.column,
            "detected": candidate.detected,
            "support": float(local_support[index]),
            "distance_to_nearest_anchor": float(distance[index]),
            "single_threshold_class": single_classes.get(cells[index]),
            "multi_threshold_class": multi_classes.get(cells[index]),
            "scores": {method: float(values[index]) for method, values in scores.items()},
        }
        for index, candidate in enumerate(candidates)
    )
    payload = {
        "support": field.tolist(),
        "missing_mask": mask.astype(int).tolist(),
        "anchors": sorted((key, list(value)) for key, value in anchors.items()),
        "candidates": [asdict(candidate) for candidate in candidates],
        "config": asdict(config),
        "metrics": {key: asdict(value) for key, value in metrics.items()},
        "rows": rows,
        "score_scaling_reference": "all_unmasked_declared_grid_cells",
        "topology_cell_reference": "last_identifiable_component_extent",
        "heldout_cell_contract": "unique_candidate_cells_disjoint_from_anchor_cells",
    }
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return SupportTopologyComparisonResult(
        metrics=metrics,
        candidates=rows,
        config=config,
        fingerprint=fingerprint,
        claim_limit=(
            "Held-out comparison is descriptive for the declared frozen inputs. It does not "
            "establish calibrated occupancy probability, colonisation, dispersal connectivity, "
            "causality, or general superiority outside the evaluated data."
        ),
    )
