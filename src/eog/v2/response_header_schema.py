"""Bounded response-header schema gate for once-only empirical validation.

This module is validation infrastructure, not an ecological operator. It verifies the
physical column names of a response entity from a separately acquired first-record
header before row-level outcome access. The header evidence must be obtained through a
bounded response firewall; this module never authorizes reading a second physical
record and never repairs a schema after outcome values have been opened.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
import io
import json
from typing import Literal


ResponseHeaderSchemaStatus = Literal[
    "header_schema_match",
    "stop_outcome_content_already_opened",
    "stop_header_parse_error",
    "stop_header_empty_column",
    "stop_header_duplicate_columns",
    "stop_header_schema_mismatch",
]

RecordTerminator = Literal["CR", "LF"]


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


def _clean_required(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be str")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{label} must be non-empty")
    return cleaned


def _require_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{label} must be bool")
    return value


def _require_positive_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be int")
    if value <= 0:
        raise ValueError(f"{label} must be > 0")
    return value


@dataclass(frozen=True)
class ResponseHeaderSchemaDeclaration:
    """Prospectively declared physical response-header contract."""

    schema_id: str
    expected_columns: tuple[str, ...]
    delimiter: str = ","
    require_exact_order: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_id", _clean_required(self.schema_id, "schema_id"))

        if isinstance(self.expected_columns, (str, bytes)):
            raise TypeError("expected_columns must be a sequence of strings")
        columns = tuple(self.expected_columns)
        if not columns:
            raise ValueError("expected_columns must contain at least one column")
        if not all(isinstance(value, str) for value in columns):
            raise TypeError("expected_columns must contain only strings")
        cleaned = tuple(value.strip() for value in columns)
        if any(not value for value in cleaned):
            raise ValueError("expected_columns must not contain empty names")
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("expected_columns must be unique")
        object.__setattr__(self, "expected_columns", cleaned)

        if not isinstance(self.delimiter, str):
            raise TypeError("delimiter must be str")
        if len(self.delimiter) != 1 or self.delimiter in {"\r", "\n"}:
            raise ValueError("delimiter must be exactly one non-record-separator character")
        _require_bool(self.require_exact_order, "require_exact_order")

    @property
    def fingerprint(self) -> str:
        return _canonical_sha256(
            {
                "schema_id": self.schema_id,
                "expected_columns": list(self.expected_columns),
                "delimiter": self.delimiter,
                "require_exact_order": self.require_exact_order,
            }
        )


@dataclass(frozen=True)
class ResponseHeaderSchemaEvidence:
    """One bounded physical header record and its firewall audit metadata."""

    header_text: str
    terminator: RecordTerminator
    bytes_consumed: int
    response_rows_opened: bool = False
    response_values_opened: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.header_text, str):
            raise TypeError("header_text must be str")
        if not self.header_text:
            raise ValueError("header_text must be non-empty")
        if self.terminator not in {"CR", "LF"}:
            raise ValueError("terminator must be 'CR' or 'LF'")
        object.__setattr__(
            self,
            "bytes_consumed",
            _require_positive_int(self.bytes_consumed, "bytes_consumed"),
        )
        _require_bool(self.response_rows_opened, "response_rows_opened")
        _require_bool(self.response_values_opened, "response_values_opened")

    @property
    def header_sha256(self) -> str:
        return hashlib.sha256(self.header_text.encode("utf-8")).hexdigest()

    @property
    def fingerprint(self) -> str:
        return _canonical_sha256(
            {
                "header_sha256": self.header_sha256,
                "terminator": self.terminator,
                "bytes_consumed": self.bytes_consumed,
                "response_rows_opened": self.response_rows_opened,
                "response_values_opened": self.response_values_opened,
            }
        )


@dataclass(frozen=True)
class ResponseHeaderSchemaResult:
    status: ResponseHeaderSchemaStatus
    ready: bool
    observed_columns: tuple[str, ...]
    missing_columns: tuple[str, ...]
    unexpected_columns: tuple[str, ...]
    order_matches: bool
    declaration_fingerprint: str
    evidence_fingerprint: str
    reason: str
    fingerprint: str


def _parse_header(header_text: str, delimiter: str) -> tuple[str, ...]:
    try:
        rows = list(csv.reader(io.StringIO(header_text), delimiter=delimiter, strict=True))
    except csv.Error as exc:
        raise ValueError(f"header parse failed: {exc}") from exc
    if len(rows) != 1:
        raise ValueError("bounded header evidence must decode to exactly one CSV record")
    return tuple(value.strip() for value in rows[0])


def evaluate_response_header_schema(
    declaration: ResponseHeaderSchemaDeclaration,
    evidence: ResponseHeaderSchemaEvidence,
) -> ResponseHeaderSchemaResult:
    """Validate physical response columns before any outcome row/value access.

    A mismatch is a pre-outcome schema stop. It may be resolved only by creating a new
    prospectively frozen response-semantics contract before row-level outcome access.
    Once response rows or values have been opened, this evaluator fails closed and does
    not authorize aliases, renames, or a rerun of the opened endpoint.
    """

    if not isinstance(declaration, ResponseHeaderSchemaDeclaration):
        raise TypeError("declaration must be ResponseHeaderSchemaDeclaration")
    if not isinstance(evidence, ResponseHeaderSchemaEvidence):
        raise TypeError("evidence must be ResponseHeaderSchemaEvidence")

    observed: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()
    unexpected: tuple[str, ...] = ()
    order_matches = False

    if evidence.response_rows_opened or evidence.response_values_opened:
        status: ResponseHeaderSchemaStatus = "stop_outcome_content_already_opened"
        reason = (
            "response header schema must be resolved before row-level outcome content; "
            "post-open repair is not authorized"
        )
    else:
        try:
            observed = _parse_header(evidence.header_text, declaration.delimiter)
        except ValueError as exc:
            status = "stop_header_parse_error"
            reason = str(exc)
        else:
            if any(not value for value in observed):
                status = "stop_header_empty_column"
                reason = "physical response header contains an empty column name"
            elif len(set(observed)) != len(observed):
                status = "stop_header_duplicate_columns"
                reason = "physical response header contains duplicate column names"
            else:
                expected = declaration.expected_columns
                expected_set = set(expected)
                observed_set = set(observed)
                missing = tuple(value for value in expected if value not in observed_set)
                unexpected = tuple(value for value in observed if value not in expected_set)
                order_matches = observed == expected
                names_match = not missing and not unexpected
                matches = names_match and (
                    order_matches or not declaration.require_exact_order
                )
                if matches:
                    status = "header_schema_match"
                    reason = (
                        "bounded physical response header matches the prospectively "
                        "declared column contract"
                    )
                else:
                    status = "stop_header_schema_mismatch"
                    reason = (
                        "physical response header does not match the prospectively "
                        "declared column contract"
                    )

    ready = status == "header_schema_match"
    payload = {
        "status": status,
        "ready": ready,
        "observed_columns": list(observed),
        "missing_columns": list(missing),
        "unexpected_columns": list(unexpected),
        "order_matches": order_matches,
        "declaration_fingerprint": declaration.fingerprint,
        "evidence_fingerprint": evidence.fingerprint,
        "reason": reason,
    }
    return ResponseHeaderSchemaResult(
        status=status,
        ready=ready,
        observed_columns=observed,
        missing_columns=missing,
        unexpected_columns=unexpected,
        order_matches=order_matches,
        declaration_fingerprint=declaration.fingerprint,
        evidence_fingerprint=evidence.fingerprint,
        reason=reason,
        fingerprint=_canonical_sha256(payload),
    )
