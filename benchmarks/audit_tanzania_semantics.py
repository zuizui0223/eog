"""Validate Tanzania source semantics/alignment before any EOG outcome.

This gate runs only after ``audit_tanzania_verified_bytes.py`` has verified the
official Dryad bytes.  It deliberately refuses to infer column meanings: an
explicit semantics mapping recovered from the official source scripts/tables is
required.  The only species-level operation allowed here is deterministic
eligibility counting; no occurrence model, graph score, AUC, or EOG result is
computed.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

EXPECTED_SITES = 14
EXPECTED_SPECIES = 89
MIN_CLASS_COUNT = 2


def _rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"missing header: {path.name}")
        rows = [dict(row) for row in reader]
    return [str(x).strip() for x in reader.fieldnames], rows


def _require_column(headers: list[str], name: str, table: str) -> None:
    if name not in headers:
        raise ValueError(f"mapped column {name!r} absent from {table}: {headers}")


def _finite(value: str, label: str) -> float:
    try:
        out = float(value)
    except Exception as exc:
        raise ValueError(f"non-numeric {label}: {value!r}") from exc
    if not math.isfinite(out):
        raise ValueError(f"non-finite {label}: {value!r}")
    return out


def _binary(value: str, label: str) -> int:
    text = str(value).strip()
    if text in {"0", "0.0"}:
        return 0
    if text in {"1", "1.0"}:
        return 1
    raise ValueError(f"non-binary occurrence {label}: {value!r}")


def _site_table(source_dir: Path, spec: dict[str, Any]) -> dict[str, Any]:
    headers, rows = _rows(source_dir / "Sites.csv")
    if len(rows) != EXPECTED_SITES:
        raise ValueError(f"Sites.csv has {len(rows)} rows; paper reports {EXPECTED_SITES} fragments")

    required = ["site_id", "patch_area", "region", "x", "y"]
    for role in required:
        if role not in spec:
            raise ValueError(f"Sites mapping missing required role: {role}")
        _require_column(headers, str(spec[role]), "Sites.csv")

    site_col = str(spec["site_id"])
    area_col = str(spec["patch_area"])
    region_col = str(spec["region"])
    x_col = str(spec["x"])
    y_col = str(spec["y"])
    ids = [str(row[site_col]).strip() for row in rows]
    if any(not x for x in ids) or len(set(ids)) != EXPECTED_SITES:
        raise ValueError("site IDs must be nonblank and unique across all 14 fragments")

    areas = [_finite(row[area_col], f"patch area for {sid}") for sid, row in zip(ids, rows)]
    if any(x <= 0 for x in areas):
        raise ValueError("patch areas must be positive")
    regions = [str(row[region_col]).strip() for row in rows]
    if len(set(regions)) != 2:
        raise ValueError(f"expected exactly two study regions, got {sorted(set(regions))}")
    coords = {
        sid: (_finite(row[x_col], f"x for {sid}"), _finite(row[y_col], f"y for {sid}"))
        for sid, row in zip(ids, rows)
    }
    return {
        "headers": headers,
        "rows": rows,
        "site_ids": ids,
        "areas": dict(zip(ids, areas)),
        "regions": dict(zip(ids, regions)),
        "coords": coords,
        "region_levels": sorted(set(regions)),
    }


def _occurrence_table(source_dir: Path, spec: dict[str, Any], sites: dict[str, Any]) -> dict[str, Any]:
    headers, rows = _rows(source_dir / "spp_occur.csv")
    layout = str(spec.get("layout") or "")
    counts: dict[str, list[int]] = {}
    site_ids = list(sites["site_ids"])

    if layout == "sites_by_species":
        site_col = str(spec.get("site_id") or "")
        species_cols = [str(x) for x in spec.get("species_columns", [])]
        _require_column(headers, site_col, "spp_occur.csv")
        if len(species_cols) != EXPECTED_SPECIES:
            raise ValueError(f"mapping must name exactly {EXPECTED_SPECIES} species columns")
        for col in species_cols:
            _require_column(headers, col, "spp_occur.csv")
        observed_sites = [str(row[site_col]).strip() for row in rows]
        if set(observed_sites) != set(site_ids) or len(observed_sites) != EXPECTED_SITES:
            raise ValueError("occurrence site IDs do not match the 14 Sites.csv IDs one-to-one")
        for species in species_cols:
            vals = [_binary(row[species], f"{species}@{row[site_col]}") for row in rows]
            counts[species] = [sum(vals), len(vals) - sum(vals)]

    elif layout == "species_by_sites":
        species_col = str(spec.get("species_id") or "")
        site_cols = [str(x) for x in spec.get("site_columns", [])]
        _require_column(headers, species_col, "spp_occur.csv")
        if len(site_cols) != EXPECTED_SITES:
            raise ValueError(f"mapping must name exactly {EXPECTED_SITES} site columns")
        for col in site_cols:
            _require_column(headers, col, "spp_occur.csv")
        mapped_site_ids = [str(x) for x in spec.get("site_ids", site_cols)]
        if len(mapped_site_ids) != EXPECTED_SITES or set(mapped_site_ids) != set(site_ids):
            raise ValueError("mapped occurrence site IDs do not match Sites.csv")
        if len(rows) != EXPECTED_SPECIES:
            raise ValueError(f"occurrence table has {len(rows)} species rows; expected {EXPECTED_SPECIES}")
        species_ids = [str(row[species_col]).strip() for row in rows]
        if any(not x for x in species_ids) or len(set(species_ids)) != EXPECTED_SPECIES:
            raise ValueError("species IDs must be nonblank and unique")
        for species, row in zip(species_ids, rows):
            vals = [_binary(row[col], f"{species}@{sid}") for col, sid in zip(site_cols, mapped_site_ids)]
            counts[species] = [sum(vals), len(vals) - sum(vals)]

    elif layout == "long":
        species_col = str(spec.get("species_id") or "")
        site_col = str(spec.get("site_id") or "")
        value_col = str(spec.get("occurrence") or "")
        for col in (species_col, site_col, value_col):
            _require_column(headers, col, "spp_occur.csv")
        seen: set[tuple[str, str]] = set()
        values: dict[str, list[int]] = {}
        for row in rows:
            species = str(row[species_col]).strip()
            site = str(row[site_col]).strip()
            if site not in set(site_ids):
                raise ValueError(f"unknown site in occurrence table: {site}")
            key = (species, site)
            if key in seen:
                raise ValueError(f"duplicate species/site occurrence row: {key}")
            seen.add(key)
            values.setdefault(species, []).append(_binary(row[value_col], f"{species}@{site}"))
        if len(values) != EXPECTED_SPECIES:
            raise ValueError(f"long occurrence table has {len(values)} species; expected {EXPECTED_SPECIES}")
        for species, vals in values.items():
            if len(vals) != EXPECTED_SITES:
                raise ValueError(f"{species} has {len(vals)} site records; expected {EXPECTED_SITES}")
            counts[species] = [sum(vals), len(vals) - sum(vals)]
    else:
        raise ValueError("occurrence mapping layout must be sites_by_species, species_by_sites, or long")

    if len(counts) != EXPECTED_SPECIES:
        raise ValueError(f"resolved {len(counts)} species; expected {EXPECTED_SPECIES}")
    eligible = sorted(
        species for species, (present, absent) in counts.items()
        if present >= MIN_CLASS_COUNT and absent >= MIN_CLASS_COUNT
    )
    return {
        "layout": layout,
        "n_species": len(counts),
        "class_counts": {k: {"presence": v[0], "absence": v[1]} for k, v in sorted(counts.items())},
        "eligibility_rule": f"presence >= {MIN_CLASS_COUNT} and absence >= {MIN_CLASS_COUNT}",
        "eligible_species": eligible,
        "n_eligible": len(eligible),
    }


def _node_table(source_dir: Path, filename: str, spec: dict[str, Any]) -> dict[str, Any]:
    headers, rows = _rows(source_dir / filename)
    x_col = str(spec.get("x") or "")
    y_col = str(spec.get("y") or "")
    for col in (x_col, y_col):
        _require_column(headers, col, filename)
    coords = [(_finite(row[x_col], f"{filename} x"), _finite(row[y_col], f"{filename} y")) for row in rows]
    if not coords:
        raise ValueError(f"{filename} has no nodes")
    return {"n_nodes": len(coords), "coords": coords, "headers": headers}


def _raster_alignment(source_dir: Path, sites: dict[str, Any], nodes: dict[str, Any], mapping: dict[str, Any]) -> dict[str, Any]:
    try:
        import rasterio  # type: ignore
    except Exception as exc:
        raise RuntimeError("rasterio is required for the semantics/alignment gate") from exc

    region_values = mapping.get("region_values")
    if not isinstance(region_values, dict) or set(region_values) != {"east", "west"}:
        raise ValueError("mapping.region_values must explicitly map east and west to Sites.csv region values")

    out: dict[str, Any] = {}
    for key, raster_name in (("east", "raster_east3.tif"), ("west", "raster_west3.tif")):
        region_value = str(region_values[key])
        with rasterio.open(source_dir / raster_name) as src:
            bounds = src.bounds
            transform = src.transform
            pixel = [abs(float(transform.a)), abs(float(transform.e))]
            region_sites = [sid for sid, region in sites["regions"].items() if region == region_value]
            if not region_sites:
                raise ValueError(f"no Sites.csv rows map to {key} region value {region_value!r}")
            outside = []
            for sid in region_sites:
                x, y = sites["coords"][sid]
                if not (bounds.left <= x <= bounds.right and bounds.bottom <= y <= bounds.top):
                    outside.append(sid)
            if outside:
                raise ValueError(f"{key} site coordinates outside {raster_name} bounds: {outside}")
            node_outside = [
                i for i, (x, y) in enumerate(nodes[key]["coords"])
                if not (bounds.left <= x <= bounds.right and bounds.bottom <= y <= bounds.top)
            ]
            if node_outside:
                raise ValueError(f"{key} nodes outside raster bounds: first indices {node_outside[:10]}")
            out[key] = {
                "region_value": region_value,
                "n_sites": len(region_sites),
                "n_nodes": nodes[key]["n_nodes"],
                "raster_crs": str(src.crs) if src.crs else None,
                "pixel_size": pixel,
                "bounds": [float(bounds.left), float(bounds.bottom), float(bounds.right), float(bounds.top)],
            }
    return out


def audit(source_dir: Path, verified_schema: Path, semantics_mapping: Path, output: Path) -> dict[str, Any]:
    verified = json.loads(verified_schema.read_text(encoding="utf-8"))
    if verified.get("full_structural_input_gate") != "pass":
        raise ValueError("verified-byte structural gate must be full pass before semantics/alignment")
    mapping = json.loads(semantics_mapping.read_text(encoding="utf-8"))
    if mapping.get("source") != "official_dryad_scripts_and_tables":
        raise ValueError("semantics mapping must attest recovery from official Dryad scripts/tables")

    sites = _site_table(source_dir, dict(mapping.get("sites") or {}))
    occurrence = _occurrence_table(source_dir, dict(mapping.get("occurrence") or {}), sites)
    node_mapping = dict(mapping.get("nodes") or {})
    nodes = {
        "east": _node_table(source_dir, "Nodes_E.csv", dict(node_mapping.get("east") or {})),
        "west": _node_table(source_dir, "Nodes_W.csv", dict(node_mapping.get("west") or {})),
    }
    alignment = _raster_alignment(source_dir, sites, nodes, mapping)

    report = {
        "status": "verified_semantics_alignment_and_eligibility_only",
        "paper_expected_sites": EXPECTED_SITES,
        "paper_expected_species": EXPECTED_SPECIES,
        "site_region_levels": sites["region_levels"],
        "alignment": alignment,
        "occurrence": occurrence,
        "published_reproduction_reference": {
            "paper_species_total": 89,
            "paper_occurrence_models_converged": 43,
            "note": "43/89 is a later source-reproduction sanity check, not a tuned eligibility target",
        },
        "species_outcomes_inspected": False,
        "eog_graph_constructed": False,
        "connectivity_parameters_selected": False,
        "next_gate": "freeze geometry-only holdout/scales and executable source formulas before any EOG outcome",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--verified-schema", type=Path, required=True)
    parser.add_argument("--semantics-mapping", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.source_dir, args.verified_schema, args.semantics_mapping, args.output), indent=2))


if __name__ == "__main__":
    main()
