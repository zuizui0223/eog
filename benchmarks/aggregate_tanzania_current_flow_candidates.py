"""Aggregate all outcome-free Tanzania current-flow candidate shards.

Shard manifests retain the stricter run-local floating-point fingerprints used
when each NPZ is written. The cross-run library contract is intentionally
quantized more coarsely because sparse LU implementations can differ by a few
ULPs across otherwise equivalent GitHub runners. Raw arrays remain float64;
only diagnostic SHA inputs and scalar summaries are normalized.
"""
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
from eog.tanzania_current_flow_contract import (
    RESISTANCE_LEVELS,
    enumerate_resistance_combinations,
)

RAYLEIGH_TOLERANCE = 1e-9
SHARD_HASH_DECIMALS = FLOAT_DECIMALS
LIBRARY_FINGERPRINT_DECIMALS = 6
FINGERPRINT_ABSOLUTE_RESOLUTION = 10.0 ** (-LIBRARY_FINGERPRINT_DECIMALS)


def _stable_float(value: float) -> float:
    """Normalize diagnostic scalars for cross-run manifest fingerprints."""
    result = float(np.round(float(value), decimals=LIBRARY_FINGERPRINT_DECIMALS))
    return 0.0 if result == 0.0 else result


def _library_array_sha256(values: np.ndarray) -> str:
    """Hash a float array under the frozen cross-run precision contract."""
    return array_sha256(values, decimals=LIBRARY_FINGERPRINT_DECIMALS)


def _physical_invariant_audit(
    combinations: np.ndarray,
    pairwise: np.ndarray,
    primary: np.ndarray,
    sensitivity: np.ndarray,
) -> dict[str, Any]:
    """Enforce label-free electrical-network invariants on the full grid."""
    if pairwise.shape != (512, 42, 42):
        raise ValueError("pairwise candidate library must have shape 512 x 42 x 42")
    if primary.shape != (512, 42) or sensitivity.shape != (512, 42):
        raise ValueError("isolation candidate libraries must have shape 512 x 42")
    if not all(np.isfinite(values).all() for values in (pairwise, primary, sensitivity)):
        raise ValueError("candidate library contains non-finite values")
    if (
        np.any(pairwise < -RAYLEIGH_TOLERANCE)
        or np.any(primary <= 0.0)
        or np.any(sensitivity <= 0.0)
    ):
        raise ValueError(
            "candidate library contains invalid negative or non-positive values"
        )

    symmetry_error = _stable_float(
        np.max(np.abs(pairwise - np.swapaxes(pairwise, 1, 2)))
    )
    diagonal_error = _stable_float(
        np.max(np.abs(np.diagonal(pairwise, axis1=1, axis2=2)))
    )
    if symmetry_error > RAYLEIGH_TOLERANCE or diagonal_error > RAYLEIGH_TOLERANCE:
        raise ValueError(
            "effective-resistance matrices violate symmetry or zero diagonal"
        )

    rounded_pairwise = np.round(
        pairwise, decimals=LIBRARY_FINGERPRINT_DECIMALS
    ).reshape(512, -1)
    rounded_primary = np.round(
        primary, decimals=LIBRARY_FINGERPRINT_DECIMALS
    )
    unique_pairwise = int(np.unique(rounded_pairwise, axis=0).shape[0])
    unique_primary = int(np.unique(rounded_primary, axis=0).shape[0])
    if unique_pairwise != 512 or unique_primary != 512:
        raise ValueError(
            "the frozen resistance grid produced duplicate candidate quantities"
        )

    levels = tuple(int(value) for value in RESISTANCE_LEVELS)
    lookup = {
        tuple(int(value) for value in row): index
        for index, row in enumerate(combinations)
    }
    if len(lookup) != 512:
        raise ValueError("resistance combinations are not unique")
    off_diagonal = ~np.eye(42, dtype=bool)
    axis_names = ("eucalyptus", "tea", "other_agriculture")
    rayleigh: dict[str, dict[str, Any]] = {}
    for axis, axis_name in enumerate(axis_names):
        comparisons = 0
        violations = 0
        minimum_increment = np.inf
        maximum_increment = -np.inf
        for combination, index in lookup.items():
            level_index = levels.index(combination[axis])
            if level_index == len(levels) - 1:
                continue
            higher = list(combination)
            higher[axis] = levels[level_index + 1]
            higher_index = lookup[tuple(higher)]
            difference = (
                pairwise[higher_index] - pairwise[index]
            )[off_diagonal]
            minimum_increment = min(
                minimum_increment, float(np.min(difference))
            )
            maximum_increment = max(
                maximum_increment, float(np.max(difference))
            )
            violations += int(
                np.any(difference < -RAYLEIGH_TOLERANCE)
            )
            comparisons += 1
        if comparisons != 448 or violations:
            raise ValueError(
                f"Rayleigh monotonicity failed for {axis_name}: "
                f"{violations} violations across {comparisons} comparisons"
            )
        rayleigh[axis_name] = {
            "n_adjacent_level_comparisons": comparisons,
            "n_violations": violations,
            "minimum_offdiagonal_increment": _stable_float(
                minimum_increment
            ),
            "maximum_offdiagonal_increment": _stable_float(
                maximum_increment
            ),
            "tolerance": RAYLEIGH_TOLERANCE,
        }

    all_one_index = lookup[(1, 1, 1)]
    all_one_difference = pairwise - pairwise[all_one_index]
    minimum_from_all_one = _stable_float(
        np.min(all_one_difference[:, off_diagonal])
    )
    if minimum_from_all_one < -RAYLEIGH_TOLERANCE:
        raise ValueError(
            "all-one resistance candidate is not the elementwise minimum"
        )

    return {
        "all_values_finite": True,
        "all_pairwise_values_nonnegative": True,
        "all_isolation_values_positive": True,
        "maximum_symmetry_error": symmetry_error,
        "maximum_diagonal_error": diagonal_error,
        "n_unique_pairwise_candidates": unique_pairwise,
        "n_unique_primary_isolation_candidates": unique_primary,
        "all_one_candidate_elementwise_minimum": True,
        "minimum_difference_from_all_one_candidate": minimum_from_all_one,
        "rayleigh_monotonicity": rayleigh,
    }


