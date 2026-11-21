"""Exhaustive EOG-v2 source-policy certificate, not empirical ecology."""
import pytest

from benchmarks import exhaustive_three_node_source_policy_v1 as m


@pytest.fixture(scope="module")
def audited():
    return m.exhaustive_native_source_policy_audit()


def test_six_directed_edges_exhaust_every_three_node_simple_graph():
    assert m.GRAPH_COUNT==64
    assert m.NODE_IDS==("A","B","C")
    assert len(m.EDGE_BITS)==6
    assert len(set(m.EDGE_BITS))==6
    assert all(a!=b for a,b in m.EDGE_BITS)
    assert m.edges_from_mask(0)==()
    assert set(m.edges_from_mask(63))==set(m.EDGE_BITS)
    assert m.edges_from_mask(5)==(("A","B"),("B","A"))
    assert m.edges_from_mask(58)==(
        ("A","C"),("B","C"),("C","A"),("C","B")
    )
    assert m.edges_from_mask(63)==m.EDGE_BITS


def test_native_fixed_positive_only_monotonicity_exact_across_64_graphs(audited):
    fixed=audited["native_fixed_policy"]
    assert (fixed["full_count"],fixed["gated_count"])==(16,32)
    assert (fixed["shared_count"],fixed["lost_count"],fixed["gained_count"])==(16,0,16)
    assert fixed["full_subset_gated"]
    assert not fixed["gated_subset_full"]
    assert fixed["compatible_set_monotone_under_positive_witness_loss"]
    assert fixed["added_positive_eliminated_worlds"]==16
    assert fixed["added_positive_retained_worlds"]==16
    assert fixed["added_positive_contraction_fraction"]==pytest.approx(0.5)
    assert "mask_63" in fixed["full_compatible_world_ids"]
    assert "mask_05" in fixed["gated_compatible_world_ids"]
    assert "mask_05" not in fixed["full_compatible_world_ids"]


def test_native_self_excluded_positive_restriction_can_lose_and_gain_worlds(audited):
    selfx=audited["native_self_excluded_policy"]
    assert (selfx["full_count"],selfx["gated_count"])==(27,16)
    assert (selfx["shared_count"],selfx["lost_count"],selfx["gained_count"],
            selfx["neither_count"])==(12,15,4,33)
    assert not selfx["full_subset_gated"]
    assert not selfx["gated_subset_full"]
    assert selfx["monotone_compatible_set_inclusion_does_not_hold"]
    assert selfx["NOT_eligible_for_fixed_source_compare_reconstructions"]
    assert "mask_58" in selfx["lost_world_ids_after_dropping_C"]
    assert "mask_05" in selfx["gained_world_ids_after_dropping_C"]
    assert "mask_63" in selfx["shared_world_ids"]
    assert len(set(selfx["full_compatible_world_ids"]) |
               set(selfx["gated_compatible_world_ids"]))==31


def test_all_64_native_EOG_decisions_equal_independent_directed_bit_logic(audited):
    rows=audited["rows"]
    assert len(rows)==64
    assert {r["edge_mask"] for r in rows}==set(range(64))
    assert {r["graph_id"] for r in rows}=={
        f"mask_{i:02d}" for i in range(64)
    }
    assert audited["native_EOG_decisions_agree_with_independent_analytic_edge_predicates_for_all_worlds"]
    for r in rows:
        expected=m.analytic_one_step_mask_compatibility(r["edge_mask"])
        assert r["EOG_fixed_full_ABC_compatible"]==int(expected["fixed_full"])
        assert r["EOG_fixed_gated_AB_compatible"]==int(expected["fixed_gated"])
        assert r["EOG_self_excluded_full_ABC_compatible"]==int(expected["self_full"])
        assert r["EOG_self_excluded_gated_AB_compatible"]==int(expected["self_gated"])
        assert r["world_fingerprint"] and r["operator_fingerprint"]
        assert r["declared_fixed_source"]=="A"


def test_three_prior_synthetic_examples_are_in_complete_world_universe(audited):
    rows=audited["rows"]
    assert audited["prior_example_world_bit_masks"]=={
        "hub":58, "isolated_C":5, "complete":63
    }
    assert (
        rows[58]["EOG_self_excluded_full_ABC_compatible"],
        rows[58]["EOG_self_excluded_gated_AB_compatible"]
    )==(1,0)
    assert (
        rows[5]["EOG_self_excluded_full_ABC_compatible"],
        rows[5]["EOG_self_excluded_gated_AB_compatible"]
    )==(0,1)
    assert (
        rows[63]["EOG_self_excluded_full_ABC_compatible"],
        rows[63]["EOG_self_excluded_gated_AB_compatible"]
    )==(1,1)


@pytest.mark.parametrize("bad_mask",[-1,64,1.0,True,"5",None])
def test_undeclared_graph_mask_fails_closed(bad_mask):
    with pytest.raises(ValueError,match="integer 0..63"):
        m.edges_from_mask(bad_mask)


def test_ecological_status_is_explicitly_not_inferred_from_synthetic_worlds(audited):
    assert audited["status"]=="COMPLETE_64_SYNTHETIC_EOG_WORLD_SOURCE_POLICY_EXHAUSTION_NOT_REAL_ECOLOGY"
    assert not audited["real_EOG_ecological_worlds_enumerated"]
    assert audited["native_fixed_source_frozen_operator_universe"]
    assert audited["graph_count"]==64
    assert audited["observations_gated"]==["A","B"]
    assert audited["observations_full"]==["A","B","C"]
    assert audited["synthetic_declared_fixed_source"]=="A"
