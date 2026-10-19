"""Adversarial tests for v40 64-seed response-blind provenance-placement controls."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from benchmarks.run_eog_provenance_placement_multiseed_v40 import (
    BUDGET, SEED_COUNT, SEED_PREFIX, BOUNDS, HYPOTHESES, V39, V23,
    PROTOCOL, _verify, _quantile, _mean, rank_random_sites,
)
from benchmarks.run_eog_imperfect_provenance_sampling_v39 import (
    bayes_information, prepare_design,
)
from benchmarks.run_eog_original_idea_virtual_worlds_v2 import _generate_base
from benchmarks.run_eog_original_idea_directed_temporal_flow_v5 import (
    _graphs, _outlet_corner, _truth_source,
)
from benchmarks.run_eog_original_idea_source_placement_v18 import (
    RULE, _candidate_sources, _source_sets,
)


def documents():
    return (
        json.loads(PROTOCOL.read_text(encoding="utf-8")),
        json.loads(V39.read_text(encoding="utf-8")),
        json.loads(V23.read_text(encoding="utf-8")),
    )


def test_original_v39_evidence_and_v40_predeclared_noisy_design_fixed():
    p, old, parent = documents()
    _verify(p, old, parent)
    assert p["status"] == (
        "FROZEN_BEFORE_V40_RANDOM_SEED_ENSEMBLE_EVALUATION__POST_V39_EXPOSURE"
    )
    assert p["parent"]["matched_full_design_rows"] == 768
    assert p["parent"]["occupancy_ambiguous_rows"] == 189
    assert p["parent"]["equal_budget_occupancy_ambiguous_rows"] == 88
    assert p["design"]["site_budget"] == BUDGET == 3
    assert p["design"]["ensemble_count"] == SEED_COUNT == 64
    assert p["design"]["seed_prefix"] == SEED_PREFIX
    assert p["design"]["observation_coverage"] == 0.6
    assert p["design"]["categorical_miscall"] == 0.1
    assert p["estimands"]["materiality_threshold_bits"] == 0.02
    assert old["parent_reconciled"]["equal_budget_occupancy_aliased_designs"] == 88
    assert old["authority"]["canonical_full_result_sha256"] == (
        "eefbd3c2ef69e532d6efc5fef66fd7ec97def75e6dd6b74d533d042e78aaa865"
    )
    assert [j["id"] for j in p["falsifiable_hypotheses"]] == list(HYPOTHESES)
    assert p["scientific_boundaries"] == BOUNDS
    assert p["scientific_boundaries"]["no_empirical_genetic_origin_assignment_accuracy_or_field_effort_estimated"]


def test_source_blind_rank_deterministic_but_changes_with_seeds():
    sites = tuple(f"node_{i:02d}" for i in range(15))
    selections = [
        rank_random_sites(sites, "synthetic-world|fixed-world-truth-blind", s)
        for s in range(SEED_COUNT)
    ]
    assert all(len(x) == 3 and len(set(x)) == 3 for x in selections)
    assert len(set(selections)) > 1
    assert rank_random_sites(sites, "synthetic-world|fixed-world-truth-blind", 0) == selections[0]
    assert rank_random_sites(tuple(reversed(sites)), "synthetic-world|fixed-world-truth-blind", 0) == selections[0]
    seed = f"{SEED_PREFIX}000"
    expected = tuple(sorted(
        sites, key=lambda node: (
            hashlib.sha256(
                f"{seed}|synthetic-world|fixed-world-truth-blind|{node}".encode()
            ).hexdigest(), node
        )
    )[:3])
    assert selections[0] == expected
    with pytest.raises(ValueError,match="exactly"):
        rank_random_sites(sites,"synthetic",64)
    with pytest.raises(ValueError,match="exactly"):
        rank_random_sites(sites,"synthetic",-1)


def test_quantile_boundary_does_not_collapse_to_zero():
    assert _quantile([7],0) == 7
    assert _quantile([7],1) == 7
    assert _quantile([1,3,5,7,9],0) == 1
    assert _quantile([1,3,5,7,9],.5) == 5
    assert _quantile([1,3,5,7,9],1) == 9
    assert _quantile([1,3,5,7],0.5) == 4
    assert _quantile([],0.5) is None
    assert _mean([1,2,3]) == 2
    assert _mean([]) is None


def test_v39_label_value_information_is_not_used_to_choose_sites():
    rows = tuple(f"n{x}" for x in range(6))
    key = "a|b|c|synthetic"
    before = rank_random_sites(rows, key, 23)
    truth_labels = {r:("source-1",) if i%2 else ("source-2",) for i,r in enumerate(rows)}
    reversed_truth = {r:("source-2",) if i%2 else ("source-1",) for i,r in enumerate(rows)}
    assert rank_random_sites(tuple(truth_labels),key,23) == before
    assert rank_random_sites(tuple(reversed_truth),key,23) == before


def test_exact_bayes_source_noise_recovers_good_vs_bad_placement_fixture():
    o = {"h1":("snapshot-a",),"h2":("snapshot-a",),"h3":("snapshot-b",)}
    reads = {
        "confluence_true": {"h1":("A",),"h2":("B",),"h3":("A",)},
        "confluence_invariant": {"h1":("A",),"h2":("A",),"h3":("A",)},
        "unique_invariant": {"h1":("C",),"h2":("C",),"h3":("C",)},
    }
    useful = bayes_information(o,reads,("confluence_true",),0.6,0.1)
    useless = bayes_information(o,reads,("confluence_invariant",),0.6,0.1)
    assert useful["additional_information_bits"] > 0
    assert useful["bayes_accuracy_gain"] > 0
    assert useless["additional_information_bits"] == pytest.approx(0,abs=1e-10)
    assert useless["bayes_accuracy_gain"] == pytest.approx(0,abs=1e-10)


def test_one_original_v23_world_can_recover_response_blind_sites_with_no_extra_assays():
    base = _generate_base(0,"low","rook")
    outlet = _outlet_corner(0,"low","rook")
    anchor = _truth_source(base,outlet)
    candidates,_ = _candidate_sources(base,outlet,anchor)
    source_sets = _source_sets(candidates,anchor)
    _, graph = _graphs(base,0.20,RULE,outlet)
    x = prepare_design(graph,source_sets["clustered"][3],"0|low|rook|0.2|clustered")
    all_sites = tuple(sorted(x["provenance_tags"]))
    if len(all_sites) >= 3:
        sample = rank_random_sites(all_sites,"0|low|rook|0.2|clustered",7)
        assert len(sample)==3
        assert all(s in x["provenance_tags"] for s in sample)
    assert "occupancy" in x and "selected" in x
    assert all(len(set(value)) <= 3 for value in x["provenance_tags"].values())


@pytest.mark.parametrize("change,pattern",[
    (lambda p:p["design"].update(ensemble_count=1),"seeds"),
    (lambda p:p["design"].update(categorical_miscall=0.2),"channel"),
    (lambda p:p["estimands"].update(materiality_threshold_bits=0.0),"threshold"),
    (lambda p:p["scientific_boundaries"].update(no_heldout_genetic_EOG_predictive_endpoint=False),"claims"),
    (lambda p:p["falsifiable_hypotheses"].pop(),"claims|threshold"),
])
def test_contract_change_fails_closed(change,pattern):
    p,old,parent = documents()
    copy_p = copy.deepcopy(p)
    change(copy_p)
    with pytest.raises(ValueError):
        _verify(copy_p,old,parent)


def test_no_genotypes_or_network_contact_and_uses_original_three_history_v39_math():
    script = (
        Path("benchmarks/run_eog_provenance_placement_multiseed_v40.py")
    ).read_text(encoding="utf-8")
    for banned in ("urllib","requests", "read_csv(", "Geneticassignment_README",
                   "Dispersaldata.txt","mcp__"):
        assert banned not in script
    assert "bayes_information" in script
    assert "prepare_design" in script
    assert "source_cover" not in script
    assert "v39_one_seed" in script
