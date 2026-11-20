"""Synthetic only: frozen nominal treatment strata of a prior toad scientific STOP."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import pytest

from benchmarks import independent_toad_geocoordinate_treatment_qc_v3 as m

P=json.loads(Path("validation/independent_toad_geocoordinate_diagnostic_v3/protocol_v3.json").read_text(encoding="utf-8"))
OLD=json.loads(Path("validation/independent_toad_source_anchor_geography_v1/protocol_v1.json").read_text(encoding="utf-8"))


def case(name, nominal, release=100, final=20, rep_rf=None, rep_cf=None):
    return {
        "Toad ID":name, "Date of re-encounter":"2021-06-01",
        "Translocated distance":str(nominal),
        "Initial Easting":"0", "Initial Northing":"0",
        "Released Easting":str(release), "Released Northing":"0",
        "Final Easting":str(final), "Final Northing":"0",
        "Distance release-final (m)":str(abs(release-final) if rep_rf is None else rep_rf),
        "Distance capture-final (m)":str(abs(final) if rep_cf is None else rep_cf),
    }


def bygroup(x,group):
    return next(row for row in x["categories"] if row["nominal_translocated_distance_m"]==group)


def test_frozen_treatment_roster_not_outcome_reclassification():
    assert P["status"]=="FROZEN_AFTER_EXTERNAL_QC_STOP_BEFORE_GROUP_SCORING"
    assert P["data_source"]["version_id"]==198534
    assert P["user_defined_treatment"]["categories"]==["0","100","250","500","other_or_missing"]
    assert P["data_source"]["prior_unstratified_release_match"]==77
    assert P["data_source"]["prior_unstratified_capture_match"]==163
    assert P["data_heldout_prospective"] is False


def test_qc_strata_preserve_all_rows_and_original_source_stop():
    rows=[
        case("control",0,release=0,final=20),
        case("moved_100",100,release=100,final=20),
        case("moved_250_bad",250,release=250,final=20,rep_rf=800),
        case("unknown",20,release=70,final=10),
    ]
    v=m.stratified_coordinate_quality(rows,P,OLD)
    assert v["source_unique_rows"]==4
    assert v["eligible_complete_coordinate_reencounters"]==4
    assert v["grand_totals"]=={
        "release_final_numeric_rows":4,
        "release_final_matches":3,
        "capture_final_numeric_rows":4,
        "capture_final_matches":4,
    }
    assert bygroup(v,"0")["release_final_matches"]==1
    assert bygroup(v,"0")["zero_class_initial_to_release_le5m"]==1
    assert bygroup(v,"250")["release_final_matches"]==0
    assert bygroup(v,"100")["positive_class_initial_to_release_gt5m"]==1
    assert bygroup(v,"other_or_missing")["all_original_deduplicated_rows"]==1
    assert v["original_stop_overridden"] is False
    assert not v["biological_movement_scored"]
    assert "moved_250_bad" not in json.dumps(v)
    assert "2021-06-01" not in json.dumps(v)


def test_within_control_reported_capture_vs_release_and_missing_count():
    data=[case("control_a",0,release=0,final=20),
          case("control_b",0,release=0,final=20,rep_rf=900),
          case("other_missing","",release=100,final=20)]
    data[2]["Final Easting"]=""
    result=m.stratified_coordinate_quality(data,P,OLD)
    zero=bygroup(result,"0")
    assert zero["all_original_deduplicated_rows"]==2
    assert zero["eligible_reencounters_with_complete_coords"]==2
    assert zero["release_equals_capture_report_matches"]==1
    assert zero["release_final_matches"]==1
    assert zero["capture_final_matches"]==2
    assert bygroup(result,"other_or_missing")["eligible_reencounters_with_complete_coords"]==0
    assert result["eligible_complete_coordinate_reencounters"]==2
    assert zero["release_final_residuals"]["median_absolute_residual_m"] is None


def test_grouped_residual_quantiles_only_when_five_or_more():
    vals=[case(f"record_{i}",100,release=100,final=20,rep_rf=(80+i)) for i in range(6)]
    out=m.stratified_coordinate_quality(vals,P,OLD)
    x=bygroup(out,"100")
    assert x["release_final_comparable"]==6
    assert x["release_final_residuals"]["median_absolute_residual_m"]==2.5
    assert x["release_final_residuals"]["q90_absolute_residual_m"]==4.5
    assert x["capture_final_residuals"]["median_absolute_residual_m"]==0


def test_numeric_bad_treatment_fails_closed_not_silently_binned():
    for raw in ("unexpected","infinity"):
        rows=[case("x",raw)]
        with pytest.raises(ValueError, match="STOP_NOMINAL_TREATMENT_FORMAT"):
            m.stratified_coordinate_quality(rows,P,OLD)
    # The original frozen missing-value contract explicitly includes "nan";
    # it is NOT an invalid numeric and must remain in "other_or_missing".
    missing=m.stratified_coordinate_quality([case("x","nan")],P,OLD)
    assert bygroup(missing,"other_or_missing")["all_original_deduplicated_rows"]==1


def test_other_numeric_value_not_rounded_to_nominal_group():
    rows=[case("a","249.9",release=250),case("b","-100",release=100)]
    out=m.stratified_coordinate_quality(rows,P,OLD)
    assert bygroup(out,"other_or_missing")["all_original_deduplicated_rows"]==2
    assert bygroup(out,"250")["all_original_deduplicated_rows"]==0


def test_group_has_no_original_ids_or_individual_positions():
    rows=[case("sensitive_to_resist_export",500,release=500,final=17)]
    out=m.stratified_coordinate_quality(rows,P,OLD)
    text=json.dumps(out)
    assert "sensitive_to_resist_export" not in text
    assert "2021-06-01" not in text
    assert "original_stop_overridden" in out
    assert out["new_eog_wf_endpoints"]==0
