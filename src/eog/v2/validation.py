"""Validation-facing public API for prospective EOG v2.

The facade is lazy so genetic, empirical-occurrence, directional-evidence, and
response-blind world-adequacy trees remain independent until accessed.
"""
from __future__ import annotations

from importlib import import_module
from typing import Final


_EVENTUAL_GENETIC_EXPORTS: Final[tuple[str, ...]] = (
    "EventualGeneticConnectivity",
    "EventualGeneticValidationBundle",
    "infer_eventual_genetic_connectivity",
    "build_eventual_genetic_validation_bundle",
)

_GENETIC_VALIDATION_EXPORTS: Final[tuple[str, ...]] = (
    "GeneticValidationConfig",
    "GeneticValidationFoldResult",
    "GeneticValidationModelResult",
    "GeneticValidationContrast",
    "GeneticValidationResult",
    "evaluate_genetic_validation_ladder",
)

_OCCURRENCE_VALIDATION_EXPORTS: Final[tuple[str, ...]] = (
    "FixedSourceOccurrenceFeatures",
    "OccurrenceModelScore",
    "FixedSourceOccurrenceValidationResult",
    "build_fixed_source_occurrence_features",
    "evaluate_fixed_source_occurrence_validation",
)

_DIRECTIONAL_EXPORTS: Final[tuple[str, ...]] = (
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

_WORLD_ADEQUACY_EXPORTS: Final[tuple[str, ...]] = (
    "StructuralAdequacyDeclaration",
    "WorldStructuralAudit",
    "WorldStructuralGateResult",
    "WorldUniverseStructuralAudit",
    "WorldUniverseStructuralGate",
    "audit_world_universe_structure",
    "apply_structural_adequacy_gate",
)

_EXPORT_MODULE: Final[dict[str, str]] = {
    **{
        name: "eog.eventual_genetic_connectivity"
        for name in _EVENTUAL_GENETIC_EXPORTS
    },
    **{name: "eog.genetic_validation" for name in _GENETIC_VALIDATION_EXPORTS},
    **{
        name: "eog.v2_empirical_occurrence_validation"
        for name in _OCCURRENCE_VALIDATION_EXPORTS
    },
    **{name: "eog.v2.evidence_discrimination" for name in _DIRECTIONAL_EXPORTS},
    **{name: "eog.v2.world_adequacy" for name in _WORLD_ADEQUACY_EXPORTS},
}

__all__ = [
    *_EVENTUAL_GENETIC_EXPORTS,
    *_GENETIC_VALIDATION_EXPORTS,
    *_OCCURRENCE_VALIDATION_EXPORTS,
    *_DIRECTIONAL_EXPORTS,
    *_WORLD_ADEQUACY_EXPORTS,
]


def __getattr__(name: str):
    module_name = _EXPORT_MODULE.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
