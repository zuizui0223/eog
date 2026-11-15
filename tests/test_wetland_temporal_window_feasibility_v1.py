"""Native temporal-window feasibility: source-anchored witness and closure guards."""
import pytest
from benchmarks import wetland_temporal_window_feasibility_v1 as m


def native_records():
    def r(site,day,doy,method,frog,toad):
        return {
            "site":site,"date":day,"doy":str(doy),"method":method,
            "surv":f"{site}:{method}:{doy}",
            "frog":str(frog),"toad":str(toad),
        }
    return [
        r("alpha","2024-03-24",84,"visual",1,0),
        r("alpha","2024-03-24",84,"dipnet",0,0),
        r("alpha","2024-03-30",90,"visual",0,0),
        r("alpha","2024-04-20",111,"visual",0,1),
        r("beta","2024-03-24",84,"visual",0,0),
        r("beta","2024-04-20",111,"visual",1,0),
    ]


def pick(profile,horizon,anchor):
    return next(x for x in profile["window_summaries"]
                if x["window_calendar_days"]==horizon and x["anchor"]==anchor)


def test_anchoring_changes_descriptive_evidence_not_native_positive():
    data,detail=m.reconstruct(native_records(),{"alpha","beta"},["frog","toad"],
                               "synthetic",windows=(7,21,91))
    assert data["source_positive_site_species"]==3
    assert data["source_native_date_count"]==5
    first=pick(data,7,"first")
    last=pick(data,7,"last")
    assert first["sites_with_two_or_more_selected_dates"]==1
    assert last["sites_with_two_or_more_selected_dates"]==0
    assert first["source_positive_pairs_retained"]==1
    assert last["source_positive_pairs_retained"]==2
    assert first["source_positive_pairs_not_seen_in_window"]==2
    assert last["source_positive_pairs_not_seen_in_window"]==1
    assert first["paired_first_vs_last_positive_symmetric_difference"]==3
    assert first["paired_first_only_positive_pairs"]==1
    assert first["paired_last_only_positive_pairs"]==2
    assert len(detail)==3*3


def test_max_91_day_window_losslessly_retains_all_native_positives():
    data,detail=m.reconstruct(native_records(),{"alpha","beta"},["frog","toad"],
                               "synthetic",windows=(7,91))
    for anchor in ("first","last"):
        row=pick(data,91,anchor)
        assert row["source_positive_pairs_retained"]==3
        assert row["source_positive_pairs_not_seen_in_window"]==0
        assert row["sites_with_two_or_more_selected_dates"]==2
    assert all(d["first_window_positive_seen"]==1 and
               d["last_window_positive_seen"]==1 for d in detail
               if d["window_calendar_days"]==91)


def test_same_day_method_rows_do_not_add_visit_dates():
    r=native_records()
    r.append(dict(r[0],method="visual",surv="alpha:visual:84",toad="1"))
    x,_=m.reconstruct(r,{"alpha","beta"},["frog","toad"],"synthetic",
                      windows=(7,91))
    assert x["source_native_date_count"]==5
    assert x["source_positive_site_species"]==3
    assert pick(x,7,"first")["sites_with_two_or_more_selected_dates"]==1


def test_invalid_group_or_calendar_doy_fails_closed():
    r=native_records()
    r[0]["doy"]="999"
    with pytest.raises(ValueError,match="date/doy"):
        m.reconstruct(r,{"alpha","beta"},["frog","toad"],"synthetic",windows=(7,))
    r=native_records()
    r[0]["surv"]="invalid"
    with pytest.raises(ValueError,match="composite"):
        m.reconstruct(r,{"alpha","beta"},["frog","toad"],"synthetic",windows=(7,))


def test_window_roster_rejects_duplicate_or_invalid_horizons():
    for horizons in ((7,7),(7,-1),(),(7,"14")):
        with pytest.raises(ValueError):
            m.reconstruct(native_records(),{"alpha","beta"},["frog","toad"],
                          "synthetic",windows=horizons)


def test_missing_source_site_and_invalid_negative_count_fails_closed():
    with pytest.raises(ValueError,match="roster"):
        m.reconstruct(native_records(),{"alpha","beta","gamma"},["frog","toad"],
                      "synthetic",windows=(7,))
    r=native_records()
    r[0]["frog"]="-1"
    with pytest.raises(ValueError,match="negative"):
        m.reconstruct(r,{"alpha","beta"},["frog","toad"],"synthetic",windows=(7,))
