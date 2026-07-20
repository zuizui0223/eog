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
from .survey_priority import (
    SurveyCandidate,
    SurveyPriorityResult,
    SurveyPriorityRow,
    SurveyPriorityWeights,
    rank_survey_candidates,
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
    "SurveyCandidate",
    "SurveyPriorityWeights",
    "SurveyPriorityRow",
    "SurveyPriorityResult",
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
    "rank_survey_candidates",
]

__version__ = "0.1.0"
