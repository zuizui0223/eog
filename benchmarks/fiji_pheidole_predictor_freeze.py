"""Freeze Fiji EGPA0079 response-free genetic predictors before VCF access.

Only the Stage-1 authorized ``sequenceMetaData.csv`` member is opened.  The focal group,
node admission, conventional reference family, EOG operator and validation/inference
settings are all fixed before any VCF/FST/WC member content is inspected.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import zipfile

import numpy as np

from eog.dynamic_island_reachability import DynamicReachabilityEdge, build_dynamic_transition_operator
from eog.eventual_genetic_connectivity import infer_eventual_genetic_connectivity


CONTRACT = Path("docs/eog_v2_fiji_pheidole_predictor_freeze_contract.md")
EXPECTED_ARCHIVE_SHA256 = "9a23543ad59d5f4de7e6f26cc91b75dc60f93c259744e640b8f6576fde89abc7"
EXPECTED_METADATA_SHA256 = "5a41f967d81e005be3b3e91f31bb1a7eae26a9e7fe3f2a495aef7162932cdfbd"
EXPECTED_FOCAL_FREEZE_FINGERPRINT = "ba3617cae074a49270b3a140dce3671cc8e8eae2f6f8d608747a5734f7a9b077"
EXPECTED_EGPA = "EGPA0079"
EXPECTED_SPECIES = "ululevu"
EXPECTED_METADATA_BASENAME = "sequencemetadata.csv"
MIN_INDIVIDUALS = 5
LOSS_SUPPORT = 0.5
EARTH_RADIUS_KM = 6371.0088
RESPONSE_TRANSFORM = "linearized_fst"
RIDGE_PENALTY = 1.0
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20260813
MISSING_COORD_TOKENS = {"", "na", "nan", "n/a", "null", "none", "."}
EXPECTED_NODE_IDS = ("BQ", "EVN", "GA", "KR", "KV", "LA", "LK", "ML", "TA", "VL3", "VL4")
CANDIDATE_IDS = ("gabriel_current_flow", "gabriel_shortest_path", "geographic")


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _parse_coordinate(value: object, *, bound: float) -> float | None:
    text = str(value or "").strip()
    if text.lower() in MISSING_COORD_TOKENS:
        return None
    parsed = float(text)
    if not math.isfinite(parsed):
        return None
    if not (-bound <= parsed <= bound):
        raise ValueError(f"coordinate outside {-bound}..{bound}: {parsed}")
    return parsed


def _load_response_free_nodes(archive: Path) -> tuple[list[dict[str, object]], str, str]:
    archive_sha = _file_sha256(archive)
    if archive_sha != EXPECTED_ARCHIVE_SHA256:
        raise ValueError("Fiji archive SHA differs from Stage-1 verified object")

    with zipfile.ZipFile(archive, "r") as handle:
        matches = [
            info for info in handle.infolist()
            if not info.is_dir()
            and PurePosixPath(info.filename).name.lower() == EXPECTED_METADATA_BASENAME
        ]
        if len(matches) != 1:
            raise ValueError(f"expected one sequenceMetaData.csv member, found {len(matches)}")
        # Hard firewall: no other archive member content is opened in Stage 2B.
        data = handle.read(matches[0])

    metadata_sha = hashlib.sha256(data).hexdigest()
    if metadata_sha != EXPECTED_METADATA_SHA256:
        raise ValueError("sequenceMetaData.csv SHA differs from Stage-1 evidence")

    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    expected_headers = {"species", "seq", "egpa", "pop", "casent", "lat", "long"}
    if set(reader.fieldnames or ()) != expected_headers:
        raise ValueError(f"unexpected Fiji sequence metadata schema: {reader.fieldnames}")

    by_population: dict[str, list[tuple[float, float]]] = {}
    population_sample_counts: dict[str, int] = {}
    all_focal_population_counts: dict[str, int] = {}
    species_labels: set[str] = set()
    for raw in reader:
        if str(raw.get("egpa") or "").strip() != EXPECTED_EGPA:
            continue
        species = str(raw.get("species") or "").strip()
        population = str(raw.get("pop") or "").strip()
        if not species or not population:
            raise ValueError("focal Fiji metadata has missing species/pop ID")
        species_labels.add(species)
        all_focal_population_counts[population] = all_focal_population_counts.get(population, 0) + 1
        latitude = _parse_coordinate(raw.get("lat"), bound=90.0)
        longitude = _parse_coordinate(raw.get("long"), bound=180.0)
        if (latitude is None) != (longitude is None):
            raise ValueError(f"population {population} has one-sided coordinate missingness")
        if latitude is not None and longitude is not None:
            by_population.setdefault(population, []).append((latitude, longitude))

    if species_labels != {EXPECTED_SPECIES}:
        raise ValueError(f"focal EGPA species label drifted: {sorted(species_labels)}")

    admitted = sorted(
        population
        for population, count in all_focal_population_counts.items()
        if count >= MIN_INDIVIDUALS and by_population.get(population)
    )
    if tuple(admitted) != EXPECTED_NODE_IDS:
        raise ValueError(f"response-free Fiji admitted nodes drifted: {admitted}")

    nodes: list[dict[str, object]] = []
    for population in admitted:
        coordinates = by_population[population]
        count = all_focal_population_counts[population]
        population_sample_counts[population] = count
        nodes.append(
            {
                "population_id": population,
                "n_individuals": count,
                "n_individuals_with_coordinates": len(coordinates),
                "latitude": float(sum(value[0] for value in coordinates) / len(coordinates)),
                "longitude": float(sum(value[1] for value in coordinates) / len(coordinates)),
                "n_unique_sample_coordinates": len({
                    (round(value[0], 8), round(value[1], 8)) for value in coordinates
                }),
            }
        )
    return nodes, archive_sha, metadata_sha


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


def _dateline_aware_local_xy(latitude: np.ndarray, longitude: np.ndarray) -> np.ndarray:
    lat = np.radians(np.asarray(latitude, dtype=float))
    lon = np.radians(np.asarray(longitude, dtype=float))
    lat0 = float(np.mean(lat))
    # Circular longitude origin keeps Fiji nodes around +/-180 degrees locally adjacent.
    lon0 = float(np.arctan2(np.mean(np.sin(lon)), np.mean(np.cos(lon))))
    delta = lon - lon0
    wrapped = np.arctan2(np.sin(delta), np.cos(delta))
    x = EARTH_RADIUS_KM * np.cos(lat0) * wrapped
    y = EARTH_RADIUS_KM * (lat - lat0)
    return np.column_stack([x, y])


def _gabriel_edges(xy: np.ndarray, tolerance: float = 1e-10) -> list[tuple[int, int]]:
    coordinates = np.asarray(xy, dtype=float)
    output: list[tuple[int, int]] = []
    for i in range(len(coordinates)):
        for j in range(i + 1, len(coordinates)):
            delta = coordinates[i] - coordinates[j]
            diameter2 = float(np.dot(delta, delta))
            if diameter2 <= 1e-16:
                raise ValueError("Fiji response-free node centroids are duplicated")
            midpoint = 0.5 * (coordinates[i] + coordinates[j])
            radius2 = 0.25 * diameter2
            d2 = np.sum(np.square(coordinates - midpoint), axis=1)
            d2[i] = d2[j] = np.inf
            if float(np.min(d2)) >= radius2 - tolerance * max(1.0, radius2):
                output.append((i, j))
    if not output:
        raise RuntimeError("Fiji Gabriel graph has no edges")
    return output


def _shortest_path_matrix(n: int, edges: list[tuple[int, int]], edge_lengths: np.ndarray) -> np.ndarray:
    distance = np.full((n, n), np.inf, dtype=float)
    np.fill_diagonal(distance, 0.0)
    for (i, j), length in zip(edges, edge_lengths):
        distance[i, j] = distance[j, i] = min(distance[i, j], float(length))
    for k in range(n):
        distance = np.minimum(distance, distance[:, [k]] + distance[[k], :])
    if not np.isfinite(distance).all():
        raise RuntimeError("Fiji Gabriel graph is disconnected")
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
        raise RuntimeError("Fiji current-flow distance is non-finite")
    return result


def prepare(archive: Path, nodes_csv: Path, predictors_csv: Path, manifest_json: Path) -> dict[str, object]:
    if not CONTRACT.exists():
        raise RuntimeError("Fiji Stage-2B contract must exist before predictor freeze")
    nodes, archive_sha, metadata_sha = _load_response_free_nodes(archive)
    ids = tuple(str(row["population_id"]) for row in nodes)
    latitude = np.asarray([row["latitude"] for row in nodes], dtype=float)
    longitude = np.asarray([row["longitude"] for row in nodes], dtype=float)

    d_geo = _haversine_matrix(latitude, longitude)
    xy = _dateline_aware_local_xy(latitude, longitude)
    gabriel = _gabriel_edges(xy)
    edge_lengths = np.asarray([np.linalg.norm(xy[i] - xy[j]) for i, j in gabriel], dtype=float)
    support_scale = float(np.median(edge_lengths))
    if not np.isfinite(support_scale) or support_scale <= 0.0:
        raise RuntimeError("Fiji Gabriel median edge scale is invalid")

    conductance = np.zeros((len(ids), len(ids)), dtype=float)
    dynamic_edges: list[DynamicReachabilityEdge] = []
    graph_edges_manifest: list[dict[str, object]] = []
    for (i, j), length in zip(gabriel, edge_lengths):
        support = float(np.exp(-float(length) / support_scale))
        conductance[i, j] = conductance[j, i] = support
        dynamic_edges.append(DynamicReachabilityEdge(i, j, geographic_support=support))
        dynamic_edges.append(DynamicReachabilityEdge(j, i, geographic_support=support))
        graph_edges_manifest.append(
            {
                "a": ids[i],
                "b": ids[j],
                "projected_length_km": float(length),
                "support": support,
            }
        )

    operator = build_dynamic_transition_operator(ids, dynamic_edges, loss_support=LOSS_SUPPORT)
    connectivity = infer_eventual_genetic_connectivity(operator)
    d_shortest = _shortest_path_matrix(len(ids), gabriel, edge_lengths)
    d_current = _effective_resistance(conductance)

    nodes_csv.parent.mkdir(parents=True, exist_ok=True)
    with nodes_csv.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "population_id",
            "n_individuals",
            "n_individuals_with_coordinates",
            "latitude",
            "longitude",
            "n_unique_sample_coordinates",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in nodes:
            writer.writerow(
                {
                    **row,
                    "latitude": f"{float(row['latitude']):.12g}",
                    "longitude": f"{float(row['longitude']):.12g}",
                }
            )

    predictors_csv.parent.mkdir(parents=True, exist_ok=True)
    pair_rows: list[dict[str, object]] = []
    with predictors_csv.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "population_a",
            "population_b",
            "geographic",
            "gabriel_shortest_path",
            "gabriel_current_flow",
            "eog_continuous_distance",
            "eog_disconnected",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
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
                pair_rows.append(row)

    candidate_family_payload = {
        "candidate_ids": list(CANDIDATE_IDS),
        "pairs": [
            {
                "a": row["population_a"],
                "b": row["population_b"],
                "geographic": row["geographic"],
                "gabriel_shortest_path": row["gabriel_shortest_path"],
                "gabriel_current_flow": row["gabriel_current_flow"],
            }
            for row in pair_rows
        ],
    }
    node_payload = [
        {
            "population_id": row["population_id"],
            "n_individuals": row["n_individuals"],
            "latitude": f"{float(row['latitude']):.12g}",
            "longitude": f"{float(row['longitude']):.12g}",
        }
        for row in nodes
    ]

    manifest: dict[str, object] = {
        "schema": "eog_v2_1_fiji_pheidole_response_free_predictors_v1",
        "status": "response-free-genetic-predictor-freeze",
        "study_doi": "10.1111/mec.15326",
        "dryad_doi": "10.5061/dryad.xd2547dcp",
        "zenodo_record": 4965569,
        "archive_sha256": archive_sha,
        "sequence_metadata_sha256": metadata_sha,
        "stage1_fingerprint": "8291537a50ad0ee7b33f81bf7a71653a6fe317853323f1bc5c98beff132fd184",
        "stage2a_focal_freeze_fingerprint": EXPECTED_FOCAL_FREEZE_FINGERPRINT,
        "focal_egpa": EXPECTED_EGPA,
        "focal_species_label": EXPECTED_SPECIES,
        "node_admission_rule": "n_individuals >= 5 and finite response-free population centroid",
        "minimum_individuals_per_node": MIN_INDIVIDUALS,
        "n_nodes": len(ids),
        "node_ids": list(ids),
        "node_fingerprint": _canonical_sha256(node_payload),
        "projection": "dateline-aware local equirectangular; circular mean longitude; wrapped offsets",
        "gabriel_edge_count": len(gabriel),
        "gabriel_edges": graph_edges_manifest,
        "support_scale_km": support_scale,
        "loss_support": LOSS_SUPPORT,
        "operator_fingerprint": operator.fingerprint,
        "eventual_connectivity_fingerprint": connectivity.fingerprint,
        "conventional_candidate_ids": list(CANDIDATE_IDS),
        "candidate_family_fingerprint": _canonical_sha256(candidate_family_payload),
        "response_transform": RESPONSE_TRANSFORM,
        "ridge_penalty": RIDGE_PENALTY,
        "outer_validation_unit": "population",
        "inner_reference_selection": "leave-one-population-out within outer training; equal-weight inner-population MSE; lexicographic tie",
        "bootstrap_unit": "outer_population_fold",
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_interval": [0.025, 0.975],
        "promotion_rule": [
            "all 11 frozen populations align to the focal genetic response",
            "all 11 outer folds estimable",
            "mean_population_delta_mse < 0",
            "population_bootstrap_upper_97_5_percent < 0",
        ],
        "contract_sha256": _file_sha256(CONTRACT),
        "nodes_csv_sha256": _file_sha256(nodes_csv),
        "predictors_csv_sha256": _file_sha256(predictors_csv),
        "genetic_member_contents_accessed": False,
        "allowed_archive_member_contents_accessed": ["dryad/VCFs/sequenceMetaData.csv"],
    }
    manifest["predictor_manifest_fingerprint"] = _canonical_sha256(manifest)
    manifest_json.parent.mkdir(parents=True, exist_ok=True)
    manifest_json.write_text(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--nodes", type=Path, required=True)
    parser.add_argument("--predictors", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    manifest = prepare(args.archive, args.nodes, args.predictors, args.manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
