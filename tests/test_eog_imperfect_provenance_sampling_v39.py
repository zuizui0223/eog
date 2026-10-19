"""Exact three-history posterior information, synthetic only."""
from __future__ import annotations

import math
from pathlib import Path

import pytest

from benchmarks.run_eog_imperfect_provenance_sampling_v39 import (
    bayes_information,
    prepare_design,
    _verify,
    PARENT,
    PROTOCOL,
    K,
    POLICIES,
    COVERAGE,
    ERRORS,
)
from benchmarks.run_eog_original_idea_virtual_worlds_v2 import _generate_base
from benchmarks.run_eog_original_idea_directed_temporal_flow_v5 import (
    _graphs, _outlet_corner, _truth_source,
)
from benchmarks.run_eog_original_idea_source_placement_v18 import (
    RULE, _candidate_sources, _source_sets,
)
import json


def fixtures():
    # h1/h2 are observationally identical at all occupancy times, h3 is not.
    occ = {"h1":("same",), "h2":("same",), "h3":("other",)}
    prov = {
        "confluence": {"h1":("source-a",), "h2":("source-b",), "h3":("source-a",)},
        "unique": {"h1":("source-a",), "h2":("source-a",), "h3":("source-a",)},
    }
    return occ, prov


def test_perfect_provenance_resolves_occupancy_alias_exactly():
    occ, prov = fixtures()
    r=bayes_information(occ,prov,("confluence",),1.0,0.0)
    assert r["baseline_bayes_accuracy"] == pytest.approx(2/3)
    assert r["baseline_conditional_entropy_bits"] == pytest.approx(2/3)
    assert r["additional_information_bits"] == pytest.approx(2/3)
    assert r["bayes_accuracy_gain"] == pytest.approx(1/3)


def test_zero_coverage_and_single_origin_carry_zero_information():
    occ, prov = fixtures()
    for error in ERRORS:
        a=bayes_information(occ,prov,("confluence",),0,error)
        assert a["additional_information_bits"] == 0
        assert a["bayes_accuracy_gain"] == 0
    for q in COVERAGE:
        for e in ERRORS:
            a=bayes_information(occ,prov,("unique",),q,e)
            assert a["additional_information_bits"] == pytest.approx(0,abs=1e-10)
            assert a["bayes_accuracy_gain"] == pytest.approx(0,abs=1e-10)


def test_noisy_recruitment_analogue_information_declines_with_error_and_missingness():
    occ, prov = fixtures()
    measured=[]
    for q in COVERAGE:
        row=[]
        for e in ERRORS:
            a=bayes_information(occ,prov,("confluence",),q,e)
            assert a["additional_information_bits"] >= 0
            assert a["bayes_accuracy_gain"] >= 0
            row.append(a["additional_information_bits"])
        assert row[0] + 1e-10 >= row[1] >= row[2] - 1e-10
        measured.append(row)
    for k in range(len(ERRORS)):
        assert all(measured[i][k] <= measured[i+1][k]+1e-10 for i in range(len(COVERAGE)-1))
    assert measured[2][1]>0


def test_all_history_specific_tag_aliases_cannot_increase_information():
    occ={"h1":("o",),"h2":("o",),"h3":("o",)}
    constant={
        "u1":{"h1":("S",),"h2":("S",),"h3":("S",)},
        "u2":{"h1":("S",),"h2":("S",),"h3":("S",)},
        "u3":{"h1":("S",),"h2":("S",),"h3":("S",)},
    }
    ans=bayes_information(occ,constant,("u1","u2","u3"),0.6,0.1)
    assert ans["additional_information_bits"] == pytest.approx(0,abs=1e-9)
    assert ans["bayes_accuracy_gain"] == pytest.approx(0,abs=1e-9)


def test_false_measurement_or_missing_history_denied():
    occ, prov = fixtures()
    with pytest.raises(ValueError,match="three"):
        bayes_information({"a":1,"b":1},prov,("confluence",),0.5,0.1)
    with pytest.raises(ValueError,match="Noise"):
        bayes_information(occ,prov,("confluence",),0.5,0.51)
    with pytest.raises(ValueError,match="not in"):
        bayes_information(occ,prov,("not-a-real-node",),0.5,0.1)
    with pytest.raises(ValueError,match="three"):
        bayes_information(occ,{"other":{"h1":1,"h2":2}},("other",),0.5,0.1)


