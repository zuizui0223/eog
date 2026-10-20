"""Fabricated-only cutoff time and noisy origin channel controls for v44."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmarks import run_eog_provenance_ecological_state_v41 as original
from benchmarks.run_eog_asof_time_provenance_v44 import (
    BUDGET, Q, ERROR, PANEL_PAIRS, HYPOTHESES, POLICIES, BOUNDARIES,
    PROTOCOL, V43, verify_contract, static_selection,
    occupied_confluence_selection, make_asof_world, make_cutoff_inputs,
    future_state, risk_given_cutoff, canonical,
)
from benchmarks.run_eog_original_idea_virtual_worlds_v2 import _node_id


def inputs():
    occupancy = {
        "h1": (("r0c0", True),),
        "h2": (("r0c0", True),),
        "h3": (("r0c0", False),),
    }
    available = {
        "h1": {"r0c0": ("source-A",)},
        "h2": {"r0c0": ("source-B",)},
        "h3": {"r0c0": None},
    }
    target = {
        "h1": (("r0c0", True),),
        "h2": (("r0c0", False),),
        "h3": (("r0c0", False),),
    }
    sites = {
        "static_confluence_top3": ("r0c0",),
        "static_sha256_random_top3": ("r0c0",),
    }
    return occupancy, available, target, sites, {"r0c0": 2}


def test_original_v43_chronology_and_all_v44_panels_frozen():
    p = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    prior = json.loads(V43.read_text(encoding="utf-8"))
    verify_contract(p, prior)
    assert tuple((r["id"],r["cutoff_t"],r["target_t"]) for r in p["fixed_forecast_pairs"]) == PANEL_PAIRS
    assert p["world_and_information_contract"]["future_label_leakage_prohibited"]
    assert p["scientific_boundaries"] == BOUNDARIES
    assert tuple(t["id"] for t in p["predeclared_hypotheses"]) == HYPOTHESES
    assert p["measurement"]["max_sites"] == BUDGET == 3
    assert p["measurement"]["q_observation_given_occupied"] == Q == .6
    assert p["measurement"]["e_miscall_given_observed"] == ERROR == .1
    assert len(PANEL_PAIRS) == 4


def test_example_cutoff_occupied_origin_tags_help_forecast_later_age_state():
    occupancy, available, target, sites, cover = inputs()
    noisy = risk_given_cutoff(
        occupancy, target, available, policy="cutoff_occupied_confluence_top3",
        fixed_selection=sites, source_cover=cover,
    )
    perfect = risk_given_cutoff(
        occupancy, target, available, policy="cutoff_occupied_confluence_top3",
        fixed_selection=sites, source_cover=cover, coverage=1.0, miscall=0.0,
    )
    assert noisy["ambiguous_target_under_cutoff_occupancy"] is True
    assert noisy["added_source_information_bits"] > 0
    assert noisy["added_target_bayes_accuracy_gain"] > 0
    assert perfect["added_source_information_bits"] >= noisy["added_source_information_bits"]
    assert perfect["added_target_bayes_accuracy_gain"] >= noisy["added_target_bayes_accuracy_gain"]
    assert noisy["unoccupied_future_source_tag_violations"] == 0
    assert noisy["mean_cutoff_occupied_selected_sites"] == pytest.approx(2/3)


def test_no_measurement_q0_carries_zero_additional_information():
    occupancy, available, target, sites, cover = inputs()
    for policy in POLICIES:
        x = risk_given_cutoff(
            occupancy, target, available, policy=policy,
            fixed_selection=sites, source_cover=cover, coverage=0.0,
        )
        assert x["added_source_information_bits"] == pytest.approx(0, abs=1e-9)
        assert x["added_target_bayes_accuracy_gain"] == pytest.approx(0, abs=1e-9)


def test_unoccupied_site_has_deterministically_no_tag_even_if_future_truth_different():
    class Poison(dict):
        def __getitem__(self, key):
            raise AssertionError("Future source tag read from absent cutoff site")
    world = {
        "nodes":((0,0),),
        "histories":{
            "h1":{"first":{(0,0):7}, "earliest":Poison()},
            "h2":{"first":{(0,0):8}, "earliest":Poison()},
            "h3":{"first":{(0,0):9}, "earliest":Poison()},
        },
    }
    occ, tags = make_cutoff_inputs(world, 2)
    assert all(not o[0][1] for o in occ.values())
    assert all(v["r0c0"] is None for v in tags.values())
    targets={h:(("r0c0",h=="h1"),) for h in occ}
    static={"static_confluence_top3":("r0c0",),
            "static_sha256_random_top3":("r0c0",)}
    result = risk_given_cutoff(
        occ, targets, tags, policy="static_confluence_top3",
        fixed_selection=static, source_cover={"r0c0":2},
    )
    assert result["added_source_information_bits"] == 0
    assert result["mean_cutoff_occupied_selected_sites"] == 0


def test_poisoned_future_label_is_rejected_not_treated_as_extra_cutoff_information():
    occupancy, available, target, sites, cover = inputs()
    poisoned={h:dict(v) for h,v in available.items()}
    poisoned["h3"]["r0c0"]=("future-source",)
    x=risk_given_cutoff(
        occupancy,target,poisoned,policy="static_confluence_top3",
        fixed_selection=sites,source_cover=cover)
    assert x["unoccupied_future_source_tag_violations"] == 1
    assert x["added_source_information_bits"] > 0  # only two cutoff-occupied histories contribute


def test_static_source_site_selections_match_original_v39_and_do_not_read_outcomes():
    base=original._generate_base(0,"low","rook")
    outlet=original._outlet_corner(0,"low","rook")
    anchor=original._truth_source(base,outlet)
    cand,_=original._candidate_sources(base,outlet,anchor)
    sets=original._source_sets(cand,anchor)
    _,graph=original._graphs(base,0.20,original.RULE,outlet)
    sources=sets["clustered"][3]
    key="0|low|rook|0.2|clustered"
    world=make_asof_world(graph,sources,key)
    parent=original.prepare_design(graph,sources,key)
    assert world["fixed_selections"]["static_confluence_top3"] == tuple(
        parent["selected"]["confluence_targeted"])
    assert world["fixed_selections"]["static_sha256_random_top3"] == tuple(
        parent["selected"]["random_response_blind"])
    occ, tags=make_cutoff_inputs(world,4)
    for h in occ:
        for site,present in occ[h]:
            assert (tags[h][site] is None) == (not present)


def test_site_policy_adapts_only_to_observed_cutoff_occupancy():
    cover={"A":3,"B":2,"C":2,"D":1,"E":3}
    o=(("A",False),("B",True),("C",True),("D",True),("E",True))
    chosen=occupied_confluence_selection(o,cover)
    assert chosen==("E","B","C")
    other=(("A",True),("B",False),("C",False),("D",True),("E",False))
    assert occupied_confluence_selection(other,cover)==("A",)


def test_invalid_misclassification_or_partial_history_denied():
    occupancy,available,target,sites,cover=inputs()
    with pytest.raises(ValueError,match="history"):
        risk_given_cutoff({"h1":occupancy["h1"]},target,available,
                          policy="static_confluence_top3",
                          fixed_selection=sites,source_cover=cover)
    with pytest.raises(ValueError,match="history"):
        risk_given_cutoff(occupancy,target,available,policy="unregistered",
                          fixed_selection=sites,source_cover=cover)
    with pytest.raises(ValueError,match="history"):
        risk_given_cutoff(occupancy,target,available,policy="static_confluence_top3",
                          fixed_selection=sites,source_cover=cover,miscall=.9)
    notags={h:dict(tags) for h,tags in available.items()}
    notags["h1"]["r0c0"]=None
    with pytest.raises(ValueError,match="occupied cutoff site"):
        risk_given_cutoff(occupancy,target,notags,policy="static_confluence_top3",
                          fixed_selection=sites,source_cover=cover)


def test_known_target_matches_cutoff_census_gives_zero_information_gain():
    o,a,_,sites,cover=inputs()
    targets={h:o[h] for h in o}
    result=risk_given_cutoff(
        o,targets,a,policy="cutoff_occupied_confluence_top3",
        fixed_selection=sites,source_cover=cover)
    assert result["ambiguous_target_under_cutoff_occupancy"] is False
    assert result["baseline_target_conditional_entropy_bits"] == 0
    assert result["added_source_information_bits"] == pytest.approx(0,abs=1e-9)
    assert result["added_target_bayes_accuracy_gain"] == pytest.approx(0,abs=1e-9)


def test_exogenous_future_state_uses_unmodified_v26_age_maps():
    world={
        "nodes":((0,0),(0,1)),
        "histories":{
            "h1":{"first":{(0,0):2,(0,1):4}},
            "h2":{"first":{(0,0):4,(0,1):6}},
            "h3":{"first":{(0,0):8,(0,1):3}},
        },
    }
    lag2=future_state(world,5,"persistent_threshold_lag2")
    assert lag2["h1"] == (("r0c0",True),("r0c1",False))
    assert lag2["h2"] == (("r0c0",False),("r0c1",False))
    assert lag2["h3"] == (("r0c0",False),("r0c1",True))
    transient=future_state(world,5,"transient_window_age1_2")
    assert transient["h1"] == (("r0c0",False),("r0c1",True))
    assert transient["h2"] == (("r0c0",True),("r0c1",False))
    assert transient["h3"] == (("r0c0",False),("r0c1",True))


def test_asof_runner_never_fetches_genetics_or_full_future_snapshots():
    content=(ROOT/"benchmarks/run_eog_asof_time_provenance_v44.py").read_text()
    for bad in ('urllib','requests','read_csv(', 'Dispersaldata.txt',
                'Geneticassignment_README.txt', 'mcp__', 'SNAPSHOT_TIMES'):
        assert bad not in content
    assert 'make_cutoff_inputs' in content
    assert 'present = bool(record["first"][node] <= cutoff)' in content
    assert 'if present:' in content
