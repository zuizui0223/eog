import eog
import eog.v2 as v2


def test_v2_namespace_is_explicitly_prospective_and_does_not_change_v01_version():
    assert eog.__version__ == "0.1.0"
    assert v2.API_STATUS == "prospective-v2-development"
    assert callable(v2.build_dynamic_transition_operator)
    assert callable(v2.infer_eventual_genetic_connectivity)
    assert callable(v2.evaluate_nested_genetic_reference_selection)
    assert callable(v2.build_dynamic_reachability_visualization_payload)
    assert "directional_dispersal" in v2.SCENARIO_IDS
