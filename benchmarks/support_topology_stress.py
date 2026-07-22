"""Frozen stress benchmark for EOG spatial support topology.

The benchmark evaluates whether the two headline structural classes in a
synthetic two-island field remain identifiable under predeclared changes to
threshold sequence, neighbourhood, raster resolution, support noise, and
occurrence-anchor position. It does not evaluate occupancy prediction or claim
superiority over SDMs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import numpy as np

from eog import SupportGridMetadata, SupportTopologyConfig, infer_support_topology


def synthetic_island_field() -> tuple[np.ndarray, np.ndarray]:
    """Return a frozen two-island support field and hard sea mask."""

    support = np.full((7, 13), 0.05, dtype=float)
    sea = np.ones_like(support, dtype=bool)

    # Western island: historical occurrence anchored.
    sea[1:6, 1:5] = False
    support[1:6, 1:5] = np.array(
        [
            [0.72, 0.78, 0.76, 0.70],
            [0.79, 0.88, 0.86, 0.77],
            [0.81, 0.91, 0.89, 0.80],
            [0.76, 0.85, 0.83, 0.75],
            [0.68, 0.74, 0.72, 0.66],
        ]
    )

    # Eastern island: identical local support range but no historical anchor.
    sea[1:6, 8:12] = False
    support[1:6, 8:12] = np.array(
        [
            [0.70, 0.76, 0.78, 0.72],
            [0.77, 0.86, 0.88, 0.79],
            [0.80, 0.89, 0.91, 0.81],
            [0.75, 0.83, 0.85, 0.76],
            [0.66, 0.72, 0.74, 0.68],
        ]
    )

    # A near-threshold one-cell patch tests transient noise sensitivity.
    sea[0, 6] = False
    support[0, 6] = 0.705
    return support, sea


def _class_signature(result) -> dict[str, int]:
    counts: dict[str, int] = {}
    for component in result.components:
        counts[component.component_class] = counts.get(component.component_class, 0) + 1
    return counts


def _headline_retained(result) -> bool:
    classes = {component.component_class for component in result.components}
    return {
        "occurrence_anchored_component",
        "persistent_detached_component",
    }.issubset(classes)


def _run(
    support: np.ndarray,
    sea: np.ndarray,
    *,
    thresholds: Iterable[float],
    neighbourhood: int = 4,
    anchor: tuple[int, int] = (2, 2),
    resolution_scale: int = 1,
):
    if resolution_scale < 1:
        raise ValueError("resolution_scale must be at least 1")
    if resolution_scale > 1:
        support = np.repeat(np.repeat(support, resolution_scale, axis=0), resolution_scale, axis=1)
        sea = np.repeat(np.repeat(sea, resolution_scale, axis=0), resolution_scale, axis=1)
        anchor = (anchor[0] * resolution_scale, anchor[1] * resolution_scale)
    return infer_support_topology(
        support,
        {"historical_west": anchor},
        SupportTopologyConfig(
            thresholds=tuple(thresholds),
            neighbourhood=neighbourhood,
            minimum_persistence_steps=2,
            unresolved_below=0.55,
        ),
        missing_mask=sea,
        grid=SupportGridMetadata(
            x_resolution=1.0 / resolution_scale,
            y_resolution=-1.0 / resolution_scale,
            crs="synthetic_equal_area",
        ),
    )


def run_benchmark(seed: int = 20260722, noise_replicates: int = 50) -> dict[str, object]:
    support, sea = synthetic_island_field()
    baseline = _run(support, sea, thresholds=(0.80, 0.70, 0.60))
    if not _headline_retained(baseline):
        raise AssertionError("baseline must contain anchored and persistent detached components")

    threshold_sequences = {
        "coarse": (0.80, 0.70, 0.60),
        "dense": (0.85, 0.80, 0.75, 0.70, 0.65, 0.60),
        "shifted": (0.82, 0.72, 0.62),
        "lower_tail": (0.80, 0.70, 0.60, 0.50),
    }
    threshold_rows = []
    for scenario_id, thresholds in threshold_sequences.items():
        result = _run(support, sea, thresholds=thresholds)
        threshold_rows.append(
            {
                "scenario_id": scenario_id,
                "thresholds": list(thresholds),
                "headline_retained": _headline_retained(result),
                "class_counts": _class_signature(result),
                "fingerprint": result.fingerprint,
            }
        )

    neighbourhood_rows = []
    for neighbourhood in (4, 8):
        result = _run(
            support,
            sea,
            thresholds=(0.80, 0.70, 0.60),
            neighbourhood=neighbourhood,
        )
        neighbourhood_rows.append(
            {
                "neighbourhood": neighbourhood,
                "headline_retained": _headline_retained(result),
                "class_counts": _class_signature(result),
                "fingerprint": result.fingerprint,
            }
        )

    resolution_rows = []
    for scale in (1, 2, 3):
        result = _run(
            support,
            sea,
            thresholds=(0.80, 0.70, 0.60),
            resolution_scale=scale,
        )
        detached = [
            component
            for component in result.components
            if component.component_class == "persistent_detached_component"
        ]
        resolution_rows.append(
            {
                "resolution_scale": scale,
                "headline_retained": _headline_retained(result),
                "detached_area": None if not detached else detached[0].area,
                "class_counts": _class_signature(result),
                "fingerprint": result.fingerprint,
            }
        )

    anchor_rows = []
    for anchor in ((1, 1), (1, 4), (4, 1), (4, 4), (2, 2)):
        result = _run(
            support,
            sea,
            thresholds=(0.80, 0.70, 0.60),
            anchor=anchor,
        )
        anchor_rows.append(
            {
                "anchor": list(anchor),
                "headline_retained": _headline_retained(result),
                "class_counts": _class_signature(result),
                "fingerprint": result.fingerprint,
            }
        )

    rng = np.random.default_rng(seed)
    available = ~sea
    noise_rows = []
    for replicate in range(noise_replicates):
        perturbed = support.copy()
        perturbed[available] = np.clip(
            perturbed[available] + rng.normal(0.0, 0.02, size=int(available.sum())),
            0.0,
            1.0,
        )
        result = _run(perturbed, sea, thresholds=(0.80, 0.70, 0.60))
        noise_rows.append(
            {
                "replicate": replicate,
                "headline_retained": _headline_retained(result),
                "transient_count": _class_signature(result).get("transient_detached_component", 0),
                "fingerprint": result.fingerprint,
            }
        )

    summary = {
        "threshold_retention": float(np.mean([row["headline_retained"] for row in threshold_rows])),
        "neighbourhood_retention": float(np.mean([row["headline_retained"] for row in neighbourhood_rows])),
        "resolution_retention": float(np.mean([row["headline_retained"] for row in resolution_rows])),
        "anchor_retention": float(np.mean([row["headline_retained"] for row in anchor_rows])),
        "noise_retention": float(np.mean([row["headline_retained"] for row in noise_rows])),
        "noise_transient_frequency": float(np.mean([row["transient_count"] > 0 for row in noise_rows])),
    }

    return {
        "benchmark": "support_topology_stress_v1",
        "seed": seed,
        "noise_replicates": noise_replicates,
        "baseline": {
            "class_counts": _class_signature(baseline),
            "fingerprint": baseline.fingerprint,
        },
        "summary": summary,
        "threshold_scenarios": threshold_rows,
        "neighbourhood_scenarios": neighbourhood_rows,
        "resolution_scenarios": resolution_rows,
        "anchor_scenarios": anchor_rows,
        "noise_scenarios": noise_rows,
        "claim_limit": (
            "Retention describes this frozen synthetic structure only; it does not establish "
            "occupancy prediction, dispersal connectivity, or superiority over support-only baselines."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260722)
    parser.add_argument("--noise-replicates", type=int, default=50)
    args = parser.parse_args()
    result = run_benchmark(seed=args.seed, noise_replicates=args.noise_replicates)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
