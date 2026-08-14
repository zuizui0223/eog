"""Ecological-traversability public API for prospective EOG v2.

The facade is lazy so occurrence-rule constraints are not imported merely by opening
the traversability namespace.
"""
from __future__ import annotations

from importlib import import_module
from typing import Final


_TRAVERSABILITY_EXPORTS: Final[tuple[str, ...]] = (
    "DispersalMode",
    "OccurrenceEnvironmentalScale",
    "EcologicalTransitionEdge",
    "TraversabilityTransitionBundle",
    "PathTraversabilitySummary",
    "fit_occurrence_environmental_scale",
    "environmental_transition_support",
    "build_traversability_transition_bundle",
    "summarize_path_traversability",
)

_OCCURRENCE_EXPORTS: Final[tuple[str, ...]] = (
    "OccurrenceTargetCompatibility",
    "OccurrenceRuleCompatibility",
    "OccurrenceRuleComparison",
    "evaluate_occurrence_rule_compatibility",
    "compare_occurrence_transition_rules",
)

_EXPORT_MODULE: Final[dict[str, str]] = {
    **{name: "eog.ecological_traversability" for name in _TRAVERSABILITY_EXPORTS},
    **{name: "eog.v2.occurrence_constraints" for name in _OCCURRENCE_EXPORTS},
}

__all__ = [*_TRAVERSABILITY_EXPORTS, *_OCCURRENCE_EXPORTS]


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
