"""Response-blind forecast of finite-world survival regimes.

This post-closure module asks a deliberately narrow question before any biological
response is opened:

    Can structural properties of a declared, adequacy-eligible world universe predict
    whether its falsifiable worlds will all fail, partly contract, or all survive?

Structural adequacy and regime prediction are kept separate. The adequacy gate certifies
that the declared universe contains the structural scales required by the study. The
regime forecast then uses one distinct response-blind quantity per falsifiable world:

    horizon_realization_ratio
      = median_horizon_reachable_fraction / largest_weak_component_fraction

The ratio asks how much of a world's largest weakly connected spatial scale is typically
realizable from a node within the declared forecast horizon. A prospectively frozen
cutoff converts each falsifiable world to a predicted survive/fail indicator. The
predicted surviving-world fraction and three-state regime follow mechanically.

Non-falsifiable sentinel worlds such as a prospectively universal external_open world
must be excluded from both the predicted and observed regime denominators. They may be
retained in Layer A for conservative scientific interpretation, but including them in the
denominator would make falsified_universe structurally impossible in some systems.

This is a prospective mechanism hypothesis, not a guarantee of world compatibility and
not a repair or rerun of any consumed EOG-WF endpoint.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Literal, Sequence

import numpy as np

from .world_adequacy import (
    WorldUniverseStructuralAudit,
    WorldUniverseStructuralGate,
)


WorldSurvivalRegime = Literal[
    "falsified_universe",
    "contracting",
    "saturated",
]


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class RegimeForecastDeclaration:
    """Prospectively frozen mapping from structure to world-survival prediction."""

    horizon_realization_cutoff: float
    non_falsifiable_world_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        cutoff = float(self.horizon_realization_cutoff)
        if not np.isfinite(cutoff) or not 0.0 < cutoff <= 1.0:
            raise ValueError("horizon_realization_cutoff must lie in (0, 1]")
        object.__setattr__(self, "horizon_realization_cutoff", cutoff)

        world_ids = tuple(str(value).strip() for value in self.non_falsifiable_world_ids)
        if any(not value for value in world_ids) or len(set(world_ids)) != len(world_ids):
            raise ValueError("non_falsifiable_world_ids must contain unique non-empty IDs")
        object.__setattr__(self, "non_falsifiable_world_ids", tuple(sorted(world_ids)))


@dataclass(frozen=True)
class WorldRegimeStructuralRow:
    world_id: str
    largest_weak_component_fraction: float
    median_horizon_reachable_fraction: float
    horizon_realization_ratio: float
    predicted_survives: bool
    audit_fingerprint: str


@dataclass(frozen=True)
class WorldSurvivalRegimeForecast:
    regime: WorldSurvivalRegime
    predicted_surviving_world_fraction: float
    predicted_surviving_world_ids: tuple[str, ...]
    predicted_failing_world_ids: tuple[str, ...]
    falsifiable_world_ids: tuple[str, ...]
    non_falsifiable_world_ids: tuple[str, ...]
    structural_rows: tuple[WorldRegimeStructuralRow, ...]
    cutoff: float
    adequacy_gate_fingerprint: str
    audit_fingerprint: str
    fingerprint: str


@dataclass(frozen=True)
class ObservedWorldSurvivalRegime:
    regime: WorldSurvivalRegime
    declared_falsifiable_world_ids: tuple[str, ...]
    non_falsifiable_world_ids: tuple[str, ...]
    surviving_falsifiable_world_ids: tuple[str, ...]
    final_surviving_world_fraction: float
    contraction_event_count: int
    contraction_context_positions: tuple[int, ...]
    surviving_falsifiable_counts: tuple[int, ...]
    fingerprint: str


@dataclass(frozen=True)
class RegimeForecastScore:
    system_count: int
    exact_match_count: int
    exact_match_fraction: float
    mean_absolute_survival_fraction_error: float
    median_absolute_survival_fraction_error: float
    chance_reference: float
    one_sided_binomial_tail_p: float
    fingerprint: str


def _regime_from_fraction(value: float) -> WorldSurvivalRegime:
    if value <= 0.0:
        return "falsified_universe"
    if value >= 1.0:
        return "saturated"
    return "contracting"


def forecast_world_survival_regime(
    audit: WorldUniverseStructuralAudit,
    gate: WorldUniverseStructuralGate,
    declaration: RegimeForecastDeclaration,
) -> WorldSurvivalRegimeForecast:
    """Forecast the three-state survival regime without biological responses."""

    if gate.audit.fingerprint != audit.fingerprint:
        raise ValueError("gate and audit fingerprints do not match")
    if not gate.passed:
        raise ValueError("structural adequacy gate must pass before regime forecasting")
    if gate.declaration.min_median_horizon_reachable_fraction is not None:
        raise ValueError(
            "v1 regime forecast requires horizon reachability to remain outside the "
            "structural adequacy gate"
        )

    by_id = {row.world_id: row for row in audit.world_audits}
    non_falsifiable = declaration.non_falsifiable_world_ids
    missing = set(non_falsifiable).difference(by_id)
    if missing:
        raise ValueError(
            f"non-falsifiable world IDs are absent from structural audit: {sorted(missing)}"
        )

    non_falsifiable_set = set(non_falsifiable)
    falsifiable = tuple(
        row.world_id
        for row in audit.world_audits
        if row.world_id not in non_falsifiable_set
    )
    if not falsifiable:
        raise ValueError("at least one falsifiable world is required")

    rows: list[WorldRegimeStructuralRow] = []
    predicted_survivors: list[str] = []
    predicted_failures: list[str] = []
    for world_id in falsifiable:
        row = by_id[world_id]
        lcc = float(row.largest_weak_component_fraction)
        reachable = float(row.median_horizon_reachable_fraction)
        if lcc <= 0.0:
            raise ValueError("largest weak component fraction must be positive")
        ratio = reachable / lcc
        if ratio < -1e-12 or ratio > 1.0 + 1e-12:
            raise ValueError(
                "median horizon reachability must not exceed the largest weak component scale"
            )
        ratio = min(1.0, max(0.0, ratio))
        survives = ratio >= declaration.horizon_realization_cutoff
        if survives:
            predicted_survivors.append(world_id)
        else:
            predicted_failures.append(world_id)
        rows.append(
            WorldRegimeStructuralRow(
                world_id=world_id,
                largest_weak_component_fraction=lcc,
                median_horizon_reachable_fraction=reachable,
                horizon_realization_ratio=ratio,
                predicted_survives=survives,
                audit_fingerprint=row.fingerprint,
            )
        )

    fraction = len(predicted_survivors) / len(falsifiable)
    regime = _regime_from_fraction(fraction)
    payload = {
        "regime": regime,
        "predicted_surviving_world_fraction": fraction,
        "predicted_surviving_world_ids": predicted_survivors,
        "predicted_failing_world_ids": predicted_failures,
        "falsifiable_world_ids": list(falsifiable),
        "non_falsifiable_world_ids": list(non_falsifiable),
        "structural_rows": [
            {
                "world_id": row.world_id,
                "largest_weak_component_fraction": row.largest_weak_component_fraction,
                "median_horizon_reachable_fraction": row.median_horizon_reachable_fraction,
                "horizon_realization_ratio": row.horizon_realization_ratio,
                "predicted_survives": row.predicted_survives,
                "audit_fingerprint": row.audit_fingerprint,
            }
            for row in rows
        ],
        "cutoff": declaration.horizon_realization_cutoff,
        "adequacy_gate_fingerprint": gate.fingerprint,
        "audit_fingerprint": audit.fingerprint,
    }
    return WorldSurvivalRegimeForecast(
        regime=regime,
        predicted_surviving_world_fraction=float(fraction),
        predicted_surviving_world_ids=tuple(predicted_survivors),
        predicted_failing_world_ids=tuple(predicted_failures),
        falsifiable_world_ids=falsifiable,
        non_falsifiable_world_ids=non_falsifiable,
        structural_rows=tuple(rows),
        cutoff=declaration.horizon_realization_cutoff,
        adequacy_gate_fingerprint=gate.fingerprint,
        audit_fingerprint=audit.fingerprint,
        fingerprint=_canonical_sha256(payload),
    )


def classify_observed_world_survival_regime(
    *,
    declared_world_ids: Sequence[str],
    surviving_world_ids_by_context: Sequence[Sequence[str]],
    non_falsifiable_world_ids: Sequence[str] = (),
) -> ObservedWorldSurvivalRegime:
    """Classify a consumed positive-evidence contraction trajectory."""

    declared = tuple(str(value).strip() for value in declared_world_ids)
    if (
        not declared
        or any(not value for value in declared)
        or len(set(declared)) != len(declared)
    ):
        raise ValueError("declared_world_ids must contain unique non-empty IDs")

    non_falsifiable = tuple(
        sorted(str(value).strip() for value in non_falsifiable_world_ids)
    )
    if any(not value for value in non_falsifiable) or len(set(non_falsifiable)) != len(
        non_falsifiable
    ):
        raise ValueError("non_falsifiable_world_ids must contain unique non-empty IDs")
    if not set(non_falsifiable).issubset(declared):
        raise ValueError("non-falsifiable worlds must be a subset of declared worlds")

    trajectories = tuple(
        tuple(str(value).strip() for value in context)
        for context in surviving_world_ids_by_context
    )
    if not trajectories:
        raise ValueError("surviving_world_ids_by_context must not be empty")
    declared_set = set(declared)
    previous: set[str] | None = None
    for index, context in enumerate(trajectories):
        current = set(context)
        if len(current) != len(context) or any(not value for value in context):
            raise ValueError("each surviving context must contain unique non-empty IDs")
        if not current.issubset(declared_set):
            raise ValueError("surviving context contains undeclared world IDs")
        if index == 0 and current != declared_set:
            raise ValueError("first context must be the complete pre-evidence world set")
        if previous is not None and not current.issubset(previous):
            raise ValueError("surviving world sets must contract monotonically")
        previous = current

    non_falsifiable_set = set(non_falsifiable)
    falsifiable = tuple(
        world_id for world_id in declared if world_id not in non_falsifiable_set
    )
    if not falsifiable:
        raise ValueError("at least one falsifiable world is required")

    count_path: list[int] = []
    contraction_positions: list[int] = []
    previous_count: int | None = None
    for index, context in enumerate(trajectories):
        current = set(context)
        count = sum(world_id in current for world_id in falsifiable)
        count_path.append(count)
        if previous_count is not None and count < previous_count:
            contraction_positions.append(index)
        previous_count = count

    final_set = set(trajectories[-1])
    survivors = tuple(world_id for world_id in falsifiable if world_id in final_set)
    fraction = len(survivors) / len(falsifiable)
    regime = _regime_from_fraction(fraction)
    payload = {
        "regime": regime,
        "declared_falsifiable_world_ids": list(falsifiable),
        "non_falsifiable_world_ids": list(non_falsifiable),
        "surviving_falsifiable_world_ids": list(survivors),
        "final_surviving_world_fraction": fraction,
        "contraction_event_count": len(contraction_positions),
        "contraction_context_positions": contraction_positions,
        "surviving_falsifiable_counts": count_path,
    }
    return ObservedWorldSurvivalRegime(
        regime=regime,
        declared_falsifiable_world_ids=falsifiable,
        non_falsifiable_world_ids=non_falsifiable,
        surviving_falsifiable_world_ids=survivors,
        final_surviving_world_fraction=float(fraction),
        contraction_event_count=len(contraction_positions),
        contraction_context_positions=tuple(contraction_positions),
        surviving_falsifiable_counts=tuple(count_path),
        fingerprint=_canonical_sha256(payload),
    )


def score_regime_forecasts(
    forecasts: Sequence[WorldSurvivalRegimeForecast],
    observations: Sequence[ObservedWorldSurvivalRegime],
    *,
    chance_reference: float = 1.0 / 3.0,
) -> RegimeForecastScore:
    """Aggregate exact-match accuracy and survival-fraction absolute error."""

    predicted = tuple(forecasts)
    observed = tuple(observations)
    if not predicted or len(predicted) != len(observed):
        raise ValueError("forecasts and observations must have equal non-zero length")
    chance = float(chance_reference)
    if not np.isfinite(chance) or not 0.0 < chance < 1.0:
        raise ValueError("chance_reference must lie strictly between 0 and 1")

    matches = [
        forecast.regime == observation.regime
        for forecast, observation in zip(predicted, observed, strict=True)
    ]
    errors = np.asarray(
        [
            abs(
                forecast.predicted_surviving_world_fraction
                - observation.final_surviving_world_fraction
            )
            for forecast, observation in zip(predicted, observed, strict=True)
        ],
        dtype=float,
    )
    n = len(matches)
    k = int(sum(matches))
    tail = sum(
        math.comb(n, value)
        * (chance**value)
        * ((1.0 - chance) ** (n - value))
        for value in range(k, n + 1)
    )
    payload = {
        "system_count": n,
        "exact_match_count": k,
        "exact_match_fraction": k / n,
        "mean_absolute_survival_fraction_error": float(np.mean(errors)),
        "median_absolute_survival_fraction_error": float(np.median(errors)),
        "chance_reference": chance,
        "one_sided_binomial_tail_p": float(tail),
    }
    return RegimeForecastScore(
        system_count=n,
        exact_match_count=k,
        exact_match_fraction=float(k / n),
        mean_absolute_survival_fraction_error=float(np.mean(errors)),
        median_absolute_survival_fraction_error=float(np.median(errors)),
        chance_reference=chance,
        one_sided_binomial_tail_p=float(tail),
        fingerprint=_canonical_sha256(payload),
    )
