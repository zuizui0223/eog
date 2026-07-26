"""Audited held-out comparison for frozen spatial support-topology analyses."""
from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from .support_topology import SupportTopologyConfig, infer_support_topology


METHOD_NAMES = (
    "support_only",
    "distance_only",
    "support_plus_distance",
    "single_threshold_detached",
    "multi_threshold_persistent",
)


@dataclass(frozen=True)
class HeldoutValidationDeclaration:
    analysis_id: str
    thresholds: tuple[float, ...]
    single_threshold: float
    neighbourhood: int = 4
    minimum_persistence_steps: int = 2
    unresolved_below: float | None = None
    support_distance_weight: float = 0.5
    frozen_before_outcomes: bool = True

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "HeldoutValidationDeclaration":
        values = dict(payload)
        values["thresholds"] = tuple(float(value) for value in values["thresholds"])
        return cls(**values)

    def validate(self) -> None:
        if not self.analysis_id.strip():
            raise ValueError("analysis_id must be non-empty")
        SupportTopologyConfig(
            thresholds=self.thresholds,
            neighbourhood=self.neighbourhood,
            minimum_persistence_steps=self.minimum_persistence_steps,
            unresolved_below=self.unresolved_below,
        ).validated_thresholds()
        if not np.isfinite(self.single_threshold):
            raise ValueError("single_threshold must be finite")
        if not 0.0 <= self.support_distance_weight <= 1.0:
            raise ValueError("support_distance_weight must lie in [0, 1]")
        if not self.frozen_before_outcomes:
            raise ValueError("declaration must be frozen before outcomes are inspected")


@dataclass(frozen=True)
class CandidateRecord:
    candidate_id: str
    row: int
    column: int
    detected: int


