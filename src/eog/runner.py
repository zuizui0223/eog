"""Audited CSV input validation and frozen comparative-EOG execution."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from .comparative import RobustReference
from .manifest import AnalysisManifest, build_result_bundle, manifest_fingerprint, validate_manifest
from .uncertainty import compare_geometry, reference_fingerprint


@dataclass(frozen=True)
class AuditedInput:
    group_a: np.ndarray
    group_b: np.ndarray
    row_count_a: int
    row_count_b: int
    fingerprint_a: str
    fingerprint_b: str


def _canonical_group_fingerprint(rows: list[tuple[str, tuple[float, ...]]]) -> str:
    payload = [
        {"row_id": row_id, "values": [format(value, ".17g") for value in values]}
        for row_id, values in sorted(rows, key=lambda item: item[0])
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def load_audited_csv(path: str | Path, manifest: AnalysisManifest) -> AuditedInput:
    """Load reserved ``row_id``/``group`` columns and manifest-declared features."""
    validate_manifest(manifest)
    expected = ["row_id", "group", *manifest.feature_names]
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != expected:
            raise ValueError(f"CSV columns must exactly match declared order: {expected}")
        seen: set[str] = set()
        grouped: dict[str, list[tuple[str, tuple[float, ...]]]] = {
            manifest.group_a: [],
            manifest.group_b: [],
        }
        for line_number, row in enumerate(reader, start=2):
            row_id = str(row["row_id"]).strip()
            group = str(row["group"]).strip()
            if not row_id:
                raise ValueError(f"empty row_id at line {line_number}")
            if row_id in seen:
                raise ValueError(f"duplicate row_id: {row_id}")
            seen.add(row_id)
            if group not in grouped:
                raise ValueError(f"unexpected group label: {group}")
            try:
                values = tuple(float(row[name]) for name in manifest.feature_names)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"non-numeric feature at line {line_number}") from exc
            if not np.isfinite(values).all():
                raise ValueError(f"non-finite feature at line {line_number}")
            grouped[group].append((row_id, values))

    if not grouped[manifest.group_a] or not grouped[manifest.group_b]:
        raise ValueError("both declared groups must contain rows")
    array_a = np.asarray([values for _, values in grouped[manifest.group_a]], dtype=float)
    array_b = np.asarray([values for _, values in grouped[manifest.group_b]], dtype=float)
    return AuditedInput(
        group_a=array_a,
        group_b=array_b,
        row_count_a=len(array_a),
        row_count_b=len(array_b),
        fingerprint_a=_canonical_group_fingerprint(grouped[manifest.group_a]),
        fingerprint_b=_canonical_group_fingerprint(grouped[manifest.group_b]),
    )


def run_frozen_analysis(
    manifest: AnalysisManifest,
    reference: RobustReference,
    inputs: AuditedInput,
) -> dict[str, Any]:
    """Execute exactly the manifest primary comparison and return a JSON-ready bundle."""
    validate_manifest(manifest)
    if reference_fingerprint(reference) != manifest.reference_fingerprint:
        raise ValueError("reference fingerprint does not match manifest")
    actual_inputs = (inputs.fingerprint_a, inputs.fingerprint_b)
    if actual_inputs != manifest.input_fingerprints:
        raise ValueError("input fingerprints do not match manifest")
    contrast = compare_geometry(
        inputs.group_a,
        inputs.group_b,
        reference,
        metric=manifest.primary_metric,
        support_class=manifest.support_class,
        n_resamples=manifest.n_resamples,
        resample_fraction=manifest.resample_fraction,
        n_permutations=manifest.n_permutations,
        random_state=manifest.random_seed,
    )
    bundle = build_result_bundle(manifest, contrast)
    return {
        "manifest_fingerprint": manifest_fingerprint(manifest),
        "analysis_id": manifest.analysis_id,
        "row_count_a": inputs.row_count_a,
        "row_count_b": inputs.row_count_b,
        "input_fingerprints": list(actual_inputs),
        "reference_fingerprint": manifest.reference_fingerprint,
        "contrast": asdict(bundle.contrast),
        "report_text": bundle.report_text,
        "software_version": manifest.software_version,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one frozen comparative EOG manifest")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.manifest, encoding="utf-8") as handle:
        manifest = AnalysisManifest.from_dict(json.load(handle))
    with open(args.reference, encoding="utf-8") as handle:
        reference = RobustReference.from_dict(json.load(handle))
    inputs = load_audited_csv(args.input, manifest)
    result = run_frozen_analysis(manifest, reference, inputs)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")


if __name__ == "__main__":
    main()
