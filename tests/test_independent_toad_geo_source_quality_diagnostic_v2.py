"""Offline synthetic checks for post-STOP toad coordinate source-QC v2.

Does not read Dryad event rows. Never validates homing/source EOG responses.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from benchmarks import independent_toad_geo_source_quality_diagnostic_v2 as m

P=json.loads(Path("validation/independent_toad_geocoordinate_diagnostic_v2/protocol_v2.json").read_text(encoding="utf-8"))
OLD=json.loads(Path("validation/independent_toad_source_anchor_geography_v1/protocol_v1.json").read_text(encoding="utf-8"))


def source_fixture(*,swap=False,scale=1.0,missing=False):
    rows=[]
    for i in range(24):
        recapture=20.0/scale
        release=100.0/scale
        first=20.0 if swap else 80.0
        second=80.0 if swap else 20.0
        row={
            "Toad ID":f"synthetic_{i:04d}",
            "Date of re-encounter":"2020-01-02",
            "Initial Easting":"0", "Initial Northing":"0",
            "Released Easting":str(release), "Released Northing":"0",
            "Final Easting":str(recapture), "Final Northing":"0",
            "Distance release-final (m)":str(first),
            "Distance capture-final (m)":str(second),
        }
        if missing and i in (2,3):
            row["Final Easting"]=""
        rows.append(row)
    return rows


def row(report,column,pair,scale):
    return next(x for x in report["predeclared_18_comparisons"]
                if x["reported_column"]==column and
                x["geometric_pair"]==pair and
                x["coordinate_multiplier"]==scale)


def test_protocol_original_stop_and_predeclared_18_grid_locked():
    assert P["status"]=="PRE_DIAGNOSTIC_FROZEN_AFTER_ORIGINAL_SCIENTIFIC_STOP"
    assert P["parent_result"]["outcome"]=="STOP_GEO_UNIT_CONCORDANCE"
    assert P["parent_result"]["primary_verdict"]=="NOT_SCORED_SOURCE_QUALITY_STOP"
    assert len(P["comparison_grid"]["coordinate_multipliers"])*len(
        P["comparison_grid"]["candidate_geometric_pairs"])*len(
        P["comparison_grid"]["two_published_columns"])==18
    assert P["output_model_fits"]==0 and P["output_new_eogwf_endpoints"]==0


def test_correct_mapping_unit_scale_one_has_original_concordance():
    z=m.diagnose_clean_rows(source_fixture(),P,OLD)
    assert z["n_diagnostic_comparisons"]==18
    assert not z["original_STOP_GEO_UNIT_CONCORDANCE_reproduced"]
    r=row(z,"Distance release-final (m)","RF",1)
    c=row(z,"Distance capture-final (m)","IF",1)
    assert (r["match_fraction"],c["match_fraction"])==(1.0,1.0)
    assert (r["median_absolute_residual_m"],c["median_absolute_residual_m"])==(0,0)
    assert z["denominator"]["distinct_identity_count"]==24
    assert z["denominator"]["date_and_six_coordinate_values_present"]==24
    assert "synthetic_" not in json.dumps(z)


def test_swapped_publisher_columns_reproduce_original_stop_without_authorizing_correction():
    z=m.diagnose_clean_rows(source_fixture(swap=True),P,OLD)
    assert z["original_STOP_GEO_UNIT_CONCORDANCE_reproduced"]
    assert row(z,"Distance release-final (m)","RF",1)["match_fraction"]==0.0
    assert row(z,"Distance release-final (m)","IF",1)["match_fraction"]==1.0
    assert row(z,"Distance capture-final (m)","RF",1)["match_fraction"]==1.0
    assert z["source_reassignment_or_original_STOP_override"] is False
    assert z["biological_direction_or_homing_estimated"] is False


def test_scaled_publisher_columns_1000_mismatch_guard_not_retuned():
    z=m.diagnose_clean_rows(source_fixture(scale=1000),P,OLD)
    assert z["original_STOP_GEO_UNIT_CONCORDANCE_reproduced"]
    assert row(z,"Distance release-final (m)","RF",1)["match_fraction"]==0
    assert row(z,"Distance release-final (m)","RF",1000)["match_fraction"]==1
    assert row(z,"Distance capture-final (m)","IF",1000)["match_fraction"]==1


def test_missing_coordinates_are_counted_not_repaired():
    z=m.diagnose_clean_rows(source_fixture(missing=True),P,OLD)
    assert z["denominator"]["source_unique_rows"]==24
    assert z["denominator"]["date_and_six_coordinate_values_present"]==22
    assert row(z,"Distance release-final (m)","RF",1)["numeric_compared_rows"]==22
    assert z["denominator"]["with_nonmissing_identity"]==24


def test_one_valid_record_quantile_not_zero():
    rows=source_fixture()[:1]
    z=m.diagnose_clean_rows(rows,P,OLD)
    a=row(z,"Distance capture-final (m)","RF",1)
    assert a["numeric_compared_rows"]==1
    assert a["median_absolute_residual_m"]==60
    assert a["q90_absolute_residual_m"]==60


def test_invalid_test_grid_must_not_change_unit_or_pair_roster():
    for name,override in (
        ("coordinate_multipliers",[0.01,1,100]),
        ("candidate_geometric_pairs",["IF","RF","IR"]),
        ("two_published_columns",["Distance capture-final (m)"])
    ):
        fake=deepcopy(P)
        fake["comparison_grid"][name]=override
        with pytest.raises(ValueError,match="STOP_FROZEN_QC"):
            m.diagnose_clean_rows(source_fixture(),fake,OLD)


def test_no_eligible_rows_is_unestimable_not_success():
    rows=source_fixture(missing=True)
    for x in rows: x["Date of re-encounter"]=""
    z=m.diagnose_clean_rows(rows,P,OLD)
    assert z["denominator"]["date_and_six_coordinate_values_present"]==0
    assert z["original_STOP_GEO_UNIT_CONCORDANCE_reproduced"] is True
    assert all(a["match_fraction"] is None for a in z["predeclared_18_comparisons"])
    assert z["parent_original_science_status"] if "parent_original_science_status" in z else True
