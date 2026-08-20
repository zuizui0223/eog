from __future__ import annotations

import pytest

from eog.v2.response_schema import (
    CategoricalTokenRule,
    ResponseTokenSchemaDeclaration,
    canonicalize_categorical_token,
    normalize_categorical_token,
)


def test_default_rule_strips_and_casefolds_but_preserves_internal_space():
    rule = CategoricalTokenRule(
        field_name="Season",
        canonical_values=("Spring", "Summer"),
    )
    assert normalize_categorical_token(rule, "  SPRING  ") == "spring"
    assert canonicalize_categorical_token(rule, "spring") == "Spring"
    with pytest.raises(ValueError, match="unknown categorical token"):
        rule.canonicalize("spr ing")


def test_internal_ascii_whitespace_equivalence_is_explicit():
    strict = CategoricalTokenRule(
        field_name="Week",
        canonical_values=("week 1", "week 2", "week 3", "week 4"),
        remove_internal_ascii_whitespace=False,
    )
    permissive = CategoricalTokenRule(
        field_name="Week",
        canonical_values=("week 1", "week 2", "week 3", "week 4"),
        remove_internal_ascii_whitespace=True,
    )

    with pytest.raises(ValueError, match="unknown categorical token"):
        strict.canonicalize("week1")
    assert permissive.canonicalize("week1") == "week 1"
    assert permissive.canonicalize(" Week\t1 ") == "week 1"
    assert strict.fingerprint != permissive.fingerprint


def test_normalization_collision_is_rejected():
    with pytest.raises(ValueError, match="collide after normalization"):
        CategoricalTokenRule(
            field_name="Week",
            canonical_values=("week 1", "week1"),
            remove_internal_ascii_whitespace=True,
        )


def test_unknown_empty_none_and_numeric_tokens_fail_closed():
    rule = CategoricalTokenRule(
        field_name="State",
        canonical_values=("present", "absent"),
    )
    with pytest.raises(ValueError, match="unknown categorical token"):
        rule.canonicalize("maybe")
    with pytest.raises(ValueError, match="normalizes to empty"):
        rule.canonicalize("   ")
    with pytest.raises(ValueError, match="must not be None"):
        rule.canonicalize(None)
    with pytest.raises(TypeError, match="token must be str"):
        rule.canonicalize(1)


def test_schema_rule_order_does_not_change_fingerprint():
    week = CategoricalTokenRule(
        field_name="Week",
        canonical_values=("week 1", "week 2"),
        remove_internal_ascii_whitespace=True,
    )
    season = CategoricalTokenRule(
        field_name="Season",
        canonical_values=("SP10", "SU10"),
    )
    first = ResponseTokenSchemaDeclaration(rules=(week, season))
    second = ResponseTokenSchemaDeclaration(rules=(season, week))
    assert first.fingerprint == second.fingerprint
    assert first.canonicalize("Week", "WEEK2") == "week 2"


def test_duplicate_schema_fields_are_rejected():
    first = CategoricalTokenRule(field_name="Week", canonical_values=("1", "2"))
    second = CategoricalTokenRule(field_name="Week", canonical_values=("a", "b"))
    with pytest.raises(ValueError, match="field names must be unique"):
        ResponseTokenSchemaDeclaration(rules=(first, second))


def test_fingerprint_changes_with_canonical_categories_and_normalization_choice():
    base = CategoricalTokenRule(
        field_name="Week",
        canonical_values=("week 1", "week 2"),
    )
    changed_values = CategoricalTokenRule(
        field_name="Week",
        canonical_values=("week 1", "week 3"),
    )
    changed_normalization = CategoricalTokenRule(
        field_name="Week",
        canonical_values=("week 1", "week 2"),
        remove_internal_ascii_whitespace=True,
    )
    assert base.fingerprint != changed_values.fingerprint
    assert base.fingerprint != changed_normalization.fingerprint


def test_invalid_rule_and_schema_types_fail_closed():
    with pytest.raises(TypeError, match="canonical_values must be a sequence"):
        CategoricalTokenRule(field_name="Week", canonical_values="week1")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="canonical_values must contain only strings"):
        CategoricalTokenRule(field_name="Week", canonical_values=(1, 2))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="field_name must be str"):
        CategoricalTokenRule(field_name=1, canonical_values=("a",))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="strip_outer_whitespace must be bool"):
        CategoricalTokenRule(
            field_name="Week",
            canonical_values=("week1",),
            strip_outer_whitespace=1,  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="rules must contain only"):
        ResponseTokenSchemaDeclaration(rules=("not-a-rule",))  # type: ignore[arg-type]
    schema = ResponseTokenSchemaDeclaration(
        rules=(CategoricalTokenRule(field_name="Week", canonical_values=("week1",)),)
    )
    with pytest.raises(TypeError, match="field_name must be str"):
        schema.rule_for(1)


def test_validation_facade_exposes_response_schema_without_root_widening():
    from eog.v2 import validation

    assert validation.CategoricalTokenRule is CategoricalTokenRule
    assert validation.ResponseTokenSchemaDeclaration is ResponseTokenSchemaDeclaration
    assert validation.normalize_categorical_token is normalize_categorical_token
    assert validation.canonicalize_categorical_token is canonicalize_categorical_token

    import eog.v2 as v2

    assert "CategoricalTokenRule" not in v2.__all__
