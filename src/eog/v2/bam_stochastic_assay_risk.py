"""Risk-bounded repeated assay design for future BAM targets.

Phase VII used finite deterministic assay-observation worlds and exact support-based
robust separation.  This module introduces full-support stochastic categorical assay
error while keeping the ecological W1 universe and future targets fixed.

Because full-support kernels overlap for every finite repeat depth, exact robust
separation remains impossible.  We therefore keep that statement separate from a
probabilistic pairwise distinguishability metric: the Bhattacharyya upper bound on
equal-prior binary pairwise Bayes error.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Hashable, Mapping, Sequence

from .bam_ecological_expansion_margin import EcologicalCoordinates, ExpandedBAMVariant


PARAMETER_FIELDS = (
    "A_level",
    "partner_required",
    "antagonist_excluded",
    "partner_range_level",
    "antagonist_range_level",
    "dispersal_radius_level",
    "barrier_permeable",
    "horizon_level",
)

FIELD_DOMAINS: dict[str, tuple[int, ...]] = {
    "A_level": (-1, 0, 1, 2),
    "partner_required": (0, 1),
    "antagonist_excluded": (0, 1),
    "partner_range_level": (-1, 0, 1),
    "antagonist_range_level": (-1, 0, 1),
    "dispersal_radius_level": (0, 1, 2),
    "barrier_permeable": (0, 1),
    "horizon_level": (0, 1, 2),
}

QUALITY_WORLDS: dict[str, float] = {
    "moderate_accuracy": 0.7,
    "high_accuracy": 0.9,
}


@dataclass(frozen=True)
class PairwiseRiskResult:
    selected_fields: tuple[str, ...]
    repeat_depth: int
    quality_calibrated: bool
    worst_bhattacharyya_affinity: float
    worst_pair_error_upper_bound: float
    worst_pair_quality_relation: str
    worst_pair_description: tuple[object, ...]


@dataclass(frozen=True)
class StochasticRepeatPlan:
    selected_fields: tuple[str, ...]
    risk_threshold: float
    repeat_cap: int
    no_calibration_min_repeat: int | None
    no_calibration_total_action_count: int | None
    quality_calibration_min_repeat: int | None
    quality_calibration_total_action_count: int | None
    no_calibration_at_minimum: PairwiseRiskResult | None
    quality_calibration_at_minimum: PairwiseRiskResult | None
    exact_robust_separation_possible_finite_repeats: bool


def categorical_assay_kernel(
    field: str,
    true_value: int,
    p_correct: float,
) -> dict[int, float]:
    """Symmetric full-support categorical error kernel."""

    if field not in FIELD_DOMAINS:
        raise ValueError(f"unknown parameter field: {field}")
    domain = FIELD_DOMAINS[field]
    if true_value not in domain:
        raise ValueError(f"true value {true_value} outside {field} domain")
    p = float(p_correct)
    if not 0.0 < p < 1.0:
        raise ValueError("p_correct must lie strictly between 0 and 1")
    if len(domain) < 2:
        raise ValueError("field domain must contain at least two codes")
    wrong = (1.0 - p) / (len(domain) - 1)
    return {
        code: (p if code == true_value else wrong)
        for code in domain
    }


def bhattacharyya_affinity(
    left: Mapping[int, float],
    right: Mapping[int, float],
) -> float:
    if set(left) != set(right):
        raise ValueError("probability mappings must share exact support")
    value = sum(
        math.sqrt(float(left[key]) * float(right[key]))
        for key in left
    )
    # Numerical roundoff only.
    return min(1.0, max(0.0, float(value)))


def single_assay_affinity(
    left: EcologicalCoordinates,
    left_quality: str,
    right: EcologicalCoordinates,
    right_quality: str,
    field: str,
) -> float:
    if left_quality not in QUALITY_WORLDS or right_quality not in QUALITY_WORLDS:
        raise ValueError("unknown assay-quality world")
    p_left = QUALITY_WORLDS[left_quality]
    p_right = QUALITY_WORLDS[right_quality]
    return bhattacharyya_affinity(
        categorical_assay_kernel(
            field,
            int(getattr(left, field)),
            p_left,
        ),
        categorical_assay_kernel(
            field,
            int(getattr(right, field)),
            p_right,
        ),
    )


def selected_field_signature(
    coords: EcologicalCoordinates,
    fields: Sequence[str],
) -> tuple[int, ...]:
    selected = tuple(str(field) for field in fields)
    if not selected:
        raise ValueError("selected fields must be non-empty")
    if len(set(selected)) != len(selected):
        raise ValueError("selected fields must be unique")
    missing = set(selected).difference(PARAMETER_FIELDS)
    if missing:
        raise ValueError(f"unknown selected fields: {sorted(missing)}")
    return tuple(int(getattr(coords, field)) for field in selected)


def _target_signature_classes(
    variants: Sequence[ExpandedBAMVariant],
    target_by_world: Mapping[str, Hashable],
    fields: Sequence[str],
) -> tuple[tuple[Hashable, tuple[int, ...]], ...]:
    rows = tuple(variants)
    if not rows:
        raise ValueError("variants must be non-empty")
    missing = {row.variant_id for row in rows}.difference(target_by_world)
    if missing:
        raise ValueError(f"target mapping missing variants: {sorted(missing)}")
    classes = {
        (
            target_by_world[row.variant_id],
            selected_field_signature(row.coordinates, fields),
        )
        for row in rows
    }
    return tuple(sorted(classes, key=lambda value: (repr(value[0]), value[1])))


def worst_target_pair_risk(
    variants: Sequence[ExpandedBAMVariant],
    target_by_world: Mapping[str, Hashable],
    selected_fields: Sequence[str],
    *,
    repeat_depth: int,
    quality_calibrated: bool,
) -> PairwiseRiskResult:
    """Worst pairwise BC/2 bound across target-discordant ecological x quality worlds."""

    fields = tuple(sorted(set(str(field) for field in selected_fields)))
    if not fields:
        raise ValueError("selected_fields must be non-empty")
    if repeat_depth < 1:
        raise ValueError("repeat_depth must be positive")
    classes = _target_signature_classes(variants, target_by_world, fields)
    if len({target for target, _ in classes}) <= 1:
        raise ValueError("future target must be unresolved in the scored fiber")

    # One representative coordinate object per selected signature is enough because
    # assay distributions depend only on the selected values.
    signature_coords = {
        signature: EcologicalCoordinates(
            **{
                field: (
                    signature[fields.index(field)]
                    if field in fields
                    else 0
                )
                for field in PARAMETER_FIELDS
            }
        )
        for _, signature in classes
    }

    worst = -1.0
    worst_desc: tuple[object, ...] | None = None
    worst_relation = ""
    for i, (target_left, sig_left) in enumerate(classes):
        for target_right, sig_right in classes[i + 1 :]:
            if target_left == target_right:
                continue
            left_coords = signature_coords[sig_left]
            right_coords = signature_coords[sig_right]
            for q_left, p_left in QUALITY_WORLDS.items():
                for q_right, p_right in QUALITY_WORLDS.items():
                    if quality_calibrated and q_left != q_right:
                        affinity = 0.0
                    else:
                        one_repeat = 1.0
                        for field in fields:
                            one_repeat *= single_assay_affinity(
                                left_coords,
                                q_left,
                                right_coords,
                                q_right,
                                field,
                            )
                        affinity = one_repeat ** int(repeat_depth)
                    if affinity > worst + 1e-15:
                        worst = affinity
                        worst_relation = (
                            "same_quality" if q_left == q_right else "cross_quality"
                        )
                        worst_desc = (
                            target_left,
                            sig_left,
                            q_left,
                            p_left,
                            target_right,
                            sig_right,
                            q_right,
                            p_right,
                        )
    if worst_desc is None:
        raise RuntimeError("no target-discordant joint pair found")
    return PairwiseRiskResult(
        selected_fields=fields,
        repeat_depth=int(repeat_depth),
        quality_calibrated=bool(quality_calibrated),
        worst_bhattacharyya_affinity=float(worst),
        worst_pair_error_upper_bound=float(worst / 2.0),
        worst_pair_quality_relation=worst_relation,
        worst_pair_description=worst_desc,
    )


def minimum_repeat_plan(
    variants: Sequence[ExpandedBAMVariant],
    target_by_world: Mapping[str, Hashable],
    selected_fields: Sequence[str],
    *,
    risk_threshold: float = 0.05,
    repeat_cap: int = 30,
) -> StochasticRepeatPlan:
    threshold = float(risk_threshold)
    if not 0.0 < threshold < 0.5:
        raise ValueError("risk_threshold must lie between 0 and 0.5")
    if repeat_cap < 1:
        raise ValueError("repeat_cap must be positive")
    fields = tuple(sorted(set(str(field) for field in selected_fields)))

    no_cal_n = None
    no_cal_result = None
    cal_n = None
    cal_result = None

    for n in range(1, repeat_cap + 1):
        if no_cal_n is None:
            result = worst_target_pair_risk(
                variants,
                target_by_world,
                fields,
                repeat_depth=n,
                quality_calibrated=False,
            )
            if result.worst_pair_error_upper_bound <= threshold + 1e-15:
                no_cal_n = n
                no_cal_result = result

        if cal_n is None:
            result = worst_target_pair_risk(
                variants,
                target_by_world,
                fields,
                repeat_depth=n,
                quality_calibrated=True,
            )
            if result.worst_pair_error_upper_bound <= threshold + 1e-15:
                cal_n = n
                cal_result = result

        if no_cal_n is not None and cal_n is not None:
            break

    no_cal_cost = None if no_cal_n is None else no_cal_n * len(fields)
    cal_cost = None if cal_n is None else cal_n * len(fields) + 1

    # Full-support same-quality target-discordant pairs exist for every unresolved
    # ecological target.  Hence no finite repeat depth gives exact support separation.
    exact_robust = False

    return StochasticRepeatPlan(
        selected_fields=fields,
        risk_threshold=threshold,
        repeat_cap=int(repeat_cap),
        no_calibration_min_repeat=no_cal_n,
        no_calibration_total_action_count=no_cal_cost,
        quality_calibration_min_repeat=cal_n,
        quality_calibration_total_action_count=cal_cost,
        no_calibration_at_minimum=no_cal_result,
        quality_calibration_at_minimum=cal_result,
        exact_robust_separation_possible_finite_repeats=exact_robust,
    )
