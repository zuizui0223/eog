"""Offline regression of the post-STOP 12h Albers datum/grid sensitivity.

No biological source ZIP is in the repository. These checks enforce the
pre-frozen estimand, frozen aggregate result, fail-closed input and the
critical missing-grid / author-CRS scientific limitation.
"""
import json
from pathlib import Path
import runpy

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1] / "validation/temporal_corridor_mckee2024"
PROTOCOL = ROOT / "post_stop_5070_5071_datum_grid_sensitivity_protocol_v1.json"
RECEIPT = ROOT / "post_stop_5070_5071_datum_grid_sensitivity_receipt_v1.json"
SCRIPT = ROOT / "replay_post_stop_5070_5071_grid_sensitivity.py"
ns = runpy.run_path(str(SCRIPT))


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_precommitted_protocol_freezes_population_crs_grid_origin_and_sizes():
    protocol = _json(PROTOCOL)
    receipt = _json(RECEIPT)
    assert protocol["status"] == "FROZEN_PRE_ORIGINAL_POINT_TRANSFORM"
    assert receipt["protocol_commit_before_point_transform"] == (
        "fa92cedd60378e48b477aa8b022d20d635c07423"
    )
    assert protocol["input"]["sha256"] == receipt["source_sha256"] == ns["SOURCE_SHA256"]
    assert protocol["input"]["size_bytes"] == ns["SOURCE_SIZE"] == 1539661
    assert protocol["input"]["candidate_A"] == "EPSG:5070"
    assert protocol["input"]["candidate_B"] == "EPSG:5071"
    assert tuple(protocol["input"]["grid_origin_in_reference_meters"]) == ns["GRID_ORIGIN"]
    assert tuple(protocol["sensitivity"]["grid_size_m"]) == ns["GRID_SIZES"]
    assert ns["_check_protocol"]()["schema"] == protocol["schema"]


def test_source_sensitivity_quantiles_are_finite_and_correctly_ordered():
    result = _json(RECEIPT)
    for field in ("WGS84_geodesic_displacement_m", "planar_3857_displacement_m"):
        vals = result[field]
        assert 0 < vals["minimum"] <= vals["median"] <= vals["p95"] <= vals["p99"] <= vals["maximum"]
    assert result["sparse_points"] == 28953
    assert result["WGS84_geodesic_displacement_m"]["median"] == pytest.approx(1.155895)
    assert result["WGS84_geodesic_displacement_m"]["maximum"] == pytest.approx(1.200898)
    assert result["planar_3857_displacement_m"]["median"] == pytest.approx(1.541077)


def test_aggregate_grid_cell_changes_reconcile_with_fixed_denominator():
    result = _json(RECEIPT)
    rows = result["fixed_grid_agreement"]
    assert [row["grid_width_m"] for row in rows] == [100, 250, 500, 1000, 5000]
    assert [row["different_cell_count"] for row in rows] == [602, 233, 114, 62, 8]
    for row in rows:
        assert row["same_cell_count"] + row["different_cell_count"] == 28953
        assert row["same_cell_fraction"] == pytest.approx(row["same_cell_count"] / 28953)


def test_pure_grid_helper_uses_one_frozen_origin_and_cell_boundary():
    origin = np.asarray(ns["GRID_ORIGIN"])
    a = origin + np.asarray([[10.0, 10.0], [99.5, 20.0], [-1.0, -1.0]])
    b = origin + np.asarray([[10.2, 10.1], [100.2, 20.0], [-1.2, -1.0]])
    results = ns["_same_grid_counts"](a, b)
    assert results[0]["grid_width_m"] == 100
    assert results[0]["same_cell_count"] == 2
    assert results[0]["different_cell_count"] == 1
    assert all(row["same_cell_count"] == 3 for row in results[1:])


def test_quantile_helper_rejects_nonfinite_and_handles_simple_vector():
    assert ns["_quantiles"](np.asarray([0., 1., 2.])) == {
        "minimum": 0.0, "median": 1.0, "p95": 1.9, "p99": 1.98, "maximum": 2.0
    }
    with pytest.raises(ValueError, match="finite"):
        ns["_quantiles"](np.asarray([0., np.nan]))
    with pytest.raises(ValueError, match="matching"):
        ns["_same_grid_counts"](np.zeros((4, 2)), np.zeros((5, 2)))


def test_missing_best_grid_never_promoted_to_exact_author_datum():
    r = _json(RECEIPT)
    p = _json(PROTOCOL)
    assert r["status"] == "CONDITIONAL_OFFLINE_BALLPARK__BEST_DATUM_GRID_UNAVAILABLE"
    assert r["PROJ_network_enabled"] is False
    assert r["best_available_datum_operation"] is False
    assert r["available_operation_count"] == 1
    assert r["unavailable_operation_count"] >= 1
    assert r["missing_grid_names_first_10"]
    assert "Ballpark" in r["available_datum_operation_description"][0]["description"]
    assert r["author_intended_CRS_verified"] is False
    assert r["source_CRS_STOP_unchanged"] is True
    assert p["transformation_policy"]["grid_downloads_allowed"] is False


def test_exact_source_sha_and_sealed_dense_holdout_enforced(tmp_path):
    bogus = tmp_path / "GPS12hrs_Locs.zip"
    bogus.write_bytes(b"not original source")
    with pytest.raises(ValueError, match="exact 12-hour source"):
        ns["_source_points"](bogus)
    receipt = _json(RECEIPT)
    assert receipt["source_sha256_verified"] is True
    assert receipt["dense_2hour_GPS_opened"] is False
    assert receipt["DBF_records_opened"] is False
    assert receipt["prediction_scored"] is False
    assert receipt["original_EOG_WF_scored_endpoints_unchanged"] == 3
