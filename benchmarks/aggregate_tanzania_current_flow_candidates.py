"""Aggregate all outcome-free Tanzania current-flow candidate shards."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from eog.tanzania_current_flow_candidates import (
    EXECUTION_SCHEMA_VERSION,
    FLOAT_DECIMALS,
    N_SHARDS,
    array_sha256,
    canonical_sha256,
)
from eog.tanzania_current_flow_contract import enumerate_resistance_combinations


def _load_region(input_dir: Path, region: str) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    manifests = []
    arrays = []
    for shard in range(N_SHARDS):
        manifest_path = input_dir / f"current_flow_{region}_shard_{shard:02d}.json"
        npz_path = input_dir / f"current_flow_{region}_shard_{shard:02d}.npz"
        if not manifest_path.exists() or not npz_path.exists():
            raise ValueError(f"missing {region} shard {shard}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema_version") != EXECUTION_SCHEMA_VERSION or manifest.get("shard_index") != shard:
            raise ValueError(f"invalid {region} shard manifest {shard}")
        with np.load(npz_path, allow_pickle=False) as data:
            payload = {key: np.asarray(data[key]) for key in data.files}
        if array_sha256(payload["pairwise_resistance"], decimals=FLOAT_DECIMALS) != manifest["pairwise_resistance_sha256"]:
            raise ValueError(f"{region} shard {shard} pairwise fingerprint mismatch")
        manifests.append(manifest)
        arrays.append(payload)
    candidate_indices = np.concatenate([row["candidate_indices"] for row in arrays]).astype(np.int64)
    order = np.argsort(candidate_indices)
    if not np.array_equal(candidate_indices[order], np.arange(512, dtype=np.int64)):
        raise ValueError(f"{region} shards do not cover candidate indices 0..511 exactly")
    combined = {
        "candidate_indices": candidate_indices[order],
        "combinations": np.concatenate([row["combinations"] for row in arrays], axis=0)[order],
        "pairwise_resistance": np.concatenate([row["pairwise_resistance"] for row in arrays], axis=0)[order],
        "isolation_primary": np.concatenate([row["isolation_primary"] for row in arrays], axis=0)[order],
        "isolation_sensitivity": np.concatenate([row["isolation_sensitivity"] for row in arrays], axis=0)[order],
    }
    expected_combinations = np.asarray(
        [[row[axis] for axis in ("eucalyptus", "tea", "other_agriculture")] for row in enumerate_resistance_combinations()],
        dtype=np.int64,
    )
    if not np.array_equal(combined["combinations"], expected_combinations):
        raise ValueError(f"{region} resistance-grid ordering drift")
    summary = {
        "region": region,
        "n_shards": len(manifests),
        "n_candidates": 512,
        "n_focal_patches": int(combined["pairwise_resistance"].shape[1]),
        "candidate_indices_sha256": array_sha256(combined["candidate_indices"]),
        "combinations_sha256": array_sha256(combined["combinations"]),
        "pairwise_resistance_sha256": array_sha256(combined["pairwise_resistance"], decimals=FLOAT_DECIMALS),
        "isolation_primary_sha256": array_sha256(combined["isolation_primary"], decimals=FLOAT_DECIMALS),
        "isolation_sensitivity_sha256": array_sha256(combined["isolation_sensitivity"], decimals=FLOAT_DECIMALS),
        "minimum_pairwise_resistance": float(np.min(combined["pairwise_resistance"])),
        "maximum_pairwise_resistance": float(np.max(combined["pairwise_resistance"])),
        "minimum_primary_isolation": float(np.min(combined["isolation_primary"])),
        "maximum_primary_isolation": float(np.max(combined["isolation_primary"])),
    }
    summary["region_fingerprint"] = canonical_sha256(summary)
    return summary, combined


def aggregate(input_dir: Path, output_dir: Path, expected_path: Path | None) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    regions = {}
    for region in ("E", "W"):
        summary, arrays = _load_region(input_dir, region)
        regions[region] = summary
        np.savez_compressed(output_dir / f"tanzania_current_flow_candidates_{region}.npz", **arrays)
    manifest = {
        "status": "tanzania_current_flow_candidate_library_generated_before_species_outcomes",
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "regions": regions,
        "scientific_boundary": {
            "species_outcomes_inspected": False,
            "current_flow_computed": True,
            "resistance_selected": False,
            "occurrence_model_fitted": False,
            "performance_metric_computed": False,
            "eog_performance_inspected": False,
        },
    }
    manifest["candidate_library_fingerprint"] = canonical_sha256(manifest)
    verified = False
    if expected_path is not None and expected_path.exists():
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        if expected.get("fingerprints_frozen") is True:
            projection = {
                "schema_version": manifest["schema_version"],
                "candidate_library_fingerprint": manifest["candidate_library_fingerprint"],
                "regions": {
                    region: {
                        key: regions[region][key]
                        for key in (
                            "n_candidates",
                            "n_focal_patches",
                            "candidate_indices_sha256",
                            "combinations_sha256",
                            "pairwise_resistance_sha256",
                            "isolation_primary_sha256",
                            "isolation_sensitivity_sha256",
                            "region_fingerprint",
                        )
                    }
                    for region in ("E", "W")
                },
            }
            if projection != expected.get("expected_projection"):
                raise ValueError("Tanzania current-flow candidate library drifted from frozen fingerprints")
            verified = True
    manifest["expected_fingerprints_verified"] = verified
    (output_dir / "candidate_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    suggestion = {
        "status": "tanzania_current_flow_candidate_expected_values",
        "fingerprints_frozen": True,
        "scientific_boundary": "candidate quantities only; frozen before species resistance selection or predictive scoring",
        "expected_projection": {
            "schema_version": manifest["schema_version"],
            "candidate_library_fingerprint": manifest["candidate_library_fingerprint"],
            "regions": {
                region: {
                    key: regions[region][key]
                    for key in (
                        "n_candidates",
                        "n_focal_patches",
                        "candidate_indices_sha256",
                        "combinations_sha256",
                        "pairwise_resistance_sha256",
                        "isolation_primary_sha256",
                        "isolation_sensitivity_sha256",
                        "region_fingerprint",
                    )
                }
                for region in ("E", "W")
            },
        },
    }
    (output_dir / "candidate_expected_suggestion.json").write_text(json.dumps(suggestion, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected", type=Path)
    args = parser.parse_args()
    print(json.dumps(aggregate(args.input_dir, args.output_dir, args.expected), indent=2))


if __name__ == "__main__":
    main()
