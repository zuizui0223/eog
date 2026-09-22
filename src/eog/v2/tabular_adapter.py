"""Strict response-blind CSV parsing for generic EOG-WF adapters.

This module owns physical CSV mechanics only. Scientific roles are resolved by a
predeclared SchemaAliasContract. It never guesses aliases, strips cell values, imputes
missing fields, interprets zeros, or opens a biological-response payload implicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
import csv
import hashlib
import io
import json
from typing import Sequence

from eog.v2.schema_adapter import FrozenSchemaResolution, SchemaAliasContract


def _sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class StrictCSVPolicy:
    """Prospectively declared physical CSV parsing policy."""

    encoding: str = "utf-8"
    allow_utf8_bom: bool = False
    require_data_rows: bool = True

    def __post_init__(self) -> None:
        encoding = str(self.encoding).strip().lower()
        if encoding not in {"utf-8"}:
            raise ValueError("only explicit utf-8 is supported by the generic CSV adapter")
        object.__setattr__(self, "encoding", encoding)

    @property
    def fingerprint(self) -> str:
        return _sha256(
            {
                "schema": "eog.strict_csv_policy.v1",
                "encoding": self.encoding,
                "allow_utf8_bom": bool(self.allow_utf8_bom),
                "require_data_rows": bool(self.require_data_rows),
            }
        )


@dataclass(frozen=True)
class FrozenTabularSource:
    """Content-addressed physical and canonical view of one safe CSV payload."""

    physical_header: tuple[str, ...]
    physical_row_count: int
    canonical_roles: tuple[str, ...]
    canonical_rows: tuple[tuple[object, ...], ...]
    source_sha256: str
    schema_resolution: FrozenSchemaResolution
    policy_fingerprint: str
    canonical_rows_fingerprint: str
    fingerprint: str

    def records(self) -> tuple[dict[str, object], ...]:
        return tuple(
            dict(zip(self.canonical_roles, row, strict=True))
            for row in self.canonical_rows
        )


def parse_response_blind_csv(
    raw: bytes,
    *,
    schema_contract: SchemaAliasContract,
    policy: StrictCSVPolicy | None = None,
) -> FrozenTabularSource:
    """Parse one explicitly response-independent CSV payload under frozen contracts."""

    if not isinstance(raw, bytes):
        raise TypeError("raw must be bytes")
    resolved_policy = StrictCSVPolicy() if policy is None else policy
    if not isinstance(resolved_policy, StrictCSVPolicy):
        raise TypeError("policy must be StrictCSVPolicy")

    has_bom = raw.startswith(b"\xef\xbb\xbf")
    if has_bom and not resolved_policy.allow_utf8_bom:
        raise ValueError("UTF-8 BOM is forbidden by the frozen CSV policy")
    payload = raw[3:] if has_bom else raw
    try:
        text = payload.decode(resolved_policy.encoding)
    except UnicodeDecodeError as exc:
        raise ValueError("CSV payload is not valid UTF-8") from exc

    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header_values = next(reader)
    except StopIteration as exc:
        raise ValueError("CSV payload is empty") from exc
    header = tuple(header_values)
    if not header or any(not value for value in header):
        raise ValueError("physical CSV header must contain non-empty columns")
    if len(header) != len(set(header)):
        raise ValueError("physical CSV header contains duplicate columns")

    resolution = schema_contract.resolve(header)
    canonical_roles = tuple(role for role, _ in resolution.role_to_physical)
    canonical_rows: list[tuple[object, ...]] = []
    physical_row_count = 0
    for row_number, row in enumerate(reader, start=2):
        if len(row) != len(header):
            raise ValueError(
                f"CSV row {row_number} has {len(row)} cells for {len(header)} columns"
            )
        physical = dict(zip(header, row, strict=True))
        canonical = resolution.canonicalize_record(physical)
        canonical_rows.append(tuple(canonical[role] for role in canonical_roles))
        physical_row_count += 1

    if resolved_policy.require_data_rows and physical_row_count == 0:
        raise ValueError("CSV payload has no data rows")

    source_sha256 = hashlib.sha256(raw).hexdigest()
    row_payload = {
        "schema": "eog.canonical_csv_rows.v1",
        "roles": list(canonical_roles),
        "rows": canonical_rows,
    }
    canonical_rows_fingerprint = _sha256(row_payload)
    object_payload = {
        "schema": "eog.frozen_tabular_source.v1",
        "physical_header": list(header),
        "physical_row_count": physical_row_count,
        "source_sha256": source_sha256,
        "schema_resolution_fingerprint": resolution.fingerprint,
        "policy_fingerprint": resolved_policy.fingerprint,
        "canonical_rows_fingerprint": canonical_rows_fingerprint,
    }
    return FrozenTabularSource(
        physical_header=header,
        physical_row_count=physical_row_count,
        canonical_roles=canonical_roles,
        canonical_rows=tuple(canonical_rows),
        source_sha256=source_sha256,
        schema_resolution=resolution,
        policy_fingerprint=resolved_policy.fingerprint,
        canonical_rows_fingerprint=canonical_rows_fingerprint,
        fingerprint=_sha256(object_payload),
    )
