import numpy as np

from eog.v2.predictive_state_gate import (
    PredictiveStateDesign,
    audit_predictive_state_refresh,
    evaluate_predictive_state_design,
)


def test_generation_shift_blocks_default_predictive_use():
    design = PredictiveStateDesign(
        repeated_measure_endpoint=True,
        train_generator_id="leave_node_out_static",
        serve_generator_id="common_fold_static",
        refresh_policy="static_reused",
        source_policy="lexicographic_single_source",
        source_label_invariant=False,
        baseline_contains_spatial_coordinates=True,
    )
    result = evaluate_predictive_state_design(design)
    assert result.status == "ineligible_generation_shift"
    assert result.predictive_use_allowed is False
    assert result.generator_parity is False
    assert "train_and_serve_feature_generators_differ" in result.reasons
    assert "prediction_facing_source_policy_depends_on_arbitrary_source_labels" in result.reasons
    assert "repeated_endpoint_reuses_static_state_without_predictive_opt_in" in result.reasons
    assert "static_state_may_duplicate_or_reencode_baseline_spatial_identity" in result.warnings


def test_static_reuse_is_structural_only_even_when_generator_matches():
    design = PredictiveStateDesign(
        repeated_measure_endpoint=True,
        train_generator_id="static_node",
        serve_generator_id="static_node",
        refresh_policy="static_reused",
        source_policy="symmetric_sources",
        source_label_invariant=True,
    )
    result = evaluate_predictive_state_design(design)
    assert result.status == "structural_only_static_reuse"
    assert result.predictive_use_allowed is False


def test_sequential_source_symmetric_design_is_candidate_not_guaranteed_benefit():
    design = PredictiveStateDesign(
        repeated_measure_endpoint=True,
        train_generator_id="sequential_preoutcome_v2",
        serve_generator_id="sequential_preoutcome_v2",
        refresh_policy="sequential_context",
        source_policy="symmetric_observed_source_set",
        source_label_invariant=True,
        baseline_contains_spatial_coordinates=True,
    )
    result = evaluate_predictive_state_design(design)
    assert result.status == "predictive_complement_candidate"
    assert result.predictive_use_allowed is True
    assert result.reasons == ()


def test_source_label_dependence_blocks_even_for_dynamic_state():
    design = PredictiveStateDesign(
        repeated_measure_endpoint=True,
        train_generator_id="sequential",
        serve_generator_id="sequential",
        refresh_policy="sequential_context",
        source_policy="lexicographically_smallest_node",
        source_label_invariant=False,
    )
    result = evaluate_predictive_state_design(design)
    assert result.status == "ineligible_source_label_dependence"
    assert result.predictive_use_allowed is False


def test_refresh_audit_detects_node_constant_reuse():
    features = np.asarray(
        [
            [0.2, 0.8],
            [0.2, 0.8],
            [0.2, 0.8],
            [0.7, 0.1],
            [0.7, 0.1],
        ],
        dtype=float,
    )
    audit = audit_predictive_state_refresh(
        features, ["node_a", "node_a", "node_a", "node_b", "node_b"]
    )
    assert audit.repeated_entity_count == 2
    assert audit.constant_repeated_entity_fraction == 1.0
    assert audit.refresh_fraction == 0.0
    assert audit.exact_unique_state_count == 2


def test_refresh_audit_detects_context_change():
    features = np.asarray(
        [
            [0.2, 0.8],
            [0.3, 0.7],
            [0.3, 0.7],
            [0.7, 0.1],
            [0.6, 0.2],
        ],
        dtype=float,
    )
    audit = audit_predictive_state_refresh(
        features, ["node_a", "node_a", "node_a", "node_b", "node_b"]
    )
    assert audit.repeated_entity_count == 2
    assert audit.constant_repeated_entity_fraction == 0.0
    assert audit.consecutive_transition_count == 3
    assert audit.changed_transition_count == 2
    assert audit.refresh_fraction == 2 / 3
