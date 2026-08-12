"""Score the frozen SW Finland EOG v2 colonization benchmark exactly once.

This is the first stage that is allowed to read the released ``outcome`` values. It
requires a previously prepared response-free feature bundle and rejects any raw-file,
contract, manifest, row-key or predictor-array drift before fitting a model.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from eog.v2_empirical_occurrence_validation import (
    _fit_ridge_logistic,
    _predict,
)

from benchmarks.finland_colonization_prepare import (
    BOOTSTRAP_REPLICATES,
    BOOTSTRAP_SEED,
    _array_sha256,
    _sha256_file,
)

EXPECTED_SCHEMA = "eog_v2_finland_colonization_response_free_bundle_v1"
RESULT_SCHEMA = "eog_v2_finland_colonization_empirical_result_v1"
PREOUTCOME_CONTRACT = Path("docs/eog_v2_finland_colonization_preoutcome_contract.md")
INFERENCE_FREEZE = Path("docs/eog_v2_finland_colonization_inference_freeze.md")


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _log_loss_rows(response: np.ndarray, probability: np.ndarray) -> np.ndarray:
    y = np.asarray(response, dtype=float)
    p = np.clip(np.asarray(probability, dtype=float), 1e-9, 1.0 - 1e-9)
    return -(y * np.log(p) + (1.0 - y) * np.log(1.0 - p))


def _brier_rows(response: np.ndarray, probability: np.ndarray) -> np.ndarray:
    y = np.asarray(response, dtype=float)
    p = np.asarray(probability, dtype=float)
    return np.square(y - p)


def _verify_manifest_and_bundle(
    raw_path: Path,
    bundle_path: Path,
    manifest_path: Path,
) -> tuple[dict[str, object], dict[str, np.ndarray]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != EXPECTED_SCHEMA:
        raise ValueError("unsupported Finland feature-bundle manifest schema")
    if manifest.get("outcome_values_accessed") is not False:
        raise ValueError("Finland feature manifest is not response-free")
    if _sha256_file(raw_path) != manifest.get("raw_sha256"):
        raise ValueError("Finland raw CSV SHA-256 does not match frozen manifest")

    observed_fingerprint = str(manifest.get("feature_bundle_fingerprint", ""))
    fingerprint_payload = dict(manifest)
    fingerprint_payload.pop("feature_bundle_fingerprint", None)
    expected_fingerprint = _canonical_sha256(fingerprint_payload)
    if observed_fingerprint != expected_fingerprint:
        raise ValueError("Finland feature-bundle manifest fingerprint mismatch")

    if not PREOUTCOME_CONTRACT.exists() or not INFERENCE_FREEZE.exists():
        raise ValueError("Finland frozen contract files are unavailable")
    current_contract = _sha256_file(PREOUTCOME_CONTRACT)
    if manifest.get("contract_sha256") != current_contract:
        raise ValueError("Finland pre-outcome contract changed after feature freeze")
    current_inference = _sha256_file(INFERENCE_FREEZE)
    if manifest.get("inference_freeze_sha256") != current_inference:
        raise ValueError("Finland inference freeze changed after feature freeze")
    if int(manifest.get("bootstrap_seed", -1)) != BOOTSTRAP_SEED:
        raise ValueError("Finland frozen bootstrap seed drifted")
    if int(manifest.get("bootstrap_replicates", -1)) != BOOTSTRAP_REPLICATES:
        raise ValueError("Finland frozen bootstrap replicate count drifted")

    with np.load(bundle_path, allow_pickle=False) as loaded:
        arrays = {name: np.asarray(loaded[name]) for name in loaded.files}
    expected_arrays = set(manifest["array_fingerprints"])
    if set(arrays) != expected_arrays:
        raise ValueError("Finland feature bundle array set does not match manifest")
    for name, expected in manifest["array_fingerprints"].items():
        observed = _array_sha256(arrays[name])
        if observed != expected:
            raise ValueError(f"Finland frozen predictor array fingerprint mismatch: {name}")

    required = {
        "r0", "r1", "r2", "dynamic", "dynamic_geo", "row_species", "row_island",
        "row_fold", "complete", "analysis_mask", "species_complete_counts",
        "species_fold_counts", "species_response_free_eligible",
    }
    if not required.issubset(arrays):
        raise ValueError("Finland feature bundle is incomplete")
    return manifest, arrays


def _read_outcomes(
    raw_path: Path,
    manifest: dict[str, object],
    arrays: dict[str, np.ndarray],
) -> np.ndarray:
    species_ids = tuple(str(value) for value in manifest["sourceful_species_ids"])
    island_ids = tuple(str(value) for value in manifest["island_ids"])
    species_index = {value: index for index, value in enumerate(species_ids)}
    island_index = {value: index for index, value in enumerate(island_ids)}

    outcome_by_key: dict[tuple[int, int], float] = {}
    with raw_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not {"spp.name", "holmkod", "outcome"}.issubset(reader.fieldnames):
            raise ValueError("Finland raw CSV lacks species/island/outcome columns")
        for row in reader:
            species = row["spp.name"].strip()
            if species not in species_index:
                continue
            island = row["holmkod"].strip()
            if island not in island_index:
                raise ValueError("Finland outcome row contains an unknown island")
            key = (species_index[species], island_index[island])
            if key in outcome_by_key:
                raise ValueError("Finland raw CSV contains duplicate species-island outcome rows")
            try:
                value = float(row["outcome"])
            except ValueError as exc:
                raise ValueError("Finland outcome must be numeric 0/1") from exc
            if value not in (0.0, 1.0):
                raise ValueError("Finland outcome must be exactly 0 or 1")
            outcome_by_key[key] = value

    row_species = arrays["row_species"].astype(int)
    row_island = arrays["row_island"].astype(int)
    row_keys = [
        [species_ids[int(row_species[index])], island_ids[int(row_island[index])]]
        for index in range(len(row_species))
    ]
    observed_key_fingerprint = hashlib.sha256(
        json.dumps(row_keys, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()
    if observed_key_fingerprint != manifest["row_key_fingerprint"]:
        raise ValueError("Finland frozen row-key fingerprint mismatch")

    response = np.full(len(row_species), np.nan, dtype=float)
    for index, key in enumerate(zip(row_species.tolist(), row_island.tolist())):
        if key not in outcome_by_key:
            raise ValueError("Finland raw CSV is missing a frozen species-island outcome row")
        response[index] = outcome_by_key[key]
    return response


def _heldout_predictions(
    matrix: np.ndarray,
    response: np.ndarray,
    folds: np.ndarray,
    mask: np.ndarray,
    *,
    l2_penalty: float,
) -> np.ndarray:
    prediction = np.full(len(response), np.nan, dtype=float)
    unique_folds = sorted(set(folds[mask].astype(int).tolist()))
    if len(unique_folds) != 5:
        raise RuntimeError("Finland primary analysis no longer spans all five frozen folds")
    for fold in unique_folds:
        test = mask & (folds == fold)
        train = mask & (folds != fold)
        if not np.any(test):
            raise RuntimeError(f"Finland frozen fold {fold} has no analysis rows")
        classes = np.unique(response[train])
        if not np.array_equal(classes, np.array([0.0, 1.0])):
            raise RuntimeError(
                f"Finland training data excluding fold {fold} lack both outcome classes; "
                "frozen folds are not redrawn"
            )
        model = _fit_ridge_logistic(matrix[train], response[train], l2_penalty=l2_penalty)
        prediction[test] = _predict(model, matrix[test])
    if not np.isfinite(prediction[mask]).all():
        raise RuntimeError("Finland held-out predictions are incomplete")
    return prediction


def score_finland(
    raw_path: str | Path,
    bundle_path: str | Path,
    manifest_path: str | Path,
) -> dict[str, object]:
    raw_path = Path(raw_path)
    bundle_path = Path(bundle_path)
    manifest_path = Path(manifest_path)
    manifest, arrays = _verify_manifest_and_bundle(raw_path, bundle_path, manifest_path)
    response = _read_outcomes(raw_path, manifest, arrays)

    analysis_mask = arrays["analysis_mask"].astype(bool)
    if int(np.sum(analysis_mask)) != int(manifest["n_rows_analysis_response_free"]):
        raise ValueError("Finland analysis mask count differs from frozen manifest")
    row_species = arrays["row_species"].astype(int)
    folds = arrays["row_fold"].astype(int)
    n_species_response_free = int(manifest["n_species_analysis_response_free"])
    if n_species_response_free < 100:
        raise RuntimeError("Finland frozen response-free eligible species count is below 100")

    matrices = {
        "R0": np.asarray(arrays["r0"], dtype=float),
        "R1": np.asarray(arrays["r1"], dtype=float),
        "R2": np.asarray(arrays["r2"], dtype=float),
        "C": np.column_stack([arrays["r2"], arrays["dynamic"]]),
        "C_geo": np.column_stack([arrays["r2"], arrays["dynamic_geo"]]),
    }
    predictions = {
        name: _heldout_predictions(
            matrix,
            response,
            folds,
            analysis_mask,
            l2_penalty=float(manifest["l2_penalty"]),
        )
        for name, matrix in matrices.items()
    }

    scores: dict[str, dict[str, float | int]] = {}
    row_log_losses = {}
    for name, prediction in predictions.items():
        losses = _log_loss_rows(response[analysis_mask], prediction[analysis_mask])
        brier = _brier_rows(response[analysis_mask], prediction[analysis_mask])
        scores[name] = {
            "log_loss": float(np.mean(losses)),
            "brier": float(np.mean(brier)),
            "n_rows": int(np.sum(analysis_mask)),
        }
        full_losses = np.full(len(response), np.nan, dtype=float)
        full_losses[analysis_mask] = losses
        row_log_losses[name] = full_losses

    species_ids = tuple(str(value) for value in manifest["sourceful_species_ids"])
    eligible_species_flag = arrays["species_response_free_eligible"].astype(bool)
    species_rows = []
    species_deltas = []
    for species_index in np.flatnonzero(eligible_species_flag):
        mask = analysis_mask & (row_species == int(species_index))
        if not np.any(mask):
            raise RuntimeError("response-free eligible Finland species has no analysis rows")
        delta = float(np.mean(row_log_losses["C"][mask] - row_log_losses["R2"][mask]))
        delta_geo = float(np.mean(row_log_losses["C_geo"][mask] - row_log_losses["R2"][mask]))
        species_deltas.append(delta)
        species_rows.append(
            {
                "species": species_ids[int(species_index)],
                "n_rows": int(np.sum(mask)),
                "delta_C_minus_R2_log_loss": delta,
                "delta_C_geo_minus_R2_log_loss": delta_geo,
            }
        )
    deltas = np.asarray(species_deltas, dtype=float)
    if len(deltas) != n_species_response_free:
        raise RuntimeError("Finland species inference count differs from response-free manifest")

    rng = np.random.default_rng(int(manifest["bootstrap_seed"]))
    bootstrap = np.empty(int(manifest["bootstrap_replicates"]), dtype=float)
    for replicate in range(len(bootstrap)):
        sample = rng.integers(0, len(deltas), size=len(deltas))
        bootstrap[replicate] = float(np.mean(deltas[sample]))
    ci_low, ci_high = [float(value) for value in np.quantile(bootstrap, [0.025, 0.975])]

    mean_species_delta = float(np.mean(deltas))
    median_species_delta = float(np.median(deltas))
    favourable_fraction = float(np.mean(deltas < 0.0))
    strong_reference_delta = float(scores["R2"]["log_loss"] - scores["R0"]["log_loss"])
    candidate_delta = float(scores["C"]["log_loss"] - scores["R2"]["log_loss"])
    candidate_geo_delta = float(scores["C_geo"]["log_loss"] - scores["R2"]["log_loss"])

    checks = {
        "minimum_species": {
            "value": len(deltas),
            "relation": ">=",
            "threshold": 100,
            "passed": len(deltas) >= 100,
        },
        "strong_reference_operational": {
            "value_R2_minus_R0_log_loss": strong_reference_delta,
            "relation": "<=",
            "threshold": 0.0,
            "passed": strong_reference_delta <= 0.0,
        },
        "mean_species_candidate_increment": {
            "value_C_minus_R2": mean_species_delta,
            "relation": "<",
            "threshold": 0.0,
            "passed": mean_species_delta < 0.0,
        },
        "bootstrap_upper_bound": {
            "value": ci_high,
            "relation": "<",
            "threshold": 0.0,
            "passed": ci_high < 0.0,
        },
    }
    if not checks["strong_reference_operational"]["passed"]:
        decision = "indeterminate_strong_reference_failure"
    elif all(check["passed"] for check in checks.values()):
        decision = "empirical_added_information_go"
    else:
        decision = "no_empirical_added_information"

    result = {
        "schema": RESULT_SCHEMA,
        "status": "frozen-finland-colonization-heldout-result",
        "raw_sha256": manifest["raw_sha256"],
        "feature_bundle_fingerprint": manifest["feature_bundle_fingerprint"],
        "contract_sha256": manifest["contract_sha256"],
        "inference_freeze_sha256": manifest["inference_freeze_sha256"],
        "admission_response_free_projection_fingerprint": manifest[
            "admission_response_free_projection_fingerprint"
        ],
        "primary_operator_fingerprint": manifest["primary_operator_fingerprint"],
        "geography_operator_fingerprint": manifest["geography_operator_fingerprint"],
        "row_key_fingerprint": manifest["row_key_fingerprint"],
        "n_species": len(deltas),
        "n_rows": int(np.sum(analysis_mask)),
        "model_scores": scores,
        "pooled_R2_minus_R0_log_loss": strong_reference_delta,
        "pooled_C_minus_R2_log_loss": candidate_delta,
        "pooled_C_geo_minus_R2_log_loss": candidate_geo_delta,
        "mean_species_C_minus_R2_log_loss": mean_species_delta,
        "median_species_C_minus_R2_log_loss": median_species_delta,
        "fraction_species_C_favourable": favourable_fraction,
        "species_bootstrap_95_interval": [ci_low, ci_high],
        "bootstrap_seed": int(manifest["bootstrap_seed"]),
        "bootstrap_replicates": int(manifest["bootstrap_replicates"]),
        "species_results": species_rows,
        "decision": decision,
        "checks": checks,
        "claim_boundary": (
            "This is held-out colonization-incidence evidence for the frozen fixed-source "
            "EOG-R graph under the SW Finland contract. It is not colonization-probability "
            "calibration, a historical-route reconstruction, or universal EOG superiority."
        ),
    }
    result["result_fingerprint"] = _canonical_sha256(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = score_finland(args.input, args.bundle, args.manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
