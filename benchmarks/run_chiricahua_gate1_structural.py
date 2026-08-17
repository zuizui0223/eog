#!/usr/bin/env python3
"""Run the frozen response-blind Chiricahua leopard frog structural Gate 1.

Only coords.dryad.csv and water.dryad.csv are consumed. The detection-history file
``y.wide.dryad.csv`` is forbidden. Structural thresholds are analyst-choice graph
scales, not inferred biological dispersal limits.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
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
EXPECTED_NODE_COUNT = 274
FOUNDER_INDICES_1_BASED = (15, 33, 274)
SAMPLED_SITE_COUNT = 47
HORIZON = 14
MIN_LCC = 0.90
MAX_ISOLATED = 0.05


def canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def read_coords(path: Path) -> tuple[tuple[str, ...], np.ndarray, tuple[str, ...]]:
    ids: list[str] = []
    coords: list[tuple[float, float]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = tuple(next(reader))
        if header != ("", "x", "y"):
            raise ValueError(f"unexpected coordinate header: {header!r}")
        for row_number, row in enumerate(reader, start=2):
            if len(row) != 3:
                raise ValueError(f"coordinate row {row_number} has {len(row)} fields")
            node_id = str(row[0]).strip()
            if not node_id:
                raise ValueError(f"empty node ID at coordinate row {row_number}")
            x = float(row[1])
            y = float(row[2])
            if not np.isfinite(x) or not np.isfinite(y):
                raise ValueError(f"non-finite coordinate at row {row_number}")
            ids.append(node_id)
            coords.append((x, y))
    node_ids = tuple(ids)
    if len(node_ids) != EXPECTED_NODE_COUNT:
        raise ValueError(f"expected {EXPECTED_NODE_COUNT} nodes, found {len(node_ids)}")
    if len(set(node_ids)) != len(node_ids):
        raise ValueError("coordinate node IDs are not unique")
    return node_ids, np.asarray(coords, dtype=float), header


def read_hydroperiod(path: Path, node_ids: tuple[str, ...]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    ids: list[str] = []
    classes: list[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = tuple(next(reader))
        if header != ("", "x"):
            raise ValueError(f"unexpected hydroperiod header: {header!r}")
        for row_number, row in enumerate(reader, start=2):
            if len(row) != 2:
                raise ValueError(f"hydroperiod row {row_number} has {len(row)} fields")
            node_id = str(row[0]).strip()
            value = str(row[1]).strip()
            if not node_id or not value:
                raise ValueError(f"empty hydroperiod identity/value at row {row_number}")
            ids.append(node_id)
            classes.append(value)
    if tuple(ids) != node_ids:
        raise ValueError("hydroperiod node IDs/order differ from coordinate node universe")
    return tuple(classes), header


def euclidean_km(coords_m: np.ndarray) -> np.ndarray:
    sq = np.sum(coords_m * coords_m, axis=1)
    dist2 = sq[:, None] + sq[None, :] - 2.0 * (coords_m @ coords_m.T)
    matrix = np.sqrt(np.maximum(dist2, 0.0)) / 1000.0
    np.fill_diagonal(matrix, 0.0)
    return matrix


def audit_to_dict(row) -> dict[str, object]:
    return {
        "world_id": row.world_id,
        "node_count": row.node_count,
        "directed_edge_count": row.directed_edge_count,
        "weak_component_count": row.weak_component_count,
        "largest_weak_component_size": row.largest_weak_component_size,
        "largest_weak_component_fraction": row.largest_weak_component_fraction,
        "isolated_node_count": row.isolated_node_count,
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
    parser.add_argument("--coords", type=Path, required=True)
    parser.add_argument("--hydroperiod", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    node_ids, coords, coord_header = read_coords(args.coords)
    hydroperiod, hydro_header = read_hydroperiod(args.hydroperiod, node_ids)
    distance = euclidean_km(coords)

    ladder = build_structural_scale_ladder(
        node_ids,
        distance,
        StructuralScaleLadderDeclaration(
            axis_id="geo",
            target_largest_component_fractions=TARGETS,
        ),
    )
    structural = structural_scale_adjacencies(ladder, distance)
    worlds = {f"structural::{world_id}": adjacency for world_id, adjacency in structural.items()}

    audit = audit_world_universe_structure(node_ids, worlds, horizon=HORIZON)
    gate = apply_structural_adequacy_gate(
        audit,
        StructuralAdequacyDeclaration(
            min_largest_weak_component_fraction=MIN_LCC,
            max_isolated_node_fraction=MAX_ISOLATED,
            require_at_least_one_world_pass=True,
        ),
    )

    audits = {row.world_id: row for row in audit.world_audits}
    level90_id = "structural::geo_lcc900"
    if level90_id not in audits:
        raise RuntimeError("expected structural 0.90 world is absent")
    level90 = audits[level90_id]

    positive_thresholds = [value for value in ladder.thresholds if value > 0.0]
    distinct_threshold_count = len({round(value, 12) for value in positive_thresholds})
    distinct_scale_pass = distinct_threshold_count >= 3
    level90_pass = (
        level90.largest_weak_component_fraction >= MIN_LCC - 1e-12
        and level90.isolated_node_fraction <= MAX_ISOLATED + 1e-12
    )

    ordered_adjacencies = [structural[level.level_id] for level in ladder.levels]
    nested_pass = all(
        np.all(~earlier | later)
        for earlier, later in zip(ordered_adjacencies, ordered_adjacencies[1:])
    )
    final_pass = bool(gate.passed and level90_pass and distinct_scale_pass and nested_pass)

    founders = tuple(node_ids[index - 1] for index in FOUNDER_INDICES_1_BASED)
    sampled_ids = node_ids[:SAMPLED_SITE_COUNT]
    x_values = coords[:, 0]
    y_values = coords[:, 1]

    payload: dict[str, object] = {
        "status": "gate1_pass_structural_adequacy" if final_pass else "gate1_stop_structural_inadequacy",
        "response_rows_opened": False,
        "detection_file_read": False,
        "node_count": len(node_ids),
        "coordinate_header": list(coord_header),
        "hydroperiod_header": list(hydro_header),
        "coordinate_units": "projected metres; pairwise distances converted to kilometres",
        "coordinate_range": {
            "x_min": float(np.min(x_values)),
            "x_max": float(np.max(x_values)),
            "y_min": float(np.min(y_values)),
            "y_max": float(np.max(y_values)),
        },
        "node_ids_fingerprint": canonical_sha256(list(node_ids)),
        "founder_indices_1_based": list(FOUNDER_INDICES_1_BASED),
        "founder_node_ids": list(founders),
        "sampled_site_count": SAMPLED_SITE_COUNT,
        "sampled_node_ids_fingerprint": canonical_sha256(list(sampled_ids)),
        "hydroperiod_counts": dict(sorted(Counter(hydroperiod).items())),
        "hydroperiod_fingerprint": canonical_sha256(
            [[node_id, value] for node_id, value in zip(node_ids, hydroperiod, strict=True)]
        ),
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
        "distinct_positive_structural_thresholds": distinct_threshold_count,
        "world_audits": [audit_to_dict(row) for row in audit.world_audits],
        "audit_horizon": HORIZON,
        "audit_fingerprint": audit.fingerprint,
        "gate_fingerprint": gate.fingerprint,
        "generic_gate_passing_world_ids": list(gate.passing_world_ids),
        "level90_pass": level90_pass,
        "distinct_scale_pass": distinct_scale_pass,
        "nested_scale_pass": nested_pass,
        "final_gate_pass": final_pass,
        "scientific_boundary": "Structural thresholds are response-blind analyst-choice scales. They are not frog dispersal limits.",
        "stop_rule": "If final_gate_pass is false, do not read y.wide.dryad.csv.",
    }
    payload["fingerprint"] = canonical_sha256(payload)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))

    if not final_pass:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
