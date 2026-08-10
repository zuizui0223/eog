"""Run one deterministic species shard of the Tanzania held-out benchmark."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from eog.tanzania_heldout_benchmark import (
    BENCHMARK_SCHEMA_VERSION,
    canonical_json,
    canonical_jsonl_sha256,
    canonical_sha256,
    run_benchmark_shard,
    validate_design_contract,
)


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"missing CSV header: {path}")
        return [dict(row) for row in reader]


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


def _npz_payload(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as data:
        return {key: np.asarray(data[key]) for key in data.files}


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(canonical_json(dict(row)))
            handle.write("\n")
    return canonical_jsonl_sha256(rows)


def run(
    *,
    source_dir: Path,
    design_contract: Path,
    feature_dir: Path,
    candidate_dir: Path,
    shard_index: int,
    n_shards: int,
    output_dir: Path,
) -> dict[str, Any]:
    if n_shards < 1 or not 0 <= shard_index < n_shards:
        raise ValueError("invalid shard_index/n_shards")
    design = json.loads(design_contract.read_text(encoding="utf-8"))
    if not isinstance(design, dict):
        raise ValueError("design contract must be a JSON object")
    eligible = validate_design_contract(design)
    selected_species = tuple(
        species_id
        for index, species_id in enumerate(eligible)
        if index % n_shards == shard_index
    )
    if not selected_species:
        raise ValueError("species shard is empty")

    feature_rows = _jsonl_rows(feature_dir / "primary_features.jsonl")
    feature_rows.extend(
        _jsonl_rows(feature_dir / "spatial_sensitivity_features.jsonl")
    )
    predictions, group_summaries = run_benchmark_shard(
        sites_rows=_csv_rows(source_dir / "Sites.csv"),
        occurrence_rows=_csv_rows(source_dir / "spp_occur.csv"),
        design=design,
        feature_rows=feature_rows,
        east_payload=_npz_payload(
            candidate_dir / "tanzania_current_flow_candidates_E.npz"
        ),
        west_payload=_npz_payload(
            candidate_dir / "tanzania_current_flow_candidates_W.npz"
        ),
        selected_species=selected_species,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    prediction_path = output_dir / f"heldout_predictions_shard_{shard_index:02d}.jsonl"
    group_path = output_dir / f"heldout_groups_shard_{shard_index:02d}.jsonl"
    prediction_sha = _write_jsonl(prediction_path, predictions)
    group_sha = _write_jsonl(group_path, group_summaries)
    valid_predictions = sum(bool(row["prediction_valid"]) for row in predictions)
    manifest: dict[str, Any] = {
        "status": "tanzania_heldout_species_shard_executed",
        "schema_version": BENCHMARK_SCHEMA_VERSION,
        "shard_index": int(shard_index),
        "n_shards": int(n_shards),
        "selected_species": list(selected_species),
        "selected_species_sha256": canonical_sha256(list(selected_species)),
        "n_selected_species": len(selected_species),
        "n_prediction_rows": len(predictions),
        "n_valid_prediction_rows": valid_predictions,
        "n_invalid_prediction_rows": len(predictions) - valid_predictions,
        "n_group_rows": len(group_summaries),
        "n_valid_groups": sum(bool(row["group_valid"]) for row in group_summaries),
        "n_invalid_groups": sum(not bool(row["group_valid"]) for row in group_summaries),
        "prediction_rows_sha256": prediction_sha,
        "group_rows_sha256": group_sha,
        "design_fingerprint": design["design_fingerprint"],
        "scientific_boundary": {
            "official_species_outcomes_executed": True,
            "heldout_predictions_generated": True,
            "per_observation_scores_computed": True,
            "aggregate_species_inference_computed": False,
            "result_direction_interpreted": False,
        },
    }
    manifest["shard_fingerprint"] = canonical_sha256(manifest)
    (output_dir / f"heldout_manifest_shard_{shard_index:02d}.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--design-contract", type=Path, required=True)
    parser.add_argument("--feature-dir", type=Path, required=True)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--n-shards", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            run(
                source_dir=args.source_dir,
                design_contract=args.design_contract,
                feature_dir=args.feature_dir,
                candidate_dir=args.candidate_dir,
                shard_index=args.shard_index,
                n_shards=args.n_shards,
                output_dir=args.output_dir,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
