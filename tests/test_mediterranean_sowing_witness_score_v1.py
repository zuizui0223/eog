"""Offline, invented seed-count tests. No study outcome data in tests."""
from __future__ import annotations
import importlib.util
from pathlib import Path

import pytest
MODULE=Path(__file__).resolve().parents[1]/"benchmarks"/"mediterranean_sowing_witness_score_v1.py"
spec=importlib.util.spec_from_file_location("seed_witness",MODULE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def record(site,sp,yr,station,arm,germ,status="absent"):
    return {"species":sp,"site":site,"year":yr,"microhabitat":"shrub",
            "station":station,"site_type":status,"treatment":arm,"germ":germ}

def example():
    rows=[]
    for n in range(1,4):
        for j in range(20):
            rows.append(record("patch1","sp1","2023",str(n),"protected",1 if j<15 else 0))
            rows.append(record("patch1","sp1","2023",str(n),"unprotected",1 if j<5 else 0))
    return rows

def test_bounds_positive_certain_and_natural_absence_witness():
    a=mod.analyse(example())
    assert a["n_geographic_sites"]==1
    assert a["n_sown_seed_rows"]==120
    assert a["n_complete_station_pairs"]==3
    x=a["natural_status_summaries"]["absent"]
    assert x["sign_counts"]["positive"]==1
    assert x["units_with_unprotected_germination_witness"]==1
    assert x["units_with_protected_germination_witness"]==1
    assert x["geographic_sites"]==1

def test_missing_germination_broadens_bounds_and_causes_abstention():
    rows=example()
    for r in rows:
        if r["treatment"]=="unprotected":r["germ"]=None
    x=mod.analyse(rows)["natural_status_summaries"]["absent"]
    assert x["sign_counts"]["unresolved"]==1

def test_unpaired_stations_cannot_make_certificates():
    rows=[r for r in example() if r["treatment"]=="protected"]
    a=mod.analyse(rows)
    assert a["n_complete_station_pairs"]==0
    assert a["pair_missingness"]["unmatched_arm"]==3
    assert a["natural_status_summaries"]["absent"]["sign_counts"]["positive"]==0

def test_sign_interval_and_no_unwarranted_zero():
    assert mod.classify(0.04,0.08)=="positive"
    assert mod.classify(-0.09,-0.03)=="negative"
    assert mod.classify(-0.001,0.001)=="operational_zero"
    assert mod.classify(-0.5,0.5)=="unresolved"
    assert mod.classify(0.0,0.05)=="unresolved"

def test_bad_schema_is_stop(tmp_path):
    p=tmp_path/"x.csv"
    p.write_text("species,site,year,station,treatment,germ\nsp,site,2023,1,protected,1\n")
    with pytest.raises(ValueError,match="SCHEMA_STOP_MISSING_HEADERS"):
        mod.parse_rows(p)
    assert mod.outcome({"germ":"NA"}) is None
    with pytest.raises(ValueError,match="SCHEMA_STOP_UNKNOWN_GERMINATION_CODE"):
        mod.outcome({"germ":"definitely"})
