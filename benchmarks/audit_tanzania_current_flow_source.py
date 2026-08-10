"""Audit and freeze Tanzania current-flow source semantics before outcomes."""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import rasterio

from eog.tanzania_current_flow_contract import summarize_current_flow_source_contract


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"missing CSV header: {path}")
        return [dict(row) for row in reader]


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _script_evidence(source_dir: Path) -> dict[str, bool]:
    usambara = _compact((source_dir / "0_usambara.R").read_text(encoding="utf-8"))
    sites = _compact((source_dir / "1_sites.R").read_text(encoding="utf-8"))
    occurrence = _compact(
        (source_dir / "2_isolation_occurrence").read_text(encoding="utf-8")
    )
    return {
        "east_script_requests_missing_new_raster_name": (
            'costE<-raster("raster_east3_new.tif")' in usambara
        ),
        "east_points_use_columns_3_and_4": "SpatialPoints(ptsE[,3:4])" in usambara,
        "west_points_use_columns_3_and_4": "SpatialPoints(ptsW[,3:4])" in usambara,
        "point_rasterization_omits_explicit_field": (
            usambara.count("rasterize(x=sites,y=cost)") == 2
        ),
        "pairwise_circuitscape_scenario": "scenario=pairwise" in usambara,
        "three_resistance_axes_each_1_to_128": all(
            token in usambara
            for token in (
                "euc<-c(1,2,4,8,16,32,64,128)",
                "tea<-c(1,2,4,8,16,32,64,128)",
                "oth<-c(1,2,4,8,16,32,64,128)",
            )
        ),
        "released_log10_area_ha_source_transform": all(
            token in sites
            for token in (
                "patchesE$logArea<-log10(patchesE$Area_ha)",
                "patchesW$logArea<-log10(patchesW$Area_ha)",
            )
        ),
        "released_inverse_log_area_weighting": all(
            token in sites
            for token in (
                "RD.E$WeightedRD<-RD.E$value*(1/RD.E$logArea)",
                "RD.W$WeightedRD<-RD.W$value*(1/RD.W$logArea)",
            )
        ),
        "downstream_resistance_columns_keyed_by_patch_number": all(
            token in sites
            for token in (
                "subset(RD.E,col==pE$patch_number[p])",
                "subset(RD.W,col==pW$patch_number[p])",
            )
        ),
        "source_glm_area_isolation_interaction": (
            'glm(occur$occur~log10(occur$area_ha)*log10(occur[,c+15]),family="binomial")'
            in occurrence
        ),
        "source_514_predictor_loop": "for(cin1:514)" in occurrence,
    }


def _raster_summary(path: Path) -> dict[str, Any]:
    with rasterio.open(path) as dataset:
        values = dataset.read(1, masked=True)
        unique = sorted(int(value) for value in np.unique(values.compressed()))
        return {
            "filename": path.name,
            "crs": str(dataset.crs),
            "height": int(dataset.height),
            "width": int(dataset.width),
            "landcover_classes": unique,
        }


def _raster_evidence(source_dir: Path) -> dict[str, object]:
    released_requested = "raster_east3_new.tif"
    verified_east = source_dir / "raster_east3.tif"
    verified_west = source_dir / "raster_west3.tif"
    if (source_dir / released_requested).exists():
        raise ValueError("unexpected released east raster alias now exists; re-audit source drift")
    if not verified_east.exists() or not verified_west.exists():
        raise ValueError("verified Tanzania raster files are missing")
    east = _raster_summary(verified_east)
    west = _raster_summary(verified_west)
    if east["landcover_classes"] != [1, 2, 3, 4]:
        raise ValueError("verified east raster does not already contain classes 1..4")
    if west["landcover_classes"] != [1, 2, 3, 4]:
        raise ValueError("verified west raster does not contain classes 1..4")
    return {
        "released_east_filename": released_requested,
        "verified_archive_east_filename": verified_east.name,
        "released_east_filename_present": False,
        "filename_mismatch": True,
        "benchmark_alias_policy": (
            "use the digest-verified raster_east3.tif only after confirming classes 1..4; "
            "do not apply the released 5-to-4 or 6-to-3 recode because those classes are absent"
        ),
        "east": east,
        "west": west,
    }


def _assert_expected(report: Mapping[str, Any], expected: Mapping[str, Any]) -> None:
    if report != expected:
        actual = json.dumps(report, sort_keys=True, indent=2)
        target = json.dumps(expected, sort_keys=True, indent=2)
        raise ValueError(
            "Tanzania current-flow source audit drifted from the committed pre-outcome "
            f"contract.\nEXPECTED:\n{target}\nACTUAL:\n{actual}"
        )


def audit(
    *,
    source_dir: Path,
    output: Path,
    expected_path: Path | None = None,
) -> dict[str, Any]:
    required = {
        "0_usambara.R",
        "1_sites.R",
        "2_isolation_occurrence",
        "Nodes_E.csv",
        "Nodes_W.csv",
        "raster_east3.tif",
        "raster_west3.tif",
    }
    missing = sorted(name for name in required if not (source_dir / name).exists())
    if missing:
        raise ValueError(f"missing verified Tanzania source files: {missing}")

    report = summarize_current_flow_source_contract(
        east_rows=_rows(source_dir / "Nodes_E.csv"),
        west_rows=_rows(source_dir / "Nodes_W.csv"),
        script_evidence=_script_evidence(source_dir),
        raster_evidence=_raster_evidence(source_dir),
    )
    if expected_path is not None:
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        _assert_expected(report, expected)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            audit(
                source_dir=args.source_dir,
                output=args.output,
                expected_path=args.expected,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
