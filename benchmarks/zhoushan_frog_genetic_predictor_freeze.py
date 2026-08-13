"""Freeze Zhoushan pond-frog EOG v2 genetic predictors before exact FST access."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from eog.dynamic_island_reachability import DynamicReachabilityEdge, build_dynamic_transition_operator
from eog.eventual_genetic_connectivity import infer_eventual_genetic_connectivity

COORDINATES = Path("benchmarks/frozen/zhoushan_frog_response_free/population_coordinates.csv")
CONTRACT = Path("docs/eog_v2_zhoushan_frog_pre_genetic_contract.md")
COORDINATE_FREEZE = Path("docs/eog_v2_zhoushan_frog_coordinate_freeze.md")
LOSS_SUPPORT = 0.5
RIDGE_PENALTY = 1.0
BOOTSTRAP_SEED = 20260813
BOOTSTRAP_REPLICATES = 10_000
EARTH_RADIUS_KM = 6371.0088

EXPECTED_IDS = (
    "Guoju", "Xiepu", "Yuanhua", "Meishan", "Fodu", "Liuheng", "Huni", "Xiashi",
    "Mayi", "Taohua", "Dengbu", "Zhujiajian", "Putuoshan", "Zhoushan", "Damao",
    "Cezi", "Jintang", "Dapengshan", "Changbai", "Xiushan", "Dayushan", "Daishan",
    "Dongji", "Qushan", "Sijiao", "Shengshan", "Huaniao",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _read_coordinates(path: Path) -> list[dict[str, object]]:
    required = {
        "population_id", "node_type", "latitude", "longitude", "coordinate_class",
        "source", "source_id", "provenance", "sensitivity_radius_km",
    }
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            missing = required - set(reader.fieldnames or ())
            raise ValueError(f"Zhoushan frozen coordinate CSV missing columns: {sorted(missing)}")
        rows: list[dict[str, object]] = []
        for raw in reader:
            record = {key: ("" if value is None else str(value).strip()) for key, value in raw.items()}
            record["latitude"] = float(record["latitude"])
            record["longitude"] = float(record["longitude"])
            record["sensitivity_radius_km"] = float(record["sensitivity_radius_km"])
            rows.append(record)
    ids = tuple(str(row["population_id"]) for row in rows)
    if ids != EXPECTED_IDS:
        raise ValueError(f"Zhoushan coordinate node order/identity drifted: {ids}")
    if len(rows) != 27 or len(set(ids)) != 27:
        raise ValueError("Zhoushan coordinate freeze must contain exactly 27 unique nodes")
    coordinates = np.asarray([[row["latitude"], row["longitude"]] for row in rows], dtype=float)
    if not np.isfinite(coordinates).all():
        raise ValueError("Zhoushan coordinates must be finite")
    if np.any((coordinates[:, 0] < 29.0) | (coordinates[:, 0] > 31.1)):
        raise ValueError("Zhoushan latitude outside frozen response-free study envelope")
    if np.any((coordinates[:, 1] < 120.5) | (coordinates[:, 1] > 123.3)):
        raise ValueError("Zhoushan longitude outside frozen response-free study envelope")
    if len({(float(a), float(b)) for a, b in coordinates}) != len(rows):
        raise ValueError("Zhoushan frozen nodes must have distinct representative coordinates")
    for row in rows:
        radius = float(row["sensitivity_radius_km"])
        if radius not in {3.0, 5.0, 10.0}:
            raise ValueError("Zhoushan sensitivity radius must be one of the predeclared values")
    return rows


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
        raise RuntimeError("Zhoushan Gabriel graph has no edges")
    return output


def _effective_resistance(conductance: np.ndarray) -> np.ndarray:
    matrix = np.asarray(conductance, dtype=float)
    if not np.allclose(matrix, matrix.T, rtol=0.0, atol=1e-12):
        raise ValueError("Zhoushan current-flow conductance must be symmetric")
    laplacian = np.diag(np.sum(matrix, axis=1)) - matrix
    pinv = np.linalg.pinv(laplacian)
    diagonal = np.diag(pinv)
    result = diagonal[:, None] + diagonal[None, :] - 2.0 * pinv
    result = np.maximum(result, 0.0)
    np.fill_diagonal(result, 0.0)
    return result


def prepare(populations_csv: Path, predictors_csv: Path, manifest_json: Path) -> dict[str, object]:
    for source in (COORDINATES, CONTRACT, COORDINATE_FREEZE):
        if not source.exists():
            raise RuntimeError(f"required Zhoushan response-free freeze file is missing: {source}")
    rows = _read_coordinates(COORDINATES)
    ids = tuple(str(row["population_id"]) for row in rows)
    latitude = np.asarray([float(row["latitude"]) for row in rows], dtype=float)
    longitude = np.asarray([float(row["longitude"]) for row in rows], dtype=float)
    d_geo = _haversine_matrix(latitude, longitude)
    xy = _local_xy(latitude, longitude)
    gabriel = _gabriel_edges(xy)
    edge_lengths = np.asarray([np.linalg.norm(xy[i] - xy[j]) for i, j in gabriel], dtype=float)
    scale = float(np.median(edge_lengths))
    if not np.isfinite(scale) or scale <= 0.0:
        raise RuntimeError("Zhoushan Gabriel support scale is invalid")

    graph_edges: list[DynamicReachabilityEdge] = []
    conductance = np.zeros((len(ids), len(ids)), dtype=float)
    for (i, j), distance in zip(gabriel, edge_lengths):
        support = float(np.exp(-distance / scale))
        conductance[i, j] = conductance[j, i] = support
        graph_edges.append(DynamicReachabilityEdge(i, j, geographic_support=support))
        graph_edges.append(DynamicReachabilityEdge(j, i, geographic_support=support))
    operator = build_dynamic_transition_operator(ids, graph_edges, loss_support=LOSS_SUPPORT)
    connectivity = infer_eventual_genetic_connectivity(operator)
    strong = _effective_resistance(conductance)
    d_env = np.zeros_like(d_geo)

    populations_csv.parent.mkdir(parents=True, exist_ok=True)
    with populations_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["population_id", "latitude", "longitude", "island_id", "node_type"],
        )
        writer.writeheader()
        for row in rows:
            population_id = str(row["population_id"])
            writer.writerow(
                {
                    "population_id": population_id,
                    "latitude": f"{float(row['latitude']):.7f}",
                    "longitude": f"{float(row['longitude']):.7f}",
                    "island_id": population_id,
                    "node_type": str(row["node_type"]),
                }
            )

    predictors_csv.parent.mkdir(parents=True, exist_ok=True)
    with predictors_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "population_a", "population_b", "geographic_distance", "environmental_distance",
                "eog_continuous_distance", "eog_disconnected", "strong_reference_distance",
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

    coordinate_payload = [
        {
            "population_id": str(row["population_id"]),
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "coordinate_class": str(row["coordinate_class"]),
            "source": str(row["source"]),
            "source_id": str(row["source_id"]),
            "sensitivity_radius_km": float(row["sensitivity_radius_km"]),
        }
        for row in rows
    ]
    coordinate_fingerprint = _canonical_sha256(coordinate_payload)
    manifest: dict[str, object] = {
        "schema": "eog_v2_zhoushan_frog_response_free_predictors_v1",
        "status": "independent-exact-fst-response-not-attached",
        "study_doi": "10.1111/mec.12634",
        "data_mirror": "Zenodo 5012316 / Dryad 10.5061/dryad.dq4g5",
        "n_populations": len(ids),
        "n_pairs": len(ids) * (len(ids) - 1) // 2,
        "population_ids": list(ids),
        "coordinate_csv": str(COORDINATES),
        "coordinate_csv_sha256": _sha256(COORDINATES),
        "coordinate_fingerprint": coordinate_fingerprint,
        "coordinate_freeze_sha256": _sha256(COORDINATE_FREEZE),
        "contract_sha256": _sha256(CONTRACT),
        "gabriel_edges": [[ids[i], ids[j]] for i, j in gabriel],
        "gabriel_edge_count": len(gabriel),
        "support_scale_km": scale,
        "loss_support": LOSS_SUPPORT,
        "operator_fingerprint": operator.fingerprint,
        "connectivity_fingerprint": connectivity.fingerprint,
        "strong_reference": "effective resistance on the same response-free Gabriel conductance graph",
        "environmental_distance_policy": "all-zero; IBE non-applicable",
        "response_source_policy": "Wiley Table S1 exact pairwise FST after predictor freeze; raw microsatellites optional replication",
        "validation_response_transform": "linearized_fst",
        "validation_ridge_penalty": RIDGE_PENALTY,
        "validation_scheme": "leave-one-population-out",
        "primary_contrast": "strong_reference_eog_minus_strong_reference_mse",
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "bootstrap_unit": "held_out_population",
        "promotion_requires_strong_reference_mse_le_ibd": True,
        "coordinate_sensitivity_policy": "one node at a time; eight compass directions at frozen per-node radius; never replaces primary coordinates",
        "populations_csv_sha256": _sha256(populations_csv),
        "predictors_csv_sha256": _sha256(predictors_csv),
        "exact_pairwise_fst_accessed": False,
        "microsatellite_file_accessed": False,
        "genetic_response_attached": False,
    }
    manifest["predictor_manifest_fingerprint"] = _canonical_sha256(manifest)
    manifest_json.parent.mkdir(parents=True, exist_ok=True)
    manifest_json.write_text(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--populations", type=Path, required=True)
    parser.add_argument("--predictors", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.populations, args.predictors, args.manifest)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
