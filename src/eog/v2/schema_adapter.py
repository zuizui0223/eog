"""Response-blind schema alias contracts for dataset-neutral EOG adapters.

The EOG core should consume semantic roles rather than hard-coded physical column
spellings. This module lets an adapter predeclare a finite set of exact aliases for
each semantic role before response access, resolve one physical header against that
declaration, and freeze the resulting mapping.

This is intentionally not a fuzzy schema repair layer. There is no case folding,
substring matching, edit-distance search, post-outcome alias discovery, or automatic
choice when multiple declared aliases are simultaneously present. Ambiguity and
undeclared required fields fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence


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


def _required_text(value: object, label: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{label} must be non-empty")
    return text


@dataclass(frozen=True)
class SchemaRole:
    """One canonical adapter role and its prospectively declared physical aliases."""

    role: str
    aliases: tuple[str, ...]
    required: bool = True

    def __post_init__(self) -> None:
        role = _required_text(self.role, "role")
        aliases = tuple(_required_text(value, "alias") for value in self.aliases)
        if not isinstance(self.required, bool):
            raise TypeError("required must be bool")
        if not aliases or len(aliases) != len(set(aliases)):
            raise ValueError("aliases must be non-empty and unique within a role")
        if role != self.role or aliases != self.aliases:
            object.__setattr__(self, "role", role)
            object.__setattr__(self, "aliases", aliases)

    @property
    def fingerprint(self) -> str:
        return _sha256(
            {
                "role": self.role,
                "aliases": list(self.aliases),
                "required": bool(self.required),
            }
        )


@dataclass(frozen=True)
class FrozenSchemaResolution:
    """Content-addressed mapping from canonical roles to one observed physical header."""

    role_to_physical: tuple[tuple[str, str | None], ...]
    physical_header: tuple[str, ...]
    unmapped_physical_columns: tuple[str, ...]
    contract_fingerprint: str
    semantic_fingerprint: str
    physical_header_fingerprint: str
    fingerprint: str

    @property
    def mapping(self) -> dict[str, str | None]:
        return dict(self.role_to_physical)

    def canonicalize_record(self, record: Mapping[str, object]) -> dict[str, object]:
        """Project one physical record to the frozen canonical roles.

        Optional roles absent from the frozen header are returned as None. A physical
        column present when the mapping was frozen but missing from the record fails
        closed.
        """

        output: dict[str, object] = {}
        for role, physical in self.role_to_physical:
            if physical is None:
                output[role] = None
                continue
            if physical not in record:
                raise ValueError(
                    f"record is missing frozen physical column {physical!r} for role {role!r}"
                )
            output[role] = record[physical]
        return output

    def canonicalize_records(
        self, records: Sequence[Mapping[str, object]]
    ) -> tuple[dict[str, object], ...]:
        return tuple(self.canonicalize_record(record) for record in records)


@dataclass(frozen=True)
class SchemaAliasContract:
    """Prospective exact-alias declaration for a response-blind dataset adapter."""

    roles: tuple[SchemaRole, ...]
    allow_unmapped_columns: bool = True

    def __post_init__(self) -> None:
        roles = tuple(self.roles)
        if not roles:
            raise ValueError("roles must not be empty")
        if any(not isinstance(role, SchemaRole) for role in roles):
            raise TypeError("roles must contain SchemaRole values")
        if not isinstance(self.allow_unmapped_columns, bool):
            raise TypeError("allow_unmapped_columns must be bool")
        role_names = [role.role for role in roles]
        if len(role_names) != len(set(role_names)):
            raise ValueError("role names must be unique")

        alias_owner: dict[str, str] = {}
        for role in roles:
            for alias in role.aliases:
                previous = alias_owner.get(alias)
                if previous is not None:
                    raise ValueError(
                        f"physical alias {alias!r} is declared for both {previous!r} "
                        f"and {role.role!r}"
                    )
                alias_owner[alias] = role.role

        if roles != self.roles:
            object.__setattr__(self, "roles", roles)

    @property
    def fingerprint(self) -> str:
        return _sha256(
            {
                "schema": "eog.schema_alias_contract.v1",
                "roles": [
                    {
                        "role": role.role,
                        "aliases": list(role.aliases),
                        "required": bool(role.required),
                    }
                    for role in self.roles
                ],
                "allow_unmapped_columns": bool(self.allow_unmapped_columns),
            }
        )

    def resolve(self, physical_header: Sequence[str]) -> FrozenSchemaResolution:
        """Resolve an observed header using only the predeclared exact aliases."""

        header = tuple(
            _required_text(value, "physical header column") for value in physical_header
        )
        if not header or len(header) != len(set(header)):
            raise ValueError("physical header must be non-empty and contain unique columns")

        role_to_physical: list[tuple[str, str | None]] = []
        used: set[str] = set()
        for role in self.roles:
            aliases = set(role.aliases)
            matches = tuple(column for column in header if column in aliases)
            if len(matches) > 1:
                raise ValueError(
                    f"multiple declared aliases are simultaneously present for role "
                    f"{role.role!r}: {matches!r}"
                )
            if not matches:
                if role.required:
                    raise ValueError(
                        f"required role {role.role!r} has no declared alias in physical header"
                    )
                role_to_physical.append((role.role, None))
                continue
            physical = matches[0]
            if physical in used:
                raise ValueError(f"physical column {physical!r} maps to more than one role")
            used.add(physical)
            role_to_physical.append((role.role, physical))

        unmapped = tuple(column for column in header if column not in used)
        if unmapped and not self.allow_unmapped_columns:
            raise ValueError(f"unmapped physical columns are forbidden: {unmapped!r}")

        semantic_payload = {
            "schema": "eog.schema_alias_resolution_semantics.v1",
            "role_to_physical": role_to_physical,
            "unmapped_physical_columns": sorted(unmapped),
            "contract_fingerprint": self.fingerprint,
        }
        semantic_fingerprint = _sha256(semantic_payload)
        header_fingerprint = _sha256(
            {
                "schema": "eog.physical_header.v1",
                "physical_header": list(header),
            }
        )
        object_payload = {
            **semantic_payload,
            "physical_header": list(header),
            "semantic_fingerprint": semantic_fingerprint,
            "physical_header_fingerprint": header_fingerprint,
        }
        return FrozenSchemaResolution(
            role_to_physical=tuple(role_to_physical),
            physical_header=header,
            unmapped_physical_columns=unmapped,
            contract_fingerprint=self.fingerprint,
            semantic_fingerprint=semantic_fingerprint,
            physical_header_fingerprint=header_fingerprint,
            fingerprint=_sha256(object_payload),
        )
