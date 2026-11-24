"""Offline regression guards for official-grid McKee source CRS sensitivity.

A real NOAA NADCON5 binary is NEVER committed to EOG. These tests check
the publisher SHA, OSGeo release fingerprint, fail-closed acquisition, and
no raw GPS/2h scoring. Synthetic planar coordinates exercise the output
math without relying on the official datum grid being available in CI.
"""
from __future__ import annotations

import json
from pathlib import Path
import runpy
import sys

import numpy as np
import pytest


HERE = Path(__file__).resolve().parents[1] / "validation/temporal_corridor_mckee2024"
PROTOCOL = HERE / "post_stop_official_nadcon5_5070_5071_protocol_v1.json"
MANIFEST = HERE / "post_stop_official_nadcon5_integrity_and_blocker_receipt_v1.json"
OLD = HERE / "post_stop_5070_5071_datum_grid_sensitivity_receipt_v1.json"
SCRIPT = HERE / "replay_post_stop_official_nadcon5_grid.py"

sys.path.insert(0,str(HERE))
try:
    m=runpy.run_path(str(SCRIPT))
finally:
    sys.path.remove(str(HERE))


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_original_source_and_grid_fingerprints_from_official_manifest():
    protocol,receipt = _read(PROTOCOL),_read(MANIFEST)
    grid=receipt["official_grid"]
    assert protocol["schema"]=="eog.mckee2024.post_stop_official_nadcon5_5070_5071_sensitivity.v1"
    assert protocol["status"]=="FROZEN_BEFORE_ACQUIRING_OFFICIAL_CONUS_DATUM_GRID_AND_NEW_COORDINATE_RECOMPUTATION"
    assert receipt["preacquisition_protocol_commit"]=="28352d5a0aafc5404d1a3652b632b98b9889d4fa"
    assert protocol["source"]["sha256"]==m["SOURCE_SHA256"]==receipt["exact_source_GPS_ZIP_SHA"]
    assert protocol["source"]["size_bytes"]==1539661
    assert m["_precommitted_contract"]()["schema"]==protocol["schema"]
    assert grid["filename"]==m["GRID_NAME"]
    assert grid["original_byte_size"]==m["GRID_BYTES"]==3522682
    assert grid["sha256"]==m["GRID_SHA"]=="e12ac2e886edafe616e0994c610ad3daa01db17c00d0e9938145d956f249fc2f"
    assert grid["source_crs"]=="EPSG:4269"
    assert grid["target_crs"]=="EPSG:4152"
    assert grid["primary_metadata_provenance"]["source_repo"]=="OSGeo/PROJ-data"
    assert grid["primary_metadata_provenance"]["source_file"]=="files.geojson"


def test_previous_offline_ballpark_results_reproduced_without_fabricating_grid_results():
    old,latest = _read(OLD),_read(MANIFEST)
    assert old["status"]=="CONDITIONAL_OFFLINE_BALLPARK__BEST_DATUM_GRID_UNAVAILABLE"
    assert old["best_available_datum_operation"] is False
    assert old["sparse_points"]==latest["historical_offline_baseline_reproduced_in_turn"]["raw_sparses_x_y_count"]==28953
    assert latest["historical_offline_baseline_reproduced_in_turn"]["grid_flip_counts"]=={
        "100":602,"250":233,"500":114,"1000":62,"5000":8
    }
    assert [z["different_cell_count"] for z in old["fixed_grid_agreement"]]==[602,233,114,62,8]
    assert old["WGS84_geodesic_displacement_m"]["median"]==pytest.approx(1.155895)
    assert latest["results"]["official_grid_corrected_geodesic_displacement_m"] is None
    assert latest["results"]["official_grid_corrected_grid_flip_counts"] is None
    assert latest["actual_download_attempt"]["TransformerGroup_5070_to_5071_best_available"] is False


def test_grid_path_rejected_before_2h_or_source_coordinate_read(tmp_path):
    fn=m["_grid_integrity"]
    with pytest.raises(ValueError,match="No trusted official"):
        fn(tmp_path / "no_such_grid.tif")
    wrong=tmp_path / m["GRID_NAME"]
    wrong.write_bytes(b"invalid geodetic grid")
    with pytest.raises(ValueError,match="byte-size mismatch"):
        fn(wrong)
    wrong.write_bytes(b"not-a-tiff")  # same official name, still invalid size
    with pytest.raises(ValueError,match="byte-size mismatch"):
        fn(wrong)
    # Malicious same-sized but wrong binary fails SHA check.
    wrong.write_bytes(b"II*\x00"+bytes(m["GRID_BYTES"]-4))
    with pytest.raises(ValueError,match="SHA256"):
        fn(wrong)


def test_source_only_grid_grid_math_synthetic_identity_is_zero_displacement():
    fn=m["_exact_displacement"]
    points=np.tile(np.asarray(( -1_000_000.0, 2_100_000.0)),(m["N"],1))
    r=fn(points,points.copy())
    assert r["geodesic_between_candidate_positions_same_5071_frame_m"]=={
        "minimum":0.0,"median":0.0,"p95":0.0,"p99":0.0,"maximum":0.0
    }
    assert r["EPSG3857_displacement_same_output_operation_m"]["maximum"]==0.0
    assert all(z["different_cell_count"]==0 for z in r["cell_agreement_5071_frame_same_webmercator_operation"])


def test_source_only_grid_math_synthetic_shift_and_invalid_coordinates():
    fn=m["_exact_displacement"]
    raw=np.tile(np.asarray((-1_000_000.0,2_100_000.0)),(m["N"],1))
    corrected=raw.copy()
    corrected[:,0]+=0.3
    out=fn(raw,corrected)
    assert out["geodesic_between_candidate_positions_same_5071_frame_m"]["median"]>0
    assert out["EPSG3857_displacement_same_output_operation_m"]["maximum"]>0
    assert sum(z["same_cell_count"]+z["different_cell_count"]
               for z in out["cell_agreement_5071_frame_same_webmercator_operation"])==5*m["N"]
    with pytest.raises(ValueError,match="shape"):
        fn(raw[:12],corrected)
    corrected[0,0]=float("nan")
    with pytest.raises(ValueError,match="nonfinite"):
        fn(raw,corrected)


def test_source_and_heldout_stops_not_rewritten():
    p=_read(PROTOCOL)
    rec=_read(MANIFEST)
    assert p["hard_stops"][0]=="Do not open/read or download 2h heldout original source"
    assert p["original_EOG_WF"]=={
        "scored":3,"scientific_stops":31,"admin_exclusions":3
    }
    assert rec["guarantees"]["dense_2h_holdout_sealed"] is True
    assert rec["guarantees"]["source_time_and_CRS_QC_STOP_retained"] is True
    assert rec["results"]["source_author_true_CRS_verified"] is False
    assert rec["results"]["source_datum_accuracy_bound_valid"] is False
