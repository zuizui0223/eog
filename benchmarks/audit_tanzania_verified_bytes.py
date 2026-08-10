"""Verify Tanzania Dryad bytes before any species-level EOG outcome.

This is deliberately a pre-outcome gate. It validates source integrity against
Dryad's frozen manifest and then inspects only structural schema needed to
establish that the non-island benchmark is executable.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

REQUIRED = (
    "Sites.csv",
    "spp_occur.csv",
    "Nodes_E.csv",
    "Nodes_W.csv",
    "raster_east3.tif",
    "raster_west3.tif",
)


def _digest(path: Path, kind: str) -> str:
    name = kind.lower().replace("-", "")
    if name not in hashlib.algorithms_available:
        raise ValueError(f"unsupported digest type in frozen Dryad manifest: {kind}")
    h = hashlib.new(name)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _csv_schema(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        rows = list(reader)
    if not rows:
        raise ValueError(f"empty CSV: {path.name}")
    header = [str(x).strip() for x in rows[0]]
    if not header or any(not x for x in header):
        raise ValueError(f"blank header in {path.name}")
    widths = {len(row) for row in rows[1:] if row}
    if widths and widths != {len(header)}:
        raise ValueError(f"ragged CSV rows in {path.name}: header={len(header)}, row_widths={sorted(widths)}")
    return {
        "headers": header,
        "n_columns": len(header),
        "n_data_rows": sum(bool(row) for row in rows[1:]),
    }


def _tiff_magic(path: Path) -> str:
    magic = path.read_bytes()[:4]
    valid = {b"II*\x00": "little_endian_tiff", b"MM\x00*": "big_endian_tiff"}
    if magic not in valid:
        raise ValueError(f"{path.name} is not a valid classic TIFF header")
    return valid[magic]


def _raster_schema(path: Path) -> dict[str, object]:
    report: dict[str, object] = {"tiff_magic": _tiff_magic(path)}
    try:
        import rasterio  # type: ignore
    except Exception:
        report["rasterio_inspected"] = False
        report["next_gate"] = "install rasterio and rerun before graph construction"
        return report
    with rasterio.open(path) as src:
        report.update({
            "rasterio_inspected": True,
            "width": int(src.width),
            "height": int(src.height),
            "count": int(src.count),
            "crs": str(src.crs) if src.crs else None,
            "bounds": [float(src.bounds.left), float(src.bounds.bottom), float(src.bounds.right), float(src.bounds.top)],
            "transform": [float(x) for x in tuple(src.transform)],
            "nodata": None if src.nodata is None else float(src.nodata),
        })
    if not report["crs"]:
        raise ValueError(f"{path.name} has no CRS; graph/matrix alignment must not proceed")
    return report


def audit(source_dir: Path, manifest_path: Path, output: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = manifest.get("files")
    if not isinstance(rows, list):
        raise ValueError("frozen source manifest has no files list")
    declared = {str(row.get("name")): row for row in rows if isinstance(row, dict)}

    integrity: dict[str, object] = {}
    schemas: dict[str, object] = {}
    for name in REQUIRED:
        row = declared.get(name)
        if row is None:
            raise ValueError(f"{name} missing from frozen Dryad manifest")
        path = source_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"required verified source byte file absent: {path}")
        expected_size = int(row.get("declared_size") or 0)
        expected_digest = str(row.get("declared_digest") or "").lower()
        digest_type = str(row.get("declared_digest_type") or "")
        if path.stat().st_size != expected_size:
            raise ValueError(f"size mismatch for {name}: got {path.stat().st_size}, expected {expected_size}")
        actual_digest = _digest(path, digest_type).lower()
        if actual_digest != expected_digest:
            raise ValueError(f"digest mismatch for {name}: got {actual_digest}, expected {expected_digest}")
        integrity[name] = {
            "size": expected_size,
            "digest_type": digest_type,
            "digest": actual_digest,
            "verified": True,
        }
        if name.endswith(".csv"):
            schemas[name] = _csv_schema(path)
        elif name.endswith(".tif"):
            schemas[name] = _raster_schema(path)

    sites = schemas["Sites.csv"]
    occur = schemas["spp_occur.csv"]
    nodes_e = schemas["Nodes_E.csv"]
    nodes_w = schemas["Nodes_W.csv"]
    if int(sites["n_data_rows"]) <= 0 or int(occur["n_data_rows"]) <= 0:
        raise ValueError("Sites.csv or spp_occur.csv has no data rows")
    if int(nodes_e["n_data_rows"]) <= 0 or int(nodes_w["n_data_rows"]) <= 0:
        raise ValueError("one or both node tables have no data rows")

    rasters_ready = all(bool(schemas[n].get("rasterio_inspected")) for n in ("raster_east3.tif", "raster_west3.tif"))
    report = {
        "status": "verified_bytes_structural_schema_only",
        "doi": manifest.get("doi"),
        "integrity": integrity,
        "schemas": schemas,
        "full_structural_input_gate": "pass" if rasters_ready else "pass_integrity_pending_rasterio_schema",
        "species_outcomes_inspected": False,
        "species_eligibility_computed": False,
        "eog_graph_constructed": False,
        "scientific_boundary": "verified source integrity and structural schema only; no species-level filtering, support fitting, graph scoring, or EOG performance",
        "next_gate": "freeze explicit column semantics/site-node-raster alignment and species eligibility before any EOG outcome",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.source_dir, args.manifest, args.output), indent=2))


if __name__ == "__main__":
    main()
