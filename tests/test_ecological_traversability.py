import numpy as np
import pytest

from eog.v2 import (
    EcologicalTransitionEdge,
    build_dynamic_transition_operator,
    build_traversability_transition_bundle,
    fit_occurrence_environmental_scale,
    summarize_first_passage,
    summarize_path_traversability,
)


def test_occurrence_environmental_scale_is_order_invariant_and_descriptive():
    states = np.array([[0.0, 0.0], [1.0, 0.0], [3.0, 0.0], [6.0, 0.0]])
    forward = fit_occurrence_environmental_scale(states, quantile=0.75)
    reverse = fit_occurrence_environmental_scale(states[::-1], quantile=0.75)

    assert forward.transition_scale == reverse.transition_scale
    assert forward.nearest_neighbor_distances == reverse.nearest_neighbor_distances
    assert forward.fingerprint == reverse.fingerprint
    assert forward.transition_scale > 0.0


def test_identical_occurrence_states_do_not_silently_define_a_transition_scale():
    with pytest.raises(ValueError, match="positive environmental spacing scale"):
        fit_occurrence_environmental_scale(np.ones((3, 2)))


def test_endpoint_ibe_can_be_zero_while_pathwise_environmental_discontinuity_is_large():
    states = np.array([[0.0], [2.0], [0.0]])
    viability = np.array([1.0, 0.01, 1.0])

    result = summarize_path_traversability(states, viability, [0, 1, 2])

    assert result.endpoint_environmental_distance == pytest.approx(0.0)
    assert result.cumulative_environmental_crossing == pytest.approx(4.0)
    assert result.environmental_bottleneck == pytest.approx(2.0)
    assert result.minimum_intermediate_viability == pytest.approx(0.01)
    assert result.niche_desert_penalty == pytest.approx(-np.log(0.01))


def test_direct_long_jump_bypasses_unrepresented_intermediate_viability():
    states = np.array([[0.0], [2.0], [0.0]])
    viability = np.array([1.0, 0.0, 1.0])

    continuous = summarize_path_traversability(states, viability, [0, 1, 2])
    jump = summarize_path_traversability(
        states,
        viability,
        [0, 2],
        dispersal_modes=["long_jump"],
    )

    assert continuous.minimum_intermediate_viability == 0.0
    assert continuous.niche_desert_penalty > 20.0
    assert jump.minimum_intermediate_viability is None
    assert jump.niche_desert_penalty == 0.0
    assert jump.long_jump_edge_count == 1


def test_continuous_transition_is_gated_by_transit_viability_but_long_jump_is_not():
    continuous = EcologicalTransitionEdge(
        0,
        1,
        geographic_support=0.5,
        environmental_distance=1.0,
        transit_viability=0.01,
        dispersal_mode="continuous",
    )
    jump = EcologicalTransitionEdge(
        0,
        1,
        geographic_support=0.5,
        environmental_distance=1.0,
        transit_viability=0.01,
        dispersal_mode="long_jump",
    )

    assert jump.effective_environmental_support(scale=1.0) == pytest.approx(
        100.0 * continuous.effective_environmental_support(scale=1.0)
    )


def test_traversability_bundle_feeds_existing_dynamic_operator_without_changing_it():
    scale = fit_occurrence_environmental_scale(
        np.array([[0.0], [1.0], [2.0], [3.0]])
    )
    edges = [
        EcologicalTransitionEdge(
            0,
            1,
            geographic_support=0.9,
            environmental_distance=1.0,
            transit_viability=1.0,
        ),
        EcologicalTransitionEdge(
            1,
            2,
            geographic_support=0.9,
            environmental_distance=1.0,
            transit_viability=0.05,
        ),
    ]
    bundle = build_traversability_transition_bundle(edges, environmental_scale=scale)
    operator = build_dynamic_transition_operator(
        ("source", "middle", "target"),
        bundle.dynamic_edges,
        loss_support=0.5,
    )
    passage = summarize_first_passage(
        operator,
        ["source"],
        "target",
        max_steps=2,
    )

    assert bundle.scale_source_fingerprint == scale.fingerprint
    assert passage.horizon_support > 0.0
    assert passage.horizon_support < 0.1
