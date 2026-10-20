"""Fabricated discrete arrival clocks only; no real biological observations."""
from __future__ import annotations
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from benchmarks.run_eog_temporal_evidence_v43 import (
    PROTOCOL, PARENT_V42, CENSUSES, TARGET, BOUNDS, CALENDAR,
    verify_protocol, required_pairs, census_at, smallest_binary_probe_set,
    evaluate_residual, risk_with_readout, _covered_pairs,
)
from benchmarks.run_eog_provenance_uncertainty_v42 import deterministic_risk


def _data(three_maturity_states=False):
    # Present T*=13, the threshold census t=11, excluded as definitional.
    a,b = (0,0),(0,1)
    histories = {
        "h1":{a:9,b:13},
        "h2":{a:12,b:10 if three_maturity_states else 13},
        "h3":{a:12,b:13},
    }
    if not three_maturity_states:
        # Only h1/h2 are observationally equivalent given the complete
        # original source/occupancy baseline; h3 is already distinguishable.
        baseline = {"h1":("same",),"h2":("same",),"h3":("different",)}
    else:
        baseline = {h:("same",) for h in histories}
    target = {
        h: tuple((f"r{n[0]}c{n[1]}", v<=11) for n,v in arrivals.items())
        for h,arrivals in histories.items()
    }
    return baseline,target,histories,(a,b)


def test_original_v42_contract_12_worlds_and_tautology_guard_unchanged():
    p=json.loads(PROTOCOL.read_text())
    parent=json.loads(PARENT_V42.read_text())
    verify_protocol(p,parent)
    assert p["source"]["reviewed_prior_counts"]["maturity_unresolved_even_by_all_perfect_source_tags"]==12
    assert p["contrasts"]["primary_non_tautological"]["exclude_target_identity_time_tstar_minus_two"]
    assert p["world_design"]["original_occupancy_census_times"]==list(CENSUSES)
    assert p["contrasts"]["fixed_calendar_census_sensitivity"]["probe_times"]==list(CALENDAR)
    assert p["scientific_boundaries"]==BOUNDS
    p["contrasts"]["primary_non_tautological"]["exclude_target_identity_time_tstar_minus_two"]=False
    with pytest.raises(ValueError,match="Tautological"):
        verify_protocol(p,parent)


def test_threshold_census_is_exact_target_definition_but_excluded_from_independent_success():
    baseline,target,arrivals,nodes=_data()
    direct=census_at(arrivals,nodes,11)
    assert direct==target
    result=evaluate_residual(baseline,target,arrivals,nodes,13)
    assert result["identity_time_t_minus_2"]==11
    assert result["definitional_full_census_resolves"] is True
    assert 11 not in set(range(13+1))-set(CENSUSES)-{11}
    assert result["fixed_calendar_one_census"]["11"]["applicable"] is False
    assert result["fixed_calendar_one_census"]["11"]["excluded_reason"]=="equals_definition_of_target"
    assert result["original_observation_retest_max_information_abs_error"]==pytest.approx(0)


def test_one_nontautological_sentinel_can_discriminate_history_pair():
    baseline,target,arrivals,nodes=_data()
    result=evaluate_residual(baseline,target,arrivals,nodes,13)
    assert result["required_unresolved_history_pairs"]==1
    assert result["baseline_target_conditional_entropy_bits"]>0
    assert result["any_non_tautological_full_census_resolves"] is True
    assert result["single_site_time_resolves"] is True
    assert result["minimum_non_tautological_binary_probe_count"]==1
    assert result["earliest_resolving_non_tautological_full_census"]==9
    assert result["earliest_resolving_single_site_time"]==[9,"r0c0"]
    assert result["fixed_calendar_one_census"]["9"]["resolved"] is True


def test_three_distinct_maturity_targets_need_two_sentinels_but_one_full_census():
    baseline,target,arrivals,nodes=_data(three_maturity_states=True)
    result=evaluate_residual(baseline,target,arrivals,nodes,13)
    assert result["required_unresolved_history_pairs"]==3
    assert result["any_non_tautological_full_census_resolves"] is True
    assert result["single_site_time_resolves"] is False
    assert result["minimum_non_tautological_binary_probe_count"]==2
    selected=result["minimum_non_tautological_binary_probes"]
    assert len(selected)==2
    assert all(event[0]!=11 for event in selected)
    assert all(event[0] not in CENSUSES for event in selected)


