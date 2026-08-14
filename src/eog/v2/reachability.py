"""Reachability-facing public API for prospective EOG v2.

The facade is intentionally lazy. Importing ``eog.v2.reachability`` should not load
presentation code, system-specific synthetic fixtures, or every prospective operator
implementation. Historical/public names are preserved and resolved only when accessed.
"""
from __future__ import annotations

from importlib import import_module
from typing import Final


_DYNAMIC_EXPORTS: Final[tuple[str, ...]] = (
    "DynamicReachabilityEdge",
    "DynamicReachabilityResult",
    "DynamicTransitionOperator",
    "FirstPassageSummary",
    "build_dynamic_transition_operator",
    "propagate_dynamic_reachability",
    "summarize_first_passage",
)

_STATE_LAYER_EXPORTS: Final[tuple[str, ...]] = (
    "AreaSupportDeclaration",
    "AreaSupportResult",
    "IslandStateLayers",
    "area_support_layers",
    "assemble_island_state_layers",
)

_NETWORK_EXPORTS: Final[tuple[str, ...]] = (
    "NetworkFluxDiagnostics",
    "BridgeNodeImportanceResult",
    "summarize_network_flux",
    "evaluate_bridge_node_importance",
)

_WORLD_EXPORTS: Final[tuple[str, ...]] = (
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
)

_RELAXATION_EXPORTS: Final[tuple[str, ...]] = (
    "MonotoneRelaxationFamily",
    "BasinMergeResult",
    "build_monotone_relaxation_family",
    "infer_basin_merge",
)

_TEMPORAL_FLOW_EXPORTS: Final[tuple[str, ...]] = (
    "TemporalWorld",
    "TemporalFlowSet",
    "build_temporal_flow_set",
)

_TEMPORAL_RECONSTRUCTION_EXPORTS: Final[tuple[str, ...]] = (
    "TemporalWorldReconstruction",
    "TemporalReconstructionUpdate",
    "reconstruct_temporal_worlds",
    "compare_temporal_reconstructions",
)

_TEMPORAL_SURVEY_EXPORTS: Final[tuple[str, ...]] = (
    "PositiveTemporalSurveyRanking",
    "rank_positive_temporal_occurrence_candidates",
)

_TEMPORAL_TRANSITION_EXPORTS: Final[tuple[str, ...]] = (
    "TemporalTransitionLandscape",
    "summarize_temporal_transition_landscape",
)

_SYNTHETIC_EXPORTS: Final[tuple[str, ...]] = (
    "SCENARIO_IDS",
    "SyntheticArchipelagoScenario",
    "build_synthetic_archipelago",
)

_PRESENTATION_EXPORTS: Final[tuple[str, ...]] = (
    "build_dynamic_reachability_visualization_payload",
    "render_dynamic_reachability_html",
)

_EXPORT_MODULE: Final[dict[str, str]] = {
    **{name: "eog.dynamic_island_reachability" for name in _DYNAMIC_EXPORTS},
    **{name: "eog.island_state_layers" for name in _STATE_LAYER_EXPORTS},
    **{name: "eog.reachability_network_diagnostics" for name in _NETWORK_EXPORTS},
    **{name: "eog.v2.world_reconstruction" for name in _WORLD_EXPORTS},
    **{name: "eog.v2.relaxation_family" for name in _RELAXATION_EXPORTS},
    **{name: "eog.v2.temporal_reachability" for name in _TEMPORAL_FLOW_EXPORTS},
    **{
        name: "eog.v2.temporal_reconstruction"
        for name in _TEMPORAL_RECONSTRUCTION_EXPORTS
    },
    **{name: "eog.v2.temporal_survey" for name in _TEMPORAL_SURVEY_EXPORTS},
    **{
        name: "eog.v2.temporal_transition_landscape"
        for name in _TEMPORAL_TRANSITION_EXPORTS
    },
    **{name: "eog.synthetic_archipelago" for name in _SYNTHETIC_EXPORTS},
    "build_dynamic_reachability_visualization_payload": "eog.reachability_visualization",
    "render_dynamic_reachability_html": "eog.reachability_html",
}

__all__ = [
    *_DYNAMIC_EXPORTS,
    *_STATE_LAYER_EXPORTS,
    *_NETWORK_EXPORTS,
    *_PRESENTATION_EXPORTS,
    *_SYNTHETIC_EXPORTS,
    *_WORLD_EXPORTS,
    *_RELAXATION_EXPORTS,
    *_TEMPORAL_FLOW_EXPORTS,
    *_TEMPORAL_RECONSTRUCTION_EXPORTS,
    *_TEMPORAL_SURVEY_EXPORTS,
    *_TEMPORAL_TRANSITION_EXPORTS,
]


def __getattr__(name: str):
    """Resolve a public reachability name from its owning implementation lazily."""

    module_name = _EXPORT_MODULE.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
