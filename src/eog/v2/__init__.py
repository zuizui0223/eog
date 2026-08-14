"""Prospective EOG v2 compatibility namespace.

The active repository direction is defined in ``docs/development_mainline.md``.
The v2 namespace is intentionally thin: new code should import from the explicit
``reachability``, ``traversability`` or ``validation`` facades rather than widening
this package root. Historical ``from eog.v2 import ...`` imports remain available
through lazy attribute routing so frozen workflows do not need to move with the
repository narrative.
"""

from __future__ import annotations

from importlib import import_module
from typing import Final


# Historical v2 convenience exports retained for frozen/reproduction compatibility.
# New prospective APIs (including finite-world reconstruction and basin merge) live
# only on their explicit owning facade.
_REACHABILITY_EXPORTS: Final[tuple[str, ...]] = (
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
)

_TRAVERSABILITY_EXPORTS: Final[tuple[str, ...]] = (
    "OccurrenceEnvironmentalScale",
    "EcologicalTransitionEdge",
    "TraversabilityTransitionBundle",
    "PathTraversabilitySummary",
    "DispersalMode",
    "fit_occurrence_environmental_scale",
    "environmental_transition_support",
    "build_traversability_transition_bundle",
    "summarize_path_traversability",
    "OccurrenceTargetCompatibility",
    "OccurrenceRuleCompatibility",
    "OccurrenceRuleComparison",
    "evaluate_occurrence_rule_compatibility",
    "compare_occurrence_transition_rules",
)

_VALIDATION_EXPORTS: Final[tuple[str, ...]] = (
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
    "FixedSourceOccurrenceFeatures",
    "OccurrenceModelScore",
    "FixedSourceOccurrenceValidationResult",
    "build_fixed_source_occurrence_features",
    "evaluate_fixed_source_occurrence_validation",
    "DirectionalStatus",
    "CombinedRuleStatus",
    "DirectionalOrderConstraint",
    "DirectionalEvidenceRow",
    "DirectionalRuleEvidence",
    "RuleEvidenceStatus",
    "TransitionRuleEvidenceComparison",
    "evaluate_directional_order_evidence",
    "combine_occurrence_and_directional_evidence",
)

_EXPORT_MODULE: Final[dict[str, str]] = {
    **{name: "reachability" for name in _REACHABILITY_EXPORTS},
    **{name: "traversability" for name in _TRAVERSABILITY_EXPORTS},
    **{name: "validation" for name in _VALIDATION_EXPORTS},
}

__all__ = [
    *_REACHABILITY_EXPORTS,
    *_TRAVERSABILITY_EXPORTS,
    *_VALIDATION_EXPORTS,
]

# Kept unchanged because frozen tests and external reproduction paths use this
# status string. The separate direction marker records the active architecture
# without rewriting the historical v2 contract.
API_STATUS = "prospective-v2-development"
DEVELOPMENT_DIRECTION = "distributional-watershed-world-reconstruction"


def __getattr__(name: str):
    """Resolve historical v2 convenience imports through the declared facade."""

    module_name = _EXPORT_MODULE.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(f"{__name__}.{module_name}")
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Expose the compatibility surface without eagerly importing its modules."""

    return sorted(set(globals()) | set(__all__))
