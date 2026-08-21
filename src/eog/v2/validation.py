"""Validation-facing public API for prospective EOG v2.

The facade is lazy so genetic, empirical-occurrence, directional-evidence, response
firewall, response-token schema, candidate preflight, prospective estimability,
outcome-access authorization, predictive complementarity, and response-blind
world-adequacy / scale-construction trees remain independent until accessed.
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

_RESPONSE_FIREWALL_EXPORTS: Final[tuple[str, ...]] = (
    "BoundedFirstRecord",
    "read_bounded_first_record_bytes",
    "read_bounded_first_record_text",
)

_RESPONSE_SCHEMA_EXPORTS: Final[tuple[str, ...]] = (
    "CategoricalTokenRule",
    "ResponseTokenSchemaDeclaration",
    "normalize_categorical_token",
    "canonicalize_categorical_token",
)

_CANDIDATE_PREFLIGHT_EXPORTS: Final[tuple[str, ...]] = (
    "CandidatePreflightStatus",
    "LayoutDesign",
    "CandidatePreflightDeclaration",
    "CandidatePreflightEvidence",
    "CandidatePreflightResult",
    "evaluate_candidate_preflight",
)

_PROSPECTIVE_ESTIMABILITY_EXPORTS: Final[tuple[str, ...]] = (
    "AggregateCountInterval",
    "AggregateEstimabilityEvidence",
    "ProspectiveEstimabilityDeclaration",
    "ProspectiveEstimabilityResult",
    "ProspectiveEstimabilityDisposition",
    "evaluate_prospective_estimability",
    "prospective_estimability_disposition",
)

_OUTCOME_ACCESS_EXPORTS: Final[tuple[str, ...]] = (
    "OutcomeAccessStatus",
    "REQUIRED_FREEZE_KEYS",
    "FrozenOutcomeAccessContract",
    "OutcomeAccessGateResult",
    "evaluate_outcome_access_gate",
)

_PREDICTIVE_COMPLEMENTARITY_EXPORTS: Final[tuple[str, ...]] = (
    "ComplementarityStatus",
    "PredictiveComplementarityDeclaration",
    "PairedOuterUnitScore",
    "PredictiveComplementarityResult",
    "evaluate_predictive_complementarity",
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

_WORLD_SCALE_EXPORTS: Final[tuple[str, ...]] = (
    "StructuralScaleLadderDeclaration",
    "StructuralScaleLevel",
    "StructuralScaleLadder",
    "build_structural_scale_ladder",
    "structural_scale_adjacencies",
    "compose_intersection_worlds",
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
    **{name: "eog.v2.response_firewall" for name in _RESPONSE_FIREWALL_EXPORTS},
    **{name: "eog.v2.response_schema" for name in _RESPONSE_SCHEMA_EXPORTS},
    **{name: "eog.v2.candidate_preflight" for name in _CANDIDATE_PREFLIGHT_EXPORTS},
    **{
        name: "eog.v2.prospective_estimability"
        for name in _PROSPECTIVE_ESTIMABILITY_EXPORTS
    },
    **{name: "eog.v2.outcome_access" for name in _OUTCOME_ACCESS_EXPORTS},
    **{
        name: "eog.v2.predictive_complementarity"
        for name in _PREDICTIVE_COMPLEMENTARITY_EXPORTS
    },
    **{name: "eog.v2.world_adequacy" for name in _WORLD_ADEQUACY_EXPORTS},
    **{name: "eog.v2.world_scale_ladder" for name in _WORLD_SCALE_EXPORTS},
}

__all__ = [
    *_EVENTUAL_GENETIC_EXPORTS,
    *_GENETIC_VALIDATION_EXPORTS,
    *_OCCURRENCE_VALIDATION_EXPORTS,
    *_DIRECTIONAL_EXPORTS,
    *_RESPONSE_FIREWALL_EXPORTS,
    *_RESPONSE_SCHEMA_EXPORTS,
    *_CANDIDATE_PREFLIGHT_EXPORTS,
    *_PROSPECTIVE_ESTIMABILITY_EXPORTS,
    *_OUTCOME_ACCESS_EXPORTS,
    *_PREDICTIVE_COMPLEMENTARITY_EXPORTS,
    *_WORLD_ADEQUACY_EXPORTS,
    *_WORLD_SCALE_EXPORTS,
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
