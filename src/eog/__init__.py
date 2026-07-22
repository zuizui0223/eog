"""Environmental occupancy geometry public API."""

from .bridge import (
    BridgeEdge,
    BridgeInference,
    BridgePath,
    BridgeWeights,
    environmental_edge_costs,
    infer_bridge,
)
from .bridge_builder import (
    BridgeGraphDeclaration,
    BridgeNode,
    BuiltBridgeGraph,
    build_bridge_graph,
    haversine_km,
)
from .bridge_sensitivity import (
    BridgeMetricSummary,
    BridgeScenarioResult,
    BridgeSensitivityResult,
    BridgeSensitivityScenario,
    evaluate_bridge_sensitivity,
)
from .support_topology import (
    ComponentRecovery,
    OccurrenceAnchor,
    SupportComponent,
    SupportGridMetadata,
    SupportTopologyConfig,
    SupportTopologyResult,
    assign_occurrence_anchors,
    evaluate_component_recovery,
    evaluate_support_topology_sensitivity,
    infer_support_topology,
    summarize_support_components,
)
from .survey_priority import (
    SurveyCandidate,
    SurveyPriorityResult,
    SurveyPriorityRow,
    SurveyPriorityWeights,
    rank_survey_candidates,
)
from .hypothesis_discrimination import (
    BridgeHypothesis,
    HypothesisDiscriminationResult,
    HypothesisDiscriminationRow,
    HypothesisDiscriminationWeights,
    rank_hypothesis_discriminating_sites,
)
from .hypothesis_adapter import (
    HypothesisAdapterResult,
    HypothesisFamilyDeclaration,
    HypothesisFamilySummary,
    build_bridge_hypotheses,
)
from .hypothesis_survey_pipeline import (
    HypothesisSurveyPipelineResult,
    run_hypothesis_survey_pipeline,
)
from .hypothesis_survey_io import (
    HypothesisSurveyRunBundle,
    load_candidates_csv,
    load_families_csv,
    load_sensitivity_csv,
    run_hypothesis_survey_csv,
)
from .hypothesis_survey_report import (
    HypothesisSurveyReport,
    render_hypothesis_survey_report,
)
from .hypothesis_survey_verify import (
    HypothesisSurveyVerification,
    verify_hypothesis_survey_bundle,
)
from .comparative import (
    RobustReference,
    fit_robust_reference,
    infer_comparative_geometry,
    transform_with_reference,
)
from .geometry import (
    OccupancyGeometry,
    infer_occupancy_geometry,
    minimum_spanning_tree,
    pairwise_distances,
    project_states,
    robust_scale,
)
from .manifest import (
    AnalysisManifest,
    ResultBundle,
    build_result_bundle,
    manifest_fingerprint,
    render_result_text,
    validate_manifest,
)
from .reference_policy import (
    ReferenceDeclaration,
    allowed_claim_scope,
    validate_reference_declaration,
)
from .runner import AuditedInput, load_audited_csv, run_frozen_analysis
from .uncertainty import ComparativeContrast, compare_geometry, reference_fingerprint

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
