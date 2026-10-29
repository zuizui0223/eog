"""Experimental geographical support topology gated by known BAM masks.

Unlike environmental MST diagnostics, these are connected-component lineages
on an explicitly aligned two-dimensional raster. The support field is fixed,
nonnegative and supplied externally; A/B/M are known Boolean constraint grids.
No SDM fit, movement history, population assignment or causal interpretation.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from typing import Any, Mapping

import numpy as np

from .support_topology import (
    SupportGridMetadata,
    SupportTopologyConfig,
    infer_support_topology,
)


_CLASSES = (
    "occurrence_anchored_component",
    "persistent_detached_component",
    "transient_detached_component",
    "low_support_or_unresolved",
)
_GROUPS = ("U", "A", "B", "M", "AB", "AM", "BM", "ABM")


def profile_bam_support_topology(
    support_field: np.ndarray,
    *,
    A: np.ndarray,
    B: np.ndarray,
    M: np.ndarray,
    occurrence_cells: Mapping[str, tuple[int, int]],
    config: SupportTopologyConfig,
    grid: SupportGridMetadata,
    missing_mask: np.ndarray | None = None,
) -> dict[str, Any]:
    """Compare geographic component *lineages* across known BAM constraints.

    Constraint-failed cells receive zero support, never a fabricated missing
    value. All declared thresholds must be strictly positive so failed cells
    cannot enter components. Anchors must be in the declared G=A&B&M.
    """
    support = np.asarray(support_field, dtype=float)
    if support.ndim != 2 or min(support.shape) < 1:
        raise ValueError("support_field must be a nonempty 2D raster")
    missing = (
        np.zeros(support.shape, dtype=bool)
        if missing_mask is None
        else np.asarray(missing_mask)
    )
    if missing.shape != support.shape or missing.dtype.kind != "b":
        raise ValueError("missing_mask must be a Boolean raster of identical shape")
    available = ~missing
    if not available.any():
        raise ValueError("no available raster cells")
    if not np.isfinite(support[available]).all() or np.any(support[available] < 0):
        raise ValueError("available support values must be finite and nonnegative")
    levels = config.validated_thresholds()
    if any(level <= 0 for level in levels):
        raise ValueError("BAM-gated topology thresholds must be strictly positive")
    grid.validate()

    masks: dict[str, np.ndarray] = {}
    for name, value in (("A", A), ("B", B), ("M", M)):
        raw = np.asarray(value)
        if raw.shape != support.shape or raw.dtype.kind != "b":
            raise ValueError(f"{name} must be a Boolean raster matching support_field")
        masks[name] = raw.copy()
    a, b, m = (masks[key] for key in ("A", "B", "M"))
    masks = {
        "U": np.ones(support.shape, dtype=bool),
        "A": a,
        "B": b,
        "M": m,
        "AB": a & b,
        "AM": a & m,
        "BM": b & m,
        "ABM": a & b & m,
    }

    # Explicit compatibility gate; no silent snapping or retroactive world repair.
    for anchor_id, cell in occurrence_cells.items():
        if len(cell) != 2:
            raise ValueError(f"anchor {anchor_id} must have row and column")
        row, col = int(cell[0]), int(cell[1])
        if not (0 <= row < support.shape[0] and 0 <= col < support.shape[1]):
            raise ValueError(f"anchor {anchor_id} is outside support grid")
        if missing[row, col]:
            raise ValueError(f"anchor {anchor_id} occupies a missing cell")
        if not masks["ABM"][row, col]:
            raise ValueError(f"anchor {anchor_id} contradicts BAM G mask")

    summaries = {}
    for name in _GROUPS:
        admitted = masks[name] & available
        # Zero is below all frozen positive thresholds, not 'unknown'.
        gated = np.where(masks[name], support, 0.0)
        topology = infer_support_topology(
            gated, occurrence_cells, config,
            missing_mask=missing, grid=grid,
        )
        summaries[name] = {
            "admitted_cell_count": int(admitted.sum()),
            "active_at_lowest_threshold": int(
                np.count_nonzero(admitted & (support >= min(levels)))
            ),
            "tracked_component_lineages": len(topology.components),
            "lineage_class_counts": {
                klass: sum(
                    item.component_class == klass for item in topology.components
                )
                for klass in _CLASSES
            },
            "topology_fingerprint": topology.fingerprint,
        }

    data: dict[str, Any] = {
        "schema": "eog.bam_gated_spatial_support_topology.v0",
        "scope": "known-mask, frozen-field structural diagnostic only",
        "grid": asdict(grid),
        "config": asdict(config),
        "shape": tuple(int(s) for s in support.shape),
        "anchor_count": len(occurrence_cells),
        "available_cell_count": int(available.sum()),
        "support_sha256": hashlib.sha256(
            np.ascontiguousarray(support, dtype="<f8").tobytes()
        ).hexdigest(),
        "missing_sha256": hashlib.sha256(missing.tobytes()).hexdigest(),
        "masks_sha256": {
            key: hashlib.sha256(value.tobytes()).hexdigest()
            for key, value in masks.items()
        },
        "groups": summaries,
        "limits": (
            "Component lineages are threshold- and neighbourhood-dependent.",
            "Geographic components do not establish dispersal, population identity, "
            "causal barriers or realized occupancy.",
            "BAM masks and support are declared inputs, not inferred mechanisms.",
            "Support must be frozen independently; masked-out cells are zero "
            "support, not unavailable data.",
        ),
    }
    data["fingerprint"] = hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)
        .encode("utf-8")
    ).hexdigest()
    return data
