"""Prepare outcome-free, focal-preserving Tanzania current-flow rasters."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import rasterio
from affine import Affine
from rasterio.transform import rowcol

from eog.tanzania_current_flow_candidates import (
    COARSENING_FACTOR,
    FOCAL_FIELD,
    N_FOCAL_PATCHES,
    SOURCE_AUDIT_FINGERPRINT,
    PreparedCurrentFlowRegion,
    canonical_sha256,
    coarsen_categorical_raster,
    write_prepared_region,
)


def _verify_source_audit(path: Path) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("audit_fingerprint") != SOURCE_AUDIT_FINGERPRINT:
        raise ValueError("Tanzania current-flow source audit fingerprint drift")
    repairs = report.get("heldout_competitor_repairs") or {}
    if repairs.get("focal_raster_field") != FOCAL_FIELD:
        raise ValueError("focal raster field drifted from patch_number repair")
    if any((report.get("scientific_boundary") or {}).values()):
        raise ValueError("source audit crossed its pre-outcome scientific boundary")
    return report


def _factor_uniqueness(rows: np.ndarray, cols: np.ndarray, factor: int) -> dict[str, int]:
    cells = [(int(row) // factor, int(col) // factor) for row, col in zip(rows, cols, strict=True)]
    return {
        "factor": int(factor),
        "n_focal_rows": len(cells),
        "n_unique_focal_cells": len(set(cells)),
        "n_collapsed_focals": len(cells) - len(set(cells)),
    }


def prepare_region(source_dir: Path, output_dir: Path, region: str) -> tuple[dict[str, Any], str]:
    raster_name = "raster_east3.tif" if region == "E" else "raster_west3.tif"
    nodes = pd.read_csv(source_dir / f"Nodes_{region}.csv").sort_values("patch_number")
    if len(nodes) != N_FOCAL_PATCHES or nodes["patch_number"].tolist() != list(range(1, 43)):
        raise ValueError(f"{region} node table must contain patch numbers 1..42")
    with rasterio.open(source_dir / raster_name) as dataset:
        classes = dataset.read(1)
        transform = dataset.transform
        nodata = int(dataset.nodata if dataset.nodata is not None else 255)
        raster_metadata = {
            "filename": raster_name,
            "crs": str(dataset.crs),
            "fine_shape": [int(dataset.height), int(dataset.width)],
            "fine_transform": list(transform)[:6],
            "fine_resolution": [float(value) for value in dataset.res],
            "nodata": nodata,
        }
    focal_rows, focal_cols = rowcol(
        transform,
        nodes["centroid_long"].to_numpy(float),
        nodes["centroid_lat"].to_numpy(float),
    )
    focal_cells = list(zip(np.asarray(focal_rows, dtype=int), np.asarray(focal_cols, dtype=int), strict=True))
    uniqueness = {
        str(factor): _factor_uniqueness(np.asarray(focal_rows), np.asarray(focal_cols), factor)
        for factor in (32, 16, 8)
    }
    if uniqueness["8"]["n_unique_focal_cells"] != N_FOCAL_PATCHES:
        raise ValueError(f"{region} factor-8 raster collapses focal identities")
    coarse, coarsening = coarsen_categorical_raster(
        classes,
        factor=COARSENING_FACTOR,
        nodata=nodata,
        focal_fine_cells=focal_cells,
    )
    coarse_width = coarse.shape[1]
    focal_flat = np.asarray(
        [(row // COARSENING_FACTOR) * coarse_width + (col // COARSENING_FACTOR) for row, col in focal_cells],
        dtype=np.int64,
    )
    coarse_transform = transform * Affine.scale(COARSENING_FACTOR, COARSENING_FACTOR)
    metadata = {
        "region": region,
        "source_audit_fingerprint": SOURCE_AUDIT_FINGERPRINT,
        "coarsening": coarsening,
        "focal_uniqueness_by_factor": uniqueness,
        "resolution_selection_rule": (
            "choose the coarsest power-of-two aggregation factor shared by both regions "
            "that preserves all 42 explicit patch_number focal identities; factor 16 "
            "collapses East focal patches, so factor 8 is fixed before species outcomes"
        ),
        "categorical_aggregation": "block mode with smallest-class tie break and fine-cell focal-class preservation",
        "coarse_transform": list(coarse_transform)[:6],
        "coarse_resolution": [
            abs(float(coarse_transform.a)),
            abs(float(coarse_transform.e)),
        ],
        "raster": raster_metadata,
        "species_outcomes_inspected": False,
    }
    prepared = PreparedCurrentFlowRegion(
        region=region,
        classes=coarse,
        focal_patch_numbers=nodes["patch_number"].to_numpy(np.int64),
        focal_flat_indices=focal_flat,
        focal_areas_ha=nodes["Area_ha"].to_numpy(float),
        metadata=metadata,
    )
    path = output_dir / f"prepared_{region}.npz"
    fingerprint = write_prepared_region(path, prepared)
    return {
        "region": region,
        "prepared_file": path.name,
        "prepared_fingerprint": fingerprint,
        "metadata": metadata,
    }, fingerprint


def prepare(source_dir: Path, source_audit: Path, output_dir: Path) -> dict[str, Any]:
    _verify_source_audit(source_audit)
    output_dir.mkdir(parents=True, exist_ok=True)
    regions = {}
    for region in ("E", "W"):
        summary, _ = prepare_region(source_dir, output_dir, region)
        regions[region] = summary
    if regions["E"]["metadata"]["focal_uniqueness_by_factor"]["16"]["n_unique_focal_cells"] >= 42:
        raise ValueError("expected factor-16 East focal collapse was not observed")
    manifest = {
        "status": "tanzania_current_flow_inputs_prepared_before_species_outcomes",
        "source_audit_fingerprint": SOURCE_AUDIT_FINGERPRINT,
        "coarsening_factor": COARSENING_FACTOR,
        "regions": regions,
        "solver_semantics": {
            "data_type": "raster",
            "scenario": "pairwise_effective_resistance",
            "habitat_map_is_resistances": True,
            "connect_four_neighbors_only": False,
            "neighbourhood": 8,
            "connect_using_avg_resistances": False,
            "edge_rule": "average adjacent cell conductances; diagonal conductance divided by sqrt(2)",
            "focal_field": FOCAL_FIELD,
        },
        "scientific_boundary": {
            "species_outcomes_inspected": False,
            "current_flow_computed": False,
            "resistance_selected": False,
            "occurrence_model_fitted": False,
            "eog_performance_inspected": False,
        },
    }
    manifest["preparation_fingerprint"] = canonical_sha256(manifest)
    (output_dir / "preparation_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--source-audit", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source_dir, args.source_audit, args.output_dir), indent=2))


if __name__ == "__main__":
    main()
