#!/usr/bin/env python3
"""Opt-in source-only official NADCON5 sensitivity for McKee 2024 12h fixes.

Only uses the exact publisher-SHA verified public sparse 12h Point source.
NEVER reads DBF attributes, GPS2h holdout or raw individual paths. No
datum grid is bundled. A trusted separately acquired NOAA grid MUST match
the exact OSGeo PROJ-data catalogue SHA/size before being loaded. This is
a conditional EPSG:5070/5071 representation comparison, not proof of
actual source CRS or position error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import warnings

import numpy as np

from replay_post_stop_5070_5071_grid_sensitivity import (
    _source_points, _quantiles, _same_grid_counts, SOURCE_SHA256,
    SOURCE_SIZE, GRID_ORIGIN, GRID_SIZES,
)

HERE = Path(__file__).resolve().parent
PROTOCOL_PATH = HERE / "post_stop_official_nadcon5_5070_5071_protocol_v1.json"
GRID_RECEIPT_PATH = HERE / "post_stop_official_nadcon5_integrity_and_blocker_receipt_v1.json"
GRID_NAME = "us_noaa_nadcon5_nad83_1986_nad83_harn_conus.tif"
GRID_BYTES = 3522682
GRID_SHA = "e12ac2e886edafe616e0994c610ad3daa01db17c00d0e9938145d956f249fc2f"
N = 28953


def _precommitted_contract():
    p = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    receipt = json.loads(GRID_RECEIPT_PATH.read_text(encoding="utf-8"))
    g = receipt["official_grid"]
    if (
        p.get("schema") != "eog.mckee2024.post_stop_official_nadcon5_5070_5071_sensitivity.v1"
        or p.get("status") != "FROZEN_BEFORE_ACQUIRING_OFFICIAL_CONUS_DATUM_GRID_AND_NEW_COORDINATE_RECOMPUTATION"
        or p["source"]["sha256"] != SOURCE_SHA256
        or p["source"]["size_bytes"] != SOURCE_SIZE
        or p["source"]["records"] != N
        or tuple(p["candidate_crs"]) != ("EPSG:5070", "EPSG:5071")
        or tuple(p["numerical_policy"]["grid_origin_webmercator_m"]) != GRID_ORIGIN
        or tuple(p["numerical_policy"]["cell_widths_m"]) != GRID_SIZES
        or g["filename"] != GRID_NAME
        or g["sha256"] != GRID_SHA
        or g["original_byte_size"] != GRID_BYTES
        or g["source_crs"] != "EPSG:4269"
        or g["target_crs"] != "EPSG:4152"
    ):
        raise ValueError("Unfrozen source, grid, CRS candidates or comparison origin")
    return p


def _grid_integrity(path: Path):
    if path.is_symlink() or not path.is_file() or path.name != GRID_NAME:
        raise ValueError("No trusted official NADCON5 grid under exact filename")
    if path.stat().st_size != GRID_BYTES:
        raise ValueError("NOAA datum grid original byte-size mismatch")
    with path.open("rb") as stream:
        tiff_magic = stream.read(4)
    if tiff_magic not in (b"II*\x00", b"MM\x00*",
                          b"II+\x00", b"MM\x00+"):
        raise ValueError("NOAA datum grid is not TIFF/BigTIFF")
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            digest.update(block)
    if digest.hexdigest() != GRID_SHA:
        raise ValueError("NOAA datum grid SHA256 does not match OSGeo catalogue")
    return {"name":GRID_NAME,"size_bytes":GRID_BYTES,"sha256":GRID_SHA}


def _exact_displacement(reference_raw, converted_5070_to_5071):
    """Compare two alternative source-CRS labels within the SAME 5071 frame.

    Under HARN/5071, raw XY is the position if the original input labels
    were 5071, and transformed XY is the position under 5070 using the
    exact NAD83→HARN grid-backed operation. Both then use the SAME
    5071→geographic and 5071→EPSG:3857 transformations. This estimand
    is intentionally distinct from the earlier separate-to-WGS84
    *ballpark* candidate comparison (which is NOT a certified bound).
    """
    from pyproj import Transformer, Geod
    if reference_raw.shape != converted_5070_to_5071.shape:
        raise ValueError("Coordinate sample shape mismatch")
    if (reference_raw.ndim!=2 or reference_raw.shape[1]!=2 or
        reference_raw.shape[0]!=N or
        not np.isfinite(reference_raw).all() or
        not np.isfinite(converted_5070_to_5071).all()):
        raise ValueError("Unexpected original original GPS point shape or nonfinite grid shifts")
    ll=Transformer.from_crs("EPSG:5071","EPSG:4326",always_xy=True)
    web=Transformer.from_crs("EPSG:5071","EPSG:3857",always_xy=True)
    # One geodetic frame for BOTH candidate positions: no independent
    # output-coordinate-transform choices hidden in the comparison.
    x0,y0=ll.transform(reference_raw[:,0],reference_raw[:,1])
    x1,y1=ll.transform(converted_5070_to_5071[:,0],converted_5070_to_5071[:,1])
    _,_,geodesic=Geod(ellps="WGS84").inv(x0,y0,x1,y1)
    wx0,wy0=web.transform(reference_raw[:,0],reference_raw[:,1])
    wx1,wy1=web.transform(converted_5070_to_5071[:,0],converted_5070_to_5071[:,1])
    a=np.column_stack((wx0,wy0))
    c=np.column_stack((wx1,wy1))
    if not np.isfinite(geodesic).all() or not np.isfinite(a).all() or not np.isfinite(c).all():
        raise ValueError("Invalid grid-corrected position outputs")
    return {
        "geodesic_between_candidate_positions_same_5071_frame_m":_quantiles(np.abs(geodesic)),
        "EPSG3857_displacement_same_output_operation_m":_quantiles(np.linalg.norm(a-c,axis=1)),
        "cell_agreement_5071_frame_same_webmercator_operation":_same_grid_counts(a,c),
    }


def run(source_zip:Path, local_grid_file:Path) -> dict:
    _precommitted_contract()
    verified=_grid_integrity(local_grid_file)  # fail before reading any source coordinates
    import pyproj
    from pyproj.transformer import TransformerGroup
    pyproj.network.set_network_enabled(False)
    # Append only an already verified private grid directory, never the
    # original GPS ZIP or an unverified grid bundle.
    pyproj.datadir.append_data_dir(str(local_grid_file.parent))
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        group=TransformerGroup("EPSG:5070","EPSG:5071",always_xy=True)
    if not group.best_available:
        raise RuntimeError("PROJ official datum grid still unavailable after SHA validation")
    matching=[
        t for t in group.transformers
        if GRID_NAME in t.definition
        and t.accuracy >= 0
        and t.accuracy <= 0.1
    ]
    if not matching:
        raise RuntimeError("No non-ballpark 5070→5071 operation using exact official NADCON5 grid")
    selected=matching[0]
    points=_source_points(source_zip)
    x,y=selected.transform(points[:,0],points[:,1],errcheck=True)
    new=np.column_stack((x,y))
    out=_exact_displacement(points,new)
    return {
        "schema":"eog.mckee2024.post_stop_official_nadcon5_5070_5071_result.v1",
        "status":"GRID_BACKED_CANDIDATE_CRS_SENSITIVITY_ONLY__AUTHOR_CRS_STOP",
        "source_sha256_verified":True,
        "source_sha256":SOURCE_SHA256,
        "sparse_fix_count":N,
        "official_grid_verification":verified,
        "pyproj_version":pyproj.__version__,
        "PROJ_version":pyproj.proj_version_str,
        "PROJ_network_enabled":pyproj.network.is_network_enabled(),
        "best_available_for_5070_to_5071":group.best_available,
        "chosen_operation_description":selected.description,
        "chosen_operation_accuracy_metadata_m":selected.accuracy,
        "chosen_pipeline":selected.definition,
        **out,
        "comparability_warning":"These grid-backed offsets are computed by 5070→5071 transformation within a common 5071 output frame. Previous ~1.156m ballpark difference was computed by two independent candidate-to-WGS84 transformations; it is a separate estimand, NOT an error bound or quantity for direct subtraction.",
        "author_intended_original_CRS_confirmed":False,
        "source_CRS_STOP_retained":True,
        "source_timestamp_STOP_retained":True,
        "dense_2h_GPS_opened":False,
        "DBF_attributes_opened":False,
        "raw_fix_coordinates_or_IDs_exported":False,
        "BBMM_or_EOG_predictions_scored":False,
        "EOG_WF_scored_endpoints_unchanged":3
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-zip",required=True,type=Path)
    p.add_argument("--official-grid",required=True,type=Path)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    data=run(a.source_zip,a.official_grid)
    text=json.dumps(data,sort_keys=True,indent=2)+"\n"
    if a.output:
        a.output.write_text(text,encoding="utf-8")
    else:
        print(text)


if __name__=="__main__":
    main()
