"""One-time exact Thalassia microsatellite validation after all pre-response freezes.

This runner is defined before pairwise FST is computed. It consumes only the exact released
workbook plus the immutable Stage-2 predictors and pre-FST manifest. Primary promotion uses
the clone-corrected response only; the complete-ramet response is descriptive sensitivity.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

from benchmarks.thalassia_genalex_stage3 import (
    FROZEN_POPULATION_IDS,
    GenAlExSchemaError,
    build_pairwise_response,
    parse_genalex_workbook,
    write_response_csv,
)
from benchmarks.zhoushan_weir_cockerham import all_pairwise_theta
from eog.genetic_reference_selection import evaluate_nested_genetic_reference_selection
from eog.genetic_validation import GeneticValidationConfig, _fit_ridge, _predict_ridge


RAW_SHA256 = "aaaab9e302c9be8cf4e108d2aee5867c0b64ed70b6d3b81bad4d60168ee7f2f3"
RAW_SIZE = 118400
STAGE2_DIR = Path("benchmarks/frozen/thalassia_stage2_predictors")
STAGE2_PREDICTORS = STAGE2_DIR / "predictors.csv"
STAGE2_MANIFEST = STAGE2_DIR / "manifest.json"
STAGE3_SCHEMA = Path("benchmarks/frozen/thalassia_stage3_schema/schema_audit.json")
PREFST_MANIFEST = Path("benchmarks/frozen/thalassia_stage3_preaccess/manifest.json")
EXPECTED_STAGE2_PREDICTORS_SHA256 = "05c3a2e65029d44532e55436bc97c33482f96fb2d1951d79a0b50c776b02b7e1"
EXPECTED_STAGE2_MANIFEST_SHA256 = "38f677f4d5f864d7d661e251c4e3970f2098ae2155a0125bb88045aa55fc442f"
EXPECTED_STAGE2_FINGERPRINT = "ef119675a596fe2044aca97b43efc618cfb7b00aee1dc3a1663ff5736c0a94ea"
EXPECTED_SCHEMA_SHA256 = "2adacdadb9bd10488e4514dce583b57156f97e964037c5683592b83524038f2b"
EXPECTED_SCHEMA_FINGERPRINT = "a0b2c6bb0755f1d09f9aa88fbe4bfa645c5a4c8f011907fe4ceb93f64ff674de"
CANDIDATE_IDS = ("gabriel_current_flow", "gabriel_shortest_path", "geographic")
RIDGE_PENALTY = 1.0
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20260813


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _verify_frozen_inputs(raw_path: Path) -> dict[str, object]:
    if raw_path.stat().st_size != RAW_SIZE or _sha256(raw_path) != RAW_SHA256:
        raise ValueError("Thalassia raw microsatellite identity drifted")
    if _sha256(STAGE2_PREDICTORS) != EXPECTED_STAGE2_PREDICTORS_SHA256:
        raise ValueError("Thalassia Stage-2 predictor bytes drifted")
    if _sha256(STAGE2_MANIFEST) != EXPECTED_STAGE2_MANIFEST_SHA256:
        raise ValueError("Thalassia Stage-2 manifest bytes drifted")
    stage2 = json.loads(STAGE2_MANIFEST.read_text(encoding="utf-8"))
    if stage2.get("fingerprint") != EXPECTED_STAGE2_FINGERPRINT:
        raise ValueError("Thalassia Stage-2 manifest fingerprint drifted")
    if stage2.get("genetic_response_attached") is not False:
        raise ValueError("Thalassia Stage-2 predictors are no longer response-free")
    if tuple(stage2.get("candidate_ids") or ()) != CANDIDATE_IDS:
        raise ValueError("Thalassia frozen conventional candidate family drifted")
    if _sha256(STAGE3_SCHEMA) != EXPECTED_SCHEMA_SHA256:
        raise ValueError("Thalassia Stage-3A schema artifact bytes drifted")
    schema = json.loads(STAGE3_SCHEMA.read_text(encoding="utf-8"))
    if schema.get("schema_fingerprint") != EXPECTED_SCHEMA_FINGERPRINT:
        raise ValueError("Thalassia Stage-3A schema fingerprint drifted")
    if schema.get("genetic_response_computed") is not False:
        raise ValueError("Thalassia schema artifact already contains a genetic response")

    prefst = json.loads(PREFST_MANIFEST.read_text(encoding="utf-8"))
    if prefst.get("status") != "frozen-after-schema-before-fst":
        raise ValueError("Thalassia pre-FST harmonization manifest is absent or stale")
    if prefst.get("schema_only_workbook_access_completed") is not True:
        raise ValueError("Thalassia pre-FST manifest must acknowledge schema-only access")
    if prefst.get("multilocus_genotypes_computed") is not False or prefst.get("genetic_response_computed") is not False:
        raise ValueError("Thalassia pre-FST manifest is not response-free")
    file_hashes = prefst.get("file_sha256") or {}
    required_paths = (
        "benchmarks/thalassia_genalex_stage3.py",
        "benchmarks/thalassia_exact_genetic_validation.py",
        "tests/test_thalassia_genalex_stage3.py",
        "docs/eog_v2_thalassia_stage3_microsatellite_contract.md",
        "docs/eog_v2_thalassia_stage3_genetic_response_contract.md",
        "src/eog/genetic_reference_selection.py",
        "benchmarks/zhoushan_weir_cockerham.py",
    )
    for raw in required_paths:
        path = Path(raw)
        expected = file_hashes.get(raw)
        if not expected or _sha256(path) != expected:
            raise ValueError(f"Thalassia pre-FST implementation drifted: {raw}")
    return {"stage2": stage2, "schema": schema, "prefst": prefst}


def _load_predictor_matrices() -> tuple[tuple[str, ...], dict[str, np.ndarray], np.ndarray, np.ndarray]:
    ids = tuple(FROZEN_POPULATION_IDS)
    index = {population_id: i for i, population_id in enumerate(ids)}
    n = len(ids)
    matrices = {candidate: np.zeros((n, n), dtype=float) for candidate in CANDIDATE_IDS}
    eog = np.zeros((n, n), dtype=float)
    disconnected = np.zeros((n, n), dtype=bool)
    seen: set[tuple[int, int]] = set()
    with STAGE2_PREDICTORS.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            a = index[raw["population_a"]]
            b = index[raw["population_b"]]
            if a == b or (min(a, b), max(a, b)) in seen:
                raise ValueError("duplicate/diagonal Thalassia Stage-2 predictor pair")
            i, j = min(a, b), max(a, b)
            seen.add((i, j))
            for candidate in CANDIDATE_IDS:
                value = float(raw[candidate])
                matrices[candidate][i, j] = matrices[candidate][j, i] = value
            value = float(raw["eog_continuous_distance"])
            eog[i, j] = eog[j, i] = value
            flag = bool(int(raw["eog_disconnected"]))
            disconnected[i, j] = disconnected[j, i] = flag
    if len(seen) != n * (n - 1) // 2:
        raise ValueError("Thalassia Stage-2 predictor pair set is incomplete")
    return ids, matrices, eog, disconnected


def _response_matrix(rows: Sequence[Mapping[str, object]], value_key: str) -> np.ndarray:
    ids = tuple(FROZEN_POPULATION_IDS)
    index = {population_id: i for i, population_id in enumerate(ids)}
    matrix = np.zeros((len(ids), len(ids)), dtype=float)
    seen: set[tuple[int, int]] = set()
    for row in rows:
        i = index[str(row["population_a"])]
        j = index[str(row["population_b"])]
        pair = (min(i, j), max(i, j))
        if pair in seen:
            raise ValueError("duplicate Thalassia genetic-response pair")
        seen.add(pair)
        value = float(row[value_key])
        matrix[i, j] = matrix[j, i] = value
    if len(seen) != len(ids) * (len(ids) - 1) // 2:
        raise ValueError("Thalassia genetic-response pair set is incomplete")
    return matrix


def _fixed_geographic_outer(theta: np.ndarray, geographic: np.ndarray) -> dict[str, object]:
    ids = tuple(FROZEN_POPULATION_IDS)
    n = len(ids)
    pairs = np.asarray([(i, j) for i in range(n) for j in range(i + 1, n)], dtype=int)
    y = np.asarray([theta[i, j] / (1.0 - theta[i, j]) for i, j in pairs], dtype=float)
    x = np.asarray([geographic[i, j] for i, j in pairs], dtype=float)[:, None]
    pooled_squared: list[float] = []
    folds: list[dict[str, object]] = []
    for outer, population_id in enumerate(ids):
        test = (pairs[:, 0] == outer) | (pairs[:, 1] == outer)
        train = ~test
        model = _fit_ridge(x[train], y[train], RIDGE_PENALTY)
        prediction = _predict_ridge(model, x[test])
        error = y[test] - prediction
        squared = np.square(error)
        pooled_squared.extend(squared.tolist())
        folds.append({"held_out_population": population_id, "mse": float(np.mean(squared))})
    return {"pooled_mse": float(np.mean(pooled_squared)), "folds": folds}


def _nested_to_dict(result) -> dict[str, object]:
    return {
        "node_ids": list(result.node_ids),
        "candidate_ids": list(result.candidate_ids),
        "n_observed_pairs": result.n_observed_pairs,
        "selection_counts": [list(value) for value in result.selection_counts],
        "baseline_pooled_mse": result.baseline_pooled_mse,
        "augmented_pooled_mse": result.augmented_pooled_mse,
        "pooled_delta_mse": result.pooled_delta_mse,
        "baseline_pooled_mae": result.baseline_pooled_mae,
        "augmented_pooled_mae": result.augmented_pooled_mae,
        "pooled_delta_mae": result.pooled_delta_mae,
        "mean_population_delta_mse": result.mean_population_delta_mse,
        "mean_population_delta_mae": result.mean_population_delta_mae,
        "fingerprint": result.fingerprint,
        "folds": [
            {
                "held_out_population": fold.held_out_population,
                "selected_reference": fold.selected_reference,
                "n_train_pairs": fold.n_train_pairs,
                "n_test_pairs": fold.n_test_pairs,
                "baseline_mse": fold.baseline_mse,
                "augmented_mse": fold.augmented_mse,
                "delta_mse": fold.delta_mse,
                "baseline_mae": fold.baseline_mae,
                "augmented_mae": fold.augmented_mae,
                "delta_mae": fold.delta_mae,
                "inner_scores": [
                    {
                        "reference_id": score.reference_id,
                        "n_inner_folds": score.n_inner_folds,
                        "mean_population_mse": score.mean_population_mse,
                        "mean_population_mae": score.mean_population_mae,
                    }
                    for score in fold.inner_scores
                ],
            }
            for fold in result.folds
        ],
    }


def _bootstrap_delta(folds: Sequence[Mapping[str, object]]) -> dict[str, object]:
    delta = np.asarray([float(fold["delta_mse"]) for fold in folds], dtype=float)
    if len(delta) != len(FROZEN_POPULATION_IDS):
        raise ValueError("Thalassia bootstrap requires exactly 17 outer population folds")
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    indices = rng.integers(0, len(delta), size=(BOOTSTRAP_RESAMPLES, len(delta)))
    means = np.mean(delta[indices], axis=1)
    lower, upper = np.quantile(means, [0.025, 0.975])
    return {
        "seed": BOOTSTRAP_SEED,
        "resamples": BOOTSTRAP_RESAMPLES,
        "mean_delta_mse": float(np.mean(delta)),
        "median_delta_mse": float(np.median(delta)),
        "fraction_negative": float(np.mean(delta < 0.0)),
        "percentile_95": [float(lower), float(upper)],
    }


def _all_complete_ramet_response(parsed) -> tuple[list[dict[str, object]], dict[str, object]]:
    populations: dict[str, dict[str, list[tuple[int, int]]]] = {}
    complete_counts: dict[str, int] = {}
    for population_id in FROZEN_POPULATION_IDS:
        records = [
            sample for sample in parsed.samples
            if sample.population_id == population_id and all(genotype is not None for genotype in sample.genotypes)
        ]
        complete_counts[population_id] = len(records)
        populations[population_id] = {
            locus: [record.genotypes[index] for record in records]  # type: ignore[list-item]
            for index, locus in enumerate(parsed.locus_order)
        }
    pairwise = all_pairwise_theta(
        populations,
        population_order=FROZEN_POPULATION_IDS,
        locus_order=parsed.locus_order,
    )
    rows = [
        {
            "population_a": result.population_a,
            "population_b": result.population_b,
            "fst_theta": float(result.theta),
            "n_usable_loci": result.n_usable_loci,
        }
        for result in pairwise
    ]
    return rows, {
        "complete_ramet_counts": complete_counts,
        "n_pairs": len(rows),
        "min_theta": float(min(row["fst_theta"] for row in rows)),
        "max_theta": float(max(row["fst_theta"] for row in rows)),
        "promotion_eligible": False,
    }


def run(raw_path: Path, primary_csv: Path, result_json: Path, sensitivity_csv: Path) -> dict[str, object]:
    frozen = _verify_frozen_inputs(raw_path)
    parsed = parse_genalex_workbook(raw_path)

    try:
        primary_rows, primary_summary = build_pairwise_response(parsed)
    except GenAlExSchemaError as exc:
        message = str(exc)
        status = (
            "non_estimable_linearized_fst_domain"
            if "non_estimable_linearized_fst_domain" in message
            else "non_estimable_insufficient_clone_corrected_genets"
            if "fewer than two complete unique MLGs" in message
            else "non_estimable_microsatellite_response"
        )
        result: dict[str, object] = {
            "status": status,
            "promotion_go": False,
            "reason": message,
            "raw_sha256": RAW_SHA256,
            "stage2_fingerprint": EXPECTED_STAGE2_FINGERPRINT,
            "schema_fingerprint": EXPECTED_SCHEMA_FINGERPRINT,
            "prefst_fingerprint": frozen["prefst"]["fingerprint"],
            "genetic_response_attempted": True,
            "nested_validation_run": False,
            "claim_boundary": "Primary response was non-estimable under the frozen pre-FST contract; no rescue was attempted.",
        }
        result["fingerprint"] = _canonical_sha256(result)
        result_json.parent.mkdir(parents=True, exist_ok=True)
        result_json.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
        return result

    write_response_csv(primary_rows, primary_csv)
    theta = _response_matrix(primary_rows, "fst_theta")
    ids, references, eog, disconnected = _load_predictor_matrices()
    nested = evaluate_nested_genetic_reference_selection(
        ids,
        theta,
        references,
        eog,
        disconnected,
        config=GeneticValidationConfig(response_transform="linearized_fst", ridge_penalty=RIDGE_PENALTY),
    )
    nested_dict = _nested_to_dict(nested)
    fixed_geo = _fixed_geographic_outer(theta, references["geographic"])
    bootstrap = _bootstrap_delta(nested_dict["folds"])

    condition1 = len(primary_rows) == 136 and set(primary_summary["population_order"]) == set(FROZEN_POPULATION_IDS)
    condition2 = float(nested.baseline_pooled_mse) <= float(fixed_geo["pooled_mse"])
    condition3 = float(bootstrap["mean_delta_mse"]) < 0.0
    condition4 = float(bootstrap["percentile_95"][1]) < 0.0
    promotion_go = bool(condition1 and condition2 and condition3 and condition4)
    if not condition1:
        status = "non_estimable_population_or_pair_alignment"
    elif not condition2:
        status = "indeterminate_selector_reference_failure"
    elif condition3 and condition4:
        status = "empirical_added_information_go"
    else:
        status = "no_empirical_added_information"

    sensitivity_rows, sensitivity_summary = _all_complete_ramet_response(parsed)
    sensitivity_csv.parent.mkdir(parents=True, exist_ok=True)
    with sensitivity_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["population_a", "population_b", "fst_theta", "n_usable_loci"])
        writer.writeheader()
        writer.writerows(sensitivity_rows)

    result = {
        "status": status,
        "promotion_go": promotion_go,
        "raw_sha256": RAW_SHA256,
        "stage2_fingerprint": EXPECTED_STAGE2_FINGERPRINT,
        "schema_fingerprint": EXPECTED_SCHEMA_FINGERPRINT,
        "prefst_fingerprint": frozen["prefst"]["fingerprint"],
        "primary_response": primary_summary,
        "primary_response_csv_sha256": _sha256(primary_csv),
        "nested": nested_dict,
        "fixed_geographic_outer": fixed_geo,
        "bootstrap": bootstrap,
        "promotion_checks": {
            "all_17_populations_136_pairs": condition1,
            "nested_selected_baseline_pooled_mse_lte_geographic": condition2,
            "mean_population_delta_mse_lt_zero": condition3,
            "bootstrap_upper_95_lt_zero": condition4,
        },
        "all_complete_ramet_sensitivity": {
            **sensitivity_summary,
            "response_csv_sha256": _sha256(sensitivity_csv),
            "used_for_promotion": False,
        },
        "claim_boundary": (
            "Independent clone-corrected symmetric 16-locus microsatellite validation. "
            "EOG never entered conventional-reference selection; all-ramet sensitivity is non-promotional; "
            "symmetric FST does not validate directionality."
        ),
    }
    result["fingerprint"] = _canonical_sha256(result)
    result_json.parent.mkdir(parents=True, exist_ok=True)
    result_json.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--primary-response", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--ramet-sensitivity", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.input, args.primary_response, args.result, args.ramet_sensitivity)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
