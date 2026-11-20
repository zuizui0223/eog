"""Frozen toad experimental source anchor: synthetic tests only, never real IDs.

The real study is evaluated once in the dedicated GitHub Actions source run.
Scientific STOP conditions are deliberately not repaired from observed results.
"""
from __future__ import annotations

from copy import deepcopy
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

import pytest
from benchmarks import independent_toad_source_anchor_geography_v1 as m

PROTOCOL = json.loads(Path("validation/independent_toad_source_anchor_geography_v1/protocol_v1.json").read_text(encoding="utf-8"))


def _synthetic_csv(*, two_bad_distances=False, duplicate_first=False, adverse=False):
    header=list(PROTOCOL["source"]["required_columns"])
    out=io.StringIO(newline="")
    writer=csv.DictWriter(out, fieldnames=header,lineterminator="\n")
    writer.writeheader()
    complete=[]
    for i in range(24):
        # Initial I=0, release R=100, recapture F=20 => 80 vs 20m.
        # Alternative F=105 produces 5 vs 105m and negative signed contrast.
        f=105.0 if adverse else 20.0
        drf=abs(100-f);dif=abs(f)
        published=drf+(9 if i in (0,1) else 0) if two_bad_distances else drf
        row={
            "Toad ID":f"synthetic_{i:03d}",
            "Date of capture":"2020-01-01",
            "Date of re-encounter":"2020-01-02",
            "Initial Easting":"0","Initial Northing":"0",
            "Released Easting":"100","Released Northing":"0",
            "Final Easting":str(f),"Final Northing":"0",
            "Distance release-final (m)":str(published),
            "Distance capture-final (m)":str(dif),
        }
        complete.append(row)
        writer.writerow(row)
    n_extra = 141
    if duplicate_first:
        writer.writerow(complete[0])
        n_extra -= 1
    for i in range(n_extra):
        writer.writerow({"Toad ID":f"missing_{i:03d}",
                         "Date of re-encounter":"", "Date of capture":"2020-01-01"})
    content=out.getvalue().encode("utf-8")
    assert len(content.splitlines())==166
    p=deepcopy(PROTOCOL)
    p["source"]["csv_size_bytes"]=len(content)
    p["source"]["csv_sha256"]=hashlib.sha256(content).hexdigest()
    return content,p


def test_first_frozen_protocol_and_no_source_row_export():
    assert PROTOCOL["status"]=="FROZEN_BEFORE_TOAD_EVENT_VALUES_READ"
    assert PROTOCOL["source"]["version_id"]==198534
    assert PROTOCOL["source"]["entire_csv_source_only_rows"]==165
    assert PROTOCOL["inferential_targets"]["thresholds_meters"]==[100,250,500]
    assert PROTOCOL["data_contract"]["min_eligible_individuals_for_directional_summary"]==20


def test_positive_case_grouping_and_all_thresholds():
    data,p=_synthetic_csv()
    z=m._analyze_verified_csv(data,p)
    assert z["status"]=="EXPLORATORY_EXTERNAL_RECAPTURE_SOURCE_ANCHOR_GEOGRAPHY_SCORED"
    assert z["primary_verdict"]=="SUPPORTED_POST_PUBLICATION_CONDITIONAL_GEOGRAPHY"
    assert z["original_row_grain"]["published_rows"]==165
    assert z["category_counts"]["relocated"]["distinct_individuals"]==24
    assert z["category_counts"]["relocated"]["positive_delta_individuals"]==24
    assert z["primary"]["mean_delta_m"]==60.0
    assert z["primary"]["mean_ambiguity_width_m"]==60.0
    assert z["primary"]["mean_source_robust_radius_m"]==80.0
    assert z["primary"]["mean_possible_radius_m"]==20.0
    assert z["radius_thresholds_by_individual_mean_event_distance"][0]["source_robust_valid_individuals"]==24
    assert z["published_distance_concordance"]["Distance release-final (m)"]["geometric_matches"]==24
    assert z["new_EOG_WF_endpoints"]==0
    assert "synthetic_000" not in json.dumps(z)
    assert "2020-01-01" not in json.dumps(z)


