"""Original-record date×method cross-witnesss from distinct source rows."""
import pytest

from benchmarks import wetland_joint_method_calendar_gate_v1 as m


def original_synthetic_rows():
    raw=[]
    def add(site,dt,doy,method,frog,newt):
        raw.append({
            "site":site,"date":dt,"doy":str(doy),
            "method":method,"surv":f"{site}:{method}:{doy}",
            "frog":str(frog),"newt":str(newt),
            "_original_csv_line":str(len(raw)+2)
        })
    # A/frog: dipnet positive at first date, AV positive 17 days later.
    # Marginal F(first14) and AV(all) are BOTH positive, joint AV(first14)
    # is negative: proof that site×taxon aggregated masks cannot be intersected.
    add("A","2024-03-24",84,"acoustic",0,0)
    add("A","2024-03-24",84,"visual",0,0)
    add("A","2024-03-24",84,"dipnet",1,1)
    add("A","2024-04-10",101,"acoustic",0,0)
    add("A","2024-04-10",101,"visual",1,0)
    # B/newt: AV first only; B/frog: later bottletrap only.
    add("B","2024-03-24",84,"acoustic",0,0)
    add("B","2024-03-24",84,"visual",0,1)
    add("B","2024-04-10",101,"acoustic",0,0)
    add("B","2024-04-10",101,"visual",0,0)
    add("B","2024-04-10",101,"bottletrap",1,0)
    return raw


def win(out,anchor,h):
    return next(x for x in out["windows"]
                if x["anchor"]==anchor and x["horizon_calendar_days"]==h)


def test_all_five_disjoint_witness_classes_with_crossed_source_rows(monkeypatch):
    monkeypatch.setitem(m.EXPECTED_COHORTS,"toy",(2,10,4,4,2))
    result=m.cohort_result(
        original_synthetic_rows(),{"A":"intervention","B":"control"},
        ["frog","newt"],"toy"
    )
    assert len(result["windows"])==14
    assert len(result["positive_pair_window_detail"])==4*14
    first=win(result,"first",14)
    assert first["native_full_all_dates_positive_pairs"]==4
    assert first["native_AV_all_dates_positive_pairs"]==2
    assert first["native_full_window_positive_pairs"]==3
    assert first["native_AV_window_positive_pairs"]==1
    assert first["class_joint_survives"]==1
    assert first["class_method_only_marginal"]==1
    assert first["class_time_only_marginal"]==0
    assert first["class_split_witness_interaction"]==1
    assert first["class_excluded_by_either_gate_alone"]==1
    assert first["full_source_positive_lost_by_joint_gate"]==3
    first_split=next(x for x in result["positive_pair_window_detail"]
                     if x["anchor"]=="first" and x["horizon_days"]==14 and
                     x["site"]=="A" and x["species"]=="frog")
    assert first_split["witness_class"]=="split_witness_interaction"
    assert first_split["in_window_source_positive_methods"]=="dipnet"
    assert first_split["AV_source_positive_outside_window_dates"]=="2024-04-10"
    assert first_split["additional_method_source_positive_inside_window_dates"]=="2024-03-24"
    assert first_split["in_window_original_positive_source_lines"]=="4"
    assert first_split["AV_source_positive_outside_window_source_lines"]=="6"
    assert first_split["split_witness_requires_distinct_original_rows"]==1

    late=win(result,"last",14)
    assert late["native_full_window_positive_pairs"]==2
    assert late["native_AV_window_positive_pairs"]==1
    assert late["class_joint_survives"]==1
    assert late["class_method_only_marginal"]==1
    assert late["class_time_only_marginal"]==1
    assert late["class_split_witness_interaction"]==0
    assert late["class_excluded_by_either_gate_alone"]==1
    for anchor in m.ANCHORS:
        full=win(result,anchor,91)
        assert full["native_full_window_positive_pairs"]==4
        assert full["native_AV_window_positive_pairs"]==2
        assert full["class_split_witness_interaction"]==0


def test_impossible_joint_source_witness_flags_rejected():
    with pytest.raises(ValueError,match="cannot exist"):
        m.class_of(False,True,True)
    with pytest.raises(ValueError,match="cannot exist"):
        m.class_of(True,False,True)
    with pytest.raises(ValueError,match="booleans"):
        m.class_of(1,True,False)


@pytest.mark.parametrize("flags,expected",[
    ((True,True,True),"joint_survives"),
    ((True,False,False),"method_only_marginal"),
    ((False,True,False),"time_only_marginal"),
    ((True,True,False),"split_witness_interaction"),
    ((False,False,False),"excluded_by_either_gate_alone"),
])
def test_source_witness_classification_disjoint(flags,expected):
    assert m.class_of(*flags)==expected


def test_bad_source_date_row_missing_core_and_duplicate_line_fail_closed(monkeypatch):
    monkeypatch.setitem(m.EXPECTED_COHORTS,"toy",(2,10,4,4,2))
    rows=original_synthetic_rows()
    bad=[x for x in rows if not (
        x["site"]=="A" and x["date"]=="2024-03-24" and
        x["method"]=="visual"
    )]
    with pytest.raises(ValueError,match="one original acoustic"):
        m.cohort_result(bad,{"A":"intervention","B":"control"},["frog","newt"],"toy")
    bad=[dict(x) for x in rows]
    bad[1]["_original_csv_line"]=bad[0]["_original_csv_line"]
    with pytest.raises(ValueError,match="row reused"):
        m.cohort_result(bad,{"A":"intervention","B":"control"},["frog","newt"],"toy")
    bad=[dict(x) for x in rows]
    bad[0]["doy"]="900"
    with pytest.raises(ValueError,match="calendar date"):
        m.cohort_result(bad,{"A":"intervention","B":"control"},["frog","newt"],"toy")


def test_exact_integer_positive_fraction_contrast_not_biology():
    result=m.signed_contrast({("A","frog")},{
        "A":"intervention","B":"control"
    },"frog","intervention","control")
    assert result["direction"]==1
    assert result["numerator"]==1
    assert result["percentage_points"]==100
    result=m.signed_contrast(set(),{"A":"intervention","B":"control"},
                             "frog","intervention","control")
    assert result["direction"]==0
    assert result["percentage_points"]==0
