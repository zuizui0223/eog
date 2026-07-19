"""Policy declarations for auditable comparative EOG references."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

ReferenceMode = Literal["external", "training-only", "pooled-descriptive"]
AnalysisIntent = Literal["prospective", "retrospective"]


@dataclass(frozen=True)
class ReferenceDeclaration:
    """Declare how a shared scaling reference was constructed and may be used."""

    mode: ReferenceMode
    intent: AnalysisIntent
    source_description: str
    fitted_before_evaluation: bool
    includes_evaluation_groups: bool
    outcome_informed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReferenceDeclaration":
        required = {
            "mode",
            "intent",
            "source_description",
            "fitted_before_evaluation",
            "includes_evaluation_groups",
            "outcome_informed",
        }
        missing = required.difference(payload)
        if missing:
            raise ValueError(f"reference declaration missing fields: {sorted(missing)}")
        declaration = cls(
            mode=str(payload["mode"]),
            intent=str(payload["intent"]),
            source_description=str(payload["source_description"]),
            fitted_before_evaluation=bool(payload["fitted_before_evaluation"]),
            includes_evaluation_groups=bool(payload["includes_evaluation_groups"]),
            outcome_informed=bool(payload["outcome_informed"]),
        )
        validate_reference_declaration(declaration)
        return declaration


def validate_reference_declaration(declaration: ReferenceDeclaration) -> None:
    """Reject reference constructions that overstate prospective validity."""
    if declaration.mode not in {"external", "training-only", "pooled-descriptive"}:
        raise ValueError("unsupported reference mode")
    if declaration.intent not in {"prospective", "retrospective"}:
        raise ValueError("unsupported analysis intent")
    if not declaration.source_description.strip():
        raise ValueError("source_description must be non-empty")
    if declaration.outcome_informed:
        raise ValueError("outcome-informed reference construction is invalid")
    if declaration.intent == "prospective" and not declaration.fitted_before_evaluation:
        raise ValueError("prospective references must be fitted before evaluation")
    if declaration.mode in {"external", "training-only"} and declaration.includes_evaluation_groups:
        raise ValueError(f"{declaration.mode} reference cannot include evaluation groups")
    if declaration.mode == "pooled-descriptive":
        if declaration.intent != "retrospective":
            raise ValueError("pooled-descriptive reference is retrospective only")
        if not declaration.includes_evaluation_groups:
            raise ValueError("pooled-descriptive reference must include the compared groups")


def allowed_claim_scope(declaration: ReferenceDeclaration) -> str:
    """Return the strongest permitted interpretation for a valid declaration."""
    validate_reference_declaration(declaration)
    if declaration.mode == "pooled-descriptive":
        return "symmetric retrospective comparison in pooled reference units"
    return "held-out comparative extent in the declared frozen reference units"
