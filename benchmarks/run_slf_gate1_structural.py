#!/usr/bin/env python3
"""Run response-blind structural Gate 1 for the spotted-lanternfly candidate."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

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
EARTH_RADIUS_KM = 6371.0088
EXCLUDED_USPS = {"AK", "HI", "PR"}
EXPECTED_NODE_COUNT = 3108
EXPECTED_GEOMETRY_FINGERPRINT = "5b05192ae33e398c5381bdab37db048373e61e9cd84523fc4f48b7a2bc8dbb07"
DISTANCE_TOLERANCE = 1e-12


def canonical_sha256(payload: object) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize(row: dict[str, str]) -> dict[str, str]:
    return {str(key).strip(): str(value).strip() for key, value in row.items()}


def read_nodes(zip_path: Path) -> tuple[tuple[str, ...], np.ndarray, str]:
    with zipfile.ZipFile(zip_path) as zf:
        names = [name for name in zf.namelist() if name.lower().endswith(".txt")]
        if len(names) != 1:
            raise ValueError(f"expected one county Gazetteer text member, found {names!r}")
        member = names[0]
        text = zf.read(member).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    required = {"USPS", "GEOID", "INTPTLAT", "INTPTLONG"}
    fields = {str(value).strip() for value in (reader.fieldnames or ())}
    if not required.issubset(fields):
        raise ValueError(f"Census schema mismatch: {sorted(fields)!r}")
    rows: list[tuple[str, float, float]] = []
    for raw in reader:
        row = normalize(raw)
        if row["USPS"] in EXCLUDED_USPS:
            continue
        rows.append((row["GEOID"], float(row["INTPTLAT"]), float(row["INTPTLONG"])))
    rows.sort(key=lambda value: value[0])
    node_ids = tuple(value[0] for value in rows)
    coords = np.asarray([[value[1], value[2]] for value in rows], dtype=float)
    if len(node_ids) != EXPECTED_NODE_COUNT or len(set(node_ids)) != len(node_ids):
        raise ValueError("Census node universe differs from frozen Gate 0")
    geometry_fingerprint = canonical_sha256(
        [[node_id, float(lat), float(lon)] for node_id, (lat, lon) in zip(node_ids, coords, strict=True)]
    )
    if geometry_fingerprint != EXPECTED_GEOMETRY_FINGERPRINT:
        raise ValueError("Census geometry fingerprint differs from Gate 0")
    return node_ids, coords, member


def haversine_matrix(coords_deg: np.ndarray) -> np.ndarray:
    lat = np.deg2rad(coords_deg[:, 0])
    lon = np.deg2rad(coords_deg[:, 1])
    xyz = np.column_stack((np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)))
    cosine = np.clip(xyz @ xyz.T, -1.0, 1.0)
    matrix = EARTH_RADIUS_KM * np.arccos(cosine)
    matrix = (matrix + matrix.T) / 2.0
    np.fill_diagonal(matrix, 0.0)
    return matrix


def distinct_threshold_count(values: tuple[float, ...]) -> int:
    if not values:
        return 0
    ordered = sorted(float(value) for value in values if value > 0.0)
    if not ordered:
        return 0
    groups = 1
    previous = ordered[0]
    for value in ordered[1:]:
        if value > previous + DISTANCE_TOLERANCE:
            groups += 1
            previous = value
    return groups


def audit_row(row) -> dict[str, object]:
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
    parser.add_argument("--census-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    node_ids, coords, member = read_nodes(args.census_zip)
    distance = haversine_matrix(coords)
    declaration = StructuralScaleLadderDeclaration(
        axis_id="geo",
        target_largest_component_fractions=TARGETS,
    )
    ladder = build_structural_scale_ladder(node_ids, distance, declaration)
    worlds = structural_scale_adjacencies(ladder, distance)
    audit = audit_world_universe_structure(node_ids, worlds, horizon=1)
    generic_gate = apply_structural_adequacy_gate(
        audit,
        StructuralAdequacyDeclaration(
            min_largest_weak_component_fraction=0.90,
            max_isolated_node_fraction=0.05,
            require_at_least_one_world_pass=True,
        ),
    )

    by_id = {row.world_id: row for row in audit.world_audits}
    level90 = by_id.get("geo_lcc900")
    if level90 is None:
        raise RuntimeError("missing frozen geo_lcc900 structural level")
    distinct = distinct_threshold_count(ladder.thresholds)
    level90_pass = bool(
        level90.largest_weak_component_fraction >= 0.90 - DISTANCE_TOLERANCE
        and level90.isolated_node_fraction <= 0.05 + DISTANCE_TOLERANCE
    )
    nested = all(
        np.all(~worlds[ladder.level_ids[index]] | worlds[ladder.level_ids[index + 1]])
        for index in range(len(ladder.level_ids) - 1)
    )
    final_pass = bool(level90_pass and distinct >= 3 and nested and generic_gate.passed)

    payload = {
        "status": "gate1_pass_structural_adequacy" if final_pass else "gate1_stop_structural_inadequacy",
        "candidate": "Spotted lanternfly US county invasion 2014-2021",
        "response_rows_opened": False,
        "response_values_parsed": False,
        "node_count": len(node_ids),
        "census_member": member,
        "geometry_fingerprint": EXPECTED_GEOMETRY_FINGERPRINT,
        "distance_metric": "Haversine county internal-point distance km",
        "earth_radius_km": EARTH_RADIUS_KM,
        "ladder_fingerprint": ladder.fingerprint,
        "distance_matrix_fingerprint": ladder.distance_matrix_fingerprint,
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
        "distinct_positive_thresholds": distinct,
        "nested": nested,
        "lcc90_pass": level90_pass,
        "world_audits": [audit_row(row) for row in audit.world_audits],
        "audit_fingerprint": audit.fingerprint,
        "generic_gate_fingerprint": generic_gate.fingerprint,
        "generic_gate_passing_world_ids": list(generic_gate.passing_world_ids),
        "final_gate_pass": final_pass,
        "next": "freeze Layer-A rules and Layer-B/comparator contract" if final_pass else "stop before response access",
    }
    payload["fingerprint"] = canonical_sha256(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "thresholds_km": [level["distance_threshold_km"] for level in payload["levels"]],
        "achieved_lcc": [level["achieved_largest_component_fraction"] for level in payload["levels"]],
        "isolated": [level["isolated_node_fraction"] for level in payload["levels"]],
        "distinct_positive_thresholds": distinct,
        "nested": nested,
        "fingerprint": payload["fingerprint"],
    }, indent=2, sort_keys=True))
    if not final_pass:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
