"""Prospective missing-token / row-admissibility gate for once-only response access.

This module is validation infrastructure, not an ecological operator.  It allows a
fresh validation attempt to freeze, before row-level outcome access, how explicitly
declared missing tokens in selected response fields are handled.

The default and safest disposition is ``stop``.  ``exclude_row`` is available only
when it is declared prospectively for that field.  The evaluator never invents
aliases, treats unknown categorical values as missing, or silently drops a row.
Unknown/non-missing categorical values remain the responsibility of
:mod:`eog.v2.response_schema`.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Literal, Mapping


MissingDisposition = Literal["stop", "exclude_row"]
ResponseRowAdmissibilityStatus = Literal[
    "include_row",
    "exclude_row_declared_missing",
    "stop_declared_missing",
    "stop_required_field_absent",
]

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


def _require_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{label} must be bool")
    return value


def _clean_nonempty_text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be str")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{label} must be non-empty")
    return cleaned


def _normalize_literal(
    value: str,
    *,
    strip_outer_whitespace: bool,
    casefold: bool,
    remove_internal_ascii_whitespace: bool,
) -> str:
    text = value
    if strip_outer_whitespace:
        text = text.strip()
    if casefold:
        text = text.casefold()
    if remove_internal_ascii_whitespace:
        text = _ASCII_WHITESPACE.sub("", text)
    return text


@dataclass(frozen=True)
class ResponseFieldMissingPolicy:
    """Prospectively frozen missing-token policy for one response field.

    ``literal_missing_tokens`` are exact text sentinels after only the declared
    normalization.  Empty strings are not permitted there; use
    ``empty_after_normalization_is_missing`` explicitly.  ``None`` likewise has its
    own switch so a candidate cannot accidentally broaden missingness by adding an
    alias after seeing the response.
    """

    field_name: str
    disposition: MissingDisposition = "stop"
    none_is_missing: bool = False
    empty_after_normalization_is_missing: bool = False
    literal_missing_tokens: tuple[str, ...] = ()
    strip_outer_whitespace: bool = True
    casefold: bool = True
    remove_internal_ascii_whitespace: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "field_name",
            _clean_nonempty_text(self.field_name, "field_name"),
        )
        if self.disposition not in {"stop", "exclude_row"}:
            raise ValueError("disposition must be 'stop' or 'exclude_row'")
        _require_bool(self.none_is_missing, "none_is_missing")
        _require_bool(
            self.empty_after_normalization_is_missing,
            "empty_after_normalization_is_missing",
        )
        _require_bool(self.strip_outer_whitespace, "strip_outer_whitespace")
        _require_bool(self.casefold, "casefold")
        _require_bool(
            self.remove_internal_ascii_whitespace,
            "remove_internal_ascii_whitespace",
        )

        if isinstance(self.literal_missing_tokens, (str, bytes)):
            raise TypeError("literal_missing_tokens must be a sequence of strings")
        tokens = tuple(self.literal_missing_tokens)
        if not all(isinstance(token, str) for token in tokens):
            raise TypeError("literal_missing_tokens must contain only strings")
        normalized = tuple(
            _normalize_literal(
                token,
                strip_outer_whitespace=self.strip_outer_whitespace,
                casefold=self.casefold,
                remove_internal_ascii_whitespace=self.remove_internal_ascii_whitespace,
            )
            for token in tokens
        )
        if any(not token for token in normalized):
            raise ValueError(
                "literal_missing_tokens must not normalize to empty; use "
                "empty_after_normalization_is_missing"
            )
        if len(set(normalized)) != len(normalized):
            raise ValueError("literal_missing_tokens collide after normalization")
        object.__setattr__(self, "literal_missing_tokens", tokens)

    @property
    def normalized_missing_tokens(self) -> frozenset[str]:
        return frozenset(
            _normalize_literal(
                token,
                strip_outer_whitespace=self.strip_outer_whitespace,
                casefold=self.casefold,
                remove_internal_ascii_whitespace=self.remove_internal_ascii_whitespace,
            )
            for token in self.literal_missing_tokens
        )

    @property
    def fingerprint(self) -> str:
        return _canonical_sha256(
            {
                "field_name": self.field_name,
                "disposition": self.disposition,
                "none_is_missing": self.none_is_missing,
                "empty_after_normalization_is_missing": self.empty_after_normalization_is_missing,
                "literal_missing_tokens": list(self.literal_missing_tokens),
                "strip_outer_whitespace": self.strip_outer_whitespace,
                "casefold": self.casefold,
                "remove_internal_ascii_whitespace": self.remove_internal_ascii_whitespace,
            }
        )

    def is_declared_missing(self, value: object) -> bool:
        if value is None:
            return self.none_is_missing
        if not isinstance(value, str):
            return False
        normalized = _normalize_literal(
            value,
            strip_outer_whitespace=self.strip_outer_whitespace,
            casefold=self.casefold,
            remove_internal_ascii_whitespace=self.remove_internal_ascii_whitespace,
        )
        if not normalized:
            return self.empty_after_normalization_is_missing
        return normalized in self.normalized_missing_tokens


@dataclass(frozen=True)
class ResponseRowAdmissibilityDeclaration:
    """Frozen field-level missingness rules used before endpoint parsing.

    Rule order is canonicalized for fingerprinting.  A field may appear at most once.
    The declaration itself does not drop anything; it only makes a later row decision
    machine-checkable.
    """

    policies: tuple[ResponseFieldMissingPolicy, ...]
    declaration_id: str = "response_row_admissibility_v1"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "declaration_id",
            _clean_nonempty_text(self.declaration_id, "declaration_id"),
        )
        if isinstance(self.policies, (str, bytes)):
            raise TypeError("policies must be a sequence of ResponseFieldMissingPolicy")
        policies = tuple(self.policies)
        if not policies:
            raise ValueError("policies must contain at least one field policy")
        if not all(isinstance(policy, ResponseFieldMissingPolicy) for policy in policies):
            raise TypeError("policies must contain only ResponseFieldMissingPolicy values")
        names = [policy.field_name for policy in policies]
        if len(set(names)) != len(names):
            raise ValueError("response row-admissibility field names must be unique")
        object.__setattr__(self, "policies", policies)

    @property
    def fingerprint(self) -> str:
        return _canonical_sha256(
            {
                "declaration_id": self.declaration_id,
                "policies": [
                    [policy.field_name, policy.fingerprint]
                    for policy in sorted(self.policies, key=lambda item: item.field_name)
                ],
            }
        )


@dataclass(frozen=True)
class ResponseRowAdmissibilityResult:
    """One row's fail-closed disposition without echoing response values."""

    status: ResponseRowAdmissibilityStatus
    include: bool
    excluded: bool
    stop: bool
    missing_fields: tuple[str, ...]
    absent_fields: tuple[str, ...]
    declaration_fingerprint: str
    reason: str
    fingerprint: str


