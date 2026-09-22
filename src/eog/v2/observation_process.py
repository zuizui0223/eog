"""Generic binary observation-process contracts for EOG-WF v2 adapters.

Candidate units and effort eligibility must already be frozen in a
NormalizedPreResponseProblem. This module only maps an opened response onto that frozen
unit universe under one predeclared negative-semantics mode.

Two modes are deliberately separated:

1. explicit_binary_tokens
   Every eligible unit must be explicitly classified as positive, negative or
   unavailable. Missing response rows are never converted to zero.

2. complete_source_zero
   After a complete response source has been successfully parsed, eligible units not
   mapped to a focal positive may become recorded non-detections. The caller must
   explicitly certify source completeness at materialization time.

Neither mode interprets zero as biological absence.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal, Sequence

from eog.v2.effort_context import EffortContextLedger
from eog.v2.problem_contract import NormalizedPreResponseProblem


ObservationMode = Literal["explicit_binary_tokens", "complete_source_zero"]


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


def _text(value: object, label: str) -> str:
    result = str(value).strip()
    if not result:
        raise ValueError(f"{label} must be non-empty")
    return result


def _unique_ids(values: Sequence[str], label: str) -> tuple[str, ...]:
    result = tuple(_text(value, label) for value in values)
    if len(result) != len(set(result)):
        raise ValueError(f"{label} must not contain duplicates")
    return result


@dataclass(frozen=True)
class BinaryObservationContract:
    """Prospective response-mapping semantics for one frozen candidate universe."""

    mode: ObservationMode
    endpoint_name: str
    positive_semantics: str
    negative_semantics: str
    unavailable_semantics: str
    zero_interpretation: str

    def __post_init__(self) -> None:
        if self.mode not in {"explicit_binary_tokens", "complete_source_zero"}:
            raise ValueError("unsupported observation mode")
        for field in (
            "endpoint_name",
            "positive_semantics",
            "negative_semantics",
            "unavailable_semantics",
            "zero_interpretation",
        ):
            value = _text(getattr(self, field), field)
            if value != getattr(self, field):
                object.__setattr__(self, field, value)

    @property
    def fingerprint(self) -> str:
        return _sha256(
            {
                "schema": "eog.binary_observation_contract.v1",
                "mode": self.mode,
                "endpoint_name": self.endpoint_name,
                "positive_semantics": self.positive_semantics,
                "negative_semantics": self.negative_semantics,
                "unavailable_semantics": self.unavailable_semantics,
                "zero_interpretation": self.zero_interpretation,
            }
        )


@dataclass(frozen=True)
class BinaryObservationRow:
    unit_id: str
    node_id: str
    context_id: str
    fold: int
    label: int
    fingerprint: str


@dataclass(frozen=True)
class BinaryObservationEndpoint:
    """Materialized labels aligned to the frozen candidate-unit order."""

    rows: tuple[BinaryObservationRow, ...]
    unavailable_unit_ids: tuple[str, ...]
    initialization_rows: tuple[BinaryObservationRow, ...]
    initialization_unavailable_unit_ids: tuple[str, ...]
    positive_count: int
    negative_count: int
    unavailable_count: int
    candidate_unit_count: int
    initialization_positive_count: int
    initialization_negative_count: int
    initialization_unavailable_count: int
    initialization_unit_count: int
    contract_fingerprint: str
    normalized_problem_fingerprint: str
    response_source_complete: bool
    fingerprint: str

    @property
    def labels(self) -> tuple[int, ...]:
        return tuple(row.label for row in self.rows)

    @property
    def scored_unit_ids(self) -> tuple[str, ...]:
        return tuple(row.unit_id for row in self.rows)

    @property
    def initialization_labels(self) -> tuple[int, ...]:
        return tuple(row.label for row in self.initialization_rows)

    @property
    def initialization_unit_ids(self) -> tuple[str, ...]:
        return tuple(row.unit_id for row in self.initialization_rows)


def materialize_binary_observation(
    problem: NormalizedPreResponseProblem,
    contract: BinaryObservationContract,
    *,
    positive_unit_ids: Sequence[str],
    explicit_negative_unit_ids: Sequence[str] = (),
    unavailable_unit_ids: Sequence[str] = (),
    effort_ledger: EffortContextLedger | None = None,
    initialization_positive_unit_ids: Sequence[str] = (),
    initialization_explicit_negative_unit_ids: Sequence[str] = (),
    initialization_unavailable_unit_ids: Sequence[str] = (),
    response_source_complete: bool = False,
) -> BinaryObservationEndpoint:
    """Map response-derived unit IDs onto the already-frozen candidate universe.

    All response parsing and taxon filtering must occur upstream. This function accepts
    only candidate-unit IDs and never inspects raw response values.
    """

    if not problem.response_locked:
        raise ValueError("normalized problem must be a frozen pre-response problem")

    candidate_order = tuple(unit.unit_id for unit in problem.candidate_units)
    candidate_set = set(candidate_order)

    if effort_ledger is None:
        initialization_order: tuple[str, ...] = ()
        initialization_metadata: dict[str, object] = {}
        if (
            initialization_positive_unit_ids
            or initialization_explicit_negative_unit_ids
            or initialization_unavailable_unit_ids
        ):
            raise ValueError(
                "initialization response IDs require a frozen effort_ledger"
            )
    else:
        if effort_ledger.candidate_units != problem.candidate_units:
            raise ValueError(
                "effort ledger candidate units differ from normalized problem"
            )
        initialization_order = effort_ledger.initialization_unit_ids
        row_by_id = {row.unit_id: row for row in effort_ledger.rows}
        initialization_metadata = {
            unit_id: row_by_id[unit_id] for unit_id in initialization_order
        }
    positive = _unique_ids(positive_unit_ids, "positive_unit_ids")
    negative = _unique_ids(explicit_negative_unit_ids, "explicit_negative_unit_ids")
    unavailable = _unique_ids(unavailable_unit_ids, "unavailable_unit_ids")
    initialization_positive = _unique_ids(
        initialization_positive_unit_ids, "initialization_positive_unit_ids"
    )
    initialization_negative = _unique_ids(
        initialization_explicit_negative_unit_ids,
        "initialization_explicit_negative_unit_ids",
    )
    initialization_unavailable = _unique_ids(
        initialization_unavailable_unit_ids,
        "initialization_unavailable_unit_ids",
    )

    for label, values in (
        ("positive", positive),
        ("negative", negative),
        ("unavailable", unavailable),
    ):
        unknown = sorted(set(values) - candidate_set)
        if unknown:
            raise ValueError(f"{label} response IDs are outside the frozen candidate universe: {unknown!r}")

    initialization_set = set(initialization_order)
    for label, values in (
        ("initialization positive", initialization_positive),
        ("initialization negative", initialization_negative),
        ("initialization unavailable", initialization_unavailable),
    ):
        unknown = sorted(set(values) - initialization_set)
        if unknown:
            raise ValueError(
                f"{label} response IDs are outside the frozen initialization universe: {unknown!r}"
            )

    positive_set = set(positive)
    negative_set = set(negative)
    unavailable_set = set(unavailable)
    initialization_positive_set = set(initialization_positive)
    initialization_negative_set = set(initialization_negative)
    initialization_unavailable_set = set(initialization_unavailable)
    if positive_set & negative_set:
        raise ValueError("positive and explicit-negative unit sets overlap")
    if positive_set & unavailable_set:
        raise ValueError("positive and unavailable unit sets overlap")
    if negative_set & unavailable_set:
        raise ValueError("explicit-negative and unavailable unit sets overlap")
    if initialization_positive_set & initialization_negative_set:
        raise ValueError(
            "initialization positive and explicit-negative unit sets overlap"
        )
    if initialization_positive_set & initialization_unavailable_set:
        raise ValueError(
            "initialization positive and unavailable unit sets overlap"
        )
    if initialization_negative_set & initialization_unavailable_set:
        raise ValueError(
            "initialization explicit-negative and unavailable unit sets overlap"
        )

    if contract.mode == "explicit_binary_tokens":
        if response_source_complete:
            raise ValueError(
                "response_source_complete is reserved for complete_source_zero mode"
            )
        classified = positive_set | negative_set | unavailable_set
        missing = sorted(candidate_set - classified)
        if missing:
            raise ValueError(
                "explicit_binary_tokens requires every frozen candidate unit to be "
                f"positive, negative or unavailable; missing {missing!r}"
            )
        initialization_classified = (
            initialization_positive_set
            | initialization_negative_set
            | initialization_unavailable_set
        )
        initialization_missing = sorted(
            initialization_set - initialization_classified
        )
        if initialization_missing:
            raise ValueError(
                "explicit_binary_tokens requires every frozen initialization unit "
                "to be positive, negative or unavailable; missing "
                f"{initialization_missing!r}"
            )
    else:
        if negative or initialization_negative:
            raise ValueError(
                "complete_source_zero derives negatives from the eligible universe; "
                "explicit negative unit IDs must be empty"
            )
        if not response_source_complete:
            raise ValueError(
                "complete_source_zero requires explicit response_source_complete=True"
            )
        negative_set = candidate_set - positive_set - unavailable_set
        initialization_negative_set = (
            initialization_set
            - initialization_positive_set
            - initialization_unavailable_set
        )

    unit_by_id = {unit.unit_id: unit for unit in problem.candidate_units}
    rows: list[BinaryObservationRow] = []
    for unit_id in candidate_order:
        if unit_id in unavailable_set:
            continue
        label = 1 if unit_id in positive_set else 0
        if contract.mode == "explicit_binary_tokens" and unit_id not in negative_set and label == 0:
            raise RuntimeError("unclassified explicit-token unit escaped validation")
        unit = unit_by_id[unit_id]
        row_payload = {
            "unit_id": unit.unit_id,
            "node_id": unit.node_id,
            "context_id": unit.context_id,
            "fold": int(unit.fold),
            "label": label,
            "contract_fingerprint": contract.fingerprint,
        }
        rows.append(
            BinaryObservationRow(
                unit_id=unit.unit_id,
                node_id=unit.node_id,
                context_id=unit.context_id,
                fold=int(unit.fold),
                label=label,
                fingerprint=_sha256(row_payload),
            )
        )

    initialization_rows: list[BinaryObservationRow] = []
    for unit_id in initialization_order:
        if unit_id in initialization_unavailable_set:
            continue
        label = 1 if unit_id in initialization_positive_set else 0
        if (
            contract.mode == "explicit_binary_tokens"
            and unit_id not in initialization_negative_set
            and label == 0
        ):
            raise RuntimeError(
                "unclassified initialization explicit-token unit escaped validation"
            )
        unit = initialization_metadata[unit_id]
        row_payload = {
            "unit_id": unit.unit_id,
            "node_id": unit.node_id,
            "context_id": unit.context_id,
            "fold": int(unit.fold),
            "label": label,
            "partition": "initialization_only",
            "contract_fingerprint": contract.fingerprint,
        }
        initialization_rows.append(
            BinaryObservationRow(
                unit_id=unit.unit_id,
                node_id=unit.node_id,
                context_id=unit.context_id,
                fold=int(unit.fold),
                label=label,
                fingerprint=_sha256(row_payload),
            )
        )

    positive_count = sum(row.label == 1 for row in rows)
    negative_count = sum(row.label == 0 for row in rows)
    unavailable_sorted = tuple(
        unit_id for unit_id in candidate_order if unit_id in unavailable_set
    )
    initialization_positive_count = sum(
        row.label == 1 for row in initialization_rows
    )
    initialization_negative_count = sum(
        row.label == 0 for row in initialization_rows
    )
    initialization_unavailable_sorted = tuple(
        unit_id
        for unit_id in initialization_order
        if unit_id in initialization_unavailable_set
    )
    payload = {
        "schema": "eog.binary_observation_endpoint.v1",
        "rows": [(row.unit_id, row.label, row.fingerprint) for row in rows],
        "unavailable_unit_ids": list(unavailable_sorted),
        "initialization_rows": [
            (row.unit_id, row.label, row.fingerprint) for row in initialization_rows
        ],
        "initialization_unavailable_unit_ids": list(
            initialization_unavailable_sorted
        ),
        "positive_count": positive_count,
        "negative_count": negative_count,
        "unavailable_count": len(unavailable_sorted),
        "candidate_unit_count": len(candidate_order),
        "initialization_positive_count": initialization_positive_count,
        "initialization_negative_count": initialization_negative_count,
        "initialization_unavailable_count": len(
            initialization_unavailable_sorted
        ),
        "initialization_unit_count": len(initialization_order),
        "contract_fingerprint": contract.fingerprint,
        "normalized_problem_fingerprint": problem.fingerprint,
        "response_source_complete": bool(response_source_complete),
    }
    return BinaryObservationEndpoint(
        rows=tuple(rows),
        unavailable_unit_ids=unavailable_sorted,
        initialization_rows=tuple(initialization_rows),
        initialization_unavailable_unit_ids=initialization_unavailable_sorted,
        positive_count=positive_count,
        negative_count=negative_count,
        unavailable_count=len(unavailable_sorted),
        candidate_unit_count=len(candidate_order),
        initialization_positive_count=initialization_positive_count,
        initialization_negative_count=initialization_negative_count,
        initialization_unavailable_count=len(
            initialization_unavailable_sorted
        ),
        initialization_unit_count=len(initialization_order),
        contract_fingerprint=contract.fingerprint,
        normalized_problem_fingerprint=problem.fingerprint,
        response_source_complete=bool(response_source_complete),
        fingerprint=_sha256(payload),
    )
