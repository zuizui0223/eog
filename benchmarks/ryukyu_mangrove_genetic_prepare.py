"""Freeze response-free EOG v2 predictors for the Ryukyu R. stylosa dataset.

The population coordinates are transcribed from Table 1 of Thomas et al. (2022). This
script does not accept or read genetic responses, migration rates, cluster assignments,
or current-direction data.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from eog.dynamic_island_reachability import DynamicReachabilityEdge, build_dynamic_transition_operator
from eog.eventual_genetic_connectivity import infer_eventual_genetic_connectivity

CONTRACT = Path("docs/eog_v2_ryukyu_mangrove_genetic_retrospective_contract.md")
LOSS_SUPPORT = 0.5
EARTH_RADIUS_KM = 6371.0088

POPULATIONS = (
    ("OKI", "Okinawa", 26.604, 128.143),
    ("MYKa", "Miyako", 24.789, 125.286),
    ("MYKb", "Miyako", 24.763, 125.282),
    ("MYKc", "Miyako", 24.752, 125.268),
    ("MYKd", "Miyako", 24.731, 125.296),
    ("ISGa", "Ishigaki", 24.542, 124.296),
    ("ISGb", "Ishigaki", 24.510, 124.279),
    ("ISGc", "Ishigaki", 24.456, 124.149),
    ("ISGd", "Ishigaki", 24.467, 124.125),
    ("IRMa", "Iriomote", 24.403, 123.830),
    ("IRMb", "Iriomote", 24.344, 123.934),
    ("IRMc", "Iriomote", 24.344, 123.928),
    ("IRMd", "Iriomote", 24.279, 123.904),
    ("IRMe", "Iriomote", 24.334, 123.728),
    ("IRMf", "Iriomote", 24.331, 123.714),
    ("IRMg", "Iriomote", 24.309, 123.683),
)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _haversine_matrix(latitude: np.ndarray, longitude: np.ndarray) -> np.ndarray:
    lat = np.radians(np.asarray(latitude, dtype=float))
    lon = np.radians(np.asarray(longitude, dtype=float))
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(dlon / 2.0) ** 2
    a = np.clip(a, 0.0, 1.0)
    return 2.0 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def _local_xy(latitude: np.ndarray, longitude: np.ndarray) -> np.ndarray:
    lat = np.radians(np.asarray(latitude, dtype=float))
    lon = np.radians(np.asarray(longitude, dtype=float))
    lat0 = float(np.mean(lat))
    lon0 = float(np.mean(lon))
    x = EARTH_RADIUS_KM * np.cos(lat0) * (lon - lon0)
    y = EARTH_RADIUS_KM * (lat - lat0)
    return np.column_stack([x, y])


def _gabriel_edges(xy: np.ndarray, tolerance: float = 1e-10) -> list[tuple[int, int]]:
    coordinates = np.asarray(xy, dtype=float)
    n = len(coordinates)
    output: list[tuple[int, int]] = []
    for i in range(n):
        for j in range(i + 1, n):
            delta = coordinates[i] - coordinates[j]
            diameter2 = float(np.dot(delta, delta))
            midpoint = 0.5 * (coordinates[i] + coordinates[j])
            radius2 = 0.25 * diameter2
            d2 = np.sum(np.square(coordinates - midpoint), axis=1)
            d2[i] = d2[j] = np.inf
            if float(np.min(d2)) >= radius2 - tolerance * max(1.0, radius2):
                output.append((i, j))
    if not output:
        raise RuntimeError("Ryukyu Gabriel graph has no edges")
    return output


def _effective_resistance(conductance: np.ndarray) -> np.ndarray:
    matrix = np.asarray(conductance, dtype=float)
    laplacian = np.diag(np.sum(matrix, axis=1)) - matrix
    pinv = np.linalg.pinv(laplacian)
    diagonal = np.diag(pinv)
    result = diagonal[:, None] + diagonal[None, :] - 2.0 * pinv
    result = np.maximum(result, 0.0)
    np.fill_diagonal(result, 0.0)
    return result


def prepare(populations_csv: str | Path, predictors_csv: str | Path, manifest_json: str | Path) -> dict[str, object]:
    ids = tuple(row[0] for row in POPULATIONS)
    islands = tuple(row[1] for row in POPULATIONS)
    latitude = np.asarray([row[2] for row in POPULATIONS], dtype=float)
    longitude = np.asarray([row[3] for row in POPULATIONS], dtype=float)
    d_geo = _haversine_matrix(latitude, longitude)
    xy = _local_xy(latitude, longitude)
    gabriel = _gabriel_edges(xy)
    edge_lengths = np.asarray([np.linalg.norm(xy[i] - xy[j]) for i, j in gabriel], dtype=float)
    scale = float(np.median(edge_lengths))
    if not np.isfinite(scale) or scale <= 0.0:
        raise RuntimeError("Ryukyu Gabriel support scale is invalid")

    edges: list[DynamicReachabilityEdge] = []
    conductance = np.zeros((len(ids), len(ids)), dtype=float)
    for (i, j), distance in zip(gabriel, edge_lengths):
        support = float(np.exp(-distance / scale))
        conductance[i, j] = conductance[j, i] = support
        edges.append(DynamicReachabilityEdge(i, j, geographic_support=support))
        edges.append(DynamicReachabilityEdge(j, i, geographic_support=support))
    operator = build_dynamic_transition_operator(ids, edges, loss_support=LOSS_SUPPORT)
    connectivity = infer_eventual_genetic_connectivity(operator)
    strong = _effective_resistance(conductance)
    d_env = np.zeros_like(d_geo)

    populations_path = Path(populations_csv)
    populations_path.parent.mkdir(parents=True, exist_ok=True)
    with populations_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["population_id", "latitude", "longitude", "island_id"])
        writer.writeheader()
        for population_id, island, lat, lon in POPULATIONS:
            writer.writerow(
                {
                    "population_id": population_id,
                    "latitude": f"{lat:.6f}",
                    "longitude": f"{lon:.6f}",
                    "island_id": island,
                }
            )

    predictors_path = Path(predictors_csv)
    predictors_path.parent.mkdir(parents=True, exist_ok=True)
    with predictors_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "population_a",
                "population_b",
                "geographic_distance",
                "environmental_distance",
                "eog_continuous_distance",
                "eog_disconnected",
                "strong_reference_distance",
            ],
        )
        writer.writeheader()
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                writer.writerow(
                    {
                        "population_a": ids[i],
                        "population_b": ids[j],
                        "geographic_distance": f"{d_geo[i, j]:.12g}",
                        "environmental_distance": "0",
                        "eog_continuous_distance": f"{connectivity.continuous_distance[i, j]:.12g}",
                        "eog_disconnected": int(connectivity.disconnected[i, j]),
                        "strong_reference_distance": f"{strong[i, j]:.12g}",
                    }
                )

    if not CONTRACT.exists():
        raise RuntimeError("Ryukyu retrospective contract must exist before predictor freeze")
    manifest = {
        "schema": "eog_v2_ryukyu_mangrove_response_free_predictors_v1",
        "status": "retrospective-external-response-not-attached",
        "study_doi": "10.3389/fmars.2022.827590",
        "dryad_doi": "10.5061/dryad.bcc2fqzdh",
        "n_populations": len(ids),
        "population_ids": list(ids),
        "island_ids": list(islands),
        "coordinate_source": "Thomas et al. 2022 Table 1",
        "gabriel_edges": [[ids[i], ids[j]] for i, j in gabriel],
        "gabriel_edge_count": len(gabriel),
        "support_scale_km": scale,
        "loss_support": LOSS_SUPPORT,
        "operator_fingerprint": operator.fingerprint,
        "connectivity_fingerprint": connectivity.fingerprint,
        "environmental_distance_policy": "all-zero; no IBE claim",
        "strong_reference": "effective resistance on response-free Gabriel conductance graph",
        "validation_response_transform": "linearized_fst",
        "validation_ridge_penalty": 1.0,
        "contract_sha256": _file_sha256(CONTRACT),
        "populations_csv_sha256": _file_sha256(populations_path),
        "predictors_csv_sha256": _file_sha256(predictors_path),
        "genetic_response_attached": False,
    }
    manifest["predictor_manifest_fingerprint"] = _canonical_sha256(manifest)
    manifest_path = Path(manifest_json)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--populations", type=Path, required=True)
    parser.add_argument("--predictors", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.populations, args.predictors, args.manifest), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
