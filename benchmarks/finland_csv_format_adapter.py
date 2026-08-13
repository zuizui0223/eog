"""Response-free CSV-format adapter for the frozen SW Finland benchmark.

This module only resolves the syntactic delimiter from the CSV header and then runs the
already-frozen admission / feature-preparation functions with that delimiter.  It never
reads the released ``outcome`` values itself and does not alter any scientific variable,
source reconstruction, graph, fold, predictor, or promotion rule.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import csv
import hashlib
import json
from pathlib import Path
from typing import Iterator


DELIMITER_CANDIDATES = (",", ";", "\t", "|")
HEADER_REQUIRED = {
    "outcome",  # existence only; values remain forbidden during response-free preparation
    "spp.name",
    "holmkod",
    "Historical_total_log",
    "Dist_to_historical_log",
}


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def detect_csv_format(path: str | Path) -> dict[str, object]:
    source = Path(path)
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        header = handle.readline()
    if not header:
        raise ValueError("Finland colonization file has no header")

    # Delimiter inference is confined to the first record.  Restrict the candidate set so
    # Sniffer cannot invent a punctuation delimiter from variable names.
    try:
        dialect = csv.Sniffer().sniff(header, delimiters="".join(DELIMITER_CANDIDATES))
        delimiter = dialect.delimiter
    except csv.Error as exc:
        raise ValueError("Finland CSV delimiter is not identifiable from the header") from exc
    if delimiter not in DELIMITER_CANDIDATES:
        raise ValueError(f"unsupported Finland CSV delimiter: {delimiter!r}")

    fields = next(csv.reader([header], delimiter=delimiter))
    fields = [value.strip() for value in fields]
    if len(fields) != len(set(fields)):
        raise ValueError("Finland CSV header contains duplicate field names")
    missing = HEADER_REQUIRED - set(fields)
    if missing:
        raise ValueError(f"Finland CSV header lacks required fields: {sorted(missing)}")

    header_bytes = header.encode("utf-8")
    payload = {
        "schema": "eog_v2_finland_csv_format_v1",
        "delimiter": delimiter,
        "delimiter_codepoint": ord(delimiter),
        "n_fields": len(fields),
        "field_names": fields,
        "header_sha256": hashlib.sha256(header_bytes).hexdigest(),
        "outcome_column_exists": "outcome" in fields,
        "outcome_values_accessed": False,
    }
    payload["fingerprint"] = _canonical_sha256(payload)
    return payload


@contextmanager
def fixed_dict_reader_delimiter(delimiter: str) -> Iterator[None]:
    """Temporarily make stdlib ``csv.DictReader`` use the frozen detected delimiter.

    The two pre-existing Finland response-free modules refer to ``csv.DictReader`` via the
    shared stdlib module.  Replacing only that constructor lets their scientific logic run
    unchanged while making the raw-file syntax explicit and reversible.
    """

    if delimiter not in DELIMITER_CANDIDATES:
        raise ValueError(f"unsupported delimiter: {delimiter!r}")
    original = csv.DictReader

    def reader(handle, *args, **kwargs):
        if "dialect" in kwargs or "delimiter" in kwargs:
            raise ValueError("Finland response-free reader must use the frozen adapter delimiter")
        return original(handle, *args, delimiter=delimiter, **kwargs)

    csv.DictReader = reader  # type: ignore[assignment]
    try:
        yield
    finally:
        csv.DictReader = original  # type: ignore[assignment]


def _load_frozen_pipeline_functions():
    """Resolve the same frozen modules in package or direct-script execution mode."""
    try:
        from benchmarks.finland_colonization_preoutcome_admission import evaluate_admission
        from benchmarks.finland_colonization_prepare import prepare_bundle
    except ModuleNotFoundError as exc:
        # ``python benchmarks/finland_csv_format_adapter.py`` puts the benchmarks directory,
        # not the repository root, on sys.path.  Falling back to sibling-module imports is a
        # pure execution-path fix; the imported source files are identical.
        if exc.name != "benchmarks":
            raise
        from finland_colonization_preoutcome_admission import evaluate_admission
        from finland_colonization_prepare import prepare_bundle
    return evaluate_admission, prepare_bundle


def run_response_free_pipeline(
    input_path: str | Path,
    *,
    admission_path: str | Path,
    bundle_path: str | Path,
    manifest_path: str | Path,
    format_manifest_path: str | Path,
) -> dict[str, object]:
    source = Path(input_path)
    format_manifest = detect_csv_format(source)
    delimiter = str(format_manifest["delimiter"])

    # Only import resolution differs between package and direct-script execution.  Both
    # paths resolve the same frozen response-free scientific functions.
    evaluate_admission, prepare_bundle = _load_frozen_pipeline_functions()

    with fixed_dict_reader_delimiter(delimiter):
        admission = evaluate_admission(source)
        if not admission.get("admitted"):
            raise RuntimeError("Finland response-free scientific admission failed")
        feature_manifest = prepare_bundle(source, bundle_path, manifest_path)

    if admission.get("outcome_values_accessed") is not False:
        raise RuntimeError("Finland admission outcome firewall was not preserved")
    if feature_manifest.get("outcome_values_accessed") is not False:
        raise RuntimeError("Finland feature-preparation outcome firewall was not preserved")

    format_manifest = dict(format_manifest)
    format_manifest.update(
        {
            "raw_sha256": admission.get("raw_sha256"),
            "admission_fingerprint": admission.get("fingerprint"),
            "feature_bundle_fingerprint": feature_manifest.get("feature_bundle_fingerprint"),
            "scientific_code_changed_by_adapter": False,
        }
    )
    format_manifest["fingerprint"] = _canonical_sha256(format_manifest)

    admission_path = Path(admission_path)
    format_manifest_path = Path(format_manifest_path)
    admission_path.parent.mkdir(parents=True, exist_ok=True)
    format_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    admission_path.write_text(
        json.dumps(admission, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    format_manifest_path.write_text(
        json.dumps(format_manifest, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    return {
        "format": format_manifest,
        "admission": admission,
        "feature_manifest": feature_manifest,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--format-manifest", type=Path, required=True)
    args = parser.parse_args()
    result = run_response_free_pipeline(
        args.input,
        admission_path=args.admission,
        bundle_path=args.bundle,
        manifest_path=args.manifest,
        format_manifest_path=args.format_manifest,
    )
    print(
        json.dumps(
            {
                "format_fingerprint": result["format"]["fingerprint"],
                "admission_fingerprint": result["admission"].get("fingerprint"),
                "feature_bundle_fingerprint": result["feature_manifest"].get(
                    "feature_bundle_fingerprint"
                ),
                "outcome_values_accessed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
