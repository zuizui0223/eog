"""No real bird observations; synthetic encounter regression and future mask tests."""
from __future__ import annotations

import copy
from datetime import date
import json
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"validation/eog_virtual_world_ecology_synthesis_v1"
sys.path.insert(0,str(ROOT/"scripts"))
from audit_helgeland_pre2015_later_site_switch_observability_v1 import inspect, PROTOCOL, reconcile_exposed_followup_counts, group_later


def rec(i,when,site,stage="capt"):
    return {"ID":i,"date":when,"Island":site,"Location":"synthetic locality",
            "stage":stage,"Year":"9999","Least_age":"hindsight","scriptsex":"hindsight"}


def sample():
    return [
        rec("a","2001-05-01","A","nest"),
        rec("a","2001-05-10","A"), # first same
        rec("a","2001-05-20","B"), # hidden later changed, lag=10
        rec("b","2001-05-01","A","nest"),
        rec("b","2001-05-10","B"), # first changed
        rec("b","2002-05-20","A","obs"), # later return to nest
        rec("c","2001-05-01","A","nest"),
        rec("c","2001-05-10","A"), # first same no later
        rec("d","2001-05-01","A","nest"),
        rec("d","2001-05-10","A"),
        rec("d","2001-06-01","B"),
        rec("d","2001-06-01","C"), # ambiguous later, no unambiguous switch
        rec("e","2001-05-01","A","nest"), # no direct followup
        rec("f","2001-05-01","A","nest"),
        rec("f","2001-05-01","B","nest"), # ambiguous nest codes
        rec("g","2001-05-01","A","nest"),
        rec("g","2001-05-10","B"),
        rec("g","2001-09-01","B"), # no return
    ]


def fixture(records=None):
    records = sample() if records is None else records
    policy=json.loads(PROTOCOL.read_text(encoding="utf-8"))
    # The real immutable protocol keeps 73593 and 4164; synthetic fixtures
    # intentionally alter only expected counts through local copy in memory.
    policy["known_prior_counts"]={
        "total_rows":len(records),"window_rows":len(records),
        "prewindow":0,"postwindow":0,"nest_ids_unique":6,
        "first_direct_followup_ids":5,"first_same":3,
        "first_different":2,"first_ambiguous":0,"no_followup":1,
    }
    return records,policy


def test_hidden_later_changes_returns_and_ambiguous_later_records():
    rows,policy=fixture()
    result=inspect(rows,policy)
    c=result["counts"]
    assert c["first_same_with_additional_date"]==2
    assert c["first_same_no_additional_date"]==1
    assert c["first_same_later_different"]==1
    assert c["first_same_later_no_different"]==1
    assert c["first_same_later_ambiguous_only"]==1
    assert c["first_changed_later_return"]==1
    assert c["first_changed_later_no_return"]==1
    assert c["first_changed_later_ambiguous_only"]==0
    assert c["lag_1_to_30_days"]==1
    assert c["lag_31_to_365_days"]==0
    assert c["lag_gt365_days"]==0
    assert result["post2014_id_island_stage_inspected"] is False
    assert result["site_code_changed_means_natal_adult_dispersal"] is False
    assert "synthetic locality" not in json.dumps(result)


def test_date_boundary_shields_future_poisoned_ID_and_site():
    rows,policy=fixture()
    class FuturePoison(dict):
        def __getitem__(self,key):
            if key!="date":
                raise AssertionError("Future source row field was accessed: "+key)
            return super().__getitem__(key)
    shielded=rows+[FuturePoison(rec("secret","2020-03-01","FUTURE","obs")),
                   FuturePoison(rec("secret","1993-12-30","HISTORIC","obs"))]
    contract=copy.deepcopy(policy)
    contract["known_prior_counts"]["total_rows"]+=2
    contract["known_prior_counts"]["postwindow"]+=1
    contract["known_prior_counts"]["prewindow"]+=1
    actual=inspect(shielded,contract)
    expected=inspect(rows,policy)
    assert actual["counts"]==expected["counts"]
    assert actual["post2014_id_island_stage_inspected"] is False


def test_source_date_year_or_age_hindsight_does_not_change_outcome():
    rows,policy=fixture()
    mutated=copy.deepcopy(rows)
    for r in mutated:
        r["Year"]="bad future value"
        r["Least_age"]="future"
        r["Least_hatchyear"]="2025"
        r["scriptsex"]="another later estimate"
    assert inspect(rows,policy)==inspect(mutated,policy)


def test_followup_lag_categories_are_observation_delays():
    rows,policy=fixture()
    rows=copy.deepcopy(rows)
    # Add an unambiguous changed site more than one year later for c.
    rows.append(rec("c","2003-05-11","B"))
    policy["known_prior_counts"]["total_rows"]+=1
    policy["known_prior_counts"]["window_rows"]+=1
    c=inspect(rows,policy)["counts"]
    assert c["first_same_later_different"]==2
    assert c["lag_gt365_days"]==1
    assert c["first_same_later_no_different"]==0


