"""Prepare the frozen SW Finland EOG v2 feature bundle without reading outcomes."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
)

from benchmarks.finland_colonization_preoutcome_admission import (
    HABITAT_COLUMNS,
    LOSS_SUPPORT,
    _deterministic_spatial_folds,
    _finite_or_none,
    _gabriel_edges,
    _load_response_free_projection,
    evaluate_admission,
)

MAX_STEPS = 5
L2_PENALTY = 1.0
BOOTSTRAP_SEED = 20260812
BOOTSTRAP_REPLICATES = 10_000
MIN_COMPLETE_ROWS_PER_SPECIES = 5
MIN_FOLDS_PER_SPECIES = 2

R0_COLUMNS = (
    "Residents_per_area_log",
    "Area_log",
    "Buffer_2_km_log",
    "Buffer_5_km_log",
    "Shannon_habitats",
    "Convolution",
    "Limestone",
    "Buildings",
    "Meadow_or_pasture",
    "Deciduous_forest",
    "Coniferous_forest",
    "Mixed_forest",
    "Sand",
    "Open_rock_or_bare_ground",
    "Marsh",
    "Shore_meadow",
    "Euref_X",
    "Euref_Y",
)
R1_EXTRA_COLUMNS = ("Dist_to_historical_log", "Historical_total_log")
R2_EXTRA_COLUMNS = ("source_pressure", "min_effective_resistance")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _array_sha256(array: np.ndarray) -> str:
    value = np.ascontiguousarray(array)
    digest = hashlib.sha256()
    digest.update(str(value.dtype).encode())
    digest.update(json.dumps(value.shape).encode())
    digest.update(value.tobytes())
    return digest.hexdigest()


def _effective_resistance(conductance: np.ndarray) -> np.ndarray:
    matrix = np.asarray(conductance, dtype=float)
    if not np.allclose(matrix, matrix.T, rtol=0.0, atol=1e-12):
        raise ValueError("Finland effective resistance requires symmetric conductance")
    laplacian = np.diag(np.sum(matrix, axis=1)) - matrix
    pinv = np.linalg.pinv(laplacian)
    diagonal = np.diag(pinv)
    resistance = diagonal[:, None] + diagonal[None, :] - 2.0 * pinv
    resistance = np.maximum(resistance, 0.0)
    np.fill_diagonal(resistance, 0.0)
    return resistance


def _integrated_kernel(transition: np.ndarray, max_steps: int) -> np.ndarray:
    q = np.asarray(transition, dtype=float)
    n = q.shape[0]
    power = np.eye(n, dtype=float)
    integrated = power.copy()
    for _ in range(max_steps):
        power = power @ q
        integrated += power
    return integrated


def _build_graph(projection: dict[str, object]):
    island_ids: tuple[str, ...] = projection["island_ids"]
    coordinates: np.ndarray = projection["coordinates"]
    habitat: np.ndarray = projection["habitat"]
    gabriel = _gabriel_edges(coordinates)
    geo_lengths = np.asarray(
        [np.linalg.norm(coordinates[i] - coordinates[j]) for i, j in gabriel], dtype=float
    )
    geo_scale = float(np.median(geo_lengths))
    habitat_scale = np.where(np.std(habitat, axis=0) > 1e-12, np.std(habitat, axis=0), 1.0)
    standardized = (habitat - np.mean(habitat, axis=0)) / habitat_scale
    env_lengths = np.asarray(
        [np.linalg.norm(standardized[i] - standardized[j]) for i, j in gabriel], dtype=float
    )
    positive = env_lengths[env_lengths > 1e-12]
    if not len(positive):
        raise RuntimeError("Finland habitat transition scale is not estimable")
    env_scale = float(np.median(positive))

    primary_edges = []
    geography_edges = []
    for (i, j), d_geo, d_env in zip(gabriel, geo_lengths, env_lengths):
        k_geo = float(np.exp(-d_geo / geo_scale))
        k_env = float(np.exp(-d_env / env_scale))
        for source, target in ((i, j), (j, i)):
            primary_edges.append(
                DynamicReachabilityEdge(
                    source,
                    target,
                    geographic_support=k_geo,
                    environmental_support=k_env,
                )
            )
            geography_edges.append(
                DynamicReachabilityEdge(source, target, geographic_support=k_geo)
            )
    primary = build_dynamic_transition_operator(island_ids, primary_edges, loss_support=LOSS_SUPPORT)
    geography = build_dynamic_transition_operator(island_ids, geography_edges, loss_support=LOSS_SUPPORT)
    return primary, geography, gabriel, geo_scale, env_scale


def _read_response_free_rows(path: Path) -> list[dict[str, object]]:
    required = {"spp.name", "holmkod", *R0_COLUMNS, *R1_EXTRA_COLUMNS}
    output = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("colonization CSV has no header")
        missing = required - set(reader.fieldnames)
        if missing:
            raise ValueError(f"Finland feature preparation missing columns: {sorted(missing)}")
        if "outcome" not in reader.fieldnames:
            raise ValueError("authoritative Finland CSV must retain its outcome column")
        for row in reader:
            # Outcome firewall: outcome is deliberately not accessed.
            record: dict[str, object] = {
                "species": row["spp.name"].strip(),
                "island": row["holmkod"].strip(),
            }
            for column in (*R0_COLUMNS, *R1_EXTRA_COLUMNS):
                record[column] = _finite_or_none(row[column])
            output.append(record)
    return output


def prepare_bundle(input_path: str | Path, bundle_path: str | Path, manifest_path: str | Path) -> dict[str, object]:
    input_path = Path(input_path)
    bundle_path = Path(bundle_path)
    manifest_path = Path(manifest_path)
    admission = evaluate_admission(input_path)
    if not admission["admitted"]:
        raise RuntimeError("Finland response-free admission failed; outcome scoring remains prohibited")
    projection = _load_response_free_projection(input_path)
    island_ids: tuple[str, ...] = projection["island_ids"]
    species_ids: tuple[str, ...] = projection["species_ids"]
    coordinates: np.ndarray = projection["coordinates"]
    primary, geography, gabriel, geo_scale, env_scale = _build_graph(projection)
    island_index = {value: index for index, value in enumerate(island_ids)}
    source_sets = {
        species: tuple(sorted(set(island_ids) - projection["species_targets"][species]))
        for species in species_ids
    }
    sourceful_species = tuple(species for species in species_ids if source_sets[species])
    species_index = {value: index for index, value in enumerate(sourceful_species)}

    # Response-free spatial fold assignment, identical for every species on an island.
    island_folds = _deterministic_spatial_folds(island_ids, coordinates)

    # Conventional source/network references.
    coordinate_delta = coordinates[:, None, :] - coordinates[None, :, :]
    geographic_distance = np.sqrt(np.sum(coordinate_delta * coordinate_delta, axis=2))
    resistance = _effective_resistance(primary.raw_support)
    primary_kernel = _integrated_kernel(primary.transition, MAX_STEPS)
    geography_kernel = _integrated_kernel(geography.transition, MAX_STEPS)

    species_source_features: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = {}
    for species in sourceful_species:
        source_indices = np.asarray([island_index[value] for value in source_sets[species]], dtype=int)
        source_pressure = np.sum(np.exp(-geographic_distance[source_indices] / geo_scale), axis=0)
        min_resistance = np.min(resistance[:, source_indices], axis=1)
        weights = np.zeros(len(island_ids), dtype=float)
        weights[source_indices] = 1.0 / float(len(source_indices))
        dynamic = weights @ primary_kernel
        dynamic_geo = weights @ geography_kernel
        species_source_features[species] = (
            source_pressure,
            min_resistance,
            dynamic,
            dynamic_geo,
        )

    raw_rows = _read_response_free_rows(input_path)
    selected_rows = [row for row in raw_rows if row["species"] in species_index]
    n = len(selected_rows)
    r0 = np.full((n, len(R0_COLUMNS)), np.nan, dtype=float)
    r1 = np.full((n, len(R0_COLUMNS) + len(R1_EXTRA_COLUMNS)), np.nan, dtype=float)
    r2 = np.full((n, len(R0_COLUMNS) + len(R1_EXTRA_COLUMNS) + len(R2_EXTRA_COLUMNS)), np.nan, dtype=float)
    dynamic = np.full(n, np.nan, dtype=float)
    dynamic_geo = np.full(n, np.nan, dtype=float)
    row_species = np.empty(n, dtype=np.int32)
    row_island = np.empty(n, dtype=np.int32)
    row_fold = np.empty(n, dtype=np.int16)

    for position, row in enumerate(selected_rows):
        species = str(row["species"])
        island = str(row["island"])
        s_index = species_index[species]
        i_index = island_index[island]
        row_species[position] = s_index
        row_island[position] = i_index
        row_fold[position] = int(island_folds[i_index])
        local = [row[column] for column in R0_COLUMNS]
        history = [row[column] for column in R1_EXTRA_COLUMNS]
        if all(value is not None for value in local):
            r0[position] = np.asarray(local, dtype=float)
        if all(value is not None for value in (*local, *history)):
            r1[position] = np.asarray([*local, *history], dtype=float)
            source_pressure, min_resistance, dyn, dyn_geo = species_source_features[species]
            r2[position] = np.asarray(
                [*local, *history, source_pressure[i_index], min_resistance[i_index]],
                dtype=float,
            )
            dynamic[position] = float(dyn[i_index])
            dynamic_geo[position] = float(dyn_geo[i_index])

    complete = np.isfinite(r2).all(axis=1) & np.isfinite(dynamic)
    species_response_free_eligible = np.zeros(len(sourceful_species), dtype=bool)
    species_complete_counts = np.zeros(len(sourceful_species), dtype=np.int32)
    species_fold_counts = np.zeros(len(sourceful_species), dtype=np.int16)
    for species_position in range(len(sourceful_species)):
        mask = complete & (row_species == species_position)
        species_complete_counts[species_position] = int(np.sum(mask))
        species_fold_counts[species_position] = int(len(set(row_fold[mask].tolist())))
        species_response_free_eligible[species_position] = bool(
            species_complete_counts[species_position] >= MIN_COMPLETE_ROWS_PER_SPECIES
            and species_fold_counts[species_position] >= MIN_FOLDS_PER_SPECIES
        )
    analysis_mask = complete & species_response_free_eligible[row_species]

    arrays = {
        "r0": r0,
        "r1": r1,
        "r2": r2,
        "dynamic": dynamic,
        "dynamic_geo": dynamic_geo,
        "row_species": row_species,
        "row_island": row_island,
        "row_fold": row_fold,
        "complete": complete.astype(np.uint8),
        "analysis_mask": analysis_mask.astype(np.uint8),
        "species_complete_counts": species_complete_counts,
        "species_fold_counts": species_fold_counts,
        "species_response_free_eligible": species_response_free_eligible.astype(np.uint8),
    }
    array_fingerprints = {name: _array_sha256(value) for name, value in arrays.items()}
    row_keys = [
        [sourceful_species[int(row_species[index])], island_ids[int(row_island[index])]]
        for index in range(n)
    ]
    row_key_fingerprint = hashlib.sha256(
        json.dumps(row_keys, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()
    contract_path = Path("docs/eog_v2_finland_colonization_preoutcome_contract.md")
    inference_path = Path("docs/eog_v2_finland_colonization_inference_freeze.md")
    if not contract_path.exists() or not inference_path.exists():
        raise RuntimeError("Finland pre-outcome contract files must exist before feature freeze")
    contract_sha256 = _sha256_file(contract_path)
    inference_sha256 = _sha256_file(inference_path)

    manifest = {
        "schema": "eog_v2_finland_colonization_response_free_bundle_v1",
        "raw_file": input_path.name,
        "raw_sha256": admission["raw_sha256"],
        "admission_response_free_projection_fingerprint": admission["response_free_projection_fingerprint"],
        "admission_operator_fingerprint": admission["operator_fingerprint"],
        "admission_source_fingerprint": admission["source_fingerprint"],
        "admission_fold_fingerprint": admission["fold_fingerprint"],
        "contract_path": str(contract_path),
        "contract_sha256": contract_sha256,
        "inference_freeze_path": str(inference_path),
        "inference_freeze_sha256": inference_sha256,
        "n_islands": len(island_ids),
        "n_sourceful_species": len(sourceful_species),
        "n_zero_source_species": admission["n_zero_source_species"],
        "n_rows_sourceful": n,
        "n_rows_analysis_response_free": int(np.sum(analysis_mask)),
        "n_species_analysis_response_free": int(np.sum(species_response_free_eligible)),
        "island_ids": list(island_ids),
        "sourceful_species_ids": list(sourceful_species),
        "r0_columns": list(R0_COLUMNS),
        "r1_columns": [*R0_COLUMNS, *R1_EXTRA_COLUMNS],
        "r2_columns": [*R0_COLUMNS, *R1_EXTRA_COLUMNS, *R2_EXTRA_COLUMNS],
        "candidate_extra": "fixed_source_dynamic_reachability",
        "sensitivity_extra": "geography_only_dynamic_reachability",
        "gabriel_edge_count": len(gabriel),
        "geographic_scale": geo_scale,
        "environmental_scale": env_scale,
        "primary_operator_fingerprint": primary.fingerprint,
        "geography_operator_fingerprint": geography.fingerprint,
        "loss_support": LOSS_SUPPORT,
        "max_steps": MAX_STEPS,
        "n_spatial_folds": 5,
        "l2_penalty": L2_PENALTY,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "min_complete_rows_per_species": MIN_COMPLETE_ROWS_PER_SPECIES,
        "min_folds_per_species": MIN_FOLDS_PER_SPECIES,
        "array_fingerprints": array_fingerprints,
        "row_key_fingerprint": row_key_fingerprint,
        "outcome_values_accessed": False,
    }
    manifest["feature_bundle_fingerprint"] = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()

    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(bundle_path, **arrays)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    manifest = prepare_bundle(args.input, args.bundle, args.manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
