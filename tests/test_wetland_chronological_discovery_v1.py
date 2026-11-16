"""Synthetic first-day/strict-later positive evidence; never true absence."""
import pytest
from benchmarks import wetland_chronological_discovery_v1 as m


def fixture():
    records=[]
    ids=iter(range(2,100))
    day=(("2024-03-24",84),("2024-03-30",90))
    for name in ("A","B","C","D","E"):
        for step,(stamp,doy) in enumerate(day):
            for method in ("acoustic","visual"):
                positive=(name=="A" and step==0 and method=="visual"
                          or name=="B" and step==1 and method=="visual"
                          or name=="C" and step==1 and method=="visual")
                records.append({
                    "site":name,"date":stamp,"doy":str(doy),"method":method,
                    "surv":f"{name}:{method}:{doy}",
                    "_csv_source_line":str(next(ids)),
                    "frog":str(int(positive))
                })
            extra=(name=="B" and step==0 or name=="D" and step==1)
            if extra:
                method="dipnet" if name=="B" else "bottletrap"
                records.append({
                    "site":name,"date":stamp,"doy":str(doy),"method":method,
                    "surv":f"{name}:{method}:{doy}",
                    "_csv_source_line":str(next(ids)),
                    "frog":"1"
                })
    return records,{name:"intervention" for name in ("A","B","C","D","E")}


def test_five_disjoint_classes_and_overlap_later_av_after_same_day_extra():
    rows,sites=fixture()
    summary, detail, horizon, target=m.reconstruct(rows,sites,["frog"],"toy")
    assert summary["source_full_positive_site_species"]==4
    assert summary["source_AV_positive_site_species"]==3
    assert summary["first_full_date_positive_site_species"]==2
    assert summary["first_AV_date_positive_site_species"]==1
    assert summary["first_full_nonpositive_later_full_positive_site_species"]==2
    # First date AV nondetection -> later AV positive at BOTH B and C.
    assert summary["first_AV_nonpositive_later_AV_positive_site_species"]==2
    assert summary["first_AV_nonpositive_same_day_additional_method_positive"]==1
    assert summary["chronology_categories"]=={
        "av_detected_first":1,
        "same_day_extra_method_only":1,
        "later_AV_first_discovery":1,
        "later_additional_only_discovery":1,
        "never_source_positive":1,
    }
    assert {d["site"]:d["source_chronology_partition"] for d in detail}=={
        "A":"av_detected_first","B":"same_day_extra_method_only",
        "C":"later_AV_first_discovery","D":"later_additional_only_discovery",
        "E":"never_source_positive"
    }
    assert summary["horizon_first_later_positive_counts"]["7"]["first_full_nonpositive_later_full_positive_by_horizon"]==2
    assert len(detail)==5 and len(horizon)==35 and target==[]


def test_earliest_date_then_later_positive_not_real_false_negative():
    rows,sites=fixture()
    summary, detail,_,_=m.reconstruct(rows,sites,["frog"],"toy")
    later=next(d for d in detail if d["site"]=="C")
    assert later["first_date_full_positive"]==0
    assert later["full_first_positive_lag_days"]==6
    assert later["full_first_positive_recorded_date"]=="2024-03-30"
    assert later["first_full_nonpositive_but_later_full_positive"]==1
    assert summary["first_recorded_date_zero_is_NOT_a_true_biological_absence"]
    missing=next(d for d in detail if d["site"]=="E")
    assert missing["never_full_source_positive_is_UNKNOWN_not_absence"]==1
    assert missing["full_first_positive_recorded_date"]==""


def test_duplicate_or_missing_av_grouping_fails_closed():
    rows,sites=fixture()
    bad=[r for r in rows if not(
        r["site"]=="A" and r["date"]=="2024-03-24"
        and r["method"]=="visual"
    )]
    with pytest.raises(ValueError,match="complete AV"):
        m.reconstruct(bad,sites,["frog"],"toy")
    extra=dict(rows[0],_csv_source_line="98")
    with pytest.raises(ValueError,match="complete AV"):
        m.reconstruct(rows+[extra],sites,["frog"],"toy")


def test_malformed_or_reused_record_or_negative_count_blocked():
    rows,sites=fixture()
    bad=[dict(r) for r in rows]
    bad[0]["doy"]="999"
    with pytest.raises(ValueError,match="day-of-year"):
        m.reconstruct(bad,sites,["frog"],"toy")
    bad=[dict(r) for r in rows]
    bad[0]["surv"]="other"
    with pytest.raises(ValueError,match="grouping key"):
        m.reconstruct(bad,sites,["frog"],"toy")
    bad=[dict(r) for r in rows]
    bad[0]["_csv_source_line"]=bad[1]["_csv_source_line"]
    with pytest.raises(ValueError,match="used more than once"):
        m.reconstruct(bad,sites,["frog"],"toy")
    bad=[dict(r) for r in rows]
    bad[0]["frog"]="-1"
    with pytest.raises(ValueError,match="negative species"):
        m.reconstruct(bad,sites,["frog"],"toy")


def test_no_empty_site_and_no_duplicate_taxon_columns():
    rows,sites=fixture()
    with pytest.raises(ValueError,match="incomplete"):
        m.reconstruct(rows,{**sites,"F":"intervention"},["frog"],"toy")
    with pytest.raises(ValueError,match="duplicate"):
        m.reconstruct(rows,sites,["frog","frog"],"toy")
    with pytest.raises(ValueError,match="empty"):
        m.reconstruct([],sites,["frog"],"toy")


def test_doy_second_visit_is_original_six_calendar_days_not_six_independent_traps():
    rows,sites=fixture()
    _,detail,_,_=m.reconstruct(rows,sites,["frog"],"toy")
    d=next(z for z in detail if z["site"]=="D")
    assert d["original_recorded_site_dates"]==2
    assert d["full_first_positive_lag_days"]==6
    assert d["earliest_positive_source_methods"]=="bottletrap"
    assert d["all_positive_recorded_methods"]=="bottletrap"