def test_adverse_result_retained_without_flip():
    data,p=_synthetic_csv(adverse=True)
    z=m._analyze_verified_csv(data,p)
    assert z["primary_verdict"]=="REFUTED_OR_NOT_SUPPORTED"
    assert z["primary"]["mean_delta_m"]==-100.0
    assert z["category_counts"]["relocated"]["negative_delta_individuals"]==24


def test_byte_identical_duplicate_deduplicates_but_not_individual():
    data,p=_synthetic_csv(duplicate_first=True)
    z=m._analyze_verified_csv(data,p)
    assert z["original_row_grain"]["exact_duplicate_rows_removed"]==1
    assert z["category_counts"]["relocated"]["distinct_individuals"]==24
    assert z["category_counts"]["relocated"]["eligible_event_rows"]==24


def test_publisher_distance_unit_mismatch_fails_not_recalibrated():
    data,p=_synthetic_csv(two_bad_distances=True)
    with pytest.raises(m.ScientificStop,match="STOP_GEO_UNIT_CONCORDANCE"):
        m._analyze_verified_csv(data,p)


def test_unpinned_csv_or_wrong_record_count_fails_before_analysis():
    data,p=_synthetic_csv()
    with pytest.raises(m.ScientificStop,match="SHA256_OR_SIZE"):
        m._as_rows(data+b"CHANGED",p)
    bad=deepcopy(p)
    bad["source"]["entire_csv_source_only_rows"]=166
    with pytest.raises(m.ScientificStop,match="STOP_ORIGINAL_CSV_ROW_GRAIN_OR_ROWCOUNT"):
        m._as_rows(data,bad)


def test_float_input_nan_or_undocumented_sentinel_hard_stops():
    tokens=set(PROTOCOL["data_contract"]["missing_values"])
    assert m._number(" NA ",tokens) is None
    assert m._number("None",tokens) is None
    with pytest.raises(m.ScientificStop,match="STOP_UNDECLARED_NUMERIC_FORMAT"):
        m._number("missing but not declared",tokens)
    with pytest.raises(m.ScientificStop,match="STOP_NONFINITE_NUMERIC_VALUE"):
        m._number("infinity",tokens)


def test_triangle_inequality_and_sham_bounds():
    assert abs(m._distance((0,0),(100,0))-m._distance((0,0),(20,0)))==80
    assert abs(m._distance((0,0),(5,0))-m._distance((0,0),(4,0)))<=5


def test_file_sha_zip_and_original_all_members_pin(monkeypatch):
    src=deepcopy(PROTOCOL)
    raw,p=_synthetic_csv()
    src["source"]["csv_size_bytes"]=p["source"]["csv_size_bytes"]
    src["source"]["csv_sha256"]=p["source"]["csv_sha256"]
    # Mock archived publisher manifest while retaining mandatory exact identities.
    pub=json.loads(m.PUBLISHER_TRANSFER.read_text(encoding="utf-8"))
    toad=next(x for x in pub["sources"] if x["id"]=="toad_jreidini_green_2022")
    expected={x["name"]:x for x in toad["expected"]}
    expected["Jreidini_and_Green_homing_toads_2021.csv"]["size"]=len(raw)
    expected["Jreidini_and_Green_homing_toads_2021.csv"]["sha256"]=hashlib.sha256(raw).hexdigest()
    # The real _verified_member must still match the original publisher manifest:
    # altered synthetic content must STOP, and a forged archive must never be scored.
    archive=io.BytesIO()
    with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("Jreidini_and_Green_homing_toads_2021.csv",raw)
        z.writestr("README_file.rtf",b"placeholder")
    with pytest.raises(m.ScientificStop,match="STOP_ORIGINAL_PUBLISHER_MEMBER_SHA256_OR_SIZE"):
        m._verified_member(archive.getvalue(),src)
