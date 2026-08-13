"""Thin frozen-format wrapper for the SW Finland one-time scorer.

Committed before the Finland ``outcome`` is accessed by EOG v2.  It verifies that the raw
CSV header/delimiter is identical to the response-free format manifest, then delegates all
scientific scoring to ``benchmarks.finland_colonization_score`` unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from benchmarks.finland_csv_format_adapter import (
    detect_csv_format,
    fixed_dict_reader_delimiter,
)
from benchmarks.finland_colonization_score import score_finland


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def score_with_frozen_format(
    raw_path: str | Path,
    bundle_path: str | Path,
    manifest_path: str | Path,
    format_manifest_path: str | Path,
) -> dict[str, object]:
    raw = Path(raw_path)
    frozen_format = json.loads(Path(format_manifest_path).read_text(encoding="utf-8"))
    if frozen_format.get("schema") != "eog_v2_finland_csv_format_v1":
        raise ValueError("unsupported Finland frozen CSV format manifest")
    if frozen_format.get("outcome_values_accessed") is not False:
        raise ValueError("Finland CSV format manifest is not response-free")
    raw_sha = _sha256(raw)
    if frozen_format.get("raw_sha256") != raw_sha:
        raise ValueError("Finland raw SHA-256 differs from response-free format freeze")

    observed = detect_csv_format(raw)
    for key in ("delimiter", "delimiter_codepoint", "n_fields", "field_names", "header_sha256"):
        if observed.get(key) != frozen_format.get(key):
            raise ValueError(f"Finland CSV format drift after response-free freeze: {key}")

    with fixed_dict_reader_delimiter(str(frozen_format["delimiter"])):
        return score_finland(raw, bundle_path, manifest_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--format-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = score_with_frozen_format(
        args.input,
        args.bundle,
        args.manifest,
        args.format_manifest,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
