"""Guard the V23 readout crossover as post-hoc synthetic evidence only."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"validation"/"eog_virtual_world_ecology_synthesis_v1"/"matched_readout_crossover_v1.json"
SCRIPT=ROOT/"scripts"/"audit_eog_history_readout_crossover_v1.py"


def report():
    return json.loads(REPORT.read_text(encoding="utf-8"))


def module():
    sys.path.insert(0,str(ROOT/"scripts"))
    try:
        spec=importlib.util.spec_from_file_location("v23_readout_audit",SCRIPT)
        assert spec and spec.loader
        m=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m
    finally:
        sys.path.pop(0)


def test_frozen_v23_matches_authoritative_digest_and_fingerprint():
    x=report()
    m=module()
    src=json.loads((
        ROOT/"validation/eog_original_idea_provenance_observability_v23/result_summary_v23.json"
    ).read_text(encoding="utf-8"))
    assert x["schema"]=="eog.virtual_worlds.history_readout_crossover.v1"
    assert x["status"]=="POST_RESULT_EXPLORATORY_NOT_PREREGISTERED"
    assert x["matched_landscapes"]==384
    assert x["three_sources_per_design"] is True
    assert x["original_result_fingerprints"]["v23"]==src["result_fingerprint"]==m.V23["fingerprint"]
    assert "sha256:"+x["original_artifact_zip_sha256"]["v23"]==src["authoritative_artifact_digest"]
    assert x["original_artifact_zip_sha256"]["v23"]==m.V23["sha256"]
    assert len(x["original_artifact_zip_sha256"])==5
    assert "ideal" in x["readout_levels"]["provenance_only"]


def test_exact_paired_outcome_counts_and_zero_false_emergent_significance():
    x=report()
    assert x["identification_by_readout"]=={
        "occupancy_only":{"clustered":231,"dispersed":348},
        "provenance_only":{"clustered":228,"dispersed":44},
        "combined":{"clustered":338,"dispersed":349},
    }
    assert x["paired_identifiability"]=={
        "occupancy_only":{"neither":14,"dispersed_only":139,"clustered_only":22,"both":209},
        "provenance_only":{"neither":155,"dispersed_only":1,"clustered_only":185,"both":43},
        "combined":{"neither":9,"dispersed_only":37,"clustered_only":26,"both":312},
    }
    for readout,counts in x["paired_identifiability"].items():
        assert sum(counts.values())==384
        assert counts["clustered_only"]+counts["both"]==x["identification_by_readout"][readout]["clustered"]
        assert counts["dispersed_only"]+counts["both"]==x["identification_by_readout"][readout]["dispersed"]
    assert x["readout_crossover"]=={
        "occupancy_d_only__provenance_c_only":78,
        "occupancy_c_only__provenance_d_only":0,
        "crossover_with_coverage_insurance_tradeoff":75,
        "crossover_with_more_clustered_provenance_memory":78,
        "combined_resolves_both_crossover_designs":78,
        "coverage_insurance_tradeoff_all_landscapes":281,
    }
    for factor,parts in x["strata"].items():
        assert sum(v["n"] for v in parts.values())==384,factor
        assert sum(v["crossovers"] for v in parts.values())==78,factor
        assert sum(v["tradeoff"] for v in parts.values())==281,factor
    assert len(x["boundaries"])>=5
    assert any("post hoc" in s for s in x["boundaries"])
    assert any("not equal-effort field recommendations" in s for s in x["boundaries"])


def fixture():
    records={}
    for place, occ, prov in (
        ("clustered",False,True),
        ("dispersed",True,False),
    ):
        ids=["r0c4","r0c3","r1c4"] if place=="clustered" else ["r0c4","r6c6","r0c0"]
        records[place]={
            "v18":{"source_ids":list(ids),"union_reachable_fraction":0.4 if place=="clustered" else 0.5,
                    "worst_source_loss_retention":0.7 if place=="clustered" else 0.2},
            "v21":{"source_ids":list(ids),"provenance_disagreement_fraction":0.8 if place=="clustered" else 0.2},
            "v22":{"source_ids":list(ids),"full_history":{"identified":occ}},
            "v23":{"source_ids":list(ids),"history_count":3,"plans":{
                "occupancy_only":{"full_history":{"identified":occ,"minimum_size":1 if occ else None}},
                "provenance_only":{"full_history":{"identified":prov,"minimum_size":2 if prov else None}},
                "combined":{"full_history":{"identified":True,"minimum_size":1}},
            }},
        }
    key=("low","rook",0.2,0)
    phases={
        "v18":{"designs":{p:{"3":records[p]["v18"]} for p in records}},
        "v21":{"designs":{p:records[p]["v21"] for p in records}},
        "v22":{"designs":{p:records[p]["v22"] for p in records}},
        "v23":{"designs":{p:records[p]["v23"] for p in records}},
    }
    return key,phases


def test_readout_crosscheck_fails_if_source_or_occupancy_contract_changes():
    script=module()
    key,good=fixture()
    row=script.paired_readout_outcomes(key,good)
    assert row["clustered"]["ids"]["provenance_only"] is True
    assert row["clustered"]["ids"]["occupancy_only"] is False
    assert row["dispersed"]["ids"]["provenance_only"] is False
    assert row["dispersed"]["ids"]["occupancy_only"] is True

    bad=copy.deepcopy(good)
    bad["v23"]["designs"]["dispersed"]["source_ids"][2]="INVALID"
    with pytest.raises(ValueError,match="source list"):
        script.paired_readout_outcomes(key,bad)

    bad=copy.deepcopy(good)
    bad["v23"]["designs"]["clustered"]["plans"]["occupancy_only"]["full_history"]["identified"]=True
    with pytest.raises(ValueError,match="occupancy arm"):
        script.paired_readout_outcomes(key,bad)

    bad=copy.deepcopy(good)
    bad["v23"]["designs"]["clustered"]["plans"]["combined"]["full_history"]["identified"]=False
    with pytest.raises(ValueError,match="combined observation"):
        script.paired_readout_outcomes(key,bad)
