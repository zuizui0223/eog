"""Build and freeze Tanzania training-only EOG structural features."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from eog.tanzania_eog_features import (
    canonical_sha256,
    generate_tanzania_eog_features,
    write_feature_artifacts,
)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"missing CSV header: {path}")
        return [dict(row) for row in reader]


def _nonestimable_signature(
    applicability: Sequence[Mapping[str, Any]],
    partition: str,
) -> tuple[list[dict[str, Any]], str]:
    rows = [
        {
            "fold_id": str(row["fold_id"]),
            "species_id": str(row["species_id"]),
            "failure_reason": row["failure_reason"],
            "training_valid_presence_count": int(
                row["training_valid_presence_count"]
            ),
            "training_valid_absence_count": int(
                row["training_valid_absence_count"]
            ),
            "heldout_valid_count": int(row["heldout_valid_count"]),
        }
        for row in applicability
        if row["analysis_partition"] == partition
        and not bool(row["anchor_feature_model_estimable"])
    ]
    rows.sort(key=lambda row: (row["fold_id"], row["species_id"]))
    return rows, canonical_sha256(rows)


def _assert_expected(
    manifest: Mapping[str, Any],
    expected: Mapping[str, Any],
    nonestimable_sha: Mapping[str, str],
) -> None:
    if expected.get("status") != "tanzania_training_only_eog_feature_expected_values":
        raise ValueError("unexpected Tanzania EOG feature expected-contract status")
    for key in (
        "design_fingerprint",
        "eligible_species_sha256",
        "n_feature_rows",
        "n_applicability_rows",
        "feature_rows_sha256",
        "applicability_rows_sha256",
        "heldout_labels_used_in_construction",
        "heldout_labels_exported",
        "occurrence_model_fitted",
        "current_flow_computed",
        "performance_metric_computed",
        "eog_performance_inspected",
    ):
        if manifest.get(key) != expected.get(key):
            raise ValueError(
                f"Tanzania EOG feature drift at {key}: "
                f"got {manifest.get(key)!r}, expected {expected.get(key)!r}"
            )

    actual_partitions = dict(manifest.get("partitions") or {})
    expected_partitions = dict(expected.get("partitions") or {})
    if set(actual_partitions) != set(expected_partitions):
        raise ValueError("Tanzania EOG feature partition set drift")
    for partition in sorted(expected_partitions):
        actual = dict(actual_partitions[partition])
        frozen = dict(expected_partitions[partition])
        for key, value in frozen.items():
            if key == "nonestimable_groups_sha256":
                if nonestimable_sha.get(partition) != value:
                    raise ValueError(
                        f"Tanzania {partition} nonestimable group fingerprint drift"
                    )
            elif actual.get(key) != value:
                raise ValueError(
                    f"Tanzania {partition} feature summary drift at {key}: "
                    f"got {actual.get(key)!r}, expected {value!r}"
                )


def build(
    *,
    source_dir: Path,
    design_contract: Path,
    expected_contract: Path,
    output_dir: Path,
) -> dict[str, Any]:
    design = json.loads(design_contract.read_text(encoding="utf-8"))
    expected = json.loads(expected_contract.read_text(encoding="utf-8"))
    if not isinstance(design, dict) or not isinstance(expected, dict):
        raise ValueError("Tanzania design/expected contracts must be JSON objects")

    records, applicability = generate_tanzania_eog_features(
        sites_rows=_rows(source_dir / "Sites.csv"),
        east_node_rows=_rows(source_dir / "Nodes_E.csv"),
        west_node_rows=_rows(source_dir / "Nodes_W.csv"),
        occurrence_rows=_rows(source_dir / "spp_occur.csv"),
        design=design,
    )
    manifest = write_feature_artifacts(
        output_dir=output_dir,
        records=records,
        applicability=applicability,
        design=design,
    )

    nonestimable_groups: dict[str, list[dict[str, Any]]] = {}
    nonestimable_sha: dict[str, str] = {}
    for partition in ("primary_loso", "spatial_mst_block"):
        rows, digest = _nonestimable_signature(applicability, partition)
        nonestimable_groups[partition] = rows
        nonestimable_sha[partition] = digest
    (output_dir / "nonestimable_groups.json").write_text(
        json.dumps(nonestimable_groups, indent=2) + "\n",
        encoding="utf-8",
    )

    _assert_expected(manifest, expected, nonestimable_sha)
    manifest = dict(manifest)
    manifest["nonestimable_groups_sha256"] = nonestimable_sha
    manifest["expected_contract_verified"] = True
    (output_dir / "feature_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--design-contract", type=Path, required=True)
    parser.add_argument("--expected-contract", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            build(
                source_dir=args.source_dir,
                design_contract=args.design_contract,
                expected_contract=args.expected_contract,
                output_dir=args.output_dir,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
