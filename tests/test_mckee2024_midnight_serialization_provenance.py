"""R 4.3 midnight-string mechanism audit on exact McKee sparse source receipts.

These tests only read aggregate JSON and synthetic clock values. They do
not open the raw 12h ZIP, any geographic feature or the dense 2h holdout.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import json
from pathlib import Path
import runpy
import sys

import pytest


ROOT=Path(__file__).resolve().parents[1] / "validation/temporal_corridor_mckee2024"
PATTERN_PROTO=ROOT / "post_stop_midnight_serialization_protocol_v1.json"
PATTERN_RECEIPT=ROOT / "post_stop_midnight_serialization_receipt_v1.json"
H3_PROTO=ROOT / "post_stop_exact_midnight_candidate_cut_protocol_v1.json"
H3_RECEIPT=ROOT / "post_stop_exact_midnight_candidate_cuts_receipt_v1.json"
SCRIPT=ROOT / "replay_post_stop_midnight_serialization.py"
sys.path.insert(0,str(ROOT))
try:
    lib=runpy.run_path(str(SCRIPT))
finally:
    sys.path.remove(str(ROOT))
SHA="556062b7426336a94fe93dd9e6b049dc6c960d3dc8135f7298f465126c6962c4"


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def test_preinspection_provenance_is_frozen_and_source_sha_is_unmodified():
    proto=load(PATTERN_PROTO)
    out=load(PATTERN_RECEIPT)
    assert proto["status"]=="FROZEN_BEFORE_NEW_PHYSICAL_TIMESTAMP_PATTERN_INSPECTION"
    assert out["protocol_committed_before_new_inspection"]=="24bb56e8c62e298d91196e3ac2361d0e2ac93314"
    assert out["source_sha256"]==proto["source"]["sha256"]==lib["SHA256"]==SHA
    assert out["timestamp_shapes"]=={"date_only":10835,"full_datetime":18118,"unexpected":0}
    assert out["original_records"]==28953
    assert out["original_group_count"]==421
    assert lib["_verify"]("patterns")["schema"]==proto["schema"]


def test_exact_midnight_absence_and_nonmidnight_controls_in_original_dbf():
    r=load(PATTERN_RECEIPT)
    assert r["exact_midnight_000000_among_complete_datetime_strings"]==0
    assert r["hour_zero_but_nonmidnight_among_complete_datetime_strings"]==379
    assert r["full_datetime_hour_histogram"]=={"00":379,"01":3193,"12":11489,"13":3057}
    assert r["complete_hour_one_exact_010000"]==3105
    assert r["complete_hour_twelve_exact_120000"]==11037
    assert r["complete_hour_thirteen_exact_130000"]==2958
    assert r["complete_datetime_minute_and_second_both_zero"]==17100
    assert r["complete_datetime_nonzero_minute_or_second"]==1018
    assert r["groups_with_both_date_only_and_complete_datetime"]==277
    assert r["source_exporter_identified_for_exact_Dryad_ZIP"] is False
    assert r["mechanistic_hypothesis_supported_not_proven"] is True
    assert r["prior_T0_full_day_clock_results_are_counterfactual_if_midnight_is_true"] is True


def test_midnight_assumption_does_not_upgrade_to_confirmed_source_truth():
    p=load(H3_PROTO)
    r=load(H3_RECEIPT)
    assert p["status"]=="FROZEN_BEFORE_ANY_NEW_SOURCE_CUT_COMPARISON_FOR_MIDNIGHT_CANDIDATE"
    assert r["pre_access_protocol_commit"]=="04b5992b8e32bad79415c32c9a745e1b1cbdc93a"
    assert p["source"]["sha256"]==r["source_sha256"]==SHA
    assert p["candidate_clock"]["original_export_provenance_confirmed"] is False
    assert r["date_only_as_exact_midnight_only_conditional"] is True
    assert r["R43_exporter_historically_confirmed_for_Dryad"] is False
    assert r["original_source_timestamp_STOP_retained"] is True
    assert r["no_2_hour_reference_opened"] is True
    assert lib["_verify"]("h3")["schema"]==p["schema"]


def test_H3_exact_midnight_cut_masks_compared_with_previous_time_worlds():
    r=load(H3_RECEIPT)
    q=r["per_clock_cut_policy"]
    assert [q["NAIVE_MOUNTAIN_LOCAL"][k]["coherent_cuts"] for k in (
        "T0_FULL_DAY_UNCERTAINTY","T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW",
        "H_R43_EXACT_MIDNIGHT_CANDIDATE"
    )]==[857,858,858]
    assert [q["AMERICA_DENVER_IANA"][k]["coherent_cuts"] for k in (
        "T0_FULL_DAY_UNCERTAINTY","T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW",
        "H_R43_EXACT_MIDNIGHT_CANDIDATE"
    )]==[889,890,959]
    assert q["NAIVE_MOUNTAIN_LOCAL"]["H_R43_EXACT_MIDNIGHT_CANDIDATE"]=={
        "coherent_cuts":858, "pairwise_cuts":858,"additional_coherent_cuts":0
    }
    assert q["AMERICA_DENVER_IANA"]["H_R43_EXACT_MIDNIGHT_CANDIDATE"]=={
        "coherent_cuts":959,"pairwise_cuts":938,"additional_coherent_cuts":21
    }
    a=r["H3_paired_cut_comparisons"]
    assert a["NAIVE_H3_vs_T1"]=={
        "common_cuts":858,"previous_only":0,"H3_only":0,
        "both_retained":27674,"groups_with_any_difference":0
    }
    assert a["IANA_H3_vs_T1"]=={
        "common_cuts":890,"previous_only":0,"H3_only":69,
        "both_retained":27573,"groups_with_any_difference":69
    }
    for v in a.values():
        assert sum(v[k] for k in ("common_cuts","previous_only","H3_only","both_retained"))==28532


def test_synthetic_date_only_is_single_midnight_under_H3_and_fold_is_preserved():
    domain=lib["conditional_H3_domain"]
    E=lib["EPOCH"]
    midnight=datetime(2018,11,4,0,0)
    row=(int((midnight-E).total_seconds()),0,0,"date",0)
    naive=domain(row,"NAIVE_MOUNTAIN_LOCAL")
    mst=domain(row,"FIXED_MST_UTC_MINUS_07")
    denver=domain(row,"AMERICA_DENVER_IANA")
    assert naive==((row[0],row[0]),)
    assert mst==((row[0]+25200,row[0]+25200),)
    assert len(denver)==1
    assert denver[0][0]==denver[0][1]
    repeated=datetime(2018,11,4,1,30)
    timed=(int((repeated-E).total_seconds()),0,0,"full",1)
    folds=domain(timed,"AMERICA_DENVER_IANA")
    assert len(folds)==2
    assert folds[1][0]-folds[0][0]==3600
    assert folds[0][0]==folds[0][1]
    assert folds[1][0]==folds[1][1]


def test_unknown_clock_and_false_GPS_are_rejected_without_export(tmp_path):
    f=lib["conditional_H3_domain"]
    with pytest.raises(ValueError,match="declared local clock"):
        f((0,0,0,"date",0),"Mars/Olympus")
    from replay_post_stop_time_interval_qc import _source_rows
    bad=tmp_path/"GPS12hrs_Locs.zip"
    bad.write_bytes(b"not exact Dryad original")
    with pytest.raises(ValueError,match="filename or byte size"):
        _source_rows(bad)
    out=load(H3_RECEIPT)
    assert out["no_ecological_model_fit_or_score"] is True
    assert out["source_geometries_unread"] is True
    assert out["raw_IDs_points_exact_dates_unpublished"] is True
    assert out["original_source_CRS_stop_retained"] is True
    assert out["original_EOG_WF_frozen_3_31_3"] is True
