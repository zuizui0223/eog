"""Regression guards for McKee 2024 sparse 12h source-QC STOP receipts.

This is NOT rerunning the published GPS payload; the verified original ZIP
is deliberately absent from GitHub. These checks keep the predeclared stage
lineage, exact QC denominators, and all source/holdout limits immutable.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "validation/temporal_corridor_mckee2024"
SOURCE_SHA = "556062b7426336a94fe93dd9e6b049dc6c960d3dc8135f7298f465126c6962c4"


def _load(filename):
    return json.loads((ROOT / filename).read_text(encoding="utf-8"))


def test_physical_source_identity_and_exact_frozen_prefix():
    gate0 = _load("gate0_publisher_metadata_frozen_v1.json")
    stage1 = _load("gate1_sparse_zip_schema_receipt_v1.json")
    assert gate0["publisher_version_id"] == 305836
    ref = next(row for row in gate0["files"] if row["file_id"] == 3334125)
    assert ref["publisher_declared_sha256"] == SOURCE_SHA
    assert ref["size_bytes"] == 1539661
    assert stage1["source_sha256"] == SOURCE_SHA
    assert stage1["sha256_matches_prior_publisher_declaration"] is True
    assert stage1["protocol_commit"] == "5030137ae5f6af0caf232d8ad4271594b8f29f0d"
    assert stage1["source_record_values_read"] is False
    assert stage1["dense_2h_holdout_opened"] is False


def test_schema_observed_physical_fields_and_count_consistency():
    row = _load("gate1_sparse_zip_schema_receipt_v1.json")
    assert [x["name"] for x in row["dbf_header"]["fields"]] == [
        "State", "Herd", "SpcsCmm", "SpcsScn", "AID",
        "SeasnYr", "Season", "Year", "Timstmp", "UTM_E", "UTM_N",
    ]
    assert row["dbf_header"]["record_count_declared"] == 28953
    assert row["shx_header"]["index_entry_count"] == 28953
    assert row["dbf_vs_shx_count_matches"] is True
    assert row["projection"]["epsg"] == 3742
    assert row["status"] == "STRUCTURE_CRS_COUNT_PASS__EXPECTED_COLUMN_ALIAS_REVIEW_REQUIRED"


def test_original_sparse_qc_failure_never_reclassified():
    protocol = _load("gate2_sparse_only_aggregate_qc_protocol_v1.json")
    receipt = _load("gate2_sparse_only_aggregate_qc_receipt_v1.json")
    assert protocol["status"] == "FROZEN_BEFORE_ANY_SPARSE_DBF_RECORD_VALUES_READ"
    assert receipt["status"] == "STOP_TIME_PARSE_COVERAGE_AND_UTM_E_SEMANTICS_UNRESOLVED"
    assert receipt["stage2_frozen_protocol_commit"] == "c5a26e202f83a09ad8af8360603c9422236ffe6d"
    assert receipt["dbf_records"] == receipt["active_records"] == 28953
    assert receipt["deleted_records"] == 0
    assert sum(receipt["herd_fix_counts"].values()) == receipt["active_records"]
    assert sum(receipt["species_common_fix_counts"].values()) == receipt["active_records"]
    assert receipt["timestamp_format_counts"]["%Y-%m-%d %H:%M:%S"] == 18118
    assert receipt["timestamp_format_counts"]["unparseable_or_missing"] == 10835
    assert receipt["parseable_fraction"] < 0.95
    assert receipt["coordinate_qc"]["UTM_E_outside_0_to_1000000"] == 28953
    assert receipt["dense_2hr_holdout_read"] is False
    assert receipt["ecological_prediction_scored"] is False


def test_poststop_format_diagnosis_is_not_a_retune():
    row = _load("post_stop_field_diagnostic_receipt_v1.json")
    assert row["record_count"] == 28953
    assert row["time_string_shape_counts"] == {
        "YYYY-MM-DD HH:MM:SS": 18118,
        "YYYY-MM-DD": 10835,
    }
    assert row["attribute_easting"]["all_negative_records"] == 28953
    assert row["original_gate2_STOP_retained"] is True
    assert row["individual_timestamps_exported"] is False
    assert row["dense_2hr_holdout_opened"] is False


def test_midnight_hypothesis_beats_noon_but_remains_conditional():
    p = _load("post_stop_semantics_hypotheses_v1.json")
    r = _load("post_stop_semantics_hypothesis_receipt_v1.json")
    assert p["status"] == "FROZEN_BEFORE_ALTERNATIVE_TIME_OR_CRS_DIAGNOSTICS"
    assert r["protocol_commit"] == "3e9ed35101b4cafe5ac31d87f949ae4796df02c3"
    assert sum(r["full_timestamp_hour_histogram"].values()) == 18118
    assert sorted(r["full_timestamp_hour_histogram"]) == ["00", "01", "12", "13"]
    assert r["date_only_records"] == 10835
    midnight = r["date_only_midnight_hypothetical"]
    noon = r["date_only_noon_negative_control"]
    assert midnight["gaps"] == noon["gaps"] == 28532
    assert midnight["gaps_10_to_14h"] == 27678
    assert noon["gaps_10_to_14h"] == 6334
    assert midnight["fraction_10_to_14h"] > 0.95
    assert noon["fraction_10_to_14h"] < 0.25
    assert noon["duplicate_timestamp_pairs"] == 10421
    assert r["date_only_interpretation_approved"] is False


def test_crs_evidence_retains_source_wkt_conflict_and_per_world_counts():
    p = _load("post_stop_crs_geometry_protocol_v1.json")
    r = _load("post_stop_crs_geometry_receipt_v1.json")
    assert p["status"] == "FROZEN_BEFORE_READING_SHP_POINT_RECORDS"
    assert r["protocol_commit"] == "f5ed446e1a5f39843bec4f7a4a396c3eb4136f6d"
    assert r["records_evaluated"] == 28953
    assert r["SHAPE_DBF_xy_consistency"]["matching_points"] == 28953
    by_crs = {row["crs"]: row for row in r["candidate_crs_evaluations"]}
    assert set(by_crs) == {"EPSG:3742", "EPSG:5070", "ESRI:102003", "EPSG:3857"}
    assert by_crs["EPSG:3742"]["within_region"] == 0
    assert by_crs["EPSG:5070"]["within_region"] == 28953
    assert r["EPSG5070_automatically_accepted"] is False
    assert r["publisher_PRJ_overwritten"] is False
    assert r["dense_2hour_holdout_opened"] is False


def test_all_stages_keep_prediction_and_dense_holdout_sealed():
    rows = [
        _load("gate1_sparse_zip_schema_receipt_v1.json"),
        _load("gate2_sparse_only_aggregate_qc_receipt_v1.json"),
        _load("post_stop_field_diagnostic_receipt_v1.json"),
        _load("post_stop_semantics_hypothesis_receipt_v1.json"),
        _load("post_stop_crs_geometry_receipt_v1.json"),
    ]
    assert all("source_sha256" in row for row in rows)
    assert all(
        row.get("ecological_scores_computed", row.get("ecological_prediction_scored", row.get("biological_prediction_scored"))) is False
        for row in rows
    )
    assert rows[-1]["EOG_WF_3_31_3_unchanged"] is True
