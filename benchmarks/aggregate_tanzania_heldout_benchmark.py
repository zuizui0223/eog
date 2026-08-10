"""Aggregate Tanzania held-out shards and run the frozen species-level inference."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from eog.tanzania_heldout_benchmark import (
    BENCHMARK_SCHEMA_VERSION,
    canonical_json,
    canonical_jsonl_sha256,
    canonical_sha256,
    summarize_prediction_contrast,
)

EXPECTED_N_SHARDS = 12
EXPECTED_SPECIES = 60
EXPECTED_PREDICTION_ROWS = 3360
EXPECTED_GROUP_ROWS = 2280
RESULT_DECIMALS = 9


def _jsonl_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            value = json.loads(text)
            if not isinstance(value, dict):
                raise ValueError(f"non-object JSONL row at {path}:{line_number}")
            rows.append(value)
    return rows


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(canonical_json(dict(row)))
            handle.write("\n")
    return canonical_jsonl_sha256(rows)


def _stable_float(value: float) -> float:
    result = round(float(value), RESULT_DECIMALS)
    return 0.0 if result == 0.0 else result


def _quantize(value: Any) -> Any:
    if isinstance(value, bool) or value is None or isinstance(value, (str, int)):
        return value
    if isinstance(value, float):
        return _stable_float(value)
    if isinstance(value, list):
        return [_quantize(item) for item in value]
    if isinstance(value, tuple):
        return [_quantize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _quantize(item) for key, item in sorted(value.items())}
    raise TypeError(f"unsupported result value for quantization: {type(value)!r}")


def _cross_run_rows_sha256(rows: Sequence[Mapping[str, Any]]) -> str:
    projected = []
    for raw in rows:
        row = {
            key: value
            for key, value in dict(raw).items()
            if key not in {"row_fingerprint_sha256", "group_fingerprint_sha256"}
        }
        projected.append(_quantize(row))
    return canonical_jsonl_sha256(projected)


def _load_shards(input_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    manifests: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    groups: list[dict[str, Any]] = []
    for shard_index in range(EXPECTED_N_SHARDS):
        manifest_path = input_dir / f"heldout_manifest_shard_{shard_index:02d}.json"
        prediction_path = input_dir / f"heldout_predictions_shard_{shard_index:02d}.jsonl"
        group_path = input_dir / f"heldout_groups_shard_{shard_index:02d}.jsonl"
        if not all(path.exists() for path in (manifest_path, prediction_path, group_path)):
            raise ValueError(f"missing held-out shard {shard_index}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        shard_predictions = _jsonl_rows(prediction_path)
        shard_groups = _jsonl_rows(group_path)
        if manifest.get("schema_version") != BENCHMARK_SCHEMA_VERSION:
            raise ValueError(f"held-out shard {shard_index} schema drift")
        if manifest.get("shard_index") != shard_index or manifest.get("n_shards") != EXPECTED_N_SHARDS:
            raise ValueError(f"held-out shard {shard_index} identity drift")
        if canonical_jsonl_sha256(shard_predictions) != manifest.get("prediction_rows_sha256"):
            raise ValueError(f"held-out shard {shard_index} prediction hash mismatch")
        if canonical_jsonl_sha256(shard_groups) != manifest.get("group_rows_sha256"):
            raise ValueError(f"held-out shard {shard_index} group hash mismatch")
        manifests.append(manifest)
        predictions.extend(shard_predictions)
        groups.extend(shard_groups)
    return manifests, predictions, groups


def _verify_complete_cohort(
    manifests: Sequence[Mapping[str, Any]],
    predictions: Sequence[Mapping[str, Any]],
    groups: Sequence[Mapping[str, Any]],
) -> list[str]:
    species_lists = [list(manifest["selected_species"]) for manifest in manifests]
    flattened = [str(value) for values in species_lists for value in values]
    if len(flattened) != EXPECTED_SPECIES or len(set(flattened)) != EXPECTED_SPECIES:
        raise ValueError("held-out shards do not partition exactly 60 species")
    species = sorted(flattened)
    if len(predictions) != EXPECTED_PREDICTION_ROWS:
        raise ValueError(
            f"expected {EXPECTED_PREDICTION_ROWS} prediction rows, got {len(predictions)}"
        )
    if len(groups) != EXPECTED_GROUP_ROWS:
        raise ValueError(f"expected {EXPECTED_GROUP_ROWS} group rows, got {len(groups)}")
    prediction_identity = {
        (
            str(row["isolation_mode"]),
            str(row["analysis_partition"]),
            str(row["fold_id"]),
            str(row["species_id"]),
            str(row["site_id"]),
        )
        for row in predictions
    }
    group_identity = {
        (
            str(row["isolation_mode"]),
            str(row["analysis_partition"]),
            str(row["fold_id"]),
            str(row["species_id"]),
        )
        for row in groups
    }
    if len(prediction_identity) != len(predictions):
        raise ValueError("duplicate held-out prediction identities")
    if len(group_identity) != len(groups):
        raise ValueError("duplicate held-out group identities")
    prediction_species_counts = Counter(str(row["species_id"]) for row in predictions)
    group_species_counts = Counter(str(row["species_id"]) for row in groups)
    if set(prediction_species_counts) != set(species) or set(prediction_species_counts.values()) != {56}:
        raise ValueError("each species must contribute 56 held-out rows across two modes")
    if set(group_species_counts) != set(species) or set(group_species_counts.values()) != {38}:
        raise ValueError("each species must contribute 38 species-fold groups across two modes")
    return species


def _selection_summary(groups: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    selected = [
        int(row["selected_candidate_index"])
        for row in groups
        if row.get("selected_candidate_index") is not None
    ]
    combinations = [
        canonical_json(row["selected_resistance_combination"])
        for row in groups
        if row.get("selected_resistance_combination") is not None
    ]
    return {
        "n_groups": len(groups),
        "n_valid_groups": sum(bool(row["group_valid"]) for row in groups),
        "n_invalid_groups": sum(not bool(row["group_valid"]) for row in groups),
        "failure_reason_counts": dict(
            sorted(
                Counter(
                    str(row["failure_reason"])
                    for row in groups
                    if not bool(row["group_valid"])
                ).items()
            )
        ),
        "n_groups_with_selected_candidate": len(selected),
        "n_distinct_selected_candidate_indices": len(set(selected)),
        "selected_candidate_index_counts": {
            str(key): value for key, value in sorted(Counter(selected).items())
        },
        "selected_resistance_combination_counts": {
            key: value for key, value in sorted(Counter(combinations).items())
        },
        "selected_candidate_sequence_sha256": canonical_sha256(selected),
    }


def _species_rows(
    summaries: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, summary in sorted(summaries.items()):
        isolation_mode, partition = key.split("::", maxsplit=1)
        log_values = summary["species_mean_log_loss_differences"]
        brier_values = summary["species_mean_brier_differences"]
        if set(log_values) != set(brier_values):
            raise ValueError("log-loss and Brier species sets differ")
        for species_id in sorted(log_values):
            rows.append(
                {
                    "isolation_mode": isolation_mode,
                    "analysis_partition": partition,
                    "species_id": species_id,
                    "mean_log_loss_difference": float(log_values[species_id]),
                    "mean_brier_difference": float(brier_values[species_id]),
                }
            )
    return rows


def _compact_contrast(summary: Mapping[str, Any]) -> dict[str, Any]:
    paired = dict(summary["paired_score_summary"])
    log = dict(summary["log_loss_species_cluster_inference"])
    brier = dict(summary["brier_species_cluster_inference"])
    return _quantize(
        {
            "n_matched": paired["n_matched"],
            "n_invalid_rows": summary["n_invalid_rows"],
            "n_species": log["n_species"],
            "mean_log_loss_reference": paired["mean_log_loss_reference"],
            "mean_log_loss_candidate": paired["mean_log_loss_candidate"],
            "micro_mean_log_loss_difference": paired["mean_log_loss_difference"],
            "macro_mean_species_log_loss_difference": log[
                "macro_mean_species_difference"
            ],
            "log_loss_bootstrap_ci95": [
                log["bootstrap_ci_lower"],
                log["bootstrap_ci_upper"],
            ],
            "log_loss_sign_flip_p_value": log["sign_flip_p_value"],
            "mean_brier_reference": paired["mean_brier_reference"],
            "mean_brier_candidate": paired["mean_brier_candidate"],
            "micro_mean_brier_difference": paired["mean_brier_difference"],
            "macro_mean_species_brier_difference": brier[
                "macro_mean_species_difference"
            ],
            "brier_bootstrap_ci95": [
                brier["bootstrap_ci_lower"],
                brier["bootstrap_ci_upper"],
            ],
            "brier_sign_flip_p_value": brier["sign_flip_p_value"],
            "invalid_reason_counts": summary["invalid_reason_counts"],
        }
    )


def _verify_inputs(
    *,
    expected: Mapping[str, Any],
    design: Mapping[str, Any],
    feature_manifest: Mapping[str, Any],
    candidate_manifest: Mapping[str, Any],
    selection_contract: Mapping[str, Any],
) -> dict[str, Any]:
    actual = {
        "design_fingerprint": design.get("design_fingerprint"),
        "eligible_species_sha256": dict(design.get("source") or {}).get(
            "eligible_species_sha256"
        ),
        "candidate_library_fingerprint": candidate_manifest.get(
            "candidate_library_fingerprint"
        ),
        "eog_feature_rows_sha256": feature_manifest.get("feature_rows_sha256"),
        "eog_applicability_rows_sha256": feature_manifest.get(
            "applicability_rows_sha256"
        ),
        "selection_contract_fingerprint": selection_contract.get(
            "contract_fingerprint"
        ),
    }
    frozen = dict(expected.get("required_inputs") or {})
    if actual != frozen:
        raise ValueError(
            "Tanzania held-out input contract drift.\nEXPECTED:\n"
            + json.dumps(frozen, sort_keys=True, indent=2)
            + "\nACTUAL:\n"
            + json.dumps(actual, sort_keys=True, indent=2)
        )
    return actual


def aggregate(
    *,
    input_dir: Path,
    design_contract: Path,
    feature_manifest_path: Path,
    candidate_manifest_path: Path,
    selection_contract_path: Path,
    expected_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    design = json.loads(design_contract.read_text(encoding="utf-8"))
    feature_manifest = json.loads(feature_manifest_path.read_text(encoding="utf-8"))
    candidate_manifest = json.loads(candidate_manifest_path.read_text(encoding="utf-8"))
    selection_contract = json.loads(
        selection_contract_path.read_text(encoding="utf-8")
    )
    input_fingerprints = _verify_inputs(
        expected=expected,
        design=design,
        feature_manifest=feature_manifest,
        candidate_manifest=candidate_manifest,
        selection_contract=selection_contract,
    )
    manifests, predictions, groups = _load_shards(input_dir)
    species = _verify_complete_cohort(manifests, predictions, groups)
    predictions.sort(
        key=lambda row: (
            str(row["isolation_mode"]),
            str(row["analysis_partition"]),
            str(row["fold_id"]),
            str(row["species_id"]),
            str(row["site_id"]),
        )
    )
    groups.sort(
        key=lambda row: (
            str(row["isolation_mode"]),
            str(row["analysis_partition"]),
            str(row["fold_id"]),
            str(row["species_id"]),
        )
    )

    summaries: dict[str, dict[str, Any]] = {}
    selection: dict[str, dict[str, Any]] = {}
    for isolation_mode in ("primary", "inverse_area_sensitivity"):
        for partition in ("primary_loso", "spatial_mst_block"):
            key = f"{isolation_mode}::{partition}"
            selected_predictions = [
                row
                for row in predictions
                if row["isolation_mode"] == isolation_mode
                and row["analysis_partition"] == partition
            ]
            selected_groups = [
                row
                for row in groups
                if row["isolation_mode"] == isolation_mode
                and row["analysis_partition"] == partition
            ]
            summaries[key] = summarize_prediction_contrast(selected_predictions)
            selection[key] = _selection_summary(selected_groups)

    species_rows = _species_rows(summaries)
    compact = {
        key: _compact_contrast(value) for key, value in sorted(summaries.items())
    }
    projection = {
        "schema_version": BENCHMARK_SCHEMA_VERSION,
        "result_decimals": RESULT_DECIMALS,
        "input_fingerprints": input_fingerprints,
        "n_species": len(species),
        "n_prediction_rows": len(predictions),
        "n_group_rows": len(groups),
        "prediction_rows_cross_run_sha256": _cross_run_rows_sha256(predictions),
        "group_rows_cross_run_sha256": _cross_run_rows_sha256(groups),
        "species_rows_cross_run_sha256": _cross_run_rows_sha256(species_rows),
        "contrasts": compact,
        "selection": _quantize(selection),
    }
    projection["result_fingerprint"] = canonical_sha256(projection)
    results_verified = False
    if expected.get("results_frozen") is True:
        frozen_projection = expected.get("expected_projection")
        if projection != frozen_projection:
            raise ValueError(
                "Tanzania held-out result drift.\nEXPECTED:\n"
                + json.dumps(frozen_projection, sort_keys=True, indent=2)
                + "\nACTUAL:\n"
                + json.dumps(projection, sort_keys=True, indent=2)
            )
        results_verified = True

    output_dir.mkdir(parents=True, exist_ok=True)
    prediction_sha = _write_jsonl(output_dir / "heldout_predictions.jsonl", predictions)
    group_sha = _write_jsonl(output_dir / "heldout_groups.jsonl", groups)
    species_sha = _write_jsonl(output_dir / "heldout_species_results.jsonl", species_rows)
    with (output_dir / "heldout_species_results.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "isolation_mode",
                "analysis_partition",
                "species_id",
                "mean_log_loss_difference",
                "mean_brier_difference",
            ],
        )
        writer.writeheader()
        writer.writerows(species_rows)

    manifest: dict[str, Any] = {
        "status": "tanzania_heldout_current_flow_eog_benchmark_executed",
        "schema_version": BENCHMARK_SCHEMA_VERSION,
        "input_fingerprints": input_fingerprints,
        "n_species": len(species),
        "n_prediction_rows": len(predictions),
        "n_group_rows": len(groups),
        "prediction_rows_sha256": prediction_sha,
        "group_rows_sha256": group_sha,
        "species_rows_sha256": species_sha,
        "cross_run_result_decimals": RESULT_DECIMALS,
        "result_projection": projection,
        "expected_results_verified": results_verified,
        "contrast_summaries": summaries,
        "selection_summaries": selection,
        "scientific_boundary": {
            "official_species_outcomes_executed": True,
            "heldout_predictions_generated": True,
            "paired_log_loss_computed": True,
            "species_cluster_inference_computed": True,
            "primary_result_available_for_interpretation": True,
            "mechanistic_colonization_probability_claimed": False,
        },
    }
    (output_dir / "heldout_result_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    suggestion = {
        **dict(expected),
        "results_frozen": True,
        "scientific_boundary": (
            "held-out result projection frozen after the first execution under "
            "the previously merged input, selection, scoring, and inference contracts"
        ),
        "expected_projection": projection,
    }
    (output_dir / "heldout_expected_suggestion.json").write_text(
        json.dumps(suggestion, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--design-contract", type=Path, required=True)
    parser.add_argument("--feature-manifest", type=Path, required=True)
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--selection-contract", type=Path, required=True)
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = aggregate(
        input_dir=args.input_dir,
        design_contract=args.design_contract,
        feature_manifest_path=args.feature_manifest,
        candidate_manifest_path=args.candidate_manifest,
        selection_contract_path=args.selection_contract,
        expected_path=args.expected,
        output_dir=args.output_dir,
    )
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "result_fingerprint": manifest["result_projection"][
                    "result_fingerprint"
                ],
                "expected_results_verified": manifest[
                    "expected_results_verified"
                ],
                "primary": manifest["result_projection"]["contrasts"][
                    "primary::primary_loso"
                ],
                "spatial_sensitivity": manifest["result_projection"][
                    "contrasts"
                ]["primary::spatial_mst_block"],
                "area_weight_sensitivity": manifest["result_projection"][
                    "contrasts"
                ]["inverse_area_sensitivity::primary_loso"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
