"""Dataset-neutral boundary between ecological source adapters and the EOG core.

This module is intentionally small.  It does not teach EOG how to read Dryad, GBIF,
GitHub CSVs, camera-trap workbooks, telemetry tables, or acoustic archives.  Those are
adapter responsibilities.  The core boundary starts only after a source has been
normalized into stable nodes, contexts, candidate units, observation semantics,
baseline roles, a heldout split, and a finite world-family declaration.

The distinction is motivated by the fresh-endpoint validation funnel: most terminal
STOPs have arisen in source transport, registry, effort/zero semantics, or schema
handling rather than in the Layer-A/Layer-B mathematics.  Generality therefore means
that new observation systems can replace the adapter without changing the exact
world-set machinery or ``symmetric_world_support_summary_v1``.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from statistics import median
from typing import Literal, Mapping, Protocol, Sequence, runtime_checkable


BaselineKind = Literal["numeric", "categorical"]
BaselineMissingPolicy = Literal[
    "forbid",
    "calibration_median_plus_indicator",
    "explicit_missing_category",
]


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _nonempty(value: object, label: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{label} must be non-empty")
    return text


@dataclass(frozen=True)
class CandidateUnit:
    """One response-evaluation unit after response-independent registry freezing."""

    unit_id: str
    node_id: str
    context_id: str
    fold: int

    def __post_init__(self) -> None:
        _nonempty(self.unit_id, "unit_id")
        _nonempty(self.node_id, "node_id")
        _nonempty(self.context_id, "context_id")
        if isinstance(self.fold, bool) or int(self.fold) <= 0:
            raise ValueError("fold must be a positive integer")


@dataclass(frozen=True)
class ObservationSemantics:
    """Human-readable but frozen mapping from survey process to binary endpoint."""

    effort_eligible_rule: str
    positive_rule: str
    negative_rule: str
    unsurveyed_rule: str
    zero_interpretation: str

    def __post_init__(self) -> None:
        for name in (
            "effort_eligible_rule",
            "positive_rule",
            "negative_rule",
            "unsurveyed_rule",
            "zero_interpretation",
        ):
            _nonempty(getattr(self, name), name)


@dataclass(frozen=True)
class BaselineFieldSpec:
    """One conventional-baseline role and its prospectively frozen missingness rule."""

    name: str
    kind: BaselineKind
    missing_policy: BaselineMissingPolicy

    def __post_init__(self) -> None:
        _nonempty(self.name, "baseline field name")
        if self.kind not in {"numeric", "categorical"}:
            raise ValueError(f"unsupported baseline kind: {self.kind!r}")
        if self.missing_policy not in {
            "forbid",
            "calibration_median_plus_indicator",
            "explicit_missing_category",
        }:
            raise ValueError(f"unsupported missing policy: {self.missing_policy!r}")
        if self.kind == "numeric" and self.missing_policy == "explicit_missing_category":
            raise ValueError("numeric fields cannot use explicit_missing_category")
        if self.kind == "categorical" and self.missing_policy == "calibration_median_plus_indicator":
            raise ValueError("categorical fields cannot use median imputation")


@dataclass(frozen=True)
class NormalizedPreResponseProblem:
    """Content-addressed intermediate representation consumed by generic EOG logic.

    Biological response values are deliberately absent.  An adapter may produce this
    object only while ``response_locked`` is true.  A later once-only observation gate
    can attach effort/response values to these already frozen candidate units.
    """

    node_ids: tuple[str, ...]
    component_ids: tuple[str, ...]
    context_ids: tuple[str, ...]
    candidate_units: tuple[CandidateUnit, ...]
    observation_semantics: ObservationSemantics
    baseline_fields: tuple[BaselineFieldSpec, ...]
    split_fingerprint: str
    world_family_fingerprint: str
    source_fingerprint: str
    response_locked: bool
    fingerprint: str


def freeze_pre_response_problem(
    *,
    node_ids: Sequence[str],
    component_ids: Sequence[str],
    context_ids: Sequence[str],
    candidate_units: Sequence[CandidateUnit],
    observation_semantics: ObservationSemantics,
    baseline_fields: Sequence[BaselineFieldSpec],
    split_fingerprint: str,
    world_family_fingerprint: str,
    source_fingerprint: str,
) -> NormalizedPreResponseProblem:
    """Validate and fingerprint the generic pre-response problem boundary."""

    nodes = tuple(_nonempty(value, "node_id") for value in node_ids)
    components = tuple(_nonempty(value, "component_id") for value in component_ids)
    contexts = tuple(_nonempty(value, "context_id") for value in context_ids)
    units = tuple(candidate_units)
    fields = tuple(baseline_fields)
    if not nodes or len(nodes) != len(set(nodes)):
        raise ValueError("node_ids must be non-empty and unique")
    if len(components) != len(nodes):
        raise ValueError("component_ids must align one-to-one with node_ids")
    if not contexts or len(contexts) != len(set(contexts)):
        raise ValueError("context_ids must be non-empty and unique")
    if not units:
        raise ValueError("candidate_units must not be empty")
    if len({unit.unit_id for unit in units}) != len(units):
        raise ValueError("candidate unit ids must be unique")
    node_set = set(nodes)
    context_set = set(contexts)
    for unit in units:
        if unit.node_id not in node_set:
            raise ValueError(f"candidate unit references unknown node: {unit.node_id}")
        if unit.context_id not in context_set:
            raise ValueError(f"candidate unit references unknown context: {unit.context_id}")
    if len({field.name for field in fields}) != len(fields):
        raise ValueError("baseline field names must be unique")
    split_fp = _nonempty(split_fingerprint, "split_fingerprint")
    world_fp = _nonempty(world_family_fingerprint, "world_family_fingerprint")
    source_fp = _nonempty(source_fingerprint, "source_fingerprint")

    payload = {
        "schema": "eog.normalized_pre_response_problem.v1",
        "node_ids": list(nodes),
        "component_ids": list(components),
        "context_ids": list(contexts),
        "candidate_units": [
            {
                "unit_id": unit.unit_id,
                "node_id": unit.node_id,
                "context_id": unit.context_id,
                "fold": int(unit.fold),
            }
            for unit in units
        ],
        "observation_semantics": {
            "effort_eligible_rule": observation_semantics.effort_eligible_rule,
            "positive_rule": observation_semantics.positive_rule,
            "negative_rule": observation_semantics.negative_rule,
            "unsurveyed_rule": observation_semantics.unsurveyed_rule,
            "zero_interpretation": observation_semantics.zero_interpretation,
        },
        "baseline_fields": [
            {
                "name": field.name,
                "kind": field.kind,
                "missing_policy": field.missing_policy,
            }
            for field in fields
        ],
        "split_fingerprint": split_fp,
        "world_family_fingerprint": world_fp,
        "source_fingerprint": source_fp,
        "response_locked": True,
    }
    return NormalizedPreResponseProblem(
        node_ids=nodes,
        component_ids=components,
        context_ids=contexts,
        candidate_units=units,
        observation_semantics=observation_semantics,
        baseline_fields=fields,
        split_fingerprint=split_fp,
        world_family_fingerprint=world_fp,
        source_fingerprint=source_fp,
        response_locked=True,
        fingerprint=_canonical_sha256(payload),
    )


@dataclass(frozen=True)
class NumericBaselineState:
    """Calibration-only numeric preprocessing state for one heldout fold."""

    feature_names: tuple[str, ...]
    medians: tuple[tuple[str, float], ...]
    field_specs: tuple[BaselineFieldSpec, ...]
    fingerprint: str

    @property
    def median_mapping(self) -> dict[str, float]:
        return dict(self.medians)


def _finite_or_none(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def fit_numeric_baseline_state(
    calibration_rows: Sequence[Mapping[str, object]],
    field_specs: Sequence[BaselineFieldSpec],
) -> NumericBaselineState:
    """Fit numeric missingness handling using calibration rows only.

    Structural identity/geometry/effort fields do not belong here and should already
    have failed closed in the adapter.  For an optional numeric baseline role,
    non-numeric/missing values are represented by the calibration median plus a
    dedicated missingness indicator.  This prevents ordinary covariate missingness from
    masquerading as a source-registry failure while avoiding heldout-response leakage.
    """

    rows = tuple(calibration_rows)
    specs = tuple(field_specs)
    if not rows:
        raise ValueError("calibration_rows must not be empty")
    numeric_specs = tuple(spec for spec in specs if spec.kind == "numeric")
    if not numeric_specs:
        raise ValueError("at least one numeric baseline field is required")
    medians: list[tuple[str, float]] = []
    feature_names: list[str] = []
    for spec in numeric_specs:
        values = [_finite_or_none(row.get(spec.name)) for row in rows]
        observed = [value for value in values if value is not None]
        if spec.missing_policy == "forbid":
            if len(observed) != len(values):
                raise ValueError(f"required numeric baseline field is missing: {spec.name}")
            feature_names.append(spec.name)
            continue
        if spec.missing_policy != "calibration_median_plus_indicator":
            raise ValueError(f"unsupported numeric missing policy for {spec.name}")
        if not observed:
            raise ValueError(f"cannot impute all-missing numeric field: {spec.name}")
        value = float(median(observed))
        medians.append((spec.name, value))
        feature_names.extend((spec.name, f"{spec.name}__missing"))
    payload = {
        "schema": "eog.numeric_baseline_state.v1",
        "feature_names": feature_names,
        "medians": medians,
        "field_specs": [
            {"name": spec.name, "kind": spec.kind, "missing_policy": spec.missing_policy}
            for spec in numeric_specs
        ],
    }
    return NumericBaselineState(
        feature_names=tuple(feature_names),
        medians=tuple(medians),
        field_specs=numeric_specs,
        fingerprint=_canonical_sha256(payload),
    )


def transform_numeric_baseline_rows(
    rows: Sequence[Mapping[str, object]],
    state: NumericBaselineState,
) -> tuple[tuple[float, ...], ...]:
    """Apply a frozen calibration-only numeric state to calibration or heldout rows."""

    medians = state.median_mapping
    output: list[tuple[float, ...]] = []
    for row in rows:
        values: list[float] = []
        for spec in state.field_specs:
            observed = _finite_or_none(row.get(spec.name))
            if spec.missing_policy == "forbid":
                if observed is None:
                    raise ValueError(f"required numeric baseline field is missing: {spec.name}")
                values.append(observed)
            else:
                is_missing = observed is None
                values.extend((medians[spec.name] if is_missing else observed, float(is_missing)))
        output.append(tuple(values))
    return tuple(output)


@runtime_checkable
class EOGDatasetAdapter(Protocol):
    """Internal adapter protocol; source-format details must stop at this boundary."""

    def freeze_pre_response(self) -> NormalizedPreResponseProblem:
        """Return a response-locked, fingerprinted normalized EOG problem."""

    def freeze_response_header(self) -> object:
        """Freeze physical response schema without opening a response row/value."""

    def materialize_response_once(self) -> object:
        """Open the prospectively authorized response once and map it to frozen units."""
