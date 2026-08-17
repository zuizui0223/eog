#!/usr/bin/env python3
"""Run the frozen response-blind rabies structural Gate 1.

Consumes only the non-response grid geometry in CovariateData.csv.  No surveillance
rows, sample counts or rabies-positive counts are accepted by this runner.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from eog.v2.world_adequacy import audit_world_universe_structure
from eog.v2.world_scale_ladder import (
    StructuralScaleLadderDeclaration,
    build_structural_scale_ladder,
    structural_scale_adjacencies,
)

TARGETS = (0.25, 0.50, 0.75, 0.90)
MIN_DISTINCT_POSITIVE_THRESHOLDS = 3
MIN_LCC_90 = 0.90
MAX_ISOLATED_90 = 0.05
EARTH_RADIUS_KM = 6371.0088


def canonical_sha256(payload: object) -> str:
    text = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_geometry(path: Path) -> tuple[tuple[str, ...], np.ndarray]:
    ids: list[str] = []
    coords: list[tuple[float, float]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"Site", "Longitude", "Latitude"}
        if not required.issubset(reader.fieldnames or ()):
            raise ValueError(f"missing required non-response columns: {reader.fieldnames!r}")
        for row in reader:
            site = str(row["Site"]).strip()
            lon = float(row["Longitude"])
            lat = float(row["Latitude"])
            if not site or not np.isfinite(lon) or not np.isfinite(lat):
                raise ValueError("site geometry must be finite and non-empty")
            ids.append(site)
            coords.append((lat, lon))
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("site IDs must be unique and non-empty")
    array = np.asarray(coords, dtype=float)
    if len({tuple(row) for row in array.tolist()}) != len(ids):
        raise ValueError("duplicate site centroids are not allowed")
    return tuple(ids), array


def haversine_matrix(coords_lat_lon_deg: np.ndarray) -> np.ndarray:
    lat = np.deg2rad(coords_lat_lon_deg[:, 0])
    lon = np.deg2rad(coords_lat_lon_deg[:, 1])
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(dlon / 2.0) ** 2
    )
    matrix = 2.0 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))
    np.fill_diagonal(matrix, 0.0)
    return matrix


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--covariates", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    node_ids, coords = read_geometry(args.covariates)
    distance = haversine_matrix(coords)
    declaration = StructuralScaleLadderDeclaration(
        axis_id="geo",
        target_largest_component_fractions=TARGETS,
    )
    ladder = build_structural_scale_ladder(node_ids, distance, declaration)
    worlds = {
        f"structural::{world_id}": adjacency
        for world_id, adjacency in structural_scale_adjacencies(ladder, distance).items()
    }
    audit = audit_world_universe_structure(node_ids, worlds, horizon=1)
    by_id = {row.world_id: row for row in audit.world_audits}

    level90_id = "structural::geo_lcc900"
    level90 = by_id[level90_id]
    distinct = len({round(value, 12) for value in ladder.thresholds if value > 0.0})
    lcc90_pass = level90.largest_weak_component_fraction >= MIN_LCC_90 - 1e-12
    isolated90_pass = level90.isolated_node_fraction <= MAX_ISOLATED_90 + 1e-12
    distinct_pass = distinct >= MIN_DISTINCT_POSITIVE_THRESHOLDS
    final_pass = bool(lcc90_pass and isolated90_pass and distinct_pass)

    result = {
        "status": (
            "gate1_pass_structural_scale_adequacy"
            if final_pass
            else "gate1_stop_structural_scale_diversity_failed"
        ),
        "response_rows_opened": False,
        "node_count": len(node_ids),
        "distance_metric": "Haversine_km",
        "target_largest_component_fractions": list(TARGETS),
        "minimum_distinct_positive_thresholds": MIN_DISTINCT_POSITIVE_THRESHOLDS,
        "distinct_positive_thresholds": distinct,
        "lcc90_requirement": MIN_LCC_90,
        "isolated90_maximum": MAX_ISOLATED_90,
        "lcc90_pass": lcc90_pass,
        "isolated90_pass": isolated90_pass,
        "distinct_scale_pass": distinct_pass,
        "final_gate_pass": final_pass,
        "levels": [
            {
                "level_id": level.level_id,
                "target_largest_component_fraction": level.target_largest_component_fraction,
                "distance_threshold_km": level.distance_threshold,
                "achieved_largest_component_fraction": level.achieved_largest_component_fraction,
                "weak_component_count": level.weak_component_count,
                "isolated_node_fraction": level.isolated_node_fraction,
                "directed_edge_count": level.directed_edge_count,
                "fingerprint": level.fingerprint,
            }
            for level in ladder.levels
        ],
        "ladder_fingerprint": ladder.fingerprint,
        "audit_fingerprint": audit.fingerprint,
        "stop_rule": (
            "If final_gate_pass is false, do not read SurveillanceData.csv data rows; "
            "do not substitute kNN, arbitrary distance thresholds, process distances, "
            "or response-tuned worlds to rescue this candidate."
        ),
    }
    result["fingerprint"] = canonical_sha256(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not final_pass:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
