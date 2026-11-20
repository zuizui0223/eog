"""Synthetic source-coordinate sign encoding audit. Original H1 remains scientific STOP."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmarks import independent_toad_release_distance_sign_qc_v4 as m

PROTOCOL=json.loads(Path("validation/independent_toad_geocoordinate_diagnostic_v4/protocol_v4.json").read_text(encoding="utf-8"))
PARENT=json.loads(Path("validation/independent_toad_source_anchor_geography_v1/protocol_v1.json").read_text(encoding="utf-8"))


def record(ident, initial, release, final, signed_reported, distance, trans_dir, move_dir, final_n=0):
    return {
        "Toad ID":ident,
        "Date of re-encounter":"2021-07-01",
        "Initial Easting":str(initial),"Initial Northing":"0",
        "Released Easting":str(release),"Released Northing":"0",
        "Final Easting":str(final),"Final Northing":str(final_n),
        "Translocated distance":str(distance),
        "Translocated direction":trans_dir,
        "Direction moved":move_dir,
        "Distance release-final (m)":str(signed_reported),
        "Distance capture-final (m)":str((final**2+final_n**2)**0.5),
    }


def bygroup(out,group):
    return next(x for x in out["signed_nominal_class_details"] if x["nominal_translocation_signed_class"]==group)


def test_protocol_has_complete_declared_seven_formulas_and_no_H1_repair():
    assert PROTOCOL["status"]=="PRE_SIGNED_FORMULA_TEST_FROZEN_POST_QC_EXPOSURE"
    assert len(PROTOCOL["signed_formulas"]["candidates"])==7
    assert PROTOCOL["immutable_previous_evidence"]["original_scientific_stop"]=="STOP_GEO_UNIT_CONCORDANCE"
    assert PROTOCOL["immutable_previous_evidence"]["release_final_abs_match"]==77
    assert PROTOCOL["immutable_previous_evidence"]["capture_final_abs_match"]==163
    assert PROTOCOL["test_type"].startswith("Post-exposure")


def test_signed_easting_radial_can_restore_signed_source_column_without_H1_scoring():
    rows=[
        record("east_relocated","0",100,20,-80,100,"E","W"),
        record("west_relocated","0",-100,-20,80,-100,"W","E"),
        record("west_control","0",0,-30,-30,0,"NA","W"),
        record("east_control","0",0,30,30,0,"NA","E"),
    ]
    z=m.analyze_source_rows(rows,PROTOCOL,PARENT)
    assert z["original_unsigned_release_final_matches"]==2
    assert z["original_capture_final_matches"]==4
    assert z["signed_metric_comparison"]["signed_easting_east_positive"]["matched"]==4
    assert z["signed_metric_comparison"]["signed_easting_west_positive"]["matched"]==0
    assert z["signed_metric_comparison"]["signed_by_direction_moved_E_positive"]["matched"]==4
    assert bygroup(z,"-100")["source_rows"]==1
    assert bygroup(z,"100")["source_rows"]==1
    assert bygroup(z,"0")["source_rows"]==2
    assert z["original_stop_overridden"] is False
    assert z["original_homing_result_scored"] is False
    assert "east_relocated" not in json.dumps(z)
    assert "west_relocated" not in json.dumps(z)


def test_signed_easting_component_does_not_automatically_equal_signed_radial():
    # dE=3, dN=4, true length=5m. Signed radial is 5m; dE=3m.
    row=record("p",0,0,3,5,0,"NA","E",final_n=4)
    x=m.analyze_source_rows([row],PROTOCOL,PARENT)
    assert x["signed_metric_comparison"]["signed_easting_east_positive"]["matched"]==1
    assert x["signed_metric_comparison"]["signed_easting_component"]["matched"]==1  # 2m tolerance
    assert m._signed_value("signed_easting_east_positive",3,4,5,"E")==5
    assert m._signed_value("signed_easting_component",3,4,5,"E")==3
    assert m._signed_value("signed_by_direction_moved_W_positive",3,4,5,"E")==-5


def test_missing_direction_does_not_drop_geographic_source_row():
    data=[record("p",0,100,20,-80,100,"E","UNKNOWN")]
    out=m.analyze_source_rows(data,PROTOCOL,PARENT)
    assert out["signed_metric_comparison"]["signed_easting_east_positive"]["matched"]==1
    assert out["signed_metric_comparison"]["signed_by_direction_moved_E_positive"]["eligible_formula_rows"]==0
    assert out["source_unique_rows"]==1
    assert bygroup(out,"100")["recorded_movement_direction_counts"]=={"missing_or_other":1}


def test_negative_signed_nominal_class_and_direction_are_kept():
    rows=[record("w",0,-100,-20,80,-100,"W","E"),
          record("e",0,100,20,-80,100,"E","W"),
          record("other",0,-100,-20,80,-99,"W","E")]
    out=m.analyze_source_rows(rows,PROTOCOL,PARENT)
    assert bygroup(out,"-100")["source_rows"]==1
    assert bygroup(out,"100")["source_rows"]==1
    assert bygroup(out,"other_or_missing")["source_rows"]==1
    assert bygroup(out,"-100")["nominal_sign_and_recorded_translocation_direction_counts"]=={"negative|W":1}


def test_source_values_are_never_reclassified_from_bad_text():
    row=record("x",0,100,20,-80,"nonsense","E","W")
    with pytest.raises(ValueError,match="STOP_UNDECLARED_NUMBER"):
        m.analyze_source_rows([row],PROTOCOL,PARENT)


def test_parent_post_stop_provenance_unmodifiable():
    data=[record("control",0,0,-5,-5,0,"NA","W")]
    z=m.analyze_source_rows(data,PROTOCOL,PARENT)
    assert z["source_record_scope"].startswith("same full original")
    assert z["new_EOG_WF_endpoints"]==0
    assert z["natural_founder_or_movement_inferred"] is False
    assert z["original_scientific_stop"]=="STOP_GEO_UNIT_CONCORDANCE"
    assert "2021-07-01" not in json.dumps(z)
