"""Exact target-specific posterior information, synthetic only."""
from __future__ import annotations

from copy import deepcopy
import json

import pytest

from benchmarks.run_eog_provenance_ecological_state_v41 import (
    BOUNDARY, FINGERPRINTS, HYPOTHESES, PROTOCOL, TARGETS,
    V23, V25, V26, V39, V40, target_bayes_information,
    _perfect_alias_status, verify_sources, _synthetic_present_targets,
)
from benchmarks.run_eog_imperfect_provenance_sampling_v39 import (
    bayes_information as original_v39_history_information,
)
from benchmarks.run_eog_original_idea_history_to_state_process_family_v26 import (
    _process_map, _age_map,
)
from benchmarks.run_eog_original_idea_virtual_worlds_v2 import _generate_base
from benchmarks.run_eog_original_idea_directed_temporal_flow_v5 import (
    _graphs, _outlet_corner, _truth_source,
)
from benchmarks.run_eog_original_idea_source_placement_v18 import (
    RULE, _candidate_sources, _source_sets,
)
from benchmarks.run_eog_imperfect_provenance_sampling_v39 import prepare_design


def files():
    protocol=json.loads(PROTOCOL.read_text(encoding="utf-8"))
    sources={
        "v23":json.loads(V23.read_text(encoding="utf-8")),
        "v25":json.loads(V25.read_text(encoding="utf-8")),
        "v26":json.loads(V26.read_text(encoding="utf-8")),
        "v39":json.loads(V39.read_text(encoding="utf-8")),
        "v40":json.loads(V40.read_text(encoding="utf-8")),
    }
    return protocol,sources


def invented():
    occupancy={"h1":("A",),"h2":("A",),"h3":("B",)}
    tags={
        "p":{"h1":("origin1",),"h2":("origin2",),"h3":("origin1",)},
        "constant":{"h1":("origin1",),"h2":("origin1",),"h3":("origin1",)}
    }
    maturity={"h1":("mature",),"h2":("immature",),"h3":("mature",)}
    no_history_target={h:("mature",) for h in occupancy}
    exact={h:h for h in occupancy}
    return occupancy,tags,maturity,no_history_target,exact


def test_noise_likelihood_exact_history_independently_matches_parent_v39():
    occ,tags,_,_,history=invented()
    for sites in ((),("p",),("constant",),("p","constant")):
        for q in (0,0.25,0.6,1):
            for e in (0,0.1,0.25):
                r=target_bayes_information(occ,history,tags,sites,q,e)
                v=original_v39_history_information(occ,tags,sites,q,e)
                assert r["information_bits"]==pytest.approx(v["additional_information_bits"],abs=1e-9)
                assert r["bayes_correct_target_gain"]==pytest.approx(v["bayes_accuracy_gain"],abs=1e-9)
                assert r["base_conditional_entropy_bits"]==pytest.approx(v["baseline_conditional_entropy_bits"],abs=1e-9)


def test_target_information_is_conditional_not_a_claim_of_full_history_recovery():
    o,t,mat,unresponsive,h=invented()
    a=target_bayes_information(o,h,t,("p",),0.6,0.1)
    b=target_bayes_information(o,mat,t,("p",),0.6,0.1)
    assert a["information_bits"]>0
    assert b["information_bits"]>0
    assert b["information_bits"]<=a["information_bits"]+1e-9
    assert b["bayes_correct_target_gain"]>0
    zero=target_bayes_information(o,unresponsive,t,("p",),0.6,0.1)
    assert zero["information_bits"]==0
    assert zero["bayes_correct_target_gain"]==0
    assert zero["base_bayes_correct_target_probability"]==pytest.approx(1)