@dataclass(frozen=True)
class ValidationBundle:
    manifest: dict[str, Any]
    metrics: dict[str, dict[str, float]]
    candidates: tuple[dict[str, Any], ...]
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest": self.manifest,
            "metrics": self.metrics,
            "candidates": list(self.candidates),
            "fingerprint": self.fingerprint,
        }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_anchors(path: Path) -> dict[str, tuple[int, int]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"anchor_id", "row", "column"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError("anchors CSV must contain anchor_id,row,column")
    anchors: dict[str, tuple[int, int]] = {}
    for row in rows:
        anchor_id = str(row["anchor_id"]).strip()
        if not anchor_id or anchor_id in anchors:
            raise ValueError("anchor IDs must be non-empty and unique")
        anchors[anchor_id] = (int(row["row"]), int(row["column"]))
    return anchors


def _load_candidates(path: Path) -> tuple[CandidateRecord, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"candidate_id", "row", "column", "detected"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError("candidates CSV must contain candidate_id,row,column,detected")
    seen: set[str] = set()
    candidates: list[CandidateRecord] = []
    for row in rows:
        candidate_id = str(row["candidate_id"]).strip()
        detected = int(row["detected"])
        if not candidate_id or candidate_id in seen:
            raise ValueError("candidate IDs must be non-empty and unique")
        if detected not in {0, 1}:
            raise ValueError("detected must be 0 or 1")
        seen.add(candidate_id)
        candidates.append(
            CandidateRecord(candidate_id, int(row["row"]), int(row["column"]), detected)
        )
    if not {item.detected for item in candidates} == {0, 1}:
        raise ValueError("held-out candidates must include both detections and non-detections")
    return tuple(candidates)


def _minmax(values: np.ndarray) -> np.ndarray:
    low = float(values.min())
    high = float(values.max())
    if high == low:
        return np.zeros_like(values, dtype=float)
    return (values - low) / (high - low)


def _roc_auc(labels: np.ndarray, scores: np.ndarray) -> float:
    positive = scores[labels == 1]
    negative = scores[labels == 0]
    return float(
        np.mean(
            [
                1.0 if p > n else 0.5 if p == n else 0.0
                for p in positive
                for n in negative
            ]
        )
    )


def _brier(labels: np.ndarray, scores: np.ndarray) -> float:
    return float(np.mean((scores - labels) ** 2))


def _birth_class_by_cell(result) -> dict[tuple[int, int], str]:
    classes: dict[tuple[int, int], str] = {}
    for component in result.components:
        for cell in component.birth_cells:
            classes[cell] = component.component_class
    return classes


def run_heldout_validation(
    *,
    support_path: Path,
    mask_path: Path,
    anchors_path: Path,
    candidates_path: Path,
    declaration_path: Path,
) -> ValidationBundle:
    declaration = HeldoutValidationDeclaration.from_dict(
        json.loads(declaration_path.read_text(encoding="utf-8"))
    )
    declaration.validate()

    support = np.load(support_path, allow_pickle=False)
    unavailable = np.load(mask_path, allow_pickle=False)
    if support.ndim != 2 or unavailable.shape != support.shape:
        raise ValueError("support and mask must be matching 2D arrays")
    unavailable = np.asarray(unavailable, dtype=bool)
    anchors = _load_anchors(anchors_path)
    candidates = _load_candidates(candidates_path)

    cells = [(item.row, item.column) for item in candidates]
    for item, cell in zip(candidates, cells):
        if not (0 <= cell[0] < support.shape[0] and 0 <= cell[1] < support.shape[1]):
            raise ValueError(f"candidate outside grid: {item.candidate_id}")
        if unavailable[cell]:
            raise ValueError(f"candidate lies on unavailable cell: {item.candidate_id}")

    # Scores are computed from frozen inputs before labels are used for metrics.
    local_support = np.asarray([support[cell] for cell in cells], dtype=float)
    anchor_cells = tuple(anchors.values())
    distance = np.asarray(
        [min(np.hypot(cell[0] - a[0], cell[1] - a[1]) for a in anchor_cells) for cell in cells],
        dtype=float,
    )
    support_score = _minmax(local_support)
    distance_score = 1.0 - _minmax(distance)
    weight = declaration.support_distance_weight
    combined_score = weight * support_score + (1.0 - weight) * distance_score

    single = infer_support_topology(
        support,
        anchors,
        SupportTopologyConfig(
            (declaration.single_threshold,),
            neighbourhood=declaration.neighbourhood,
            minimum_persistence_steps=1,
            unresolved_below=declaration.unresolved_below,
        ),
        missing_mask=unavailable,
    )
    multi = infer_support_topology(
        support,
        anchors,
        SupportTopologyConfig(
            declaration.thresholds,
            neighbourhood=declaration.neighbourhood,
            minimum_persistence_steps=declaration.minimum_persistence_steps,
            unresolved_below=declaration.unresolved_below,
        ),
        missing_mask=unavailable,
    )
    single_classes = _birth_class_by_cell(single)
    multi_classes = _birth_class_by_cell(multi)
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
    labels = np.asarray([item.detected for item in candidates], dtype=int)
    metrics = {
        name: {"roc_auc": _roc_auc(labels, values), "brier_score": _brier(labels, values)}
        for name, values in scores.items()
    }
    candidate_rows = tuple(
        {
            "candidate_id": item.candidate_id,
            "row": item.row,
            "column": item.column,
            "detected": item.detected,
            "support": float(local_support[index]),
            "distance_to_nearest_anchor": float(distance[index]),
            "single_threshold_class": single_classes.get(cells[index]),
            "multi_threshold_class": multi_classes.get(cells[index]),
            "scores": {name: float(values[index]) for name, values in scores.items()},
        }
        for index, item in enumerate(candidates)
    )
    inputs = {
        path.name: _sha256_file(path)
        for path in (
            support_path,
            mask_path,
            anchors_path,
            candidates_path,
            declaration_path,
        )
    }
    manifest = {
        "declaration": asdict(declaration),
        "input_sha256": inputs,
        "support_shape": list(support.shape),
        "candidate_count": len(candidates),
        "positive_count": int(labels.sum()),
        "topology_fingerprint": multi.fingerprint,
        "method_names": list(METHOD_NAMES),
        "claim_limit": (
            "Scores are comparative diagnostics, not calibrated occurrence probabilities. "
            "This bundle does not establish colonisation, dispersal connectivity, historical routes, "
            "causal barriers, or confirmatory evidence unless the declaration and inputs were frozen independently."
        ),
    }
    payload = {
        "manifest": manifest,
        "metrics": metrics,
        "candidates": list(candidate_rows),
    }
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return ValidationBundle(manifest, metrics, candidate_rows, fingerprint)


def write_validation_bundle(bundle: ValidationBundle, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "validation_bundle.json").write_text(
        json.dumps(bundle.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with (output_dir / "candidate_scores.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "candidate_id",
            "row",
            "column",
            "detected",
            "support",
            "distance_to_nearest_anchor",
            "single_threshold_class",
            "multi_threshold_class",
            *METHOD_NAMES,
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in bundle.candidates:
            flat = {key: value for key, value in row.items() if key != "scores"}
            flat.update(row["scores"])
            writer.writerow(flat)