def _load_region(
    input_dir: Path, region: str
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    manifests = []
    arrays = []
    for shard in range(N_SHARDS):
        manifest_path = (
            input_dir
            / f"current_flow_{region}_shard_{shard:02d}.json"
        )
        npz_path = (
            input_dir
            / f"current_flow_{region}_shard_{shard:02d}.npz"
        )
        if not manifest_path.exists() or not npz_path.exists():
            raise ValueError(f"missing {region} shard {shard}")
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
        if (
            manifest.get("schema_version") != EXECUTION_SCHEMA_VERSION
            or manifest.get("shard_index") != shard
        ):
            raise ValueError(f"invalid {region} shard manifest {shard}")
        with np.load(npz_path, allow_pickle=False) as data:
            payload = {
                key: np.asarray(data[key]) for key in data.files
            }
        # Verify the exact file produced inside this run. This remains stricter
        # than the tolerance-aware cross-run scientific fingerprint.
        if (
            array_sha256(
                payload["pairwise_resistance"],
                decimals=SHARD_HASH_DECIMALS,
            )
            != manifest["pairwise_resistance_sha256"]
        ):
            raise ValueError(
                f"{region} shard {shard} pairwise fingerprint mismatch"
            )
        manifests.append(manifest)
        arrays.append(payload)

    candidate_indices = np.concatenate(
        [row["candidate_indices"] for row in arrays]
    ).astype(np.int64)
    order = np.argsort(candidate_indices)
    if not np.array_equal(
        candidate_indices[order], np.arange(512, dtype=np.int64)
    ):
        raise ValueError(
            f"{region} shards do not cover candidate indices 0..511 exactly"
        )
    combined = {
        "candidate_indices": candidate_indices[order],
        "combinations": np.concatenate(
            [row["combinations"] for row in arrays], axis=0
        )[order],
        "pairwise_resistance": np.concatenate(
            [row["pairwise_resistance"] for row in arrays], axis=0
        )[order],
        "isolation_primary": np.concatenate(
            [row["isolation_primary"] for row in arrays], axis=0
        )[order],
        "isolation_sensitivity": np.concatenate(
            [row["isolation_sensitivity"] for row in arrays], axis=0
        )[order],
    }
    expected_combinations = np.asarray(
        [
            [
                row[axis]
                for axis in (
                    "eucalyptus",
                    "tea",
                    "other_agriculture",
                )
            ]
            for row in enumerate_resistance_combinations()
        ],
        dtype=np.int64,
    )
    if not np.array_equal(
        combined["combinations"], expected_combinations
    ):
        raise ValueError(f"{region} resistance-grid ordering drift")

    physical_invariants = _physical_invariant_audit(
        combined["combinations"],
        combined["pairwise_resistance"],
        combined["isolation_primary"],
        combined["isolation_sensitivity"],
    )
    summary = {
        "region": region,
        "n_shards": len(manifests),
        "n_candidates": 512,
        "n_focal_patches": int(
            combined["pairwise_resistance"].shape[1]
        ),
        "candidate_indices_sha256": array_sha256(
            combined["candidate_indices"]
        ),
        "combinations_sha256": array_sha256(
            combined["combinations"]
        ),
        "pairwise_resistance_sha256": _library_array_sha256(
            combined["pairwise_resistance"]
        ),
        "isolation_primary_sha256": _library_array_sha256(
            combined["isolation_primary"]
        ),
        "isolation_sensitivity_sha256": _library_array_sha256(
            combined["isolation_sensitivity"]
        ),
        "minimum_pairwise_resistance": _stable_float(
            np.min(combined["pairwise_resistance"])
        ),
        "maximum_pairwise_resistance": _stable_float(
            np.max(combined["pairwise_resistance"])
        ),
        "minimum_primary_isolation": _stable_float(
            np.min(combined["isolation_primary"])
        ),
        "maximum_primary_isolation": _stable_float(
            np.max(combined["isolation_primary"])
        ),
        "physical_invariants": physical_invariants,
    }
    summary["region_fingerprint"] = canonical_sha256(summary)
    return summary, combined


def _expected_projection(
    schema_version: str, library_fingerprint: str, regions: dict[str, Any]
) -> dict[str, Any]:
    keys = (
        "n_candidates",
        "n_focal_patches",
        "candidate_indices_sha256",
        "combinations_sha256",
        "pairwise_resistance_sha256",
        "isolation_primary_sha256",
        "isolation_sensitivity_sha256",
        "region_fingerprint",
    )
    return {
        "schema_version": schema_version,
        "candidate_library_fingerprint": library_fingerprint,
        "regions": {
            region: {key: regions[region][key] for key in keys}
            for region in ("E", "W")
        },
    }


def aggregate(
    input_dir: Path,
    output_dir: Path,
    expected_path: Path | None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    regions = {}
    for region in ("E", "W"):
        summary, arrays = _load_region(input_dir, region)
        regions[region] = summary
        np.savez_compressed(
            output_dir
            / f"tanzania_current_flow_candidates_{region}.npz",
            **arrays,
        )
    manifest = {
        "status": (
            "tanzania_current_flow_candidate_library_generated_"
            "before_species_outcomes"
        ),
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "regions": regions,
        "fingerprint_policy": {
            "raw_array_storage": "float64_unmodified",
            "run_local_shard_hash_decimals": SHARD_HASH_DECIMALS,
            "cross_run_library_hash_decimals": LIBRARY_FINGERPRINT_DECIMALS,
            "cross_run_absolute_resolution": FINGERPRINT_ABSOLUTE_RESOLUTION,
            "scope": "diagnostic fingerprints and scalar summaries only",
        },
        "scientific_boundary": {
            "species_outcomes_inspected": False,
            "current_flow_computed": True,
            "resistance_selected": False,
            "occurrence_model_fitted": False,
            "performance_metric_computed": False,
            "eog_performance_inspected": False,
        },
    }
    manifest["candidate_library_fingerprint"] = canonical_sha256(
        manifest
    )
    projection = _expected_projection(
        manifest["schema_version"],
        manifest["candidate_library_fingerprint"],
        regions,
    )

    verified = False
    if expected_path is not None and expected_path.exists():
        expected = json.loads(
            expected_path.read_text(encoding="utf-8")
        )
        if expected.get("fingerprints_frozen") is True:
            frozen = expected.get("expected_projection")
            if projection != frozen:
                raise ValueError(
                    "Tanzania current-flow candidate library drifted "
                    "from frozen tolerance-aware fingerprints.\nEXPECTED:\n"
                    + json.dumps(frozen, sort_keys=True, indent=2)
                    + "\nACTUAL:\n"
                    + json.dumps(projection, sort_keys=True, indent=2)
                )
            verified = True
    manifest["expected_fingerprints_verified"] = verified
    (output_dir / "candidate_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    suggestion = {
        "status": "tanzania_current_flow_candidate_expected_values",
        "fingerprints_frozen": True,
        "scientific_boundary": (
            "candidate quantities only; frozen before species resistance "
            "selection or predictive scoring"
        ),
        "fingerprint_policy": manifest["fingerprint_policy"],
        "expected_projection": projection,
    }
    (output_dir / "candidate_expected_suggestion.json").write_text(
        json.dumps(suggestion, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            aggregate(
                args.input_dir,
                args.output_dir,
                args.expected,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
