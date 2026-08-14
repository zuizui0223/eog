"""Environmental occupancy geometry public compatibility API.

The root namespace is frozen for v0.1 reproduction paths, so historical public
names remain available.  Imports are resolved lazily to keep unrelated geometry,
topology, bridge, island and survey implementation trees decoupled at package
import time.  Prospective development belongs behind explicit operator facades;
see ``docs/development_mainline.md``.
"""

from __future__ import annotations

from importlib import import_module
from typing import Final


_MODULE_EXPORTS: Final[dict[str, tuple[str, ...]]] = {
    "geometry": (
        "OccupancyGeometry",
        "robust_scale",
        "pairwise_distances",
        "minimum_spanning_tree",
        "infer_occupancy_geometry",
        "project_states",
    ),
    "comparative": (
        "RobustReference",
        "fit_robust_reference",
        "transform_with_reference",
        "infer_comparative_geometry",
    ),
    "reference_policy": (
        "ReferenceDeclaration",
        "validate_reference_declaration",
        "allowed_claim_scope",
    ),
    "uncertainty": (
        "ComparativeContrast",
        "reference_fingerprint",
        "compare_geometry",
    ),
    "manifest": (
        "AnalysisManifest",
        "ResultBundle",
        "manifest_fingerprint",
        "validate_manifest",
        "render_result_text",
        "build_result_bundle",
    ),
    "runner": (
        "AuditedInput",
        "load_audited_csv",
        "run_frozen_analysis",
    ),
    "bridge": (
        "BridgeEdge",
        "BridgeInference",
        "BridgePath",
        "BridgeWeights",
        "environmental_edge_costs",
        "infer_bridge",
    ),
    "bridge_builder": (
        "BridgeNode",
        "BridgeGraphDeclaration",
        "BuiltBridgeGraph",
        "haversine_km",
        "build_bridge_graph",
    ),
    "bridge_sensitivity": (
        "BridgeSensitivityScenario",
        "BridgeScenarioResult",
        "BridgeMetricSummary",
        "BridgeSensitivityResult",
        "evaluate_bridge_sensitivity",
    ),
    "island_reachability": (
        "IslandReachabilityScenario",
        "IslandReachabilityScenarioResult",
        "IslandReachabilityResult",
        "default_aislands_reachability_scenarios",
        "evaluate_island_reachability",
        "nearest_anchor_distance_km",
    ),
    "conditional_reachability": (
        "ConditionalConcordance",
        "conditional_reachability_concordance",
    ),
    "support_model": (
        "PenalizedLogisticSupportModel",
        "SupportModelError",
        "fit_penalized_logistic_support",
    ),
    "support_topology": (
        "SupportGridMetadata",
        "SupportTopologyConfig",
        "OccurrenceAnchor",
        "SupportComponent",
        "SupportTopologyResult",
        "ComponentRecovery",
        "assign_occurrence_anchors",
        "infer_support_topology",
        "summarize_support_components",
        "evaluate_component_recovery",
        "evaluate_support_topology_sensitivity",
    ),
    "survey_priority": (
        "SurveyCandidate",
        "SurveyPriorityWeights",
        "SurveyPriorityRow",
        "SurveyPriorityResult",
        "rank_survey_candidates",
    ),
    "hypothesis_discrimination": (
        "BridgeHypothesis",
        "HypothesisDiscriminationWeights",
        "HypothesisDiscriminationRow",
        "HypothesisDiscriminationResult",
        "rank_hypothesis_discriminating_sites",
    ),
    "hypothesis_adapter": (
        "HypothesisFamilyDeclaration",
        "HypothesisFamilySummary",
        "HypothesisAdapterResult",
        "build_bridge_hypotheses",
    ),
    "hypothesis_survey_pipeline": (
        "HypothesisSurveyPipelineResult",
        "run_hypothesis_survey_pipeline",
    ),
    "hypothesis_survey_io": (
        "HypothesisSurveyRunBundle",
        "load_sensitivity_csv",
        "load_families_csv",
        "load_candidates_csv",
        "run_hypothesis_survey_csv",
    ),
    "hypothesis_survey_verify": (
        "HypothesisSurveyVerification",
        "verify_hypothesis_survey_bundle",
    ),
    "hypothesis_survey_report": (
        "HypothesisSurveyReport",
        "render_hypothesis_survey_report",
    ),
}