def test_target_known_from_occupancy_yields_zero_new_ecological_information():
    occ,tags,mat,_,h=invented()
    mature_by_occupancy={"h1":("a",),"h2":("a",),"h3":("b",)}
    r=target_bayes_information(occ,mature_by_occupancy,tags,("p",),0.6,0.1)
    assert r["base_conditional_entropy_bits"]==pytest.approx(0)
    assert r["information_bits"]==pytest.approx(0,abs=1e-10)
    assert r["bayes_correct_target_gain"]==pytest.approx(0,abs=1e-10)


def test_static_unique_origin_and_zero_coverage_are_sound_negative_controls():
    occ,tags,mat,_,_=invented()
    for e in (0,0.1,0.25):
        assert target_bayes_information(occ,mat,tags,("p",),0,e)["information_bits"]==0
        for q in (0.25,0.6,1):
            r=target_bayes_information(occ,mat,tags,("constant",),q,e)
            assert r["information_bits"]==pytest.approx(0,abs=1e-9)
            assert r["bayes_correct_target_gain"]==pytest.approx(0,abs=1e-9)


def test_perfect_full_tags_may_resolve_history_or_leave_ecological_targets_aliased():
    occ,tags,mature,_,_=invented()
    statuses=_perfect_alias_status(occ,tags,{"persistent_threshold_lag2":mature})
    assert statuses["history_unresolved"] is False
    assert statuses["source_and_occupancy_equivalent_but_target_differs"]["persistent_threshold_lag2"] is False
    tags2={
        "p":{"h1":("same",),"h2":("same",),"h3":("same",)}
    }
    again=_perfect_alias_status(occ,tags2,{"persistent_threshold_lag2":mature})
    assert again["history_unresolved"] is True
    assert again["source_and_occupancy_equivalent_but_target_differs"]["persistent_threshold_lag2"] is True


def test_age_mappings_are_identical_to_predeclared_v26_processes():
    ages=(("n1",0),("n2",1),("n3",2),("n4",3),("n5",4))
    assert _process_map("persistent_threshold_lag2",ages)==(
        ("n1",False),("n2",False),("n3",True),("n4",True),("n5",True)
    )
    assert _process_map("transient_window_age1_2",ages)==(
        ("n1",False),("n2",True),("n3",True),("n4",False),("n5",False)
    )
    assert _process_map("saturating_age_class_cap3",ages)==(
        ("n1",0),("n2",1),("n3",2),("n4",3),("n5",3)
    )
    assert _process_map("history_blind_occupancy",ages)==tuple((n,True) for n,_ in ages)
    assert _age_map(((0,0),(0,1)),{(0,0):3,(0,1):4},5)==(
        ("r0c0",2),("r0c1",1)
    )


def test_prior_v23_to_v40_source_and_five_v41_hypotheses_are_fixed():
    p,s=files()
    verify_sources(p,s)
    assert p["fixed_design"]["perfect_combined_aliases_with_different_lag2_mature_target"]==12
    assert p["fixed_design"]["perfect_combined_aliases_with_different_transient_age1_2_target"]==45
    assert p["fixed_design"]["parent_lag2_age_sensitive_worlds"]==726
    assert p["source_tag_assay"]["coverage_q"]==0.6
    assert p["source_tag_assay"]["miscall_e"]==0.1
    assert tuple(t["id"] for t in p["falsifiable_predictions"])==HYPOTHESES
    assert p["scientific_boundaries"]==BOUNDARY
    assert len(TARGETS)==5
    assert s["v40"]["authority"]["full_canonical_json_sha256"]==FINGERPRINTS["v40"]


def test_forged_ecological_claims_or_noise_selection_changes_fail_closed():
    p,s=files()
    change=deepcopy(p)
    change["scientific_boundaries"]["no_fourth_EOG_WF_predictive_endpoint_or_submission_change"]=False
    with pytest.raises(ValueError,match="boundary"):
        verify_sources(change,s)
    change=deepcopy(p)
    change["source_tag_assay"]["miscall_e"]=0.01
    with pytest.raises(ValueError,match="model"):
        verify_sources(change,s)
    change=deepcopy(p)
    change["present_state_targets"]["persistent_threshold_lag2"]="lag 3"
    with pytest.raises(ValueError):
        verify_sources(change,s)


