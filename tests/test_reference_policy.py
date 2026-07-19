import pytest

from eog import ReferenceDeclaration, allowed_claim_scope, validate_reference_declaration


def test_external_prospective_reference_is_valid():
    declaration = ReferenceDeclaration(
        mode="external",
        intent="prospective",
        source_description="archived calibration background",
        fitted_before_evaluation=True,
        includes_evaluation_groups=False,
    )
    validate_reference_declaration(declaration)
    assert "held-out" in allowed_claim_scope(declaration)


def test_training_only_reference_rejects_evaluation_groups():
    declaration = ReferenceDeclaration(
        mode="training-only",
        intent="prospective",
        source_description="baseline group",
        fitted_before_evaluation=True,
        includes_evaluation_groups=True,
    )
    with pytest.raises(ValueError, match="cannot include evaluation groups"):
        validate_reference_declaration(declaration)


def test_pooled_reference_is_retrospective_only():
    declaration = ReferenceDeclaration(
        mode="pooled-descriptive",
        intent="prospective",
        source_description="all compared groups",
        fitted_before_evaluation=True,
        includes_evaluation_groups=True,
    )
    with pytest.raises(ValueError, match="retrospective only"):
        validate_reference_declaration(declaration)


def test_outcome_informed_reference_is_rejected():
    declaration = ReferenceDeclaration(
        mode="external",
        intent="prospective",
        source_description="reference selected after viewing group labels",
        fitted_before_evaluation=True,
        includes_evaluation_groups=False,
        outcome_informed=True,
    )
    with pytest.raises(ValueError, match="outcome-informed"):
        validate_reference_declaration(declaration)


def test_declaration_round_trip():
    original = ReferenceDeclaration(
        mode="pooled-descriptive",
        intent="retrospective",
        source_description="pooled occurrence groups",
        fitted_before_evaluation=False,
        includes_evaluation_groups=True,
    )
    restored = ReferenceDeclaration.from_dict(original.to_dict())
    assert restored == original
    assert "retrospective" in allowed_claim_scope(restored)
