"""Exact source method coverage & evidence subset negative controls."""
import pytest
from benchmarks import wetland_paired_method_core_v1 as m


def fixture():
    def row(site,doy,day,method,frog,newt,n):
        return {
            "site":site,"doy":str(doy),"date":day,
            "method":method,"surv":f"{site}:{method}:{doy}",
            "frog":str(frog),"newt":str(newt),"_source_csv_line":n
        }
    return [
        row("A",84,"2024-03-24","acoustic",1,0,2),
        row("A",84,"2024-03-24","visual",0,0,3),
        row("A",84,"2024-03-24","dipnet",0,1,4),
        row("A",90,"2024-03-30","acoustic",0,0,5),
        row("A",90,"2024-03-30","visual",1,0,6),
        row("B",84,"2024-03-24","acoustic",0,0,7),
        row("B",84,"2024-03-24","visual",0,0,8),
        row("B",84,"2024-03-24","bottletrap",0,1,9),
        row("B",84,"2024-03-24","bottletrap",0,0,10),
    ]


def test_exact_complementary_methods_and_aquatic_only_positive():
    v,days,pairs=m.profile("synthetic",fixture(),{"A","B"},["frog","newt"])
    assert v["source_site_dates"]==3
    assert v["paired_method_dates_with_exactly_one_row_each"]==3
    assert v["paired_method_native_rows"]==6
    assert v["native_positive_site_species"]==3
    assert v["paired_core_positive_site_species"]==1
    assert v["native_positive_site_species_unseen_by_paired_core"]==2
    assert v["daily_full_method_positive_site_date_species"]==4
    assert v["daily_paired_core_positive_site_date_species"]==2
    assert v["site_date_groups_without_method_row"]["dipnet"]==2
    assert v["site_date_groups_without_method_row"]["bottletrap"]==2
    assert v["per_species"]["newt"]["paired_core_positive_sites"]==0
    assert v["per_species"]["newt"]["positive_sites_undetected_by_paired_core"]==2
    assert sum(int(x["only_additional_methods_detect_positive"]) for x in pairs)==2
    a=[x for x in days if x["site"]=="A" and x["date"]=="2024-03-24" and x["species"]=="newt"][0]
    assert a["paired_core_positive"]==0
    assert a["full_source_positive"]==1
    assert a["dipnet_row_represented_in_csv"]==1
    b=[x for x in days if x["site"]=="B" and x["species"]=="newt"][0]
    assert b["bottletrap_row_represented_in_csv"]==1
    assert b["full_source_positive"]==1
    assert len(days)==6


def test_missing_acoustic_row_fails_closed():
    values=[x for x in fixture() if x["_source_csv_line"]!=2]
    with pytest.raises(ValueError,match="paired acoustic"):
        m.profile("synthetic",values,{"A","B"},["frog","newt"])


def test_duplicate_visual_row_fails_closed():
    values=fixture()
    values.append(dict(values[1],_source_csv_line=20))
    with pytest.raises(ValueError,match="paired visual"):
        m.profile("synthetic",values,{"A","B"},["frog","newt"])


def test_reused_native_row_fails_closed():
    values=fixture()
    values[1]["_source_csv_line"]=2
    with pytest.raises(ValueError,match="counted twice"):
        m.profile("synthetic",values,{"A","B"},["frog","newt"])


def test_not_same_as_field_effort_and_missing_row_not_deployment():
    values=fixture()
    values=[x for x in values if x["method"]!="dipnet"]
    v,days,_=m.profile("synthetic",values,{"A","B"},["frog","newt"])
    assert v["site_date_groups_without_method_row"]["dipnet"]==3
    assert v["method_row_absence_is_not_field_method_absence"]
    assert v["two_core_methods_same_recorded_coverage_not_equal_effort"]


def test_native_species_and_date_checks_fail_closed():
    v=fixture()
    v[0]["frog"]="-3"
    with pytest.raises(ValueError,match="negative"):
        m.profile("synthetic",v,{"A","B"},["frog","newt"])
    v=fixture()
    v[0]["doy"]="99"
    with pytest.raises(ValueError,match="calendar DOY"):
        m.profile("synthetic",v,{"A","B"},["frog","newt"])
