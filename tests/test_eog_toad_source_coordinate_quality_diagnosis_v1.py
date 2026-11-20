"""Synthetic-only tests for post-STOP toad coordinate-distance QC diagnosis.

No primary H1 rerun. All source IDs, coordinates and dates in these tests
are fabricated and must not be emitted in any real-data aggregate receipt.
"""
from copy import deepcopy
import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from scripts import eog_toad_source_coordinate_quality_diagnosis_v1 as m

P = json.loads(Path("validation/independent_toad_coordinate_diagnosis_v1/protocol_v1.json").read_text(encoding="utf-8"))
ROOT=json.loads(Path("validation/independent_toad_source_anchor_geography_v1/protocol_v1.json").read_text(encoding="utf-8"))


def make_csv(*, wrong_capture_final=True, invalid_distance=False):
    original=deepcopy(ROOT)
    audit=deepcopy(P)
    cols=list(original["source"]["required_columns"])
    f=io.StringIO(newline="")
    wr=csv.DictWriter(f,fieldnames=cols,lineterminator="\n")
    wr.writeheader()
    for i in range(30):
        row={
            "Toad ID":f"synthetic-{i}",
            "Date of capture":"2000-01-01",
            "Date of re-encounter":"2000-01-02",
            "Initial Easting":"0", "Initial Northing":"0",
            "Released Easting":"100", "Released Northing":"0",
            "Final Easting":"20", "Final Northing":"0",
            "Distance release-final (m)":"80",
            "Distance capture-final (m)": (
                "non_numeric" if invalid_distance and i==0
                else "200" if wrong_capture_final else "20"
            ),
        }
        wr.writerow(row)
    for i in range(135):
        wr.writerow({"Toad ID":f"unknown-{i}","Date of re-encounter":""})
    data=f.getvalue().encode("utf-8")
    checksum=hashlib.sha256(data).hexdigest()
    for protocol in (original,audit):
        protocol["source"]["csv_size_bytes"]=len(data)
        protocol["source"]["csv_sha256"]=checksum
    return data,original,audit


def test_original_H1_quality_failure_reproduced_without_any_bio_effect():
    data,orig,audit=make_csv()
    result=m._diagnose(data,orig,audit)
    assert result["status"]=="SOURCE_DISTANCE_QC_DIAGNOSIS_COMPLETED_ORIGINAL_GEO_STOP_RETAINED"
    assert result["parent_H1_status"]=="NOT_SCORED_GEO_UNIT_CONCORDANCE_STOP"
    assert result["row_quality_denominators"]["published_rows"]==165
    assert result["row_quality_denominators"]["published_h1_coordinate_and_recapture_eligible_rows"]==30
    qc=result["frozen_original_distance_concordance"]
    assert qc["Distance release-final (m)"]["fraction_matched"]==1.0
    assert qc["Distance capture-final (m)"]["fraction_matched"]==0.0
    diagnostic=result["fixed_alternative_pair_and_scale_diagnostics"]["Distance capture-final (m)"]["IF"]["1"]
    assert diagnostic["comparisons"]==30
    assert diagnostic["ratio_unsigned_median"]==10.0
    assert result["primary_H1_rescored"] is False
    assert result["biological_effect_computed"] is False
    assert "synthetic-0" not in json.dumps(result)
    assert "2000-01-02" not in json.dumps(result)


def test_prior_stop_not_retrospectively_overturned_if_source_alternatively_matches():
    data,orig,audit=make_csv(wrong_capture_final=False)
    with pytest.raises(m.ScientificStop,match="STOP_REPRODUCED_QUALITY_GATE_CONTRADICTS_FROZEN_PRIMARY_STOP"):
        m._diagnose(data,orig,audit)


def test_invalid_numeric_distance_is_recorded_as_format_failure_not_imputed():
    data,orig,audit=make_csv(invalid_distance=True)
    result=m._diagnose(data,orig,audit)
    assert result["frozen_original_distance_concordance"]["Distance capture-final (m)"]["invalid_original_QC"]==1
    assert result["fixed_alternative_pair_and_scale_diagnostics"]["Distance capture-final (m)"]["IF"]["1"]["comparisons"]==29


def test_source_sha_version_and_count_must_remain_exact():
    data,orig,audit=make_csv()
    audit["source"]["csv_sha256"]="0"*64
    with pytest.raises(m.ScientificStop,match="STOP_REOPENED_QUALITY_SOURCE_IDENTITY_CHANGED"):
        m._diagnose(data,orig,audit)
    data,orig,audit=make_csv()
    with pytest.raises(m.ScientificStop,match="SHA256_OR_SIZE"):
        m._diagnose(data+b"x",orig,audit)


def test_only_predeclared_axes_and_units_are_checked():
    assert P["parent_primary_scientific_stop"]=="STOP_GEO_UNIT_CONCORDANCE"
    assert P["audit_scope"]["allowed_scales_for_exploratory_quality"]==[0.001,1,1000]
    assert P["output"]["primary_H1_rescored"] is False
    assert P["output"]["new_EOG_WF_endpoints"]==0
    assert m._quantile([10,20,30,40],.25)==17.5
    assert m._quantile([],.5) is None
