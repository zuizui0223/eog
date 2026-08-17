#!/usr/bin/env python3
"""Run the prospectively frozen Glanville EOG-WF structural Gate 1.

This runner consumes only the non-response patch network declared in
validation/glanville_eogwf/gate1_scale_adequacy_declaration.json. It must never read
survey_data.tsv or any occupancy/abundance response.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from eog.v2.world_adequacy import (
    StructuralAdequacyDeclaration,
    apply_structural_adequacy_gate,
    audit_world_universe_structure,
)
from eog.v2.world_scale_ladder import (
    StructuralScaleLadderDeclaration,
    build_structural_scale_ladder,
    structural_scale_adjacencies,
)

TARGETS = (0.25, 0.50, 0.75, 0.90)
PROCESS_DISTANCE_KM = 1.0
HORIZON = 1
MAX_ISOLATED_FRACTION = 0.05
MIN_LCC_FRACTION = 0.90
EXPECTED_COLUMNS = ("patch", "x", "y", "area")


def canonical_sha256(payload: object) -> str:
    text = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_patch_network(path: Path) -> tuple[tuple[str, ...], np.ndarray, np.ndarray]:
    node_ids: list[str] = []
    coords: list[tuple[float, float]] = []
    areas: list[float] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != EXPECTED_COLUMNS:
            raise ValueError(
                f"patch_network schema mismatch: {reader.fieldnames!r} != {EXPECTED_COLUMNS!r}"
            )
        for row in reader:
            patch = str(row["patch"]).strip()
            if not patch:
                raise ValueError("empty patch ID")
            x = float(row["x"])
            y = float(row["y"])
            area = float(row["area"])
            if not all(np.isfinite(v) for v in (x, y, area)):
                raise ValueError("patch geometry must be finite")
            if area < 0.0:
                raise ValueError("patch area must be non-negative")
            node_ids.append(patch)
            coords.append((x, y))
            areas.append(area)
    ids = tuple(node_ids)
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("patch IDs must be unique and non-empty")
    return ids, np.asarray(coords, dtype=float), np.asarray(areas, dtype=float)


def euclidean_distance_matrix(coords: np.ndarray) -> np.ndarray:
    sq = np.sum(coords * coords, axis=1)
    dist2 = sq[:, None] + sq[None, :] - 2.0 * (coords @ coords.T)
    matrix = np.sqrt(np.maximum(dist2, 0.0))
    np.fill_diagonal(matrix, 0.0)
    return matrix


def row_to_dict(row) -> dict[str, object]:
    return {
        "world_id": row.world_id,
        "node_count": row.node_count,
        "directed_edge_count": row.directed_edge_count,
        "weak_component_count": row.weak_component_count,
        "largest_weak_component_fraction": row.largest_weak_component_fraction,
        "isolated_node_fraction": row.isolated_node_fraction,
        "mean_out_degree": row.mean_out_degree,
        "median_out_degree": row.median_out_degree,
        "max_out_degree": row.max_out_degree,
        "median_horizon_reachable_fraction": row.median_horizon_reachable_fraction,
        "min_horizon_reachable_fraction": row.min_horizon_reachable_fraction,
        "max_horizon_reachable_fraction": row.max_horizon_reachable_fraction,
        "horizon": row.horizon,
        "fingerprint": row.fingerprint,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--patch-network", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    node_ids, coords, areas = read_patch_network(args.patch_network)
    distance = euclidean_distance_matrix(coords)

    ladder = build_structural_scale_ladder(
        node_ids,
        distance,
        StructuralScaleLadderDeclaration(
            axis_id="geo",
            target_largest_component_fractions=TARGETS,
        ),
    )
    structural = structural_scale_adjacencies(ladder, distance)

    process = distance <= PROCESS_DISTANCE_KM + 1e-12
    np.fill_diagonal(process, False)
    worlds: dict[str, np.ndarray] = {"process_mean_dispersal_1km": process}
    for world_id, adjacency in structural.items():
        worlds[f"structural::{world_id}"] = adjacency

    audit = audit_world_universe_structure(node_ids, worlds, horizon=HORIZON)
    declaration = StructuralAdequacyDeclaration(
        min_largest_weak_component_fraction=MIN_LCC_FRACTION,
        max_isolated_node_fraction=MAX_ISOLATED_FRACTION,
        require_at_least_one_world_pass=True,
    )
    gate = apply_structural_adequacy_gate(audit, declaration)

    audits = {row.world_id: row for row in audit.world_audits}
    level90_id = "structural::geo_lcc900"
    if level90_id not in audits:
        raise RuntimeError("expected structural 0.90 world is missing")
    level90 = audits[level90_id]

    rounded_thresholds = {round(value, 12) for value in ladder.thresholds if value > 0.0}
    distinct_scale_pass = len(rounded_thresholds) >= 3
    level90_pass = (
        level90.largest_weak_component_fraction >= MIN_LCC_FRACTION - 1e-12
        and level90.isolated_node_fraction <= MAX_ISOLATED_FRACTION + 1e-12
    )
    structural_passing_worlds = tuple(
        row.world_id
        for row in gate.world_results
        if row.passed and row.world_id.startswith("structural::")
    )
    final_pass = bool(gate.passed and level90_pass and distinct_scale_pass and structural_passing_worlds)

    payload = {
        "status": "gate1_pass_structural_adequacy" if final_pass else "gate1_stop_structural_inadequacy",
        "response_content_opened": False,
        "response_file_read": False,
        "node_count": len(node_ids),
        "patch_network_schema": list(EXPECTED_COLUMNS),
        "coordinate_units": "km",
        "coordinate_reference_system": "EPSG:3067",
        "area_summary_ha": {
            "min": float(np.min(areas)),
            "median": float(np.median(areas)),
            "max": float(np.max(areas)),
        },
        "process_reference": {
            "world_id": "process_mean_dispersal_1km",
            "distance_threshold_km": PROCESS_DISTANCE_KM,
            "interpretation": "mean dispersal reference; not maximum dispersal distance",
        },
        "structural_targets": list(TARGETS),
        "structural_ladder": [
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
        "distinct_positive_structural_thresholds": len(rounded_thresholds),
        "world_audits": [row_to_dict(row) for row in audit.world_audits],
        "audit_fingerprint": audit.fingerprint,
        "gate_fingerprint": gate.fingerprint,
        "generic_gate_passing_world_ids": list(gate.passing_world_ids),
        "structural_gate_passing_world_ids": list(structural_passing_worlds),
        "level90_pass": level90_pass,
        "distinct_scale_pass": distinct_scale_pass,
        "final_gate_pass": final_pass,
        "stop_rule": "If final_gate_pass is false, do not read survey_data.tsv response fields.",
    }
    payload["fingerprint"] = canonical_sha256(payload)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))

    if not final_pass:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
