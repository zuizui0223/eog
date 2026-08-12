"""Prospective EOG v2 dynamic-island API.

This namespace is intentionally separate from :mod:`eog`'s frozen v0.1 public API.
Objects exposed here remain prospective method-development interfaces until the v2
promotion gates are complete.
"""

from .dynamic_island_reachability import (
    DynamicReachabilityEdge,
    DynamicReachabilityResult,
    DynamicTransitionOperator,
    FirstPassageSummary,
    build_dynamic_transition_operator,
    propagate_dynamic_reachability,
    summarize_first_passage,
)
from .eventual_genetic_connectivity import (
    EventualGeneticConnectivity,
    EventualGeneticValidationBundle,
    build_eventual_genetic_validation_bundle,
    infer_eventual_genetic_connectivity,
)
from .genetic_validation import (
    GeneticValidationConfig,
    GeneticValidationContrast,
    GeneticValidationFoldResult,
    GeneticValidationModelResult,
    GeneticValidationResult,
    evaluate_genetic_validation_ladder,
)
from .island_state_layers import (
    AreaSupportDeclaration,
    AreaSupportResult,
    IslandStateLayers,
    area_support_layers,
    assemble_island_state_layers,
)
from .reachability_network_diagnostics import (
    BridgeNodeImportanceResult,
    NetworkFluxDiagnostics,
    evaluate_bridge_node_importance,
    summarize_network_flux,
)
from .reachability_visualization import build_dynamic_reachability_visualization_payload
from .synthetic_archipelago import SCENARIO_IDS, SyntheticArchipelagoScenario, build_synthetic_archipelago

__all__ = [
    "DynamicReachabilityEdge",
    "DynamicReachabilityResult",
    "DynamicTransitionOperator",
    "FirstPassageSummary",
    "build_dynamic_transition_operator",
    "propagate_dynamic_reachability",
    "summarize_first_passage",
    "EventualGeneticConnectivity",
    "EventualGeneticValidationBundle",
    "infer_eventual_genetic_connectivity",
    "build_eventual_genetic_validation_bundle",
    "GeneticValidationConfig",
    "GeneticValidationFoldResult",
    "GeneticValidationModelResult",
    "GeneticValidationContrast",
    "GeneticValidationResult",
    "evaluate_genetic_validation_ladder",
    "AreaSupportDeclaration",
    "AreaSupportResult",
    "IslandStateLayers",
    "area_support_layers",
    "assemble_island_state_layers",
    "NetworkFluxDiagnostics",
    "BridgeNodeImportanceResult",
    "summarize_network_flux",
    "evaluate_bridge_node_importance",
    "build_dynamic_reachability_visualization_payload",
    "SCENARIO_IDS",
    "SyntheticArchipelagoScenario",
    "build_synthetic_archipelago",
]

API_STATUS = "prospective-v2-development"
