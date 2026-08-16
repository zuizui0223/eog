#!/usr/bin/env python3
"""Freeze the response-blind 20-world Azores connectivity universe.

Gate 4 consumes only the frozen Gate 3 climate table. Species-island incidence,
held-out labels, predictive outcomes and fitted response models are not accepted.
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
NODE_ORDER = (
    "corvo", "flores", "faial", "pico", "graciosa",
    "sao_jorge", "terceira", "sao_miguel", "santa_maria",
)
GEO_LEVELS = (("q25", 0.25), ("q50", 0.50), ("q75", 0.75), ("q90", 0.90))
ENV_LEVELS = (("q50", 0.50), ("q75", 0.75))
EXPECTED_CLIMATE_SHA256 = "ee2aabd22256dd11bbd412ec59443750af695befc85444cc6f79ea1c3946e22a"
EXPECTED_WORLDS = 20
EARTH_RADIUS_KM = 6371.0088


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha(payload: object) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return 2.0 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


def load_climate(path: Path) -> list[dict[str, str]]:
    actual_sha = sha256(path)
    if actual_sha != EXPECTED_CLIMATE_SHA256:
        raise ValueError(f"Azores frozen climate SHA changed: {actual_sha}")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != len(NODE_ORDER):
        raise ValueError(f"expected {len(NODE_ORDER)} frozen nodes, got {len(rows)}")
    if tuple(row["island_id"] for row in rows) != NODE_ORDER:
        raise ValueError("Azores climate node order differs from the frozen Gate 2 order")
    required = {
        "island_id", "geonameid", "latitude", "longitude",
        *[f"chelsa_{v}" for v in VARIABLES],
        *[f"worldclim_{v}" for v in VARIABLES],
    }
    if not required.issubset(rows[0]):
        raise ValueError(f"climate table missing columns: {sorted(required - set(rows[0]))}")
    return rows


def pairwise_geo(rows: list[dict[str, str]]) -> np.ndarray:
    n = len(rows)
    matrix = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            value = haversine_km(
                float(rows[i]["latitude"]), float(rows[i]["longitude"]),
                float(rows[j]["latitude"]), float(rows[j]["longitude"]),
            )
            matrix[i, j] = matrix[j, i] = value
    return matrix


def standardized_env(rows: list[dict[str, str]], prefix: str) -> tuple[np.ndarray, dict[str, object]]:
    data = np.asarray([[float(row[f"{prefix}_{v}"]) for v in VARIABLES] for row in rows], dtype=float)
    if not np.isfinite(data).all():
        raise ValueError(f"{prefix} climate contains non-finite frozen values")
    means = data.mean(axis=0)
    sds = data.std(axis=0, ddof=1)
    if not np.isfinite(sds).all() or np.any(sds <= 0):
        raise ValueError(f"{prefix} climate has zero/non-finite sample standard deviation")
    z = (data - means) / sds
    delta = z[:, None, :] - z[None, :, :]
    distances = np.sqrt(np.sum(delta * delta, axis=2))
    stats = {
        "variables": list(VARIABLES),
        "means": {v: float(means[k]) for k, v in enumerate(VARIABLES)},
        "sample_sds": {v: float(sds[k]) for k, v in enumerate(VARIABLES)},
    }
    return distances, stats


def positive_upper(matrix: np.ndarray) -> np.ndarray:
    values = matrix[np.triu_indices_from(matrix, k=1)]
    values = values[values > 0]
    if values.size == 0:
        raise ValueError("pairwise distance matrix contains no positive upper-triangle distances")
    return values


def quantiles(matrix: np.ndarray, levels: tuple[tuple[str, float], ...]) -> dict[str, float]:
    values = positive_upper(matrix)
    return {name: float(np.quantile(values, q, method="linear")) for name, q in levels}


def components(n: int, edges: list[tuple[int, int]]) -> list[list[int]]:
    adjacency: list[list[int]] = [[] for _ in range(n)]
    for i, j in edges:
        adjacency[i].append(j)
        adjacency[j].append(i)
    seen: set[int] = set()
    result: list[list[int]] = []
    for start in range(n):
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        comp: list[int] = []
        while stack:
            node = stack.pop()
            comp.append(node)
            for nxt in sorted(adjacency[node], reverse=True):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        result.append(sorted(comp))
    return sorted(result, key=lambda comp: comp[0])


def freeze_worlds(climate_csv: Path, output_json: Path, output_manifest: Path) -> dict[str, object]:
    rows = load_climate(climate_csv)
    node_ids = tuple(row["island_id"] for row in rows)
    geo = pairwise_geo(rows)
    chelsa, chelsa_stats = standardized_env(rows, "chelsa")
    worldclim, worldclim_stats = standardized_env(rows, "worldclim")

    geo_thresholds = quantiles(geo, GEO_LEVELS)
    chelsa_thresholds = quantiles(chelsa, ENV_LEVELS)
    worldclim_thresholds = quantiles(worldclim, ENV_LEVELS)
    worlds: list[dict[str, object]] = []

    def add_world(
        world_id: str,
        family: str,
        geo_limit: float,
        env_matrix: np.ndarray | None = None,
        env_limit: float | None = None,
    ) -> None:
        edge_indices: list[tuple[int, int]] = []
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                if geo[i, j] > geo_limit:
                    continue
                if env_matrix is not None and env_limit is not None and env_matrix[i, j] > env_limit:
                    continue
                edge_indices.append((i, j))
        body: dict[str, object] = {
            "world_id": world_id,
            "family": family,
            "geographic_threshold_km": float(geo_limit),
            "environment_threshold": None if env_limit is None else float(env_limit),
            "edges": [[node_ids[i], node_ids[j]] for i, j in edge_indices],
            "components": [[node_ids[i] for i in comp] for comp in components(len(rows), edge_indices)],
        }
        body["fingerprint"] = canonical_sha(body)
        worlds.append(body)

    for geo_name, _ in GEO_LEVELS:
        add_world(
            world_id=f"geo_{geo_name}_env_none",
            family="geography_only",
            geo_limit=geo_thresholds[geo_name],
        )
    for geo_name, _ in GEO_LEVELS:
        for env_name, _ in ENV_LEVELS:
            add_world(
                world_id=f"geo_{geo_name}_chelsa_{env_name}",
                family=f"chelsa_{env_name}",
                geo_limit=geo_thresholds[geo_name],
                env_matrix=chelsa,
                env_limit=chelsa_thresholds[env_name],
            )
    for geo_name, _ in GEO_LEVELS:
        for env_name, _ in ENV_LEVELS:
            add_world(
                world_id=f"geo_{geo_name}_worldclim_{env_name}",
                family=f"worldclim_{env_name}",
                geo_limit=geo_thresholds[geo_name],
                env_matrix=worldclim,
                env_limit=worldclim_thresholds[env_name],
            )

    family_counts = {
        name: sum(world["family"] == name for world in worlds)
        for name in ("geography_only", "chelsa_q50", "chelsa_q75", "worldclim_q50", "worldclim_q75")
    }
    expected_counts = {
        "geography_only": 4,
        "chelsa_q50": 4,
        "chelsa_q75": 4,
        "worldclim_q50": 4,
        "worldclim_q75": 4,
    }
    if len(worlds) != EXPECTED_WORLDS or len({world["world_id"] for world in worlds}) != EXPECTED_WORLDS:
        raise AssertionError("Azores world universe is not exactly 20 unique worlds")
    if family_counts != expected_counts:
        raise AssertionError(f"Azores world family counts changed: {family_counts}")

    payload: dict[str, object] = {
        "status": "preoutcome_world_universe_freeze",
        "climate_csv_sha256": sha256(climate_csv),
        "node_order": list(node_ids),
        "geographic_distance": {
            "metric": "great_circle_haversine_km",
            "earth_radius_km": EARTH_RADIUS_KM,
            "thresholds": geo_thresholds,
        },
        "chelsa_environment": {
            "metric": "euclidean_after_9_node_sample_sd_standardization",
            "standardization": chelsa_stats,
            "thresholds": chelsa_thresholds,
        },
        "worldclim_environment": {
            "metric": "euclidean_after_9_node_sample_sd_standardization",
            "standardization": worldclim_stats,
            "thresholds": worldclim_thresholds,
        },
        "family_counts": family_counts,
        "world_count": len(worlds),
        "worlds": worlds,
        "species_incidence_used": False,
        "heldout_outcomes_scored": False,
        "predictive_model_fitted": False,
    }
    payload["world_universe_fingerprint"] = canonical_sha(payload)

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "status": "preoutcome_world_universe_freeze",
        "climate_csv_sha256": sha256(climate_csv),
        "worlds_json_sha256": sha256(output_json),
        "world_universe_fingerprint": payload["world_universe_fingerprint"],
        "world_count": len(worlds),
        "family_counts": family_counts,
        "species_incidence_used": False,
        "heldout_outcomes_scored": False,
        "predictive_model_fitted": False,
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
