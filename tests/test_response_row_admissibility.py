from __future__ import annotations

import pytest

from eog.v2.response_row_admissibility import (
    ResponseFieldMissingPolicy,
    ResponseRowAdmissibilityDeclaration,
    evaluate_response_row_admissibility,
)


def _declaration() -> ResponseRowAdmissibilityDeclaration:
    return ResponseRowAdmissibilityDeclaration(
        policies=(
            ResponseFieldMissingPolicy(
                field_name="species",
                disposition="exclude_row",
                none_is_missing=True,
                empty_after_normalization_is_missing=True,
                literal_missing_tokens=("NA", "unknown"),
            ),
            ResponseFieldMissingPolicy(
                field_name="plot",
                disposition="stop",
                none_is_missing=True,
                empty_after_normalization_is_missing=True,
            ),
        )
    )


def test_declared_empty_species_can_be_excluded_only_when_predeclared():
    result = evaluate_response_row_admissibility(
        _declaration(),
        {"species": "   ", "plot": "1"},
    )
    assert result.status == "exclude_row_declared_missing"
    assert result.include is False
    assert result.excluded is True
    assert result.stop is False
    assert result.missing_fields == ("species",)
    assert result.absent_fields == ()


def test_declared_stop_missing_takes_precedence_over_exclusion():
    result = evaluate_response_row_admissibility(
        _declaration(),
        {"species": "NA", "plot": None},
    )
    assert result.status == "stop_declared_missing"
    assert result.stop is True
    assert result.excluded is False
    assert result.missing_fields == ("plot", "species")


def test_absent_declared_field_stops_before_token_disposition():
    result = evaluate_response_row_admissibility(
        _declaration(),
        {"species": "DM"},
    )
    assert result.status == "stop_required_field_absent"
    assert result.absent_fields == ("plot",)
    assert result.stop is True


def test_unknown_nonmissing_token_is_not_reinterpreted_as_missing():
    result = evaluate_response_row_admissibility(
        _declaration(),
        {"species": "mystery-code", "plot": "1"},
    )
    assert result.status == "include_row"
    assert result.missing_fields == ()
    # A later categorical response-token schema remains responsible for rejecting
    # an unknown non-missing category.  This gate must never convert it to missing.


def test_literal_missing_normalization_is_explicit_and_fingerprinted():
    strict = ResponseFieldMissingPolicy(
        field_name="species",
        disposition="exclude_row",
        literal_missing_tokens=("not available",),
        remove_internal_ascii_whitespace=False,
    )
    compact = ResponseFieldMissingPolicy(
        field_name="species",
        disposition="exclude_row",
        literal_missing_tokens=("not available",),
        remove_internal_ascii_whitespace=True,
    )
    assert strict.is_declared_missing(" NOT AVAILABLE ") is True
    assert strict.is_declared_missing("notavailable") is False
    assert compact.is_declared_missing("notavailable") is True
    assert strict.fingerprint != compact.fingerprint


def test_empty_and_none_are_not_missing_unless_explicitly_declared():
    policy = ResponseFieldMissingPolicy(field_name="species", disposition="stop")
    declaration = ResponseRowAdmissibilityDeclaration(policies=(policy,))

    empty = evaluate_response_row_admissibility(declaration, {"species": ""})
    none = evaluate_response_row_admissibility(declaration, {"species": None})
    assert empty.status == "include_row"
    assert none.status == "include_row"


def test_policy_order_does_not_change_declaration_fingerprint():
    a = ResponseFieldMissingPolicy(
        field_name="species",
        disposition="exclude_row",
        empty_after_normalization_is_missing=True,
    )
    b = ResponseFieldMissingPolicy(
        field_name="plot",
        disposition="stop",
        none_is_missing=True,
    )
    first = ResponseRowAdmissibilityDeclaration(policies=(a, b))
    second = ResponseRowAdmissibilityDeclaration(policies=(b, a))
    assert first.fingerprint == second.fingerprint


def test_result_fingerprint_does_not_depend_on_raw_missing_spelling():
    declaration = ResponseRowAdmissibilityDeclaration(
        policies=(
            ResponseFieldMissingPolicy(
                field_name="species",
                disposition="exclude_row",
                literal_missing_tokens=("NA", "unknown"),
            ),
        )
    )
    na = evaluate_response_row_admissibility(declaration, {"species": "NA"})
    unknown = evaluate_response_row_admissibility(declaration, {"species": "UNKNOWN"})
    assert na.status == unknown.status
    assert na.missing_fields == unknown.missing_fields
    assert na.fingerprint == unknown.fingerprint


def test_invalid_declarations_fail_closed():
    with pytest.raises(ValueError, match="disposition"):
        ResponseFieldMissingPolicy(field_name="species", disposition="drop")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="sequence of strings"):
        ResponseFieldMissingPolicy(field_name="species", literal_missing_tokens="NA")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="contain only strings"):
        ResponseFieldMissingPolicy(field_name="species", literal_missing_tokens=(1,))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="normalize to empty"):
        ResponseFieldMissingPolicy(field_name="species", literal_missing_tokens=("   ",))
    with pytest.raises(ValueError, match="collide"):
        ResponseFieldMissingPolicy(
            field_name="species",
            literal_missing_tokens=("NA", " na "),
        )
    with pytest.raises(ValueError, match="field names must be unique"):
        ResponseRowAdmissibilityDeclaration(
            policies=(
                ResponseFieldMissingPolicy(field_name="species"),
                ResponseFieldMissingPolicy(field_name="species"),
            )
        )
    with pytest.raises(TypeError, match="row must be a mapping"):
        evaluate_response_row_admissibility(_declaration(), [])  # type: ignore[arg-type]


def test_validation_facade_exposes_row_admissibility_without_root_widening():
    from eog.v2 import validation

    assert validation.ResponseFieldMissingPolicy is ResponseFieldMissingPolicy
    assert validation.ResponseRowAdmissibilityDeclaration is ResponseRowAdmissibilityDeclaration
    assert validation.evaluate_response_row_admissibility is evaluate_response_row_admissibility

    import eog.v2 as v2

    assert "ResponseRowAdmissibilityDeclaration" not in v2.__all__