def test_synthetic_v23_same_world_reconstructs_target_family():
    base=_generate_base(0,"low","rook")
    outlet=_outlet_corner(0,"low","rook")
    anchor=_truth_source(base,outlet)
    candidates,_=_candidate_sources(base,outlet,anchor)
    sets=_source_sets(candidates,anchor)
    _,graph=_graphs(base,0.20,RULE,outlet)
    x=prepare_design(graph,sets["clustered"][3],"r0-synthetic")
    t=_synthetic_present_targets(graph,sets["clustered"][3])
    assert set(t)==set(TARGETS)
    assert set(x["occupancy"])==set(t["exact_activation_history"])
    assert all(len(per_hist)==3 for per_hist in t.values())
    assert len(set(t["history_blind_occupancy"].values()))==1


def test_outcome_generator_contains_no_original_genetic_data_import_or_lookahead():
    text=__import__("pathlib").Path(
        "benchmarks/run_eog_provenance_ecological_state_v41.py"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "import urllib", "import requests","read_csv(", "Dispersaldata.txt",
        "Geneticassignment_README.txt", "mcp__"
    ):
        assert forbidden not in text
    assert "bayes_information" in text
    assert "_process_map" in text


def test_original_v41_full_result_frozen_sha256_and_ecological_target_contrast():
    receipt = json.loads((
        PROTOCOL.parent / "result_frozen_v41.json"
    ).read_text(encoding="utf-8"))
    assert receipt["schema"] == (
        "eog.original_idea.noisy_provenance_ecological_state_value.frozen_review_v41"
    )
    assert receipt["pre_result_protocol_commit"] == (
        "a812771a2d033b634dc95aceac0dc311a842a1e0"
    )
    auth=receipt["authority"]
    assert auth["github_actions_run_id"] == 39248967844
    assert auth["github_actions_artifact_id"] == 12184367871
    assert auth["artifact_zip_sha256"] == (
        "9d98a1cc1704954f9c9f8f9487f85748a1368f6422fbd3125b6ee964647f4527"
    )
    assert auth["complete_canonical_json_sha256"] == (
        "34f6f2bd94b9b22854eb699c97607ec2b9408f0ea55bcd6d5103a4019581125d"
    )
    c=receipt["contrast_counts_on_189_occupancy_aliases"]
    assert c["confluence_source_tags_improve_both_history_and_lag2_maturity_in_designs"]==48
    assert c["confluence_source_tags_improve_history_but_not_lag2_maturity_in_designs"]==72
    assert c["confluence_source_tags_improve_lag2_maturity_in_designs"]==48
    a=receipt["confluence_mean_over_189_occupancy_alias"]
    assert a["exact_activation_history"]["positive_worlds"]==120
    assert a["exact_activation_history"]["information_bits"]==pytest.approx(0.4041694132190281)
    assert a["persistent_threshold_lag2"]["information_bits"]==pytest.approx(0.14064779,abs=1e-8)
    assert a["transient_window_age1_2"]["information_bits"]==pytest.approx(0.17751462,abs=1e-8)
    assert a["saturating_age_class_cap3"]["information_bits"]==pytest.approx(0.20838477,abs=1e-8)
    assert receipt["perfect_full_source_alias_target_disagreement_counts"] == {
        "exact_activation_history":81,
        "history_blind_occupancy":0,
        "persistent_threshold_lag2":12,
        "transient_window_age1_2":45,
        "saturating_age_class_cap3":45,
    }
    assert all(v=="SUPPORTED" for v in receipt["predeclared_verdicts"].values())
    assert all(v==0 for v in receipt["negative_controls"].values())
    assert receipt["scientific_bounds"]["2021_genetic_archive_raw_data_not_accessed"] is True
    assert receipt["scientific_bounds"]["no_new_EOG_WF_empirical_endpoint"] is True
