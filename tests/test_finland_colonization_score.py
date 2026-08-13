import csv
import hashlib
import json

import numpy as np
import pytest

from benchmarks.finland_colonization_prepare import _array_sha256, _sha256_file
from benchmarks.finland_colonization_score import (
    INFERENCE_FREEZE,
    PREOUTCOME_CONTRACT,
    _canonical_sha256,
    score_finland,
)


def _write_fixture(tmp_path, *, n_species=100):
    species_ids = [f"sp_{index:03d}" for index in range(n_species)]
    island_ids = [f"island_{index}" for index in range(10)]
    n_rows = n_species * len(island_ids)
    row_species = np.repeat(np.arange(n_species, dtype=np.int32), len(island_ids))
    row_island = np.tile(np.arange(len(island_ids), dtype=np.int32), n_species)
    row_fold = (row_island % 5).astype(np.int16)
    outcome = (row_island % 2).astype(float)

    # R0/R1/R2 contain no information; C has a strong frozen dynamic signal.
    r0 = np.zeros((n_rows, 1), dtype=float)
    r1 = np.zeros((n_rows, 2), dtype=float)
    r2 = np.zeros((n_rows, 3), dtype=float)
    dynamic = np.where(outcome > 0.5, 0.9, 0.1).astype(float)
    dynamic_geo = np.full(n_rows, 0.5, dtype=float)
    complete = np.ones(n_rows, dtype=np.uint8)
    analysis_mask = np.ones(n_rows, dtype=np.uint8)
    species_complete_counts = np.full(n_species, len(island_ids), dtype=np.int32)
    species_fold_counts = np.full(n_species, 5, dtype=np.int16)
    species_eligible = np.ones(n_species, dtype=np.uint8)
    arrays = {
        "r0": r0,
        "r1": r1,
        "r2": r2,
        "dynamic": dynamic,
        "dynamic_geo": dynamic_geo,
        "row_species": row_species,
        "row_island": row_island,
        "row_fold": row_fold,
        "complete": complete,
        "analysis_mask": analysis_mask,
        "species_complete_counts": species_complete_counts,
        "species_fold_counts": species_fold_counts,
        "species_response_free_eligible": species_eligible,
    }

    raw_path = tmp_path / "colonization_select.csv"
    with raw_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["spp.name", "holmkod", "outcome"])
        writer.writeheader()
        for s, i, y in zip(row_species, row_island, outcome):
            writer.writerow(
                {
                    "spp.name": species_ids[int(s)],
                    "holmkod": island_ids[int(i)],
                    "outcome": int(y),
                }
            )

    bundle_path = tmp_path / "features.npz"
    np.savez_compressed(bundle_path, **arrays)
    row_keys = [
        [species_ids[int(row_species[index])], island_ids[int(row_island[index])]]
        for index in range(n_rows)
    ]
    row_key_fingerprint = hashlib.sha256(
        json.dumps(row_keys, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()
    manifest = {
        "schema": "eog_v2_finland_colonization_response_free_bundle_v1",
        "raw_file": raw_path.name,
        "raw_sha256": _sha256_file(raw_path),
        "admission_response_free_projection_fingerprint": "admission" * 8,
        "admission_operator_fingerprint": "operator" * 8,
        "admission_source_fingerprint": "source" * 10 + "abcd",
        "admission_fold_fingerprint": "fold" * 16,
        "contract_path": str(PREOUTCOME_CONTRACT),
        "contract_sha256": _sha256_file(PREOUTCOME_CONTRACT),
        "inference_freeze_path": str(INFERENCE_FREEZE),
        "inference_freeze_sha256": _sha256_file(INFERENCE_FREEZE),
        "n_islands": len(island_ids),
        "n_sourceful_species": n_species,
        "n_zero_source_species": 0,
        "n_rows_sourceful": n_rows,
        "n_rows_analysis_response_free": n_rows,
        "n_species_analysis_response_free": n_species,
        "island_ids": island_ids,
        "sourceful_species_ids": species_ids,
        "r0_columns": ["x"],
        "r1_columns": ["x", "history"],
        "r2_columns": ["x", "history", "network"],
        "candidate_extra": "fixed_source_dynamic_reachability",
        "sensitivity_extra": "geography_only_dynamic_reachability",
        "gabriel_edge_count": 9,
        "geographic_scale": 1.0,
        "environmental_scale": 1.0,
        "primary_operator_fingerprint": "p" * 64,
        "geography_operator_fingerprint": "g" * 64,
        "loss_support": 0.55,
        "max_steps": 5,
        "n_spatial_folds": 5,
        "l2_penalty": 1.0,
        "bootstrap_seed": 20260812,
        "bootstrap_replicates": 10_000,
        "min_complete_rows_per_species": 5,
        "min_folds_per_species": 2,
        "array_fingerprints": {name: _array_sha256(value) for name, value in arrays.items()},
        "row_key_fingerprint": row_key_fingerprint,
        "outcome_values_accessed": False,
    }
    manifest["feature_bundle_fingerprint"] = _canonical_sha256(manifest)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return raw_path, bundle_path, manifest_path


def test_finland_scorer_uses_species_bootstrap_and_strong_reference_gate(tmp_path):
    raw, bundle, manifest = _write_fixture(tmp_path)
    result = score_finland(raw, bundle, manifest)
    assert result["n_species"] == 100
    assert result["n_rows"] == 1000
    assert result["model_scores"]["R2"]["log_loss"] == pytest.approx(
        result["model_scores"]["R0"]["log_loss"]
    )
    assert result["model_scores"]["C"]["log_loss"] < result["model_scores"]["R2"]["log_loss"]
    assert result["mean_species_C_minus_R2_log_loss"] < 0.0
    assert result["species_bootstrap_95_interval"][1] < 0.0
    assert result["decision"] == "empirical_added_information_go"
    assert result["bootstrap_seed"] == 20260812
    assert result["bootstrap_replicates"] == 10_000
    assert len(result["result_fingerprint"]) == 64


def test_finland_scorer_rejects_predictor_tampering_before_outcome_fit(tmp_path):
    raw, bundle, manifest = _write_fixture(tmp_path)
    with np.load(bundle, allow_pickle=False) as loaded:
        arrays = {name: np.asarray(loaded[name]) for name in loaded.files}
    arrays["dynamic"] = arrays["dynamic"].copy()
    arrays["dynamic"][0] += 0.01
    np.savez_compressed(bundle, **arrays)
    with pytest.raises(ValueError, match="predictor array fingerprint mismatch"):
        score_finland(raw, bundle, manifest)


def test_finland_scorer_rejects_manifest_contract_drift(tmp_path):
    raw, bundle, manifest_path = _write_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text())
    manifest["inference_freeze_sha256"] = "0" * 64
    fingerprint_payload = dict(manifest)
    fingerprint_payload.pop("feature_bundle_fingerprint")
    manifest["feature_bundle_fingerprint"] = _canonical_sha256(fingerprint_payload)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="inference freeze changed"):
        score_finland(raw, bundle, manifest_path)
