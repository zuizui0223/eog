"""Negative controls for the native site-date×method observation ledger."""
import pytest
from benchmarks import wetland_native_visit_ledger_v1 as m


def fixture():
    dates=[
        ("2024-03-29","89"),
        ("2024-04-27","118"),
    ]
    def row(day,method,frog,toad,n):
        return {
            "site":"alpha","date":dates[day][0],"doy":dates[day][1],
            "method":method,
            "surv":f"alpha:{method}:{dates[day][1]}",
            "frog":str(frog),"toad":str(toad),
            "_source_csv_line":n
        }
    return [
        row(0,"acoustic",0,0,2),
        row(0,"visual",1,0,3),
        row(0,"bottletrap",0,0,4),
        row(0,"bottletrap",0,1,5),
        row(1,"acoustic",0,0,6),
        row(1,"visual",0,0,7),
        row(1,"dipnet",0,0,8)
    ]


def test_missing_method_is_not_false_absence():
    profile,method,days=m.build_cohort(fixture(),{"alpha"},["frog","toad"],"small")
    assert profile["distinct_site_dates"]==2
    assert profile["distinct_site_date_methods"]==6
    assert profile["recorded_positive_site_species_pairs"]==2
    assert profile["daily_union_preserves_every_native_site_species_positive"]
    assert profile["native_site_species_positive_at_single_recorded_date"]==2
    assert profile["source_method_species_status_cell_counts"]=={
        "METHOD_NOT_RECORDED":4,
        "RECORDED_NONDETECTION":10,
        "RECORDED_POSITIVE":2,
    }
    missing=[row for row in method if row["date"]=="2024-04-27" and row["method"]=="bottletrap"]
    assert len(missing)==2
    assert all(x["observation_status"]=="METHOD_NOT_RECORDED" and x["detected"]=="" for x in missing)
    sampled_zeros=[row for row in method if row["date"]=="2024-04-27" and row["method"]=="visual"]
    assert all(x["observation_status"]=="RECORDED_NONDETECTION" and x["detected"]=="0" for x in sampled_zeros)
    assert len(days)==4


def test_bottletrap_same_key_rows_preserved_and_ored():
    profile,method,_=m.build_cohort(fixture(),{"alpha"},["frog","toad"],"small")
    assert len(profile["duplicated_group_keys_not_resolved"])==1
    d=profile["duplicated_group_keys_not_resolved"][0]
    assert d["source_csv_lines"]==[4,5] and d["source_row_count"]==2
    out=[x for x in method if x["method"]=="bottletrap" and x["date"]=="2024-03-29" and x["species"]=="toad"]
    assert len(out)==1
    assert out[0]["source_csv_lines"]=="4;5"
    assert out[0]["positive_source_row_count"]==1
    assert out[0]["observation_status"]=="RECORDED_POSITIVE"
    assert out[0]["detected"]=="1"


def test_invalid_doy_fails_closed():
    records=fixture()
    records[0]["doy"]="90"
    with pytest.raises(ValueError,match="day-of-year"):
        m.build_cohort(records,{"alpha"},["frog","toad"],"small")


def test_composite_key_drift_fails_closed():
    records=fixture()
    records[0]["surv"]="invalid"
    with pytest.raises(ValueError,match="composite"):
        m.build_cohort(records,{"alpha"},["frog","toad"],"small")


def test_source_row_reuse_or_negative_count_fails_closed():
    records=fixture()
    records[1]["_source_csv_line"]=2
    with pytest.raises(ValueError,match="used twice"):
        m.build_cohort(records,{"alpha"},["frog","toad"],"small")
    records=fixture()
    records[1]["frog"]="-1"
    with pytest.raises(ValueError,match="negative native"):
        m.build_cohort(records,{"alpha"},["frog","toad"],"small")


def test_missing_source_site_fails_closed():
    with pytest.raises(ValueError,match="not every source site"):
        m.build_cohort(fixture(),{"alpha","beta"},["frog","toad"],"small")



def test_date_padded_history_preserves_actual_visits_not_pseudo_twenty():
    profile,_,daily=m.build_cohort(fixture(),{"alpha"},["frog","toad"],"small")
    padded,summary=m.make_padded_site_visit_history(profile,daily,["frog","toad"],"small")
    assert summary["within_site_max_recorded_visit_dates"]==2
    assert summary["padded_site_visit_species_cells"]==4
    assert summary["recorded_site_visit_species_cells"]==4
    assert summary["nonexistent_visit_cells_preserved_as_NA"]==0
    assert summary["site_species_positive_union_preserved"]
    assert all(z["visit_status"]=="RECORDED_VISIT_DATE" for z in padded)
    assert [z["recorded_detection"] for z in padded]==["1","1","0","0"]


def test_unvisited_site_ordinal_is_NA_not_zero():
    profile,_,daily=m.build_cohort(fixture(),{"alpha"},["frog","toad"],"small")
    source_day=profile["per_site"]["alpha"]["recorded_visit_dates"]
    profile["per_site"]["beta"]={
        "recorded_visit_dates":[source_day[0]],
        "distinct_recorded_visit_count":1,
        "calendar_span_days":0,
        "native_source_row_count":1
    }
    for sp in ("frog","toad"):
        daily.append({
            "site":"beta","date":source_day[0],"species":sp,"recorded_positive":0
        })
    profile["recorded_positive_site_species_pairs"]=2
    padded,summary=m.make_padded_site_visit_history(profile,daily,["frog","toad"],"small")
    assert summary["padded_site_visit_species_cells"]==8
    assert summary["nonexistent_visit_cells_preserved_as_NA"]==2
    unavailable=[x for x in padded if x["site"]=="beta" and x["within_site_visit_ordinal"]==2]
    assert len(unavailable)==2
    assert all(x["recorded_detection"]=="" and x["visit_status"]=="NO_VISIT_RECORDED" for x in unavailable)
