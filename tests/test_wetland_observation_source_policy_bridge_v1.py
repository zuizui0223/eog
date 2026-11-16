"""Source-policy monotonicity guard uses REAL EOG APIs on an explicit toy graph.

No synthetic node is a geographic wetland and no rule support is a field
occupancy / movement probability.
"""
import pytest

from eog.v2.world_reconstruction import reconstruct_compatible_worlds
from benchmarks import wetland_observation_source_policy_bridge_v1 as m


def test_eog_fixed_source_compatible_world_set_only_expands_when_C_dropped():
    r=m.evaluate_source_policies(m.synthetic_worlds())
    fixed=r["fixed_source"]
    assert fixed["compatibility_before_all_occurrences"]==["complete"]
    assert fixed["compatibility_after_dropping_C"]==["complete","isolated_C"]
    assert fixed["positive_constraint_loss_expands_compatible_set"]
    update=fixed["added_positive_EOG_native_compare_reconstructions_update"]
    assert update["retained_world_ids"]==["complete"]
    assert update["eliminated_world_ids"]==["isolated_C"]
    assert update["contraction_fraction"]==pytest.approx(0.5)
    assert update["after_addition_compatible_set_narrowed"]
    assert all(
        entry["source_policy"]=="fixed"
        and entry["fixed_source_ids"]==["A"]
        for panel in fixed["results"].values()
        for entry in panel["world_compatibility"].values()
    )


def test_eog_self_excluded_peer_source_reweighting_swaps_world_membership():
    r=m.evaluate_source_policies(m.synthetic_worlds())
    selfx=r["self_excluded"]
    assert selfx["compatible_sets"]=={
        "all_three":["complete","hub"],
        "gated_two":["complete","isolated_C"],
    }
    assert selfx["gained_compatible_worlds_after_dropping_C"]==["isolated_C"]
    assert selfx["lost_compatible_worlds_after_dropping_C"]==["hub"]
    assert selfx["both_sets_have_equal_compatible_world_count_but_different_membership"]
    assert not selfx["self_excluded_monotone_world_set_inclusion_claim_valid"]
    assert selfx["NOT_eligible_for_EOG_fixed_source_compare_reconstructions"]
    hub_full=selfx["results"]["all_three"]["hub"]
    hub_drop=selfx["results"]["gated_two"]["hub"]
    assert hub_full["compatible"] and hub_full["unsupported_occurrence_ids"]==[]
    assert not hub_drop["compatible"]
    assert hub_drop["unsupported_occurrence_ids"]==["A","B"]
    assert hub_drop["coverage_fraction"]==0.0
    isolated_full=selfx["results"]["all_three"]["isolated_C"]
    isolated_drop=selfx["results"]["gated_two"]["isolated_C"]
    assert not isolated_full["compatible"]
    assert isolated_full["unsupported_occurrence_ids"]==["C"]
    assert isolated_drop["compatible"]
    assert isolated_drop["coverage_fraction"]==1.0
    assert all(
        v["source_policy"]=="self_excluded"
        for pair in selfx["results"].values()
        for v in pair.values()
    )


def test_peer_source_composition_changes_with_obs_not_world_definition():
    r=m.evaluate_source_policies(m.synthetic_worlds())
    assert r["world_operator_fingerprints_frozen_across_both_observation_sets"]
    assert not r["real_wetland_nodes_mapped_to_synthetic_ABC"]
    full_target_a=next(
        z for z in r["self_excluded"]["results"]["all_three"]["hub"]["targets"]
        if z["target"]=="A"
    )
    gated_target_a=next(
        z for z in r["self_excluded"]["results"]["gated_two"]["hub"]["targets"]
        if z["target"]=="A"
    )
    assert full_target_a["source_ids"]==["B","C"]
    assert gated_target_a["source_ids"]==["B"]
    assert full_target_a["first_passage_support"]>0.0
    assert gated_target_a["first_passage_support"]==0.0


def test_fixed_source_reconstruction_rejects_removing_declared_source_A():
    worlds=m.synthetic_worlds()
    with pytest.raises(ValueError,match="observed fixed sources"):
        reconstruct_compatible_worlds(worlds,("B","C"),max_steps=1)


def test_original_native_wetland_not_abstract_graph():
    assert m.NODE_IDS==("A","B","C")
    assert m.SOURCE_SITE not in m.NODE_IDS
    assert m.SOURCE_SPECIES=="Hyla arborea"
    assert m.ORIGINAL_WITNESS_EXPECTED=={
        ("2024-03-24","visual",6),("2024-05-30","dipnet",368)
    }
    assert len(m.synthetic_worlds())==3


def test_original_source_guard_rejects_tampered_survey_before_real_ecological_mapping(tmp_path):
    fake_s=tmp_path/"fake_surveys.csv"
    fake_t=tmp_path/"fake_sites.csv"
    fake_s.write_text("site,method\nfake,visual\n")
    fake_t.write_text("site,ci\nfake,control\n")
    with pytest.raises(ValueError,match="source SHA256 mismatch"):
        m.authenticate_wetland_split(fake_s,fake_t)
