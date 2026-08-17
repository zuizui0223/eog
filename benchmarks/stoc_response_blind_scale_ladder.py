#!/usr/bin/env python3
"""Post-hoc, response-blind structural scale-ladder diagnostic for STOC.

This script is NOT a STOC rescue analysis. It reads only site/period/coordinate and
six environmental columns, never species responses. Its sole purpose is to show how
the generic structural scale-ladder constructor brackets local-to-spanning graph
regimes on the same node universe whose frozen nearest-neighbour quantile worlds were
all falsified during the independent attempt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from eog.v2.world_adequacy import audit_world_universe_structure
from eog.v2.world_scale_ladder import (
    StructuralScaleLadderDeclaration,
    build_structural_scale_ladder,
    compose_intersection_worlds,
    structural_scale_adjacencies,
)

EXPECTED_BLOB_SHA = "4bfa2cd39a7e90340ad6a319e5c611e8646462c8"
EXPECTED_SIZE = 330891
CALIBRATION_PERIOD = "2006-2011"
EARTH_RADIUS_KM = 6371.0088
META_USECOLS = (
    "site",
    "period",
    "x_wgs84",
    "y_wgs84",
    "temp",
    "precip",
    "cover_agri",
    "cover_water",
    "cover_wet",
    "sdiv_hab",
)
ENV_COLUMNS = (
    "temp",
    "precip",
    "cover_agri",
    "cover_water",
    "cover_wet",
    "sdiv_hab",
)
TARGETS = (0.25, 0.50, 0.75, 0.90)


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def canonical_sha256(payload: object) -> str:
    text = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def haversine_matrix(lon_deg: np.ndarray, lat_deg: np.ndarray) -> np.ndarray:
    lon = np.radians(np.asarray(lon_deg, dtype=float))
    lat = np.radians(np.asarray(lat_deg, dtype=float))
    dlon = lon[:, None] - lon[None, :]
    dlat = lat[:, None] - lat[None, :]
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(dlon / 2.0) ** 2
    result = 2.0 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))
    np.fill_diagonal(result, 0.0)
    return result


def euclidean_matrix(values: np.ndarray) -> np.ndarray:
    x = np.asarray(values, dtype=float)
    sq = np.sum(x * x, axis=1)
    dist2 = sq[:, None] + sq[None, :] - 2.0 * (x @ x.T)
    result = np.sqrt(np.maximum(dist2, 0.0))
    np.fill_diagonal(result, 0.0)
    return result


def level_rows(ladder):
    return [
        {
            "level_id": row.level_id,
            "target_largest_component_fraction": row.target_largest_component_fraction,
            "distance_threshold": row.distance_threshold,
            "achieved_largest_component_fraction": row.achieved_largest_component_fraction,
            "weak_component_count": row.weak_component_count,
            "isolated_node_fraction": row.isolated_node_fraction,
            "directed_edge_count": row.directed_edge_count,
            "fingerprint": row.fingerprint,
        }
        for row in ladder.levels
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    raw = args.source.read_bytes()
    if len(raw) != EXPECTED_SIZE:
        raise SystemExit(f"source size mismatch: {len(raw)}")
    if git_blob_sha1(raw) != EXPECTED_BLOB_SHA:
        raise SystemExit("source Git blob mismatch")

    # Explicit usecols firewall: species columns are never parsed by this diagnostic.
    frame = pd.read_csv(args.source, usecols=META_USECOLS)
    frame = frame[frame["period"].astype(str) == CALIBRATION_PERIOD].copy()
    frame["_site_key"] = frame["site"].astype(str)
    frame = frame.sort_values("_site_key").reset_index(drop=True)
    if len(frame) != 1003:
        raise SystemExit(f"expected 1003 calibration sites, got {len(frame)}")

    node_ids = tuple(frame["_site_key"].tolist())
    lon = frame["x_wgs84"].to_numpy(float)
    lat = frame["y_wgs84"].to_numpy(float)
    geo_distance = haversine_matrix(lon, lat)

    env = frame.loc[:, ENV_COLUMNS].to_numpy(float)
    mean = np.mean(env, axis=0)
    sd = np.std(env, axis=0, ddof=0)
    if np.any(sd <= 1e-12):
        raise SystemExit("zero-SD environmental predictor")
    env_z = (env - mean) / sd
    env_distance = euclidean_matrix(env_z)

    geo_ladder = build_structural_scale_ladder(
        node_ids,
        geo_distance,
        StructuralScaleLadderDeclaration(
            axis_id="geo",
            target_largest_component_fractions=TARGETS,
        ),
    )
    env_ladder = build_structural_scale_ladder(
        node_ids,
        env_distance,
        StructuralScaleLadderDeclaration(
            axis_id="env",
            target_largest_component_fractions=TARGETS,
        ),
    )

    geo_worlds = structural_scale_adjacencies(geo_ladder, geo_distance)
    env_worlds = structural_scale_adjacencies(env_ladder, env_distance)
    composed = compose_intersection_worlds(
        geo_worlds,
        env_worlds,
        include_primary_only=True,
    )
    audit = audit_world_universe_structure(node_ids, composed, horizon=8)

    audit_by_id = {row.world_id: row for row in audit.world_audits}
    primary_rows = []
    for level in geo_ladder.levels:
        world_id = f"primary::{level.level_id}"
        row = audit_by_id[world_id]
        primary_rows.append(
            {
                "world_id": world_id,
                "distance_threshold_km": level.distance_threshold,
                "largest_weak_component_fraction": row.largest_weak_component_fraction,
                "weak_component_count": row.weak_component_count,
                "isolated_node_fraction": row.isolated_node_fraction,
                "median_horizon_reachable_fraction": row.median_horizon_reachable_fraction,
            }
        )

    payload = {
        "status": "posthoc_nonconfirmatory_response_blind_scale_ladder_diagnostic",
        "species_response_columns_parsed": False,
        "source_git_blob_sha": EXPECTED_BLOB_SHA,
        "calibration_period": CALIBRATION_PERIOD,
        "node_count": len(node_ids),
        "targets": list(TARGETS),
        "old_frozen_stoc_geo_q90_threshold_km": 18.110714907817556,
        "old_frozen_stoc_geo_q90_largest_component_fraction": 87 / 1003,
        "geography_ladder": level_rows(geo_ladder),
        "environment_ladder": level_rows(env_ladder),
        "primary_geography_world_audit": primary_rows,
        "composed_world_count": len(composed),
        "composed_most_spanning_world_id": audit.most_spanning_world_id,
        "composed_audit_fingerprint": audit.fingerprint,
        "note": "This diagnostic demonstrates structural scale bracketing only. It does not reopen STOC prediction and must not be interpreted as independent confirmation.",
    }
    payload["fingerprint"] = canonical_sha256(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
