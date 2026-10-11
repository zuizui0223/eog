"""Invented encounters only: preserve all post-2014 outcome variables unseen."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
sys.path.insert(0, str(ROOT / "scripts"))
from audit_helgeland_pre2015_first_vs_ever_site_switch_v1 import analyze


def row(ident, when, site, stage):
    return {"ID": ident, "date": when, "Island": site, "Location": site+"_local",
            "stage": stage, "Year": "FUTURE_INFERRED", "Least_age": "900",
            "scriptsex": "INFERRED"}


def fabricated():
    return [
        row("a","2000-01-01","A","nest"),
        row("a","2000-02-01","A","capt"),
        row("a","2001-03-01","B","obs"),  # first same, later different
        row("b","2001-01-01","A","nest"),
        row("b","2001-02-01","B","capt"),
        row("b","2001-03-01","A","obs"),  # first different, later same
        row("c","2002-01-01","A","nest"),
        row("c","2002-02-01","B","obs"),  # first different, one day
        row("d","2003-01-01","A","nest"),
        row("d","2003-02-01","A","capt"), # first same, one day
        row("e","2004-01-01","A","nest"),
        row("e","2004-02-01","A","capt"),
        row("e","2004-02-01","B","obs"),  # first date ambiguous, any different
        row("f","2005-01-01","A","nest"), # never followed
        row("g","2006-01-01","A","nest"),
        row("g","2006-01-02","B","nest"), # ambiguous nest source
        row("h","2007-01-01","A","capt"), # no nest
    ]


def policy_for(rows):
    p=json.loads((BASE/"helgeland_pre2015_first_vs_any_switch_contract_v1.json").read_text())
    p["pre_exposed_expected"]={
        "whole_source_rows":len(rows),
        "eligible_pre2015_rows":17,
        "pre1994_date_masked":0,
        "post2014_date_masked":0,
        "unique_nest_source_ids":6,
        "ambiguous_nest_source_ids":1,
        "nest_ids_without_later_direct":1,
        "nest_ids_with_later_direct":5,
        "first_same":2,
        "first_different":2,
        "first_ambiguous":1,
    }
    return p


def test_first_only_understates_ever_observed_different_code():
    rows=fabricated()
    policy=policy_for(rows)
    # Protocol defines 'whole_source_rows' as the prior row-count guard:
    policy["pre_exposed_expected"]["whole_file_rows_date_checked"]=len(rows)
    del policy["pre_exposed_expected"]["whole_source_rows"]
    result=analyze(rows, policy)
    c=result["counts"]
    assert c["nest_ids_with_later_direct"]==5
    assert c["first_same"]==2
    assert c["first_different"]==2
    assert c["first_ambiguous"]==1
    assert c["any_later_different"]==4
    assert c["first_same_then_later_different"]==1
    assert c["first_different_then_later_same"]==1
    assert c["one_followup_day_count"]==3
    assert c["two_or_more_followup_days_count"]==2
    assert c["any_later_different_with_only_one_followup_day"]==2
    assert c["any_later_different_with_two_or_more_followup_days"]==2
    assert c["ever_different_among_first_same_one_followup_day"]==0
    assert c["ever_different_among_first_same_two_or_more_followup_days"]==1
    assert result["biological_natal_dispersal_rate_estimated"] is False
    assert result["future_2015_2022_id_island_stage_inspected"] is False
    assert "a_local" not in json.dumps(result)


def test_post_cutoff_poison_row_never_reads_identity_or_stage():
    class FuturePoison(dict):
        def __getitem__(self, key):
            if key != "date":
                raise RuntimeError("post-cutoff ID/site/stage accessed")
            return super().__getitem__(key)
    rows=fabricated()+[
        FuturePoison(row("a","2015-01-01","B","obs")),
        FuturePoison(row("a","1993-12-31","B","nest")),
    ]
    p=policy_for(rows)
    p["pre_exposed_expected"]["whole_file_rows_date_checked"]=len(rows)
    del p["pre_exposed_expected"]["whole_source_rows"]
    p["pre_exposed_expected"]["post2014_date_masked"]=1
    p["pre_exposed_expected"]["pre1994_date_masked"]=1
    x=analyze(rows,p)
    assert x["counts"]["first_same_then_later_different"]==1
    assert x["counts"]["post2014_date_masked"]==1
    assert x["counts"]["pre1994_date_masked"]==1


def test_retro_Year_Least_age_sex_do_not_influence_observation_metric():
    rows=fabricated()
    p=policy_for(rows)
    p["pre_exposed_expected"]["whole_file_rows_date_checked"]=len(rows)
    del p["pre_exposed_expected"]["whole_source_rows"]
    changed=copy.deepcopy(rows)
    for r in changed:
        r["Year"]="MALFORMED"
        r["Least_age"]="NEGATIVE_HINDSIGHT"
        r["Least_hatchyear"]="3000"
        r["scriptsex"]="RETRO"
    assert analyze(rows,p)==analyze(changed,p)


def test_unfrozen_denominators_cannot_be_changed():
    rows=fabricated()
    p=policy_for(rows)
    p["pre_exposed_expected"]["whole_file_rows_date_checked"]=len(rows)
    del p["pre_exposed_expected"]["whole_source_rows"]
    p["pre_exposed_expected"]["first_different"]=999
    with pytest.raises(ValueError,match="denominator changed"):
        analyze(rows,p)


def test_future_hindsight_scientific_claim_cannot_be_enabled():
    rows=fabricated()
    p=policy_for(rows)
    p["pre_exposed_expected"]["whole_file_rows_date_checked"]=len(rows)
    del p["pre_exposed_expected"]["whole_source_rows"]
    p["scientific_bounds"]["no_independent_heldout_ecological_model_score"]=False
    with pytest.raises(ValueError, match="scientific claim"):
        analyze(rows,p)


def test_real_original_exposure_and_source_identity_are_explicit():
    p=json.loads((BASE/"helgeland_pre2015_first_vs_any_switch_contract_v1.json").read_text())
    assert p["status"]=="FROZEN_AFTER_FIRST_FOLLOWUP_223_EXPOSED__BEFORE_ANY_LATER_SWITCH_INSPECTION"
    assert p["pre_exposed_expected"]["first_different"]==223
    assert p["pre_exposed_expected"]["nest_ids_with_later_direct"]==4164
    assert p["pre_exposed_expected"]["whole_source_rows"]==73593
    assert p["cutoff"]["max"]=="2014-12-31"
    source=(ROOT/"scripts/audit_helgeland_pre2015_first_vs_ever_site_switch_v1.py").read_text()
    assert source.index('stamp = strict_observed_date(row["date"])') < source.index('ident = (row["ID"] or "").strip()')
    for banned in ('row["Year"]','row["Least_age"]','row["scriptsex"]',
                   'read_csv(', 'import pandas', 'urllib'):
        assert banned not in source
