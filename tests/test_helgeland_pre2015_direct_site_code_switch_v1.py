"""Pure synthetic evidence guards for pre-2015 site-code switching (NO real outcomes)."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"validation/eog_virtual_world_ecology_synthesis_v1"
sys.path.insert(0,str(ROOT/"scripts"))
from audit_helgeland_pre2015_direct_site_code_switch_v1 import count_site_code_switches


def policy_for(records):
    policy=json.loads((BASE/"helgeland_pre2015_direct_code_switch_protocol_v1.json").read_text())
    policy["expected_source_row_count_from_prior_qc"]=len(records)
    return policy


def obs(id,when,site,stage="nest"):
    # Deliberately wrong/hindsight values must not influence the site-code result.
    return {"ID":id,"date":when,"Island":site,"Location":site+" locality",
            "stage":stage,"Year":"9999","Least_age":"2","scriptsex":"future"}


def fixtures():
    return [
        obs("a","2000-05-01","A"),
        obs("a","2000-05-09","B","capt"), # changed first observed site code
        obs("b","2001-06-01","C"),
        obs("b","2001-06-05","C","obs"), # unchanged
        obs("c","2002-05-02","A"),
        obs("c","2002-05-03","B"),        # ambiguous nest islands
        obs("c","2002-05-10","A","capt"),
        obs("d","2003-05-01","A"),        # no later direct encounter
        obs("e","2004-05-01","A"),
        obs("e","2004-05-10","A","capt"),
        obs("e","2004-05-10","B","obs"), # ambiguous first later observation
        obs("f","2004-04-15","A","capt"),# no nest record
    ]


def test_synthetic_changed_same_ambiguous_and_absent_fates():
    rows=fixtures()
    result=count_site_code_switches(rows,policy_for(rows))
    cnt=result["counts"]
    assert cnt["whole_file_rows_date_checked"]==12
    assert cnt["eligible_pre2015_rows"]==12
    assert cnt["distinct_ids_observed_pre2015"]==6
    assert cnt["ids_with_any_pre2015_nest_record"]==5
    assert cnt["ids_with_unique_pre2015_nest_code"]==4
    assert cnt["ids_with_ambiguous_pre2015_nest_code"]==1
    assert cnt["unique_nest_ids_with_first_later_direct_encounter"]==3
    assert cnt["first_followup_changed_island_code"]==1
    assert cnt["first_followup_same_island_code"]==1
    assert cnt["first_followup_ambiguous_island_code"]==1
    assert cnt["unique_nest_ids_without_later_direct_encounter"]==1
    assert result["scientific_boundaries"]["site_code_switch_is_proven_natal_dispersal"] is False
    assert result["scientific_boundaries"]["ecological_forecast_authorized"] is False
    assert "a locality" not in json.dumps(result)
    assert '"a"' not in json.dumps(result)


def test_future_dates_are_masked_BEFORE_any_ID_stage_site_inspection():
    original=fixtures()
    class FuturePoison(dict):
        def __getitem__(self, key):
            if key!="date":
                raise RuntimeError("Future source data accessed: "+str(key))
            return super().__getitem__(key)
    future=FuturePoison(obs("a","2015-01-01","EVERYWHERE","nest"))
    ancient=FuturePoison(obs("z","1993-12-31","SOMEWHERE","capt"))
    rows=original+[future,ancient]
    result=count_site_code_switches(rows,policy_for(rows))
    cnt=result["counts"]
    assert cnt["pre1994_rows_suppressed_by_date_only"]==1
    assert cnt["post2014_rows_suppressed_by_date_only"]==1
    assert cnt["eligible_pre2015_rows"]==len(original)
    assert cnt["first_followup_changed_island_code"]==1
    assert result["scientific_boundaries"]["future_2015_2022_destination_values_accessed"] is False


def test_unknown_year_and_derived_age_do_not_change_result():
    original=fixtures()
    changed=copy.deepcopy(original)
    for r in changed:
        r["Year"]="UNTRUSTED_AFTER_THE_FACT"
        r["Least_age"]="999"
        r["Least_hatchyear"]="1900"
        r["scriptsex"]="BACKFILLED"
    assert count_site_code_switches(original,policy_for(original))==(
        count_site_code_switches(changed,policy_for(changed)))


def test_source_row_total_mismatch_and_window_changes_fail():
    rows=fixtures()
    protocol=policy_for(rows)
    protocol["expected_source_row_count_from_prior_qc"]-=1
    with pytest.raises(ValueError,match="row count"):
        count_site_code_switches(rows,protocol)
    protocol=policy_for(rows)
    protocol["window"]["last_observation_date_inclusive"]="2022-12-31"
    with pytest.raises(ValueError,match="window altered"):
        count_site_code_switches(rows,protocol)


def test_attempt_to_authorize_ecological_forecast_fails():
    data=fixtures()
    p=policy_for(data)
    p["holds"]["ecological_model_or_independent_heldout_benchmark_authorized"]=True
    with pytest.raises(ValueError,match="ecological forecast"):
        count_site_code_switches(data,p)


def test_actual_protocol_preserves_2015_2022_as_unseen():
    p=json.loads((BASE/"helgeland_pre2015_direct_code_switch_protocol_v1.json").read_text())
    assert p["expected_source_row_count_from_prior_qc"]==73593
    assert p["window"]["last_observation_date_inclusive"]=="2014-12-31"
    assert p["window"]["target_2015_through_2022_encounter_sites_are_never_inspected"] is True
    assert p["input_columns"]==["ID","Island","Location","date","stage"]
    assert p["holds"]["ecological_model_or_independent_heldout_benchmark_authorized"] is False
    script=(ROOT/"scripts/audit_helgeland_pre2015_direct_site_code_switch_v1.py").read_text()
    assert 'stamp=strict_observed_date(row["date"])' in script
    assert script.index('if stamp>hi:') < script.index('ident=(row["ID"] or "").strip()')
    for forbidden in ('row["Year"]','row["Least_age"]','row["scriptsex"]',
                      'read_csv(', "import pandas", "urllib"):
        assert forbidden not in script


def test_first_encounter_same_site_can_hide_later_observed_site_switch():
    rows=[
        obs("synthetic_id","2001-05-01","A","nest"),
        obs("synthetic_id","2001-05-05","A","capt"),
        obs("synthetic_id","2002-05-20","B","obs"),
    ]
    observed=count_site_code_switches(rows,policy_for(rows))["counts"]
    assert observed["first_followup_same_island_code"]==1
    assert observed["first_followup_changed_island_code"]==0
    # This deliberately demonstrates that first subsequent observation is
    # NOT equivalent to subsequent permanent dispersal or natal recruitment.


def test_frozen_real_pre2015_aggregate_receipt_is_exploratory_not_recruitment():
    path=(BASE/"helgeland_pre2015_first_direct_site_code_frozen_v1.json")
    observed=json.loads(path.read_text(encoding="utf-8"))
    assert observed["schema"]=="eog.helgeland.pre2015.direct_code_switch.frozen_observed_v1"
    assert observed["authority"]["github_actions_run_id"]==37888118673
    assert observed["authority"]["artifact_id"]==11596374594
    assert observed["authority"]["artifact_zip_sha256"]==(
        "2f7767d193397f34d598d9c8d21609da52f5c90e073fea29354271d263f03b6e"
    )
    c=observed["counts"]
    assert c["whole_file_rows_date_checked"]==73593
    assert c["eligible_pre2015_rows"]==51162
    assert c["post2014_rows_suppressed_by_date_only"]==21361
    assert c["pre1994_rows_suppressed_by_date_only"]==1070
    assert c["ids_with_any_pre2015_nest_record"]==10742
    assert c["ids_with_unique_pre2015_nest_code"]==10737
    assert c["ids_with_ambiguous_pre2015_nest_code"]==5
    assert c["unique_nest_ids_with_first_later_direct_encounter"]==4164
    assert c["first_followup_same_island_code"]==3941
    assert c["first_followup_changed_island_code"]==223
    assert c["first_followup_ambiguous_island_code"]==0
    assert c["unique_nest_ids_without_later_direct_encounter"]==6573
    assert all(k is True for k in observed["interpretation"].values()
               if isinstance(k,bool) and k is not False)
    assert observed["interpretation"]["independent_ecological_prediction_authorized"] is False
    assert observed["interpretation"]["source_2015_2022_event_destinations_not_examined"] is True