def evaluate_response_row_admissibility(
    declaration: ResponseRowAdmissibilityDeclaration,
    row: Mapping[str, object],
) -> ResponseRowAdmissibilityResult:
    """Apply only prospectively declared missing-token dispositions to ``row``.

    Precedence is strict:

    1. an absent declared field stops;
    2. a declared missing token with ``stop`` stops;
    3. otherwise any declared missing token with ``exclude_row`` excludes the row;
    4. otherwise the row is included and categorical parsing can continue.

    The returned fingerprint records field names and disposition only, never the raw
    response values.
    """

    if not isinstance(declaration, ResponseRowAdmissibilityDeclaration):
        raise TypeError("declaration must be ResponseRowAdmissibilityDeclaration")
    if not isinstance(row, Mapping):
        raise TypeError("row must be a mapping")

    absent = tuple(sorted(policy.field_name for policy in declaration.policies if policy.field_name not in row))
    missing_policies = tuple(
        policy
        for policy in declaration.policies
        if policy.field_name in row and policy.is_declared_missing(row[policy.field_name])
    )
    missing = tuple(sorted(policy.field_name for policy in missing_policies))

    if absent:
        status: ResponseRowAdmissibilityStatus = "stop_required_field_absent"
        reason = "one or more fields covered by the frozen row-admissibility declaration are absent"
    elif any(policy.disposition == "stop" for policy in missing_policies):
        status = "stop_declared_missing"
        reason = "a prospectively declared missing token has stop disposition"
    elif missing_policies:
        status = "exclude_row_declared_missing"
        reason = "row is excluded only because a prospectively declared missing token has exclude_row disposition"
    else:
        status = "include_row"
        reason = "no prospectively declared missing token was encountered"

    include = status == "include_row"
    excluded = status == "exclude_row_declared_missing"
    stop = status.startswith("stop_")
    payload = {
        "status": status,
        "include": include,
        "excluded": excluded,
        "stop": stop,
        "missing_fields": list(missing),
        "absent_fields": list(absent),
        "declaration_fingerprint": declaration.fingerprint,
        "reason": reason,
    }
    return ResponseRowAdmissibilityResult(
        status=status,
        include=include,
        excluded=excluded,
        stop=stop,
        missing_fields=missing,
        absent_fields=absent,
        declaration_fingerprint=declaration.fingerprint,
        reason=reason,
        fingerprint=_canonical_sha256(payload),
    )
