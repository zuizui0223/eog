"""Freeze Thalassia response-free conventional references and exact-eventual EOG.

This stage consumes only the byte-frozen Stage-1 17-site coordinates.  It never opens
microsatellite or SNP files and attaches no genetic response.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from pyproj import CRS, Transformer

from eog.dynamic_island_reachability import DynamicReachabilityEdge, build_dynamic_transition_operator
from eog.eventual_genetic_connectivity import infer_eventual_genetic_connectivity


STAGE1_DIR = Path("benchmarks/frozen/thalassia_response_free")
STAGE1_COORDINATES = STAGE1_DIR / "population_coordinates.csv"
STAGE1_MANIFEST = STAGE1_DIR / "stage1_manifest.json"
CONTRACT = Path("docs/eog_v2_thalassia_stage2_predictor_contract.md")
NESTED_CONTRACT = Path("docs/eog_v2_nested_genetic_reference_contract.md")
EXPECTED_STAGE1_FINGERPRINT = "12a34c597dbf4130ad1dcda8a9822504291a0ac7d4f34fa31c43d8d373d49764"
EXPECTED_COORDINATE_SHA256 = "7311e561ec2dbeecc57b0b6d8b83b4819697f23480303bcb4478e5750660ce49"
EXPECTED_COORDINATE_FINGERPRINT = "334948e6af43c50d5fb7bfec3396065a1c39d64e0bab7eb5f4a767a42249245d"
EXPECTED_GENETIC_SHA256 = "aaaab9e302c9be8cf4e108d2aee5867c0b64ed70b6d3b81bad4d60168ee7f2f3"
EXPECTED_NODE_IDS = (
    "BIA", "TUA", "AMB", "KEN", "BIT", "PAL", "JEP", "PAR", "BAN",
    "NAT", "KUP", "MAT", "DRI", "PAD", "CK", "MI", "Ex2",
)
CANDIDATE_IDS = ("gabriel_current_flow", "gabriel_shortest_path", "geographic")
LOSS_SUPPORT = 0.5
EARTH_RADIUS_KM = 6371.0088
RESPONSE_TRANSFORM = "linearized_fst"
RIDGE_PENALTY = 1.0
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20260813


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _load_nodes() -> tuple[list[dict[str, object]], dict[str, object]]:
    if not CONTRACT.exists() or not NESTED_CONTRACT.exists():
        raise RuntimeError("Thalassia Stage-2 and generic nested-selector contracts must exist")
    if _file_sha256(STAGE1_COORDINATES) != EXPECTED_COORDINATE_SHA256:
        raise ValueError("Thalassia frozen Stage-1 coordinate CSV drifted")
    manifest = json.loads(STAGE1_MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("fingerprint") != EXPECTED_STAGE1_FINGERPRINT:
        raise ValueError("Thalassia Stage-1 manifest fingerprint drifted")
    if manifest.get("coordinate_fingerprint") != EXPECTED_COORDINATE_FINGERPRINT:
        raise ValueError("Thalassia Stage-1 coordinate fingerprint drifted")
    opaque = manifest.get("opaque_genetic_file") or {}
    if opaque.get("sha256") != EXPECTED_GENETIC_SHA256:
        raise ValueError("Thalassia opaque genetic-file identity drifted")
    if opaque.get("contents_accessed") is not False or opaque.get("container_inspected") is not False:
        raise ValueError("Thalassia Stage-1 genetic firewall is no longer intact")

    rows: list[dict[str, object]] = []
    with STAGE1_COORDINATES.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        expected = {"population_id", "site_name", "latitude", "longitude", "gps_row"}
        if set(reader.fieldnames or ()) != expected:
            raise ValueError(f"unexpected Thalassia coordinate schema: {reader.fieldnames}")
        for raw in reader:
            latitude = float(raw["latitude"])
            longitude = float(raw["longitude"])
            if not (math.isfinite(latitude) and -90.0 <= latitude <= 90.0):
                raise ValueError("invalid Thalassia latitude")
            if not (math.isfinite(longitude) and -180.0 <= longitude <= 180.0):
                raise ValueError("invalid Thalassia longitude")
            rows.append(
                {
                    "population_id": raw["population_id"],
                    "site_name": raw["site_name"],
                    "latitude": latitude,
                    "longitude": longitude,
                    "gps_row": int(raw["gps_row"]),
                }
            )
    if tuple(str(row["population_id"]) for row in rows) != EXPECTED_NODE_IDS:
        raise ValueError("Thalassia Stage-1 node order/identity drifted")
    payload = [
        {
            "population_id": row["population_id"],
            "site_name": row["site_name"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "gps_row": row["gps_row"],
        }
        for row in rows
    ]
    if _canonical_sha256(payload) != EXPECTED_COORDINATE_FINGERPRINT:
        raise ValueError("Thalassia coordinate content does not match frozen fingerprint")
    return rows, manifest


def _haversine_matrix(latitude: np.ndarray, longitude: np.ndarray) -> np.ndarray:
    lat = np.radians(np.asarray(latitude, dtype=float))
    lon = np.radians(np.asarray(longitude, dtype=float))
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(dlon / 2.0) ** 2
    a = np.clip(a, 0.0, 1.0)
    result = 2.0 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))
    np.fill_diagonal(result, 0.0)
    return result


def _circular_mean_degrees(longitude: np.ndarray) -> float:
    radians = np.radians(np.asarray(longitude, dtype=float))
    return float(np.degrees(np.arctan2(np.mean(np.sin(radians)), np.mean(np.cos(radians)))))


def _azimuthal_equidistant_xy(latitude: np.ndarray, longitude: np.ndarray) -> tuple[np.ndarray, dict[str, float | str]]:
    lat0 = float(np.mean(np.asarray(latitude, dtype=float)))
    lon0 = _circular_mean_degrees(longitude)
    target = CRS.from_proj4(
        f"+proj=aeqd +lat_0={lat0:.15g} +lon_0={lon0:.15g} +datum=WGS84 +units=m +no_defs"
    )
    transformer = Transformer.from_crs("EPSG:4326", target, always_xy=True)
    x_m, y_m = transformer.transform(np.asarray(longitude, dtype=float), np.asarray(latitude, dtype=float))
    xy = np.column_stack([x_m, y_m]).astype(float) / 1000.0
    if not np.isfinite(xy).all():
        raise RuntimeError("Thalassia azimuthal-equidistant projection produced non-finite coordinates")
    return xy, {
        "method": "WGS84 azimuthal equidistant centered on response-free sample mean latitude/circular-mean longitude",
        "center_latitude": lat0,
        "center_longitude": lon0,
    }


def _gabriel_edges(xy: np.ndarray, tolerance: float = 1e-10) -> list[tuple[int, int]]:
    coordinates = np.asarray(xy, dtype=float)
    output: list[tuple[int, int]] = []
    for i in range(len(coordinates)):
        for j in range(i + 1, len(coordinates)):
            delta = coordinates[i] - coordinates[j]
            diameter2 = float(np.dot(delta, delta))
            if diameter2 <= 1e-16:
                raise ValueError("Thalassia response-free nodes project to duplicate coordinates")
            midpoint = 0.5 * (coordinates[i] + coordinates[j])
            radius2 = 0.25 * diameter2
            d2 = np.sum(np.square(coordinates - midpoint), axis=1)
            d2[i] = d2[j] = np.inf
            if float(np.min(d2)) >= radius2 - tolerance * max(1.0, radius2):
                output.append((i, j))
    if not output:
        raise RuntimeError("Thalassia Gabriel graph has no edges")
    return output


def _shortest_path_matrix(n: int, edges: list[tuple[int, int]], edge_lengths: np.ndarray) -> np.ndarray:
    distance = np.full((n, n), np.inf, dtype=float)
    np.fill_diagonal(distance, 0.0)
    for (i, j), length in zip(edges, edge_lengths):
        distance[i, j] = distance[j, i] = min(distance[i, j], float(length))
    for k in range(n):
        distance = np.minimum(distance, distance[:, [k]] + distance[[k], :])
    if not np.isfinite(distance).all():
        raise RuntimeError("Thalassia Gabriel graph is disconnected")
    return distance


def _effective_resistance(conductance: np.ndarray) -> np.ndarray:
    matrix = np.asarray(conductance, dtype=float)
    laplacian = np.diag(np.sum(matrix, axis=1)) - matrix
    pinv = np.linalg.pinv(laplacian)
    diagonal = np.diag(pinv)
    result = diagonal[:, None] + diagonal[None, :] - 2.0 * pinv
    result = np.maximum(result, 0.0)
    np.fill_diagonal(result, 0.0)
    if not np.isfinite(result).all():
        raise RuntimeError("Thalassia current-flow distance is non-finite")
    return result


def freeze(predictors_csv: Path, manifest_json: Path) -> dict[str, object]:
    nodes, stage1 = _load_nodes()
    ids = tuple(str(row["population_id"]) for row in nodes)
    latitude = np.asarray([row["latitude"] for row in nodes], dtype=float)
    longitude = np.asarray([row["longitude"] for row in nodes], dtype=float)

    d_geo = _haversine_matrix(latitude, longitude)
    xy, projection = _azimuthal_equidistant_xy(latitude, longitude)
    gabriel = _gabriel_edges(xy)
    edge_lengths = np.asarray([d_geo[i, j] for i, j in gabriel], dtype=float)
    support_scale = float(np.median(edge_lengths))
    if not np.isfinite(support_scale) or support_scale <= 0.0:
        raise RuntimeError("Thalassia Gabriel median geodesic edge scale is invalid")

    conductance = np.zeros((len(ids), len(ids)), dtype=float)
    dynamic_edges: list[DynamicReachabilityEdge] = []
    graph_edges: list[dict[str, object]] = []
    for (i, j), length in zip(gabriel, edge_lengths):
        support = float(np.exp(-float(length) / support_scale))
        conductance[i, j] = conductance[j, i] = support
        dynamic_edges.append(DynamicReachabilityEdge(i, j, geographic_support=support))
        dynamic_edges.append(DynamicReachabilityEdge(j, i, geographic_support=support))
        graph_edges.append({"a": ids[i], "b": ids[j], "geodesic_length_km": float(length), "support": support})

    operator = build_dynamic_transition_operator(ids, dynamic_edges, loss_support=LOSS_SUPPORT)
    connectivity = infer_eventual_genetic_connectivity(operator)
    d_shortest = _shortest_path_matrix(len(ids), gabriel, edge_lengths)
    d_current = _effective_resistance(conductance)

    predictors_csv.parent.mkdir(parents=True, exist_ok=True)
    pair_payload: list[dict[str, object]] = []
    with predictors_csv.open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "population_a", "population_b", "geographic", "gabriel_shortest_path",
            "gabriel_current_flow", "eog_continuous_distance", "eog_disconnected",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                row = {
                    "population_a": ids[i],
                    "population_b": ids[j],
                    "geographic": f"{d_geo[i, j]:.12g}",
                    "gabriel_shortest_path": f"{d_shortest[i, j]:.12g}",
                    "gabriel_current_flow": f"{d_current[i, j]:.12g}",
                    "eog_continuous_distance": f"{connectivity.continuous_distance[i, j]:.12g}",
                    "eog_disconnected": int(connectivity.disconnected[i, j]),
                }
                writer.writerow(row)
                pair_payload.append(row)

    candidate_payload = {
        "candidate_ids": list(CANDIDATE_IDS),
        "node_ids": list(ids),
        "geographic": d_geo.tolist(),
        "gabriel_shortest_path": d_shortest.tolist(),
        "gabriel_current_flow": d_current.tolist(),
    }
    graph_payload = {"node_ids": list(ids), "projection": projection, "edges": graph_edges, "support_scale_km": support_scale}
    manifest: dict[str, object] = {
        "schema": "eog_v2_1_thalassia_response_free_predictors_v1",
        "status": "response-free-genetic-predictor-freeze",
        "study_doi": "10.1111/mec.13966",
        "dryad_doi": "10.5061/dryad.404rm",
        "source_stage1_fingerprint": stage1["fingerprint"],
        "source_coordinate_sha256": EXPECTED_COORDINATE_SHA256,
        "source_coordinate_fingerprint": EXPECTED_COORDINATE_FINGERPRINT,
        "opaque_genetic_file_sha256": EXPECTED_GENETIC_SHA256,
        "genetic_workbook_contents_accessed": False,
        "genetic_response_attached": False,
        "n_populations": len(ids),
        "n_pairs": len(pair_payload),
        "population_ids": list(ids),
        "projection": projection,
        "gabriel_edge_count": len(gabriel),
        "graph_edges": graph_edges,
        "support_scale_km": support_scale,
        "loss_support": LOSS_SUPPORT,
        "candidate_ids": list(CANDIDATE_IDS),
        "candidate_family_fingerprint": _canonical_sha256(candidate_payload),
        "graph_fingerprint": _canonical_sha256(graph_payload),
        "operator_fingerprint": operator.fingerprint,
        "connectivity_fingerprint": connectivity.fingerprint,
        "environmental_distance_policy": "all-zero / IBE non-applicable",
        "response_transform": RESPONSE_TRANSFORM,
        "ridge_penalty": RIDGE_PENALTY,
        "outer_unit": "population",
        "inner_selector": "leave-one-population-out; equal-weight inner-population MSE; lexicographic exact tie",
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "promotion_rule": {
            "all_frozen_populations_mechanically_aligned": True,
            "nested_selected_conventional_pooled_mse_must_be_lte_geographic_pooled_mse": True,
            "mean_outer_population_selected_plus_eog_minus_selected_mse_must_be_lt_zero": True,
            "population_bootstrap_95pct_upper_bound_must_be_lt_zero": True,
            "no_candidate_removal_or_addition_after_genetic_response_access": True,
        },
        "stage2_contract_sha256": _file_sha256(CONTRACT),
        "nested_selector_contract_sha256": _file_sha256(NESTED_CONTRACT),
    }
    manifest["predictors_csv_sha256"] = _file_sha256(predictors_csv)
    manifest["fingerprint"] = _canonical_sha256(manifest)
    manifest_json.parent.mkdir(parents=True, exist_ok=True)
    manifest_json.write_text(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictors", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    result = freeze(args.predictors, args.manifest)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
