"""Prepare the frozen SW Finland strict-source cohort without reading outcomes.

This response-free redesign preserves the original 471-island graph, predictors, folds,
fit settings and inference contract. It changes only species eligibility: the exact
180-species sourceful list whose released potential-target complement cardinality equals
the independently decoded positive historical-island count is used. No historical source
is repaired, deleted, or inferred.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

if __package__ in {None, ""}:
    _repo_root = str(Path(__file__).resolve().parents[1])
    if _repo_root not in sys.path:
        sys.path.insert(0, _repo_root)

from benchmarks.finland_csv_format_adapter import detect_csv_format, fixed_dict_reader_delimiter
from benchmarks.finland_historical_count_grid import decode_integer_historical_counts
from benchmarks.finland_colonization_preoutcome_admission import (
    CONSISTENCY_R2,
    EXPECTED_ISLANDS,
    _best_affine_transform_r2,
    _canonical_sha256,
    _deterministic_spatial_folds,
    _load_response_free_projection,
)
from benchmarks.finland_colonization_prepare import (
    BOOTSTRAP_REPLICATES,
    BOOTSTRAP_SEED,
    L2_PENALTY,
    MAX_STEPS,
    MIN_COMPLETE_ROWS_PER_SPECIES,
    MIN_FOLDS_PER_SPECIES,
    R0_COLUMNS,
    R1_EXTRA_COLUMNS,
    R2_EXTRA_COLUMNS,
    _array_sha256,
    _build_graph,
    _effective_resistance,
    _integrated_kernel,
    _read_response_free_rows,
    _sha256_file,
)

STRICT_SPECIES_PATH = Path("benchmarks/frozen/finland_strict_source_cohort/exact_complement_species.txt")
STRICT_SUMMARY_PATH = Path("benchmarks/frozen/finland_strict_source_cohort/response_free_summary.json")
STRICT_CONTRACT_PATH = Path("docs/eog_v2_finland_strict_source_cohort_contract.md")
ORIGINAL_CONTRACT_PATH = Path("docs/eog_v2_finland_colonization_preoutcome_contract.md")
INFERENCE_FREEZE_PATH = Path("docs/eog_v2_finland_colonization_inference_freeze.md")
EXPECTED_STRICT_LIST_SHA256 = "e218f94e5facd4ed330a80b0fead0012b31fd5cb7b7b026f2ee0ff326277b2bc"
EXPECTED_SOURCE_IDENTIFIABILITY_FP = "06f38cb7a5d1321c5dde4072ee0c1329f52de05a55fed353909b342e3f4e2afd"
EXPECTED_RAW_SHA256 = "72b631033ef36210ee19b151dc4f6569760262d68f70b9ce6de6c8a11afeb957"
EXPECTED_STRICT_SPECIES = 180
MIN_STRICT_ANALYSIS_SPECIES = 100
STRICT_BUNDLE_SCHEMA = "eog_v2_finland_strict_source_response_free_bundle_v1"


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _strict_species() -> tuple[str, ...]:
    if _file_sha256(STRICT_SPECIES_PATH) != EXPECTED_STRICT_LIST_SHA256:
        raise RuntimeError("Finland frozen strict species list SHA-256 drifted")
    values = tuple(line.rstrip("\n") for line in STRICT_SPECIES_PATH.read_text(encoding="utf-8").splitlines())
    if len(values) != EXPECTED_STRICT_SPECIES or len(set(values)) != len(values) or any(not value for value in values):
        raise RuntimeError("Finland frozen strict species list is malformed")
    return values


def _decoded_counts(projection: dict[str, object]) -> dict[str, int]:
    island_ids: tuple[str, ...] = projection["island_ids"]
    universe = set(island_ids)
    species = []
    candidate = []
    released = []
    for taxon in projection["species_ids"]:
        values = projection["species_history_values"].get(taxon, [])
        if not values:
            continue
        unique = sorted({float(value) for value in values})
        if len(unique) != 1:
            raise ValueError(f"Historical_total_log varies within species {taxon}")
        species.append(taxon)
        candidate.append(len(universe - projection["species_targets"][taxon]))
        released.append(unique[0])
    decoded, metadata = decode_integer_historical_counts(
        np.asarray(candidate, dtype=float),
        np.asarray(released, dtype=float),
        max_count=len(island_ids),
    )
    summary = json.loads(STRICT_SUMMARY_PATH.read_text(encoding="utf-8"))
    if summary.get("source_identifiability_fingerprint") != EXPECTED_SOURCE_IDENTIFIABILITY_FP:
        raise RuntimeError("Finland strict-source response-free summary fingerprint drifted")
    if summary.get("n_strict_sourceful_exact_complement_species") != EXPECTED_STRICT_SPECIES:
        raise RuntimeError("Finland strict-source response-free summary count drifted")
    expected_grid = summary.get("historical_count_grid") or {}
    for key in ("transform", "intercept", "slope", "candidate_exact_line_support"):
        if key not in expected_grid:
            raise RuntimeError("Finland frozen historical-count grid summary is incomplete")
    if metadata["transform"] != expected_grid["transform"]:
        raise RuntimeError("Finland historical-count decoder transform drifted")
    if not np.allclose(
        [metadata["intercept"], metadata["slope"]],
        [expected_grid["intercept"], expected_grid["slope"]],
        rtol=0.0,
        atol=1e-12,
    ):
        raise RuntimeError("Finland historical-count standardization grid drifted")
    return {taxon: int(count) for taxon, count in zip(species, decoded.tolist(), strict=True)}


def evaluate_strict_admission(input_path: str | Path) -> dict[str, object]:
    source = Path(input_path)
    raw_sha = _file_sha256(source)
    if raw_sha != EXPECTED_RAW_SHA256:
        raise ValueError("Finland strict-source raw SHA-256 mismatch")
    fmt = detect_csv_format(source)
    with fixed_dict_reader_delimiter(str(fmt["delimiter"])):
        projection = _load_response_free_projection(source)

    island_ids: tuple[str, ...] = projection["island_ids"]
    coordinates: np.ndarray = projection["coordinates"]
    strict_species = _strict_species()
    available_species = set(projection["species_ids"])
    if not set(strict_species).issubset(available_species):
        missing = sorted(set(strict_species) - available_species)
        raise RuntimeError(f"Finland frozen strict species missing from raw data: {missing[:5]}")
    decoded = _decoded_counts(projection)
    universe = set(island_ids)

    recomputed_exact = tuple(
        sorted(
            taxon
            for taxon, true_count in decoded.items()
            if true_count > 0
            and len(universe - projection["species_targets"][taxon]) == true_count
        )
    )
    if set(recomputed_exact) != set(strict_species) or len(recomputed_exact) != EXPECTED_STRICT_SPECIES:
        raise RuntimeError("Finland response-free exact-complement cohort no longer reproduces the frozen list")

    source_sets = {
        taxon: tuple(sorted(universe - projection["species_targets"][taxon]))
        for taxon in strict_species
    }
    if any(len(source_sets[taxon]) != decoded[taxon] or not source_sets[taxon] for taxon in strict_species):
        raise RuntimeError("Finland strict source cardinality drifted")

    island_index = {island: index for index, island in enumerate(island_ids)}
    source_coordinate_cache = {
        taxon: coordinates[np.asarray([island_index[value] for value in source_sets[taxon]], dtype=int)]
        for taxon in strict_species
    }
    distance_x: list[float] = []
    distance_y: list[float] = []
    for taxon, island, released in projection["nearest_records"]:
        if taxon not in source_sets or released is None:
            continue
        target_coordinate = coordinates[island_index[island]]
        reconstructed = float(
            np.min(np.linalg.norm(source_coordinate_cache[taxon] - target_coordinate, axis=1))
        )
        distance_x.append(reconstructed)
        distance_y.append(float(released))
    nearest_fit = _best_affine_transform_r2(np.asarray(distance_x), np.asarray(distance_y))

    primary, geography, gabriel, geo_scale, env_scale = _build_graph(projection)
    folds = _deterministic_spatial_folds(island_ids, coordinates)
    fold_payload = {island: int(folds[index]) for index, island in enumerate(island_ids)}
    source_payload = {taxon: list(source_sets[taxon]) for taxon in strict_species}
    source_fp = _canonical_sha256(source_payload)
    fold_fp = _canonical_sha256(fold_payload)
    projection_fp = _canonical_sha256(
        {
            "raw_sha256": raw_sha,
            "strict_species_list_sha256": EXPECTED_STRICT_LIST_SHA256,
            "island_ids": list(island_ids),
            "source_sets": source_payload,
            "primary_operator_fingerprint": primary.fingerprint,
            "folds": fold_payload,
        }
    )

    checks = {
        "raw_identity": {"passed": raw_sha == EXPECTED_RAW_SHA256},
        "island_universe": {
            "value": len(island_ids),
            "required": EXPECTED_ISLANDS,
            "passed": len(island_ids) == EXPECTED_ISLANDS,
        },
        "strict_species_count": {
            "value": len(strict_species),
            "required": EXPECTED_STRICT_SPECIES,
            "passed": len(strict_species) == EXPECTED_STRICT_SPECIES,
        },
        "strict_species_minimum": {
            "value": len(strict_species),
            "required_minimum": MIN_STRICT_ANALYSIS_SPECIES,
            "passed": len(strict_species) >= MIN_STRICT_ANALYSIS_SPECIES,
        },
        "nearest_history_consistency": {
            "value": float(nearest_fit["r2"]),
            "required_minimum": CONSISTENCY_R2,
            "passed": float(nearest_fit["r2"]) >= CONSISTENCY_R2,
        },
    }
    admitted = bool(all(value["passed"] for value in checks.values()))
    result = {
        "status": "finland-strict-source-response-free-admission",
        "admitted": admitted,
        "outcome_values_accessed": False,
        "raw_sha256": raw_sha,
        "n_islands": len(island_ids),
        "n_species_strict": len(strict_species),
        "strict_species_list_sha256": EXPECTED_STRICT_LIST_SHA256,
        "source_identifiability_fingerprint": EXPECTED_SOURCE_IDENTIFIABILITY_FP,
        "nearest_history_release_fit": nearest_fit,
        "source_fingerprint": source_fp,
        "fold_fingerprint": fold_fp,
        "response_free_projection_fingerprint": projection_fp,
        "primary_operator_fingerprint": primary.fingerprint,
        "geography_operator_fingerprint": geography.fingerprint,
        "gabriel_edge_count": len(gabriel),
        "geographic_scale": geo_scale,
        "environmental_scale": env_scale,
        "checks": checks,
    }
    result["fingerprint"] = _canonical_sha256(result)
    return result


def prepare_strict_bundle(
    input_path: str | Path,
    bundle_path: str | Path,
    manifest_path: str | Path,
) -> dict[str, object]:
    input_path = Path(input_path)
    bundle_path = Path(bundle_path)
    manifest_path = Path(manifest_path)
    admission = evaluate_strict_admission(input_path)
    if not admission["admitted"]:
        raise RuntimeError("Finland strict-source response-free admission failed")
    fmt = detect_csv_format(input_path)
    with fixed_dict_reader_delimiter(str(fmt["delimiter"])):
        projection = _load_response_free_projection(input_path)
        raw_rows = _read_response_free_rows(input_path)

    island_ids: tuple[str, ...] = projection["island_ids"]
    coordinates: np.ndarray = projection["coordinates"]
    strict_species = _strict_species()
    species_index = {value: index for index, value in enumerate(strict_species)}
    island_index = {value: index for index, value in enumerate(island_ids)}
    universe = set(island_ids)
    source_sets = {
        taxon: tuple(sorted(universe - projection["species_targets"][taxon]))
        for taxon in strict_species
    }

    primary, geography, gabriel, geo_scale, env_scale = _build_graph(projection)
    island_folds = _deterministic_spatial_folds(island_ids, coordinates)
    coordinate_delta = coordinates[:, None, :] - coordinates[None, :, :]
    geographic_distance = np.sqrt(np.sum(coordinate_delta * coordinate_delta, axis=2))
    resistance = _effective_resistance(primary.raw_support)
    primary_kernel = _integrated_kernel(primary.transition, MAX_STEPS)
    geography_kernel = _integrated_kernel(geography.transition, MAX_STEPS)

    species_source_features: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = {}
    for taxon in strict_species:
        source_indices = np.asarray([island_index[value] for value in source_sets[taxon]], dtype=int)
        source_pressure = np.sum(np.exp(-geographic_distance[source_indices] / geo_scale), axis=0)
        min_resistance = np.min(resistance[:, source_indices], axis=1)
        weights = np.zeros(len(island_ids), dtype=float)
        weights[source_indices] = 1.0 / float(len(source_indices))
        dynamic = weights @ primary_kernel
        dynamic_geo = weights @ geography_kernel
        species_source_features[taxon] = (source_pressure, min_resistance, dynamic, dynamic_geo)

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
        taxon = str(row["species"])
        island = str(row["island"])
        s_index = species_index[taxon]
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
            source_pressure, min_resistance, dyn, dyn_geo = species_source_features[taxon]
            r2[position] = np.asarray(
                [*local, *history, source_pressure[i_index], min_resistance[i_index]], dtype=float
            )
            dynamic[position] = float(dyn[i_index])
            dynamic_geo[position] = float(dyn_geo[i_index])

    complete = np.isfinite(r2).all(axis=1) & np.isfinite(dynamic)
    species_response_free_eligible = np.zeros(len(strict_species), dtype=bool)
    species_complete_counts = np.zeros(len(strict_species), dtype=np.int32)
    species_fold_counts = np.zeros(len(strict_species), dtype=np.int16)
    for position in range(len(strict_species)):
        mask = complete & (row_species == position)
        species_complete_counts[position] = int(np.sum(mask))
        species_fold_counts[position] = int(len(set(row_fold[mask].tolist())))
        species_response_free_eligible[position] = bool(
            species_complete_counts[position] >= MIN_COMPLETE_ROWS_PER_SPECIES
            and species_fold_counts[position] >= MIN_FOLDS_PER_SPECIES
        )
    analysis_mask = complete & species_response_free_eligible[row_species]
    n_analysis_species = int(np.sum(species_response_free_eligible))
    if n_analysis_species < MIN_STRICT_ANALYSIS_SPECIES:
        raise RuntimeError(
            f"Finland strict-source complete/fold gate retained only {n_analysis_species} species < {MIN_STRICT_ANALYSIS_SPECIES}"
        )

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
        [strict_species[int(row_species[index])], island_ids[int(row_island[index])]]
        for index in range(n)
    ]
    row_key_fingerprint = hashlib.sha256(
        json.dumps(row_keys, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()

    manifest = {
        "schema": STRICT_BUNDLE_SCHEMA,
        "raw_file": input_path.name,
        "raw_sha256": admission["raw_sha256"],
        "strict_admission_fingerprint": admission["fingerprint"],
        "admission_response_free_projection_fingerprint": admission["response_free_projection_fingerprint"],
        "admission_operator_fingerprint": admission["primary_operator_fingerprint"],
        "admission_source_fingerprint": admission["source_fingerprint"],
        "admission_fold_fingerprint": admission["fold_fingerprint"],
        "contract_path": str(ORIGINAL_CONTRACT_PATH),
        "contract_sha256": _sha256_file(ORIGINAL_CONTRACT_PATH),
        "strict_cohort_contract_path": str(STRICT_CONTRACT_PATH),
        "strict_cohort_contract_sha256": _sha256_file(STRICT_CONTRACT_PATH),
        "strict_species_list_path": str(STRICT_SPECIES_PATH),
        "strict_species_list_sha256": EXPECTED_STRICT_LIST_SHA256,
        "source_identifiability_fingerprint": EXPECTED_SOURCE_IDENTIFIABILITY_FP,
        "inference_freeze_path": str(INFERENCE_FREEZE_PATH),
        "inference_freeze_sha256": _sha256_file(INFERENCE_FREEZE_PATH),
        "n_islands": len(island_ids),
        "n_sourceful_species": len(strict_species),
        "n_zero_source_species": 0,
        "n_rows_sourceful": n,
        "n_rows_analysis_response_free": int(np.sum(analysis_mask)),
        "n_species_analysis_response_free": n_analysis_species,
        "island_ids": list(island_ids),
        "sourceful_species_ids": list(strict_species),
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
        "loss_support": 0.55,
        "max_steps": MAX_STEPS,
        "n_spatial_folds": 5,
        "l2_penalty": L2_PENALTY,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "min_complete_rows_per_species": MIN_COMPLETE_ROWS_PER_SPECIES,
        "min_folds_per_species": MIN_FOLDS_PER_SPECIES,
        "minimum_analysis_species": MIN_STRICT_ANALYSIS_SPECIES,
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
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    fmt = detect_csv_format(args.input)
    with fixed_dict_reader_delimiter(str(fmt["delimiter"])):
        admission = evaluate_strict_admission(args.input)
    args.admission.parent.mkdir(parents=True, exist_ok=True)
    args.admission.write_text(
        json.dumps(admission, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    if not admission["admitted"]:
        raise SystemExit("Finland strict-source response-free admission failed")
    manifest = prepare_strict_bundle(args.input, args.bundle, args.manifest)
    print(json.dumps({
        "status": admission["status"],
        "admitted": admission["admitted"],
        "outcome_values_accessed": False,
        "n_species_strict": admission["n_species_strict"],
        "n_species_analysis_response_free": manifest["n_species_analysis_response_free"],
        "feature_bundle_fingerprint": manifest["feature_bundle_fingerprint"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()