"""Response-blind categorical token schema for once-only validation.

This module is validation infrastructure, not an ecological operator. It freezes the
small, deterministic text-normalization choices needed to interpret categorical
response tokens before row-level outcome access. A later response opening may use the
frozen rules, but may not invent aliases or alter normalization after seeing a token.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re


_ASCII_WHITESPACE = re.compile(r"[ \t\r\n\f\v]+")


def _canonical_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _clean_text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be str")
    if not value.strip():
        raise ValueError(f"{label} must be non-empty")
    return value


def _require_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{label} must be bool")
    return value


@dataclass(frozen=True)
class CategoricalTokenRule:
    """Frozen normalization and allowed categories for one response field.

    Normalization is intentionally narrow and deterministic. The rule can strip outer
    whitespace, Unicode-casefold the token, and optionally remove ASCII whitespace
    characters anywhere in the token. No fuzzy matching, punctuation removal, numeric
    coercion, or post-hoc alias table is performed.
    """

    field_name: str
    canonical_values: tuple[str, ...]
    strip_outer_whitespace: bool = True
    casefold: bool = True
    remove_internal_ascii_whitespace: bool = False

    def __post_init__(self) -> None:
        field = _clean_text(self.field_name, "field_name").strip()
        object.__setattr__(self, "field_name", field)

        if isinstance(self.canonical_values, (str, bytes)):
            raise TypeError("canonical_values must be a sequence of category strings")
        values = tuple(self.canonical_values)
        if not values:
            raise ValueError("canonical_values must contain at least one category")
        if not all(isinstance(value, str) for value in values):
            raise TypeError("canonical_values must contain only strings")
        if any(not value.strip() for value in values):
            raise ValueError("canonical_values must not contain empty categories")
        if len(set(values)) != len(values):
            raise ValueError("canonical_values must be unique before normalization")
        object.__setattr__(self, "canonical_values", values)

        _require_bool(self.strip_outer_whitespace, "strip_outer_whitespace")
        _require_bool(self.casefold, "casefold")
        _require_bool(
            self.remove_internal_ascii_whitespace,
            "remove_internal_ascii_whitespace",
        )

        normalized = [normalize_categorical_token(self, value) for value in values]
        if len(set(normalized)) != len(normalized):
            collisions: dict[str, list[str]] = {}
            for raw, norm in zip(values, normalized, strict=True):
                collisions.setdefault(norm, []).append(raw)
            repeated = {
                norm: raw_values
                for norm, raw_values in collisions.items()
                if len(raw_values) > 1
            }
            raise ValueError(
                "canonical categories collide after normalization: "
                f"{repeated}"
            )

    @property
    def normalized_to_canonical(self) -> dict[str, str]:
        return {
            normalize_categorical_token(self, value): value
            for value in self.canonical_values
        }

    @property
    def fingerprint(self) -> str:
        return _canonical_sha256(
            {
                "field_name": self.field_name,
                "canonical_values": list(self.canonical_values),
                "strip_outer_whitespace": self.strip_outer_whitespace,
                "casefold": self.casefold,
                "remove_internal_ascii_whitespace": self.remove_internal_ascii_whitespace,
            }
        )

    def canonicalize(self, value: object) -> str:
        """Return the declared canonical category or fail closed for an unknown token."""

        return canonicalize_categorical_token(self, value)


def normalize_categorical_token(rule: CategoricalTokenRule, value: object) -> str:
    """Apply only the normalization operations prospectively declared by ``rule``."""

    if not isinstance(rule, CategoricalTokenRule):
        raise TypeError("rule must be CategoricalTokenRule")
    if value is None:
        raise ValueError(f"{rule.field_name} token must not be None")
    if not isinstance(value, str):
        raise TypeError(f"{rule.field_name} token must be str")
    text = value
    if rule.strip_outer_whitespace:
        text = text.strip()
    if rule.casefold:
        text = text.casefold()
    if rule.remove_internal_ascii_whitespace:
        text = _ASCII_WHITESPACE.sub("", text)
    if not text:
        raise ValueError(f"{rule.field_name} token normalizes to empty")
    return text


def canonicalize_categorical_token(rule: CategoricalTokenRule, value: object) -> str:
    """Map a raw token to one predeclared category; unknown values are rejected."""

    normalized = normalize_categorical_token(rule, value)
    mapping = rule.normalized_to_canonical
    try:
        return mapping[normalized]
    except KeyError as exc:
        raise ValueError(
            f"unknown categorical token for {rule.field_name!r}: {value!r}"
        ) from exc


@dataclass(frozen=True)
class ResponseTokenSchemaDeclaration:
    """Frozen collection of per-field categorical token rules.

    Rule order is not scientifically meaningful, so schema fingerprinting canonicalizes
    by field name. Field names themselves must be unique.
    """

    rules: tuple[CategoricalTokenRule, ...]
    schema_id: str = "response_token_schema_v1"

    def __post_init__(self) -> None:
        schema_id = _clean_text(self.schema_id, "schema_id").strip()
        object.__setattr__(self, "schema_id", schema_id)
        if isinstance(self.rules, (str, bytes)):
            raise TypeError("rules must be a sequence of CategoricalTokenRule values")
        rules = tuple(self.rules)
        if not rules:
            raise ValueError("rules must contain at least one categorical field")
        if not all(isinstance(rule, CategoricalTokenRule) for rule in rules):
            raise TypeError("rules must contain only CategoricalTokenRule values")
        names = [rule.field_name for rule in rules]
        if len(set(names)) != len(names):
            raise ValueError("response token schema field names must be unique")
        object.__setattr__(self, "rules", rules)

    @property
    def fingerprint(self) -> str:
        return _canonical_sha256(
            {
                "schema_id": self.schema_id,
                "rules": [
                    {
                        "field_name": rule.field_name,
                        "fingerprint": rule.fingerprint,
                    }
                    for rule in sorted(self.rules, key=lambda item: item.field_name)
                ],
            }
        )

    def rule_for(self, field_name: object) -> CategoricalTokenRule:
        if not isinstance(field_name, str):
            raise TypeError("field_name must be str")
        field = field_name.strip()
        if not field:
            raise ValueError("field_name must be non-empty")
        for rule in self.rules:
            if rule.field_name == field:
                return rule
        raise KeyError(f"field {field!r} is not declared in response token schema")

    def canonicalize(self, field_name: object, value: object) -> str:
        return self.rule_for(field_name).canonicalize(value)
