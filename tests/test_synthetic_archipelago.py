import numpy as np

from eog.synthetic_archipelago import SCENARIO_IDS, build_synthetic_archipelago


def test_all_predeclared_synthetic_archipelagos_build_deterministically():
    assert set(SCENARIO_IDS) == {
        "geography_only",
        "environmental_isolation",
        "stepping_stone",
        "missing_intermediate",
        "single_bottleneck",
        "redundant_routes",
        "area_persistence",
        "directional_dispersal",
        "rare_long_jump",
        "local_extinction",
        "unsurveyed_intermediate",
        "multiple_sources",
    }
    for scenario_id in SCENARIO_IDS:
        a = build_synthetic_archipelago(scenario_id)
        b = build_synthetic_archipelago(scenario_id)
        assert a.fingerprint == b.fingerprint
        assert a.build_operator().fingerprint == b.build_operator().fingerprint


def test_local_extinction_keeps_historical_reachability_separate_from_current_occurrence():
    scenario = build_synthetic_archipelago("local_extinction")
    target = scenario.node_ids.index("target")
    assert scenario.historical_reached[target]
    assert not scenario.current_occurrence[target]


def test_unsurveyed_intermediate_remains_in_graph_but_is_not_a_source():
    scenario = build_synthetic_archipelago("unsurveyed_intermediate")
    step2 = scenario.node_ids.index("step2")
    assert not scenario.surveyed_mask[step2]
    assert "step2" not in scenario.source_ids
    operator = scenario.build_operator()
    assert np.any(operator.raw_support[step2] > 0.0)
    assert np.any(operator.raw_support[:, step2] > 0.0)


def test_directional_fixture_has_asymmetric_raw_transition_support():
    scenario = build_synthetic_archipelago("directional_dispersal")
    operator = scenario.build_operator()
    assert operator.raw_support[0, 1] > operator.raw_support[1, 0]
    assert operator.raw_support[1, 2] > operator.raw_support[2, 1]


def test_area_fixture_changes_area_without_changing_local_environment():
    scenario = build_synthetic_archipelago("area_persistence")
    small = scenario.node_ids.index("small_target")
    large = scenario.node_ids.index("large_target")
    assert scenario.area[small] < scenario.area[large]
    assert np.array_equal(
        scenario.environmental_state[small],
        scenario.environmental_state[large],
    )


def test_multiple_source_fixture_declares_sources_without_promoting_target():
    scenario = build_synthetic_archipelago("multiple_sources")
    assert scenario.source_ids == ("left_source", "right_source")
    target = scenario.node_ids.index("target")
    assert not scenario.current_occurrence[target]
