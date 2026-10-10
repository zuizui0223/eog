"""Fabricated-only cases for first-site vs ever-site detection and censoring."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"validation/eog_virtual_world_ecology_synthesis_v1"
sys.path.insert(0,str(ROOT/"scripts"))
from audit_helgeland_pre2015_followup_horizons_v1 import diagnose


def enc(id,day,site,stage):
    return {"ID":id,"date":day,"Island":site,"Location":site+" locality",
            "stage":stage,"Year":"FUTURE_DERIVED","Least_age":"HINDSIGHT"}


def sample():
    return [
        enc("a","2000-01-01","A","nest"),
        enc("a","2000-01-05","A","capt"),
        enc("a","2000-03-01","B","obs"),
        enc("b","2001-05-01","C","nest"),
        enc("b","2001-06-01","D","obs"),
        enc("b","2001-07-01","C","capt"),
        enc("c","2014-12-20","A","nest"),
        enc("c","2014-12-25","B","capt"),
        enc("d","2002-06-01","A","nest"),
        enc("d","2002-06-02","B","nest"),
        enc("d","2002-06-03","B","obs"),
        enc("e","2003-02-01","A","nest"),
        enc("e","2003-02-02","A","capt"),
        enc("f","2004-01-01","A","nest"),
        enc("g","2005-05-01","A","nest"),
        enc("g","2005-05-05","A","capt"),
        enc("g","2005-05-05","B","obs"),
    ]


def policy(rows):
    p=copy.deepcopy(json.loads(
        (BASE/"helgeland_pre2015_followup_horizon_protocol_v1.json").read_text()))
    b=p["known_pr642"]
    b.update(whole_file_rows_date_checked=len(rows),
             eligible_pre2015_rows=len(rows),
             suppressed_post2014_rows=0,suppressed_pre1994_rows=0,
             unique_nest_site_id_count=6,ambiguous_nest_site_id_count=1,
             first_later_direct_observed_id_count=5,
             first_followup_same_site_id_count=2,
             first_followup_different_site_id_count=2,
             first_followup_ambiguous_site_id_count=1)
    return p


def test_first_same_can_hide_later_change_and_return_to_source():
    x=diagnose(sample(),policy(sample()))
    c=x["counts"]
    assert c["first_followup_same_site_id_count"]==2
    assert c["first_followup_different_site_id_count"]==2
    assert c["first_followup_ambiguous_site_id_count"]==1
    assert c["any_later_different_site_id_count"]==4
    assert c["first_same_then_later_different_site_id_count"]==1
    assert c["first_different_then_later_source_site_id_count"]==1
    assert c["first_followup_same_never_observed_different_later_count"]==1
    assert x["independent_ecological_score_authorized"] is False
    assert "a locality" not in json.dumps(x)


def test_full_calendar_30_and_365_day_eligible_windows_are_distinct():
    x=diagnose(sample(),policy(sample()))["counts"]
    assert x["eligible_30d_full_window_nest_id_count"]==5
    assert x["eligible_30d_direct_observed_id_count"]==3
    assert x["eligible_30d_different_site_observed_id_count"]==1
    assert x["eligible_365d_full_window_nest_id_count"]==5
    assert x["eligible_365d_direct_observed_id_count"]==4
    assert x["eligible_365d_different_site_observed_id_count"]==3


def test_post2014_poisoned_future_island_id_and_stage_never_consulted():
    class Poison(dict):
        def __getitem__(self,key):
            if key!="date":
                raise RuntimeError("Future field leaked: "+key)
            return super().__getitem__(key)
    rows=sample()+[Poison(enc("sensitive","2015-01-01","SECRET","obs"))]
    p=policy(rows)
    p["known_pr642"]["eligible_pre2015_rows"]=len(sample())
    p["known_pr642"]["suppressed_post2014_rows"]=1
    r=diagnose(rows,p)
    assert r["counts"]["suppressed_post2014_rows"]==1
    assert r["counts"]["any_later_different_site_id_count"]==4
    assert r["all_2015_2022_id_island_stage_outcomes_masked"] is True


def test_inferred_year_and_age_never_affect_site_result():
    original=sample()
    changed=copy.deepcopy(original)
    for row in changed:
        row["Year"]="REPLACED_WITH_LATE_INFO"
        row["Least_age"]="777"
        row["Least_hatchyear"]="1800"
        row["scriptsex"]="BACKFILLED"
    assert diagnose(original,policy(original))==diagnose(changed,policy(changed))


def test_protocol_or_previous_exposed_count_change_is_rejected():
    p=policy(sample())
    p["known_pr642"]["first_followup_different_site_id_count"]+=1
    with pytest.raises(ValueError,match="first-followup counts changed"):
        diagnose(sample(),p)
    p=policy(sample())
    p["horizons_days"]=[365,730]
    with pytest.raises(ValueError,match="Forbidden"):
        diagnose(sample(),p)


def test_original_contract_retains_exposed_denominators_and_no_heldout_claim():
    p=json.loads((BASE/"helgeland_pre2015_followup_horizon_protocol_v1.json").read_text())
    b=p["known_pr642"]
    assert b["first_followup_same_site_id_count"]==3941
    assert b["first_followup_different_site_id_count"]==223
    assert b["first_later_direct_observed_id_count"]==4164
    assert b["unique_nest_site_id_count"]==10737
    assert p["time_end"]=="2014-12-31"
    assert all(p["stop_flags"].values())
    assert p["status"]=="FROZEN_AFTER_PR642_OUTCOME_EXPOSURE_BEFORE_ALL_LATER_SCAN"


def test_no_overbroad_uses_or_raw_ids_in_report_source():
    src=(ROOT/"scripts/audit_helgeland_pre2015_followup_horizons_v1.py").read_text()
    for forbidden in ('row["Year"]','row["Least_age"]','row["scriptsex"]',
                      "import pandas","read_csv(","urllib.request","requests.get("):
        assert forbidden not in src
    assert src.index('if observed>cutoff:') < src.index('ident=(row["ID"] or "").strip()')
