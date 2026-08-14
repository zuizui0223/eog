import eog
import eog.v2 as v2
import eog.v2.reachability as reachability
import eog.v2.traversability as traversability
import eog.v2.validation as validation


def test_v2_keeps_historical_convenience_exports_backward_compatible():
    assert eog.__version__ == "0.1.0"
    assert v2.API_STATUS == "prospective-v2-development"
    assert v2.build_dynamic_transition_operator is reachability.build_dynamic_transition_operator
    assert v2.fit_occurrence_environmental_scale is traversability.fit_occurrence_environmental_scale
    assert v2.evaluate_genetic_validation_ladder is validation.evaluate_genetic_validation_ladder
    assert v2.evaluate_directional_order_evidence is validation.evaluate_directional_order_evidence


def test_new_finite_world_and_basin_merge_apis_stay_on_explicit_reachability_facade():
    for name in (
        "FiniteWorld",
        "FiniteWorldReconstruction",
        "FiniteWorldFlowSet",
        "RelaxationFrontier",
        "ReconstructionUpdate",
        "PositiveOccurrenceSurveyRanking",
        "forward_reachable_configuration",
        "reconstruct_compatible_worlds",
        "build_world_flow_set",
        "minimum_relaxation_frontier",
        "compare_reconstructions",
        "rank_positive_occurrence_candidates",
        "MonotoneRelaxationFamily",
        "BasinMergeResult",
        "build_monotone_relaxation_family",
        "infer_basin_merge",
    ):
        assert hasattr(reachability, name)
        assert not hasattr(v2, name)


def test_v2_facades_keep_estimands_separated():
    assert hasattr(reachability, "summarize_first_passage")
    assert hasattr(reachability, "reconstruct_compatible_worlds")
    assert hasattr(reachability, "build_world_flow_set")
    assert hasattr(reachability, "infer_basin_merge")
    assert not hasattr(reachability, "evaluate_genetic_validation_ladder")
    assert not hasattr(reachability, "evaluate_directional_order_evidence")
    assert hasattr(traversability, "summarize_path_traversability")
    assert hasattr(traversability, "compare_occurrence_transition_rules")
    assert not hasattr(traversability, "FiniteWorldReconstruction")
    assert not hasattr(traversability, "BasinMergeResult")
    assert not hasattr(traversability, "GeneticValidationConfig")
    assert not hasattr(traversability, "evaluate_directional_order_evidence")
    assert hasattr(validation, "GeneticValidationConfig")
    assert hasattr(validation, "evaluate_directional_order_evidence")
    assert not hasattr(validation, "FiniteWorldReconstruction")
    assert not hasattr(validation, "BasinMergeResult")
    assert not hasattr(validation, "EcologicalTransitionEdge")