def test_frozen_claim_escalation_and_prior_count_changes_are_rejected():
    rows,policy=fixture()
    policy["bounds"]["heldout_scoring_authorized"]=True
    with pytest.raises(ValueError,match="claim gates"):
        inspect(rows,policy)
    rows,policy=fixture()
    policy["known_prior_counts"]["first_same"]=999
    with pytest.raises(ValueError,match="first-followup"):
        inspect(rows,policy)




def test_ambiguous_later_return_requires_original_nest_code_among_conflicting_sites():
    first=date(2001,5,10)
    # Conflicting later codes B and C contain no natal A:
    # not a candidate return to A, even though the day is ambiguous.
    other=[(date(2001,6,1),"B"),(date(2001,6,1),"C")]
    assert group_later(other,first,"A",True)==("not_observed",None,True)
    # Mixed A/C contains natal A but is not an unambiguous return.
    candidate=[(date(2001,6,1),"A"),(date(2001,6,1),"C")]
    assert group_later(candidate,first,"A",True)==("ambiguous",None,True)
    # Once another day clearly observes natal A, it is a return-code
    # positive encounter, not proof of movement or settlement.
    clear=candidate+[(date(2001,6,2),"A")]
    assert group_later(clear,first,"A",True)==("observed",23,True)


def test_new_unique_date_categories_reconcile_with_exposed_any_code_counts():
    rows,policy=fixture()
    counts=inspect(rows,policy)["counts"]
    # Original PR643 counted both the uniquely later B and the contradictory
    # same-day B/C: 2 ever-different among first-same; only 1 is unambiguous.
    exposed={
        "schema":"eog.helgeland.pre2015.followup_horizon.frozen_observed_v1",
        "status":"FOLLOWUP_WINDOW_SENSITIVITY_OBSERVED__ECOLOGICAL_HOLD",
        "source":{"source_bytes_and_firstline_independently_verified":True,
                  "calendar_cutoff":"2014-12-31","version_id":421942,"file_id":4576411},
        "counts":{"first_same_then_later_different_site_id_count":2,
                  "first_followup_same_never_observed_different_later_count":1,
                  "first_different_then_later_source_site_id_count":1,
                  "first_followup_same_site_id_count":3}
    }
    reconcile_exposed_followup_counts(counts,exposed)
    incorrect=copy.deepcopy(exposed)
    incorrect["counts"]["first_same_then_later_different_site_id_count"]=1
    with pytest.raises(ValueError,match="contradict exposed"):
        reconcile_exposed_followup_counts(counts,incorrect)
    incorrect=copy.deepcopy(exposed)
    incorrect["counts"]["first_different_then_later_source_site_id_count"]=0
    with pytest.raises(ValueError,match="contradict exposed"):
        reconcile_exposed_followup_counts(counts,incorrect)
    incorrect=copy.deepcopy(exposed)
    incorrect["source"]["source_bytes_and_firstline_independently_verified"]=False
    with pytest.raises(ValueError,match="receipt source"):
        reconcile_exposed_followup_counts(counts,incorrect)


def test_reconciliation_requires_actual_prior_frozen_numbers():
    rows,policy=fixture()
    counts=inspect(rows,policy)["counts"]
    previous=json.loads((BASE/"helgeland_pre2015_followup_horizon_observed_frozen_v1.json").read_text(encoding="utf-8"))
    assert previous["counts"]["first_same_then_later_different_site_id_count"]==228
    assert previous["counts"]["first_followup_same_never_observed_different_later_count"]==3713
    assert previous["counts"]["first_different_then_later_source_site_id_count"]==2
    assert counts["first_same_later_different"]+counts["first_same_later_ambiguous_only"]==2


def test_real_contract_is_post_exposure_and_source_first():
    policy=json.loads(PROTOCOL.read_text(encoding="utf-8"))
    assert policy["known_prior_counts"]["first_same"]==3941
    assert policy["known_prior_counts"]["first_different"]==223
    assert policy["known_prior_counts"]["total_rows"]==73593
    assert policy["window"]==["1994-01-01","2014-12-31"]
    assert policy["bounds"]["post_exposure_exploratory"] is True
    assert policy["bounds"]["heldout_scoring_authorized"] is False
    code=(ROOT/"scripts/audit_helgeland_pre2015_later_site_switch_observability_v1.py").read_text()
    assert code.index('stamp=strict_observed_date(row["date"])') < code.index('ident=(row["ID"] or "").strip()')
    for bad in ('row["Year"]','row["Least_age"]','row["scriptsex"]',
                'read_csv(', 'import pandas', 'urllib'):
        assert bad not in code
