"""Audit the frozen Tanzania Dryad source without computing EOG outcomes."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def _sha(path: Path) -> str:
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    return h


def _table(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    fields = list(rows[0].keys()) if rows else []
    binary: list[str] = []
    numeric: list[str] = []
    unique: dict[str, int] = {}
    for field in fields:
        values = [str(r.get(field, "")).strip() for r in rows if str(r.get(field, "")).strip() != ""]
        unique[field] = len(set(values))
        if values and set(values) <= {"0", "1", "0.0", "1.0"}:
            binary.append(field)
        try:
            if values:
                for value in values:
                    float(value)
                numeric.append(field)
        except ValueError:
            pass
    return {
        "path": path.name,
        "sha256": _sha(path),
        "n_rows": len(rows),
        "columns": fields,
        "binary_columns": binary,
        "numeric_columns": numeric,
        "unique_counts": unique,
    }


def audit(source_dir: Path, output: Path) -> dict[str, object]:
    raw = source_dir / "raw"
    required = ["Sites.csv", "spp_occur.csv", "Nodes_E.csv", "Nodes_W.csv", "raster_east3.tif", "raster_west3.tif"]
    missing = [name for name in required if not (raw / name).exists()]
    if missing:
        raise ValueError(f"missing frozen source files: {missing}")

    tables = {name: _table(raw / name) for name in required if name.endswith(".csv")}
    rasters: dict[str, object] = {}
    try:
        import rasterio
    except ImportError as exc:
        raise RuntimeError("rasterio is required for source audit") from exc
    for name in ("raster_east3.tif", "raster_west3.tif"):
        path = raw / name
        with rasterio.open(path) as ds:
            rasters[name] = {
                "sha256": _sha(path),
                "driver": ds.driver,
                "crs": None if ds.crs is None else ds.crs.to_string(),
                "width": ds.width,
                "height": ds.height,
                "count": ds.count,
                "dtype": list(ds.dtypes),
                "nodata": ds.nodata,
                "bounds": [ds.bounds.left, ds.bounds.bottom, ds.bounds.right, ds.bounds.top],
                "transform": list(ds.transform)[:6],
            }

    occurrence = tables["spp_occur.csv"]
    report = {
        "dataset": "Brodie & Newmark Tanzania forest-fragment benchmark",
        "doi": "10.5061/dryad.p042h0c",
        "tables": tables,
        "rasters": rasters,
        "published_species_count_reference": 43,
        "occurrence_schema_only": {
            "rows": occurrence["n_rows"],
            "columns": occurrence["columns"],
            "binary_columns": occurrence["binary_columns"],
            "note": "No taxa are retained/excluded and no EOG statistic is computed in this audit.",
        },
        "scientific_boundary": "pre-EOG source/schema freeze only; species-level EOG performance not inspected",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(audit(args.source_dir, args.output), indent=2))


if __name__ == "__main__":
    main()
