"""Offline claim-boundary tests for cross-sourced official Baggs locator audit."""
import json
from pathlib import Path
import runpy

import pytest

ROOT = Path(__file__).resolve().parents[1] / "validation" / "temporal_corridor_mckee2024"
PROTOCOL = ROOT / "post_stop_official_baggs_locator_protocol_v1.json"
RECEIPT = ROOT / "post_stop_official_baggs_locator_receipt_v1.json"
PRODUCER = ROOT / "replay_official_baggs_bbox_locator.py"
SHA = "556062b7426336a94fe93dd9e6b049dc6c960d3dc8135f7298f465126c6962c4"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_official_reference_geometry_and_source_frozen_before_comparison():
    p = _load(PROTOCOL)
    r = _load(RECEIPT)
    assert p["status"] == "FROZEN_BEFORE_CROSS_SOURCE_SPATIAL_COMPARISON"
    assert r["protocol_commit"] == "4c1d19db6567e34e949fdc98359c36fca5b4b63a"
    assert p["source"]["sha256"] == r["source_sha256"] == SHA
    assert p["source"]["file_id"] == 3334125
    assert p["source"]["allowable_herd"] == "AtlanticRim"
    assert p["source"]["file_name"] == "GPS12hrs_Locs.zip"
    assert p["dense_2h_access"] is False
    ref = p["independent_geographic_reference"]
    assert ref["provider"].startswith("Wyoming Game and Fish Department")
    assert ref["official_spatial_reference"].startswith("EPSG:3857")
    bbox = [
        ref["public_full_extent_web_mercator_" + field]
        for field in ("xmin", "ymin", "xmax", "ymax")
    ]
    assert bbox == r["wgfd_extent_epsg3857"]
    assert p["predeclared_buffer_meters"] == r["predeclared_extension_meters"] == 5000


def test_coarse_registration_supports_albers_family_not_a_unique_author_crs():
    p = _load(PROTOCOL)
    r = _load(RECEIPT)
    candidates = [x["crs"] for x in p["hypotheses"]]
    assert candidates == [
        "EPSG:3742", "EPSG:5070", "EPSG:5071",
        "ESRI:102003", "EPSG:3857",
    ]
    counts = {x["input_crs"]: x for x in r["crs_diagnostics"]}
    assert list(counts) == candidates
    assert r["AtlanticRim_records"] == 17248
    assert r["all_12h_records"] == 28953
    assert all(x["finite_transform_count"] == 17248 for x in counts.values())
    assert counts["EPSG:3742"]["inside_public_full_bbox_count"] == 0
    assert counts["EPSG:5070"]["inside_public_full_bbox_count"] == 16533
    assert counts["EPSG:5071"]["inside_public_full_bbox_count"] == 16533
    assert counts["EPSG:5070"]["inside_full_bbox_plus_5km_count"] == 16812
    assert counts["EPSG:5071"]["inside_full_bbox_plus_5km_count"] == 16812
    assert counts["ESRI:102003"]["inside_public_full_bbox_count"] == 0
    assert counts["EPSG:3857"]["inside_public_full_bbox_count"] == 0
    assert r["crs_author_intent_confirmed"] is False
    assert p["mainline"].startswith("SOURCE_QC_DIAGNOSTIC_ONLY")


def test_source_could_share_original_herds_and_no_field_outcome_was_scored():
    p, r = _load(PROTOCOL), _load(RECEIPT)
    warnings = " ".join(p["claim_boundary"]).lower()
    assert "not independent ecological replication" in warnings
    assert "bounding envelope" in warnings
    assert r["source_prj_epsg_declared"] == 3742
    assert r["two_hour_holdout_opened"] is False
    assert r["raw_coordinates_or_animal_ids_exported"] is False
    assert r["ecological_prediction_scored"] is False
    assert r["EOG_WF_scored_endpoints_unchanged"] == 3


def test_replay_producer_imports_without_source_and_rejects_fake_archive(tmp_path):
    source = runpy.run_path(str(PRODUCER))
    assert source["BBOX"] == tuple(_load(RECEIPT)["wgfd_extent_epsg3857"])
    assert source["CODES"] == tuple(x["crs"] for x in _load(PROTOCOL)["hypotheses"])
    bad = tmp_path / "GPS12hrs_Locs.zip"
    bad.write_bytes(b"this is not a GPS source")
    with pytest.raises(ValueError, match="exact-size"):
        source["_source"](bad)