def test_adjacent_arrivals_without_intermediate_measurement_other_than_target():
    a=(0,0)
    arrivals={"h1":{a:10},"h2":{a:12},"h3":{a:12}}
    baseline={"h1":("same",),"h2":("same",),"h3":("different",)}
    target={h:(("r0c0",v[a]<=11),) for h,v in arrivals.items()}
    r=evaluate_residual(baseline,target,arrivals,(a,),13)
    # t=10 has a difference, even though direct target time t=11 is withheld.
    assert r["single_site_time_resolves"] is True
    assert r["earliest_resolving_non_tautological_full_census"]==10


def test_can_be_information_theoretically_unidentifiable_by_remaining_time_grid():
    a=(0,0)
    arrivals={"h1":{a:11},"h2":{a:12},"h3":{a:12}}
    baseline={"h1":("same",),"h2":("same",),"h3":("different",)}
    target={h:(("r0c0",v[a]<=11),) for h,v in arrivals.items()}
    r=evaluate_residual(baseline,target,arrivals,(a,),13)
    assert r["definitional_full_census_resolves"] is True
    assert r["any_non_tautological_full_census_resolves"] is False
    assert r["single_site_time_resolves"] is False
    assert r["minimum_non_tautological_binary_probe_count"] is None
    assert r["all_non_tautological_binary_events_can_resolve"] is False
    assert r["single_best_non_tautological_full_census"]["information_bits"]==pytest.approx(0)


def test_exact_binary_set_cover_prefers_minimal_deterministic_probes():
    pairs=(("a","b"),("b","c"),("a","c"))
    events={
        (10,"r0c0"):{"a":1,"b":0,"c":0},
        (12,"r0c1"):{"a":0,"b":1,"c":0},
        (8,"r0c9"):{"a":1,"b":1,"c":1},
    }
    assert _covered_pairs(pairs,events[(8,"r0c9")])==0
    selected=smallest_binary_probe_set(pairs,events,budget=3)
    assert selected==((10,"r0c0"),(12,"r0c1"))
    assert smallest_binary_probe_set((),events)==()
    assert smallest_binary_probe_set(pairs,{(10,"r0c9"):{"a":1,"b":1,"c":1}}) is None
    with pytest.raises(ValueError,match="budget"):
        smallest_binary_probe_set(pairs,events,budget=4)


def test_untrusted_time_node_target_changes_stop_instead_of_rescoring():
    baseline,target,arrivals,nodes=_data()
    with pytest.raises(ValueError,match="no source/occupancy-equivalent"):
        evaluate_residual(
            {h:(h,) for h in baseline},target,arrivals,nodes,13)
    with pytest.raises(ValueError,match="nodes"):
        evaluate_residual(baseline,target,arrivals,nodes+((1,1),),13)
    wrong=dict(target)
    wrong["h1"]=(("r0c0",False),("r0c1",False))
    with pytest.raises(ValueError,match="definition"):
        evaluate_residual(baseline,wrong,arrivals,nodes,13)


def test_exact_conditional_entropy_of_target_nonnegative_and_original_baselines_not_new():
    baseline,target,arrivals,nodes=_data()
    old=deterministic_risk(baseline,target)["entropy_bits"]
    actual=risk_with_readout(baseline,target,census_at(arrivals,nodes,9))["entropy_bits"]
    assert 0<=actual<old
    assert risk_with_readout(baseline,target,census_at(arrivals,nodes,8))["entropy_bits"]==pytest.approx(old)


def test_no_external_biological_data_in_new_runner():
    text=(ROOT/"benchmarks/run_eog_temporal_evidence_v43.py").read_text()
    for forbidden in ("read_csv(","urllib","requests","Dispersaldata.txt","Geneticassignment_README.txt","mcp__"):
        assert forbidden not in text