def test_predeclared_parent_simulation_and_frozen_scientific_stop():
    p=json.loads(PROTOCOL.read_text())
    parent=json.loads(PARENT.read_text())
    _verify(p,parent)
    assert p["parent"]["parent_design_rows"]==768
    assert p["parent"]["parent_occupancy_exact_identifiable"]==579
    assert p["parent"]["parent_full_perfect_provenance_plus_occupancy_identifiable"]==687
    assert len(p["predeclared_hypotheses"])==5
    assert p["provenance_assay"]["selection_budget"]==K==3
    assert p["scientific_boundaries"]["new_EOG_WF_endpoint_scored"] is False
    assert p["scientific_boundaries"]["empirical_genotype_snp_data_read"] is False
    assert p["scientific_boundaries"]["site_selection_uses_truth_origin_labels"] is False
    corrupt=json.loads(PROTOCOL.read_text())
    corrupt["provenance_assay"]["misassignment_probabilities"]=[0.0,0.1,0.45]
    with pytest.raises(ValueError,match="model"):
        _verify(corrupt,parent)


def test_fixed_v23_landscape_uses_topological_sites_without_historical_labels():
    base=_generate_base(0,"low","rook")
    outlet=_outlet_corner(0,"low","rook")
    anchor=_truth_source(base,outlet)
    candidates,_=_candidate_sources(base,outlet,anchor)
    sets=_source_sets(candidates,anchor)
    assert sets
    _,graph=_graphs(base,0.20,RULE,outlet)
    x=prepare_design(graph,sets["clustered"][3],"sample-fixed")
    assert set(x["selected"])==set(POLICIES)
    assert all(len(x["selected"][v])<=K for v in POLICIES)
    assert x["static_confluence_site_count"]>=0
    assert x["static_unique_origin_site_count"]>=0
    assert len(x["occupancy"])==3
    assert len(x["provenance_tags"]) > 0
    xx=prepare_design(graph,sets["clustered"][3],"sample-fixed")
    assert x["selected"]==xx["selected"]


def test_no_real_world_genotypes_or_hidden_external_data_imported():
    source=Path("benchmarks/run_eog_imperfect_provenance_sampling_v39.py").read_text()
    for bad in ("import urllib", "import requests", "read_csv(", "mcp__",
                "Geneticassignment_README", "Dispersaldata.txt"):
        assert bad.lower() not in source.lower()


def test_first_independently_inspected_768_world_noisy_source_tag_result_is_frozen():
    f=Path("validation/eog_original_idea_imperfect_provenance_v39/result_frozen_v39.json")
    z=json.loads(f.read_text(encoding="utf-8"))
    assert z["schema"]=="eog.original_idea.imperfect_source_provenance_sampling.frozen_review_v39"
    assert z["pre_scoring_protocol_commit"]=="582833e08d3f35075783ff51a845deee26dc8468"
    assert z["authority"]["original_actions_run_id"]==39237967536
    assert z["authority"]["artifact_id"]==12180415330
    assert z["authority"]["artifact_zip_sha256"]==(
        "ad41b561b4ed1255252dc094749c318320976d289bb06664239b088b4828dd75"
    )
    assert z["authority"]["canonical_full_result_sha256"]==(
        "eefbd3c2ef69e532d6efc5fef66fd7ec97def75e6dd6b74d533d042e78aaa865"
    )
    assert z["parent_reconciled"]=={
        "design_rows":768,"occupancy_exact_identified":579,
        "ideal_full_provenance_plus_occupancy_exact_identified":687,
        "occupancy_alias_count":189,"equal_budget_occupancy_aliased_designs":88
    }
    t=z["primary_fixed_setting"]
    assert t["coverage"]==0.6 and t["miscall"]==0.1 and t["n"]==88
    assert t["confluence_targeted"]["mean_information_bits"]==pytest.approx(0.6558164099798183)
    assert t["random_response_blind"]["mean_information_bits"]==pytest.approx(0.648676018353758)
    assert t["confluence_targeted"]["mean_accuracy_gain"]==pytest.approx(0.33305599621211984)
    assert t["random_response_blind"]["mean_accuracy_gain"]==pytest.approx(0.3303464015151503)
    assert all(v=="SUPPORTED" for v in z["hypotheses"].values())
    assert z["scientific_boundaries"]["source_tags_are_first_arrival_synthetic_not_empirical_genetic_ancestry"]
    assert z["scientific_boundaries"]["miscall_and_coverage_rates_are_assumed_not_estimated"]
    assert z["scientific_boundaries"]["no_EOG_WF_endpoint_scored"]