_EXPORT_MODULE: Final[dict[str, str]] = {
    name: module_name
    for module_name, names in _MODULE_EXPORTS.items()
    for name in names
}

# Preserve the historical public ordering to avoid changing wildcard-import or
# generated-document behaviour unnecessarily.
__all__ = [
    "OccupancyGeometry",
    "RobustReference",
    "ReferenceDeclaration",
    "ComparativeContrast",
    "AnalysisManifest",
    "ResultBundle",
    "AuditedInput",
    "BridgeEdge",
    "BridgeInference",
    "BridgePath",
    "BridgeWeights",
    "BridgeNode",
    "BridgeGraphDeclaration",
    "BuiltBridgeGraph",
    "BridgeSensitivityScenario",
    "BridgeScenarioResult",
    "BridgeMetricSummary",
    "BridgeSensitivityResult",
    "IslandReachabilityScenario",
    "IslandReachabilityScenarioResult",
    "IslandReachabilityResult",
    "ConditionalConcordance",
    "PenalizedLogisticSupportModel",
    "SupportModelError",
    "SupportGridMetadata",
    "SupportTopologyConfig",
    "OccurrenceAnchor",
    "SupportComponent",
    "SupportTopologyResult",
    "ComponentRecovery",
    "SurveyCandidate",
    "SurveyPriorityWeights",
    "SurveyPriorityRow",
    "SurveyPriorityResult",
    "BridgeHypothesis",
    "HypothesisDiscriminationWeights",
    "HypothesisDiscriminationRow",
    "HypothesisDiscriminationResult",
    "HypothesisFamilyDeclaration",
    "HypothesisFamilySummary",
    "HypothesisAdapterResult",
    "HypothesisSurveyPipelineResult",
    "HypothesisSurveyRunBundle",
    "HypothesisSurveyVerification",
    "HypothesisSurveyReport",
    "robust_scale",
    "fit_robust_reference",
    "transform_with_reference",
    "reference_fingerprint",
    "compare_geometry",
    "manifest_fingerprint",
    "validate_manifest",
    "render_result_text",
    "build_result_bundle",
    "load_audited_csv",
    "run_frozen_analysis",
    "pairwise_distances",
    "minimum_spanning_tree",
    "infer_occupancy_geometry",
    "infer_comparative_geometry",
    "validate_reference_declaration",
    "allowed_claim_scope",
    "project_states",
    "environmental_edge_costs",
    "infer_bridge",
    "haversine_km",
    "build_bridge_graph",
    "evaluate_bridge_sensitivity",
    "default_aislands_reachability_scenarios",
    "evaluate_island_reachability",
    "nearest_anchor_distance_km",
    "conditional_reachability_concordance",
    "fit_penalized_logistic_support",
    "assign_occurrence_anchors",
    "infer_support_topology",
    "summarize_support_components",
    "evaluate_component_recovery",
    "evaluate_support_topology_sensitivity",
    "rank_survey_candidates",
    "rank_hypothesis_discriminating_sites",
    "build_bridge_hypotheses",
    "run_hypothesis_survey_pipeline",
    "load_sensitivity_csv",
    "load_families_csv",
    "load_candidates_csv",
    "run_hypothesis_survey_csv",
    "verify_hypothesis_survey_bundle",
    "render_hypothesis_survey_report",
]

__version__ = "0.1.0"


def __getattr__(name: str):
    """Resolve frozen public names without eagerly importing unrelated modules."""

    module_name = _EXPORT_MODULE.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(f"{__name__}.{module_name}")
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Expose the frozen public surface without forcing implementation imports."""

    return sorted(set(globals()) | set(__all__))
