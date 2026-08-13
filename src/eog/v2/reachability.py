"""Reachability-facing public API for prospective EOG v2."""

from ..dynamic_island_reachability import (
    DynamicReachabilityEdge,
    DynamicReachabilityResult,
    DynamicTransitionOperator,
    FirstPassageSummary,
    build_dynamic_transition_operator,
    propagate_dynamic_reachability,
    summarize_first_passage,
)
from ..island_state_layers import (
    AreaSupportDeclaration,
    AreaSupportResult,
    IslandStateLayers,
    area_support_layers,
    assemble_island_state_layers,
)
from ..reachability_html import render_dynamic_reachability_html
from ..reachability_network_diagnostics import (
    BridgeNodeImportanceResult,
    NetworkFluxDiagnostics,
    evaluate_bridge_node_importance,
    summarize_network_flux,
)
from ..reachability_visualization import build_dynamic_reachability_visualization_payload
from ..synthetic_archipelago import SCENARIO_IDS, SyntheticArchipelagoScenario, build_synthetic_archipelago

__all__ = [
    "DynamicReachabilityEdge",
    "DynamicReachabilityResult",
    "DynamicTransitionOperator",
    "FirstPassageSummary",
    "build_dynamic_transition_operator",
    "propagate_dynamic_reachability",
    "summarize_first_passage",
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
    "render_dynamic_reachability_html",
    "SCENARIO_IDS",
    "SyntheticArchipelagoScenario",
    "build_synthetic_archipelago",
]
