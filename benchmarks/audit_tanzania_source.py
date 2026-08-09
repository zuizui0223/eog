"""Audit the frozen public Dryad metadata for the Tanzania benchmark."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_ANALYSIS_INPUTS = {
    "Sites.csv", "spp_occur.csv", "Nodes_E.csv", "Nodes_W.csv",
    "raster_east3.tif", "raster_west3.tif",
}


def audit(manifest_path: Path, output: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = manifest.get("files")
    if not isinstance(files, list):
        raise ValueError("source manifest does not contain a file list")
    by_name = {str(row.get("name")): row for row in files if isinstance(row, dict)}
    missing = sorted(REQUIRED_ANALYSIS_INPUTS - set(by_name))
    if missing:
        raise ValueError(f"required Tanzania analysis inputs absent from Dryad inventory: {missing}")

    inputs: dict[str, object] = {}
    for name in sorted(REQUIRED_ANALYSIS_INPUTS):
        row = by_name[name]
        size = int(row.get("declared_size") or 0)
        digest = str(row.get("declared_digest") or "")
        digest_type = str(row.get("declared_digest_type") or "")
        if size <= 0 or not digest or not digest_type:
            raise ValueError(f"incomplete declared integrity metadata for {name}")
        inputs[name] = {
            "declared_size": size,
            "declared_digest": digest,
            "declared_digest_type": digest_type,
            "mime_type": row.get("mime_type"),
        }

    report = {
        "dataset": "Brodie & Newmark Tanzania forest-fragment benchmark",
        "doi": "10.5061/dryad.p042h0c",
        "published_species_count_reference": 43,
        "required_analysis_inputs": inputs,
        "binary_bytes_verified": False,
        "schema_inspected": False,
        "eligibility_computed": False,
        "next_gate": "Obtain the six required source files in an environment permitted by Dryad, verify every declared size/digest, then freeze table/raster schema before any EOG outcome.",
        "scientific_boundary": "pre-EOG source identity/integrity metadata only; no taxon filtering or EOG performance inspected",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.manifest, args.output), indent=2))


if __name__ == "__main__":
    main()
