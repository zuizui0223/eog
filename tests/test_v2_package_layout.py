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


def test_new_prospective_reachability_apis_stay_on_explicit_facade():
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
        "ForecastGateDeclaration",
        "WorldForecastMember",
        "ForecastNodeEnvelope",
        "WorldSetForecast",
        "ForecastUpdate",
        "ForecastFrontierCandidate",
        "ForecastFrontierRanking",
        "build_worldset_forecast",
        "forecast_from_occurrences",
        "update_worldset_forecast",
        "rank_worldset_forecast_frontier",
        "MonotoneRelaxationFamily",
        "BasinMergeResult",
        "build_monotone_relaxation_family",
        "infer_basin_merge",
        "TemporalWorld",
        "TemporalFlowSet",
        "build_temporal_flow_set",
        "TemporalWorldReconstruction",
        "TemporalReconstructionUpdate",
        "reconstruct_temporal_worlds",
        "compare_temporal_reconstructions",
        "PositiveTemporalSurveyRanking",
        "rank_positive_temporal_occurrence_candidates",
        "TemporalTransitionLandscape",
        "TemporalTransitionUniverseUpdate",
        "summarize_temporal_transition_landscape",
        "compare_temporal_transition_universes",
        "TemporalRelaxationDeclaration",
        "TemporalRelaxationFrontier",
        "minimum_temporal_relaxation_frontier",
    ):
        assert hasattr(reachability, name)
        assert not hasattr(v2, name)


def test_v2_facades_keep_estimands_separated():
    assert hasattr(reachability, "summarize_first_passage")
    assert hasattr(reachability, "reconstruct_compatible_worlds")
    assert hasattr(reachability, "build_world_flow_set")
    assert hasattr(reachability, "forecast_from_occurrences")
    assert hasattr(reachability, "update_worldset_forecast")
    assert hasattr(reachability, "rank_worldset_forecast_frontier")
    assert hasattr(reachability, "infer_basin_merge")
    assert hasattr(reachability, "build_temporal_flow_set")
    assert hasattr(reachability, "reconstruct_temporal_worlds")
    assert hasattr(reachability, "rank_positive_temporal_occurrence_candidates")
    assert hasattr(reachability, "summarize_temporal_transition_landscape")
    assert hasattr(reachability, "compare_temporal_transition_universes")
    assert hasattr(reachability, "minimum_temporal_relaxation_frontier")
    assert not hasattr(reachability, "evaluate_genetic_validation_ladder")
    assert not hasattr(reachability, "evaluate_directional_order_evidence")
    assert hasattr(traversability, "summarize_path_traversability")
    assert hasattr(traversability, "compare_occurrence_transition_rules")
    assert not hasattr(traversability, "FiniteWorldReconstruction")
    assert not hasattr(traversability, "WorldSetForecast")
    assert not hasattr(traversability, "BasinMergeResult")
    assert not hasattr(traversability, "TemporalFlowSet")
    assert not hasattr(traversability, "TemporalWorldReconstruction")
    assert not hasattr(traversability, "PositiveTemporalSurveyRanking")
    assert not hasattr(traversability, "TemporalTransitionLandscape")
    assert not hasattr(traversability, "TemporalTransitionUniverseUpdate")
    assert not hasattr(traversability, "TemporalRelaxationFrontier")
    assert not hasattr(traversability, "GeneticValidationConfig")
    assert not hasattr(traversability, "evaluate_directional_order_evidence")
    assert hasattr(validation, "GeneticValidationConfig")
    assert hasattr(validation, "evaluate_directional_order_evidence")
    assert not hasattr(validation, "FiniteWorldReconstruction")
    assert not hasattr(validation, "WorldSetForecast")
    assert not hasattr(validation, "BasinMergeResult")
    assert not hasattr(validation, "TemporalFlowSet")
    assert not hasattr(validation, "TemporalWorldReconstruction")
    assert not hasattr(validation, "PositiveTemporalSurveyRanking")
    assert not hasattr(validation, "TemporalTransitionLandscape")
    assert not hasattr(validation, "TemporalTransitionUniverseUpdate")
    assert not hasattr(validation, "TemporalRelaxationFrontier")
    assert not hasattr(validation, "EcologicalTransitionEdge")
