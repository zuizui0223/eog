import pytest
from eog.v2.adequacy_complete_ladder import plan_adequacy_complete_lcc_targets
from eog.v2.world_adequacy import StructuralAdequacyDeclaration

def test_algar_38_nodes_adds_integer_aware_target_for_isolated_ceiling():
    p=plan_adequacy_complete_lcc_targets(38,(0.25,0.50,0.75,0.90),StructuralAdequacyDeclaration(min_largest_weak_component_fraction=0.90,max_isolated_node_fraction=0.05))
    assert p.max_isolated_nodes==1
    assert 37/38 in p.required_lcc_targets
    assert p.completed_targets[-1]==37/38

def test_lcc_minimum_is_rounded_to_attainable_finite_n_fraction():
    p=plan_adequacy_complete_lcc_targets(7,(0.5,),StructuralAdequacyDeclaration(min_largest_weak_component_fraction=0.8))
    assert p.required_lcc_targets==(6/7,)

def test_zero_isolated_ceiling_requires_full_component_target():
    p=plan_adequacy_complete_lcc_targets(20,(0.5,0.9),StructuralAdequacyDeclaration(max_isolated_node_fraction=0.0))
    assert p.completed_targets[-1]==1.0

def test_horizon_reachability_is_independent_design_problem():
    p=plan_adequacy_complete_lcc_targets(40,(0.5,0.9),StructuralAdequacyDeclaration(min_largest_weak_component_fraction=0.9,min_median_horizon_reachable_fraction=0.5))
    assert p.horizon_reachability_requires_independent_design is True

@pytest.mark.parametrize("n",[0,1,True])
def test_invalid_node_count_fails_closed(n):
    with pytest.raises(ValueError):
        plan_adequacy_complete_lcc_targets(n,(0.9,),StructuralAdequacyDeclaration(min_largest_weak_component_fraction=0.9))
