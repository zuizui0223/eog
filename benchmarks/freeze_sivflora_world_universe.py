#!/usr/bin/env python3
"""Freeze the 20 response-blind SIVFLORA connectivity worlds.

The world universe depends only on the frozen 22-node coordinates and two frozen climate
representations. Species incidence is neither accepted nor read by this script.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


VARIABLES = ("bio1", "bio5", "bio6", "bio12", "bio15")
GEO_LEVELS = (("q25", 0.25), ("q50", 0.50), ("q75", 0.75), ("q90", 0.90))
ENV_LEVELS = (("q50", 0.50), ("q75", 0.75))
EXPECTED_NODES = 22
EXPECTED_WORLDS = 20
EARTH_RADIUS_KM = 6371.0088


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_sha(payload: object) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


def _pairwise_geo(rows: list[dict[str, str]]) -> np.ndarray:
    n = len(rows)
    matrix = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            d = _haversine_km(
                float(rows[i]["latitude"]),
                float(rows[i]["longitude"]),
                float(rows[j]["latitude"]),
                float(rows[j]["longitude"]),
            )
            matrix[i, j] = matrix[j, i] = d
    return matrix


def _standardized_env(rows: list[dict[str, str]], prefix: str) -> tuple[np.ndarray, dict[str, object]]:
    data = np.asarray([[float(row[f"{prefix}_{v}"]) for v in VARIABLES] for row in rows], dtype=float)
    if not np.isfinite(data).all():
        raise ValueError(f"{prefix} climate contains non-finite frozen node values")
    means = data.mean(axis=0)
    sds = data.std(axis=0, ddof=1)
    if not np.isfinite(sds).all() or np.any(sds <= 0):
        raise ValueError(f"{prefix} has zero/non-finite climate standard deviation")
    z = (data - means) / sds
    n = len(rows)
    distances = np.zeros((n, n), dtype=float)
    for i in range(n):
        delta = z[i + 1 :] - z[i]
        if delta.size:
            d = np.sqrt(np.sum(delta * delta, axis=1))
            distances[i, i + 1 :] = d
            distances[i + 1 :, i] = d
    stats = {
        "variables": list(VARIABLES),
        "means": {v: float(means[k]) for k, v in enumerate(VARIABLES)},
        "sample_sds": {v: float(sds[k]) for k, v in enumerate(VARIABLES)},
    }
    return distances, stats


def _positive_upper(matrix: np.ndarray) -> np.ndarray:
    upper = matrix[np.triu_indices_from(matrix, k=1)]
    positive = upper[upper > 0]
    if positive.size == 0:
        raise ValueError("pairwise distance matrix has no positive distances")
    return positive


def _quantiles(matrix: np.ndarray, levels: tuple[tuple[str, float], ...]) -> dict[str, float]:
    values = _positive_upper(matrix)
    return {
        name: float(np.quantile(values, q, method="linear"))
        for name, q in levels
    }


def _components(n: int, edges: list[tuple[int, int]]) -> list[list[int]]:
    adjacency = [[] for _ in range(n)]
    for i, j in edges:
        adjacency[i].append(j)
        adjacency[j].append(i)
    seen: set[int] = set()
    components: list[list[int]] = []
    for start in range(n):
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        comp: list[int] = []
        while stack:
            node = stack.pop()
            comp.append(node)
            for nxt in adjacency[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        components.append(sorted(comp))
    return sorted(components, key=lambda c: c[0])


def freeze_worlds(climate_csv: Path, output_json: Path, output_manifest: Path) -> dict[str, object]:
    with climate_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != EXPECTED_NODES:
        raise ValueError(f"expected {EXPECTED_NODES} climate nodes, got {len(rows)}")
    required = {
        "island_id", "acronym", "node_name", "latitude", "longitude",
        *[f"chelsa_{v}" for v in VARIABLES],
        *[f"worldclim_{v}" for v in VARIABLES],
    }
    if not required.issubset(rows[0]):
        raise ValueError(f"climate table missing columns: {sorted(required - set(rows[0]))}")

    node_ids = tuple(str(row["island_id"]) for row in rows)
    if node_ids != tuple(str(i) for i in range(1, EXPECTED_NODES + 1)):
        raise ValueError("climate node order must be frozen island IDs 1..22")

    geo = _pairwise_geo(rows)
    chelsa, chelsa_stats = _standardized_env(rows, "chelsa")
    worldclim, worldclim_stats = _standardized_env(rows, "worldclim")
    geo_thresholds = _quantiles(geo, GEO_LEVELS)
    chelsa_thresholds = _quantiles(chelsa, ENV_LEVELS)
    worldclim_thresholds = _quantiles(worldclim, ENV_LEVELS)

    worlds: list[dict[str, object]] = []

    def add_world(world_id: str, geo_limit: float, env_matrix: np.ndarray | None, env_limit: float | None, family: str) -> None:
        edges_index: list[tuple[int, int]] = []
        for i in range(EXPECTED_NODES):
            for j in range(i + 1, EXPECTED_NODES):
                if geo[i, j] > geo_limit:
                    continue
                if env_matrix is not None and env_limit is not None and env_matrix[i, j] > env_limit:
                    continue
                edges_index.append((i, j))
        edges = [[node_ids[i], node_ids[j]] for i, j in edges_index]
        components = [[node_ids[i] for i in comp] for comp in _components(EXPECTED_NODES, edges_index)]
        body = {
            "world_id": world_id,
            "family": family,
            "edges": edges,
            "components": components,
        }
        body["fingerprint"] = _canonical_sha(body)
        worlds.append(body)

    for geo_name, _ in GEO_LEVELS:
        add_world(
            f"geo_{geo_name}_env_none",
            geo_thresholds[geo_name],
            None,
            None,
            "geography_only",
        )
    for geo_name, _ in GEO_LEVELS:
        for env_name, _ in ENV_LEVELS:
            add_world(
                f"geo_{geo_name}_chelsa_{env_name}",
                geo_thresholds[geo_name],
                chelsa,
                chelsa_thresholds[env_name],
                f"chelsa_{env_name}",
            )
    for geo_name, _ in GEO_LEVELS:
        for env_name, _ in ENV_LEVELS:
            add_world(
                f"geo_{geo_name}_worldclim_{env_name}",
                geo_thresholds[geo_name],
                worldclim,
                worldclim_thresholds[env_name],
                f"worldclim_{env_name}",
            )

    if len(worlds) != EXPECTED_WORLDS or len({w["world_id"] for w in worlds}) != EXPECTED_WORLDS:
        raise AssertionError("declared SIVFLORA world universe is not exactly 20 unique worlds")

    payload = {
        "status": "preoutcome_world_universe_freeze",
        "climate_csv_sha256": _sha256(climate_csv),
        "node_order": list(node_ids),
        "node_names": [row["node_name"] for row in rows],
        "geographic_distance": {
            "metric": "great_circle_haversine_km",
            "earth_radius_km": EARTH_RADIUS_KM,
            "thresholds": geo_thresholds,
        },
        "chelsa_environment": {
            "metric": "euclidean_after_22_node_sample_sd_standardization",
            "standardization": chelsa_stats,
            "thresholds": chelsa_thresholds,
        },
        "worldclim_environment": {
            "metric": "euclidean_after_22_node_sample_sd_standardization",
            "standardization": worldclim_stats,
            "thresholds": worldclim_thresholds,
        },
        "world_count": len(worlds),
        "worlds": worlds,
        "species_incidence_used": False,
        "heldout_outcomes_scored": False,
    }
    payload["world_universe_fingerprint"] = _canonical_sha(payload)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "status": "preoutcome_world_universe_freeze",
        "climate_csv_sha256": _sha256(climate_csv),
        "worlds_json_sha256": _sha256(output_json),
        "world_universe_fingerprint": payload["world_universe_fingerprint"],
        "world_count": len(worlds),
        "species_incidence_used": False,
        "heldout_outcomes_scored": False,
    }
    output_manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--climate", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-manifest", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(freeze_worlds(args.climate, args.output_json, args.output_manifest), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
