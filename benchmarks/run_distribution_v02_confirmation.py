"""Prospectively frozen independent synthetic confirmation for EOG v0.2.

The scientific contract itself remains immutable with ``execution_authorized=false``.
A separate authorization file may later enable the first confirmation execution only
when it hard-matches the frozen contract Git-blob SHA. ``--validate-only`` checks seed
separation, model identity, source Git-blob hashes, and promotion-gate completeness
without generating any confirmation labels or fitted outcomes.

Once a matching authorization is explicitly changed to true, the runner executes
exactly the frozen 12-seed x 6-regime design with the fixed alpha=0.125 structural
ensemble. No model family, alpha, generator, comparator, or gate is selected from
confirmation outcomes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from eog.distribution_ensemble import (
    EOGStructuralEnsembleConfig,
    fit_eog_structural_ensemble,
)
from benchmarks.distribution_model_noisy_regimes import (
    DEVELOPMENT_SEEDS,
    REGIMES,
    _auc,
    _brier,
    _fit_comparator_predictions,
    build_noisy_landscape,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "benchmarks" / "distribution_v02_confirmation_contract.json"
DEFAULT_AUTHORIZATION = (
    ROOT / "benchmarks" / "distribution_v02_confirmation_authorization.json"
)


def _log_loss(labels: np.ndarray, scores: np.ndarray) -> float:
    labels = np.asarray(labels, dtype=float)
    scores = np.clip(np.asarray(scores, dtype=float), 1e-12, 1.0 - 1e-12)
    return float(
        np.mean(-(labels * np.log(scores) + (1.0 - labels) * np.log1p(-scores)))
    )


def _metrics(labels: np.ndarray, scores: np.ndarray) -> dict[str, float]:
    return {
        "auc": _auc(labels, scores),
        "brier": _brier(labels, scores),
        "log_loss": _log_loss(labels, scores),
    }


def _git_blob_sha(path: Path) -> str:
    payload = path.read_bytes()
    header = f"blob {len(payload)}\0".encode()
    return hashlib.sha1(header + payload).hexdigest()


def load_contract(path: Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if payload.get("schema_version") != "eog_distribution_v02_confirmation_contract_v1":
        raise ValueError("unexpected v0.2 confirmation contract schema")
    return payload


def load_authorization(path: Path = DEFAULT_AUTHORIZATION) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if payload.get("schema_version") != "eog_distribution_v02_confirmation_authorization_v1":
        raise ValueError("unexpected v0.2 confirmation authorization schema")
    return payload


def validate_contract(contract: dict[str, Any]) -> dict[str, Any]:
    development = tuple(int(value) for value in contract["development_seeds_excluded"])
    confirmation = tuple(int(value) for value in contract["confirmation_seeds"])
    regimes = tuple(str(value) for value in contract["regimes"])
    if development != tuple(DEVELOPMENT_SEEDS):
        raise ValueError("contract development-seed exclusion does not match source")
    if set(development).intersection(confirmation):
        raise ValueError("development and confirmation seeds overlap")
    if len(confirmation) != len(set(confirmation)) or len(confirmation) < 8:
        raise ValueError("confirmation seeds must be unique with at least eight seeds")
    if regimes != tuple(REGIMES):
        raise ValueError("confirmation regime order does not match frozen generator")
    if int(contract["n_modules_per_seed"]) != 24:
        raise ValueError("confirmation n_modules_per_seed must remain 24")
    candidate = contract["candidate_model"]
    if float(candidate["stack_weight"]) != 0.125:
        raise ValueError("confirmation stack_weight must remain 0.125")
    if candidate["formula"] != "D = 0.875 * D_probability_gate + 0.125 * D_cross_fitted_stack":
        raise ValueError("confirmation ensemble formula drifted")
    if contract.get("execution_authorized") is not False:
        raise ValueError(
            "scientific confirmation contract must remain immutable with execution_authorized=false"
        )

    gate = contract["promotion_gates"]
    required_gate_keys = {
        "null_regime_maximum_mean_log_loss_harm_vs_environmental",
        "maximum_single_seed_log_loss_harm_vs_environmental",
        "each_structural_regime_requires_positive_mean_log_loss_gain_vs_environmental",
        "each_structural_regime_requires_positive_mean_log_loss_gain_vs_single_path",
    }
    if set(gate) != required_gate_keys:
        raise ValueError("confirmation promotion_gates are incomplete or contain drift")
    if float(gate["null_regime_maximum_mean_log_loss_harm_vs_environmental"]) != 0.01:
        raise ValueError("null mean log-loss noninferiority margin drifted")
    if float(gate["maximum_single_seed_log_loss_harm_vs_environmental"]) != 0.05:
        raise ValueError("single-seed harm cap drifted")
    if gate["each_structural_regime_requires_positive_mean_log_loss_gain_vs_environmental"] is not True:
        raise ValueError("structural environmental-gain gate must remain true")
    if gate["each_structural_regime_requires_positive_mean_log_loss_gain_vs_single_path"] is not True:
        raise ValueError("structural single-path-gain gate must remain true")

    expected_blobs = contract["frozen_source_blobs"]
    blob_checks = {}
    for name, declaration in sorted(expected_blobs.items()):
        path = ROOT / declaration["path"]
        observed = _git_blob_sha(path)
        expected = declaration["git_blob_sha"]
        blob_checks[name] = {
            "path": declaration["path"],
            "expected": expected,
            "observed": observed,
            "matches": observed == expected,
        }
        if observed != expected:
            raise ValueError(f"frozen source blob mismatch for {name}: {path}")

    return {
        "schema": "eog_distribution_v02_confirmation_validation_v1",
        "scientific_contract_execution_authorized": bool(contract["execution_authorized"]),
        "development_confirmation_seed_overlap": 0,
        "n_confirmation_seeds": len(confirmation),
        "n_regimes": len(regimes),
        "n_modules_per_seed": int(contract["n_modules_per_seed"]),
        "stack_weight": float(candidate["stack_weight"]),
        "blob_checks": blob_checks,
        "promotion_gates": gate,
        "valid": True,
    }


def validate_authorization(
    contract_path: Path,
    authorization: dict[str, Any],
) -> dict[str, Any]:
    observed_contract_blob = _git_blob_sha(Path(contract_path))
    expected_contract_blob = str(authorization["expected_contract_git_blob_sha"])
    matches = observed_contract_blob == expected_contract_blob
    if not matches:
        raise ValueError("confirmation authorization does not match frozen contract Git blob")
    return {
        "schema": "eog_distribution_v02_authorization_validation_v1",
        "execution_authorized": bool(authorization["execution_authorized"]),
        "expected_contract_git_blob_sha": expected_contract_blob,
        "observed_contract_git_blob_sha": observed_contract_blob,
        "contract_matches": matches,
        "valid": True,
    }


def run_confirmation(
    contract: dict[str, Any],
    authorization: dict[str, Any],
    *,
    contract_path: Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    validation = validate_contract(contract)
    authorization_validation = validate_authorization(contract_path, authorization)
    if not authorization_validation["execution_authorized"]:
        raise RuntimeError(
            "v0.2 confirmation execution is not authorized; validate-only mode is permitted"
        )

    seeds = tuple(int(value) for value in contract["confirmation_seeds"])
    n_modules = int(contract["n_modules_per_seed"])
    alpha = float(contract["candidate_model"]["stack_weight"])
    per_regime: dict[str, list[dict[str, Any]]] = {regime: [] for regime in REGIMES}
    integrity = {
        "contract_validated": validation["valid"],
        "authorization_validated": authorization_validation["valid"],
        "authorization_contract_match": authorization_validation["contract_matches"],
        "development_confirmation_seed_overlap_zero": set(DEVELOPMENT_SEEDS).isdisjoint(seeds),
        "all_target_labels_held_out": True,
        "all_probability_models_cross_fitted": True,
        "all_stack_models_cross_fitted": True,
        "all_predictions_finite": True,
    }

    for regime in REGIMES:
        for seed in seeds:
            bundle = build_noisy_landscape(regime, seed, n_modules=n_modules)
            ensemble = fit_eog_structural_ensemble(
                bundle.nodes,
                bundle.observed_ids,
                bundle.observed_response,
                EOGStructuralEnsembleConfig(
                    base_config=bundle.config,
                    stack_weight=alpha,
                    stacked_fusion_l2_penalty=1.0,
                ),
                barriers=bundle.barriers,
                gate_fold_ids=bundle.gate_folds,
                reference_provenance=f"v0.2 independent confirmation {regime} seed {seed}",
            )
            labels = np.asarray(bundle.target_response, dtype=int)
            ensemble_prediction = ensemble.predict(bundle.target_ids)
            comparator = _fit_comparator_predictions(bundle, ensemble.probability_model)
            scores = {
                "environmental": np.asarray(
                    ensemble_prediction.environmental_support, dtype=float
                ),
                "nearest_source": np.asarray(
                    comparator["environmental_plus_nearest_source"], dtype=float
                ),
                "single_path": np.asarray(
                    comparator["environmental_plus_single_path"], dtype=float
                ),
                "eog_ensemble": np.asarray(
                    ensemble_prediction.distribution_support, dtype=float
                ),
            }
            integrity["all_target_labels_held_out"] &= set(bundle.target_ids).isdisjoint(
                bundle.observed_ids
            )
            integrity["all_probability_models_cross_fitted"] &= bool(
                ensemble.probability_model.structural_gate_cross_fitted
            )
            integrity["all_stack_models_cross_fitted"] &= bool(
                ensemble.stacked_model.gate_fold_ids
            )
            integrity["all_predictions_finite"] &= all(
                np.isfinite(values).all() for values in scores.values()
            )
            per_regime[regime].append(
                {
                    "seed": seed,
                    "n_positive_targets": int(np.sum(labels == 1)),
                    "n_negative_targets": int(np.sum(labels == 0)),
                    "metrics": {
                        name: _metrics(labels, values) for name, values in scores.items()
                    },
                    "ensemble_fingerprint": ensemble.fingerprint,
                }
            )

    summary = {}
    maximum_seed_harm = -float("inf")
    for regime, rows in per_regime.items():
        mean = {}
        for method in ("environmental", "nearest_source", "single_path", "eog_ensemble"):
            mean[method] = {
                metric: float(
                    np.mean([row["metrics"][method][metric] for row in rows])
                )
                for metric in ("auc", "brier", "log_loss")
            }
        seed_harms = [
            row["metrics"]["eog_ensemble"]["log_loss"]
            - row["metrics"]["environmental"]["log_loss"]
            for row in rows
        ]
        maximum_seed_harm = max(maximum_seed_harm, max(seed_harms))
        summary[regime] = {
            "mean": mean,
            "eog_minus_environmental_mean_log_loss": mean["eog_ensemble"]["log_loss"]
            - mean["environmental"]["log_loss"],
            "eog_minus_single_path_mean_log_loss": mean["eog_ensemble"]["log_loss"]
            - mean["single_path"]["log_loss"],
            "eog_minus_nearest_source_mean_log_loss": mean["eog_ensemble"]["log_loss"]
            - mean["nearest_source"]["log_loss"],
            "worst_seed_log_loss_harm_vs_environmental": float(max(seed_harms)),
        }

    gates = contract["promotion_gates"]
    null_regimes = tuple(contract["null_regimes"])
    structural_regimes = tuple(contract["structural_regimes"])
    gate_results = {
        "integrity": bool(all(integrity.values())),
        "null_mean_log_loss_noninferiority": all(
            summary[regime]["eog_minus_environmental_mean_log_loss"]
            <= float(gates["null_regime_maximum_mean_log_loss_harm_vs_environmental"])
            for regime in null_regimes
        ),
        "single_seed_harm_cap": maximum_seed_harm
        <= float(gates["maximum_single_seed_log_loss_harm_vs_environmental"]),
        "structural_mean_log_loss_gain_vs_environmental": all(
            summary[regime]["eog_minus_environmental_mean_log_loss"] < 0.0
            for regime in structural_regimes
        ),
        "structural_mean_log_loss_gain_vs_single_path": all(
            summary[regime]["eog_minus_single_path_mean_log_loss"] < 0.0
            for regime in structural_regimes
        ),
    }
    promotion_pass = bool(all(gate_results.values()))
    result = {
        "schema": "eog_distribution_v02_independent_confirmation_v1",
        "status": "first_authorized_independent_confirmation",
        "candidate_formula": contract["candidate_model"]["formula"],
        "stack_weight": alpha,
        "confirmation_seeds": list(seeds),
        "n_modules_per_seed": n_modules,
        "regimes": list(REGIMES),
        "integrity_checks": integrity,
        "summary": summary,
        "gate_results": gate_results,
        "promotion_pass": promotion_pass,
        "maximum_seed_log_loss_harm_vs_environmental": float(maximum_seed_harm),
        "per_regime": per_regime,
        "scientific_boundary": contract["scientific_boundary"],
    }
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    result["result_fingerprint"] = hashlib.sha256(canonical).hexdigest()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--authorization", type=Path, default=DEFAULT_AUTHORIZATION)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    contract = load_contract(args.contract)
    if args.validate_only:
        payload = {
            "contract": validate_contract(contract),
        }
        if args.authorization.exists():
            payload["authorization"] = validate_authorization(
                args.contract, load_authorization(args.authorization)
            )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    authorization = load_authorization(args.authorization)
    result = run_confirmation(
        contract,
        authorization,
        contract_path=args.contract,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
