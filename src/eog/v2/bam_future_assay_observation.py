"""Robust future-target evidence design under assay observation-process uncertainty.

Ecological hypotheses are W1 BAM variants.  Observation-process uncertainty is a
separate finite axis describing how categorical parameter assays are coded.

The robust design target is a declared future binary decision, not exact ecological or
observation-world identity.  Pairs of joint hypotheses that imply the same future
decision need not be separated.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Hashable, Mapping, Sequence

from .bam_ecological_expansion_margin import EcologicalCoordinates, ExpandedBAMVariant
from .robust_evidence_design import robustly_separates


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

ORDINAL_FIELDS = frozenset(
    {
        "A_level",
        "partner_range_level",
        "antagonist_range_level",
        "dispersal_radius_level",
        "horizon_level",
    }
)
BINARY_FIELDS = frozenset(
    {
        "partner_required",
        "antagonist_excluded",
        "barrier_permeable",
    }
)

OBSERVATION_WORLDS = ("calibrated", "systematically_miscalibrated")


@dataclass(frozen=True)
class JointAssayHypothesis:
    ecological_world_id: str
    observation_world_id: str
    future_target: Hashable

    @property
    def joint_id(self) -> str:
        return f"{self.ecological_world_id}::{self.observation_world_id}"


@dataclass(frozen=True)
class RobustTargetActionRanking:
    action_id: str
    robust_split_target_pair_count: int
    unresolved_target_pair_count: int


@dataclass(frozen=True)
class RobustFutureTargetPlan:
    joint_hypothesis_ids: tuple[str, ...]
    target_discordant_pair_count: int
    rankings: tuple[RobustTargetActionRanking, ...]
    minimum_action_ids: tuple[str, ...] | None
    minimum_size: int | None
    all_target_pairs_separated: bool
    insufficient_action_library: bool


def _field_value(coords: EcologicalCoordinates, field: str) -> int:
    if field not in PARAMETER_FIELDS:
        raise ValueError(f"unknown parameter field: {field}")
    return int(getattr(coords, field))


def observed_assay_code(
    coords: EcologicalCoordinates,
    field: str,
    observation_world_id: str,
) -> str:
    """Return deterministic categorical code under one global assay-process world."""

    value = _field_value(coords, field)
    if observation_world_id == "calibrated":
        observed = value
    elif observation_world_id == "systematically_miscalibrated":
        if field in ORDINAL_FIELDS:
            observed = value + 1
        elif field in BINARY_FIELDS:
            observed = 1 - value
        else:
            raise RuntimeError(f"field type not declared: {field}")
    else:
        raise ValueError(f"unknown observation world: {observation_world_id}")
    return str(observed)


def build_joint_hypotheses(
    variants: Sequence[ExpandedBAMVariant],
    target_by_ecological_world: Mapping[str, Hashable],
) -> tuple[JointAssayHypothesis, ...]:
    rows = tuple(variants)
    if not rows:
        raise ValueError("variants must be non-empty")
    ids = [row.variant_id for row in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("variant IDs must be unique")
    missing = set(ids).difference(target_by_ecological_world)
    if missing:
        raise ValueError(f"target mapping missing variants: {sorted(missing)}")
    return tuple(
        sorted(
            (
                JointAssayHypothesis(
                    ecological_world_id=row.variant_id,
                    observation_world_id=obs_id,
                    future_target=target_by_ecological_world[row.variant_id],
                )
                for row in rows
                for obs_id in OBSERVATION_WORLDS
            ),
            key=lambda row: row.joint_id,
        )
    )


def target_discordant_pairs(
    hypotheses: Sequence[JointAssayHypothesis],
) -> tuple[tuple[str, str], ...]:
    rows = tuple(hypotheses)
    by_id = {row.joint_id: row for row in rows}
    if len(by_id) != len(rows):
        raise ValueError("joint hypothesis IDs must be unique")
    ids = tuple(sorted(by_id))
    return tuple(
        (ids[i], ids[j])
        for i in range(len(ids))
        for j in range(i + 1, len(ids))
        if by_id[ids[i]].future_target != by_id[ids[j]].future_target
    )


def build_action_supports(
    variants: Sequence[ExpandedBAMVariant],
    hypotheses: Sequence[JointAssayHypothesis],
) -> dict[str, dict[str, frozenset[str]]]:
    by_variant = {row.variant_id: row for row in variants}
    joint_ids = {row.joint_id for row in hypotheses}
    if not joint_ids:
        raise ValueError("hypotheses must be non-empty")

    actions: dict[str, dict[str, frozenset[str]]] = {}
    for field in PARAMETER_FIELDS:
        assay = {}
        repeat = {}
        for hypothesis in hypotheses:
            coords = by_variant[hypothesis.ecological_world_id].coordinates
            code = observed_assay_code(
                coords,
                field,
                hypothesis.observation_world_id,
            )
            assay[hypothesis.joint_id] = frozenset({code})
            repeat[hypothesis.joint_id] = frozenset({f"{code}|{code}"})
        actions[f"assay:{field}"] = assay
        actions[f"repeat2:{field}"] = repeat

    actions["assay_process_calibration"] = {
        hypothesis.joint_id: frozenset({hypothesis.observation_world_id})
        for hypothesis in hypotheses
    }

    for action_id, rows in actions.items():
        if set(rows) != joint_ids:
            raise RuntimeError(
                f"action {action_id} does not cover exact joint hypothesis universe"
            )
    return actions


def robust_target_pair_mask(
    pairs: Sequence[tuple[str, str]],
    action_support: Mapping[str, Sequence[str] | set[str] | frozenset[str]],
) -> int:
    mask = 0
    for i, (left, right) in enumerate(pairs):
        if robustly_separates(action_support[left], action_support[right]):
            mask |= 1 << i
    return mask


def _canonical_action_masks(
    pairs: Sequence[tuple[str, str]],
    action_supports: Mapping[
        str,
        Mapping[str, Sequence[str] | set[str] | frozenset[str]],
    ],
    action_ids: Sequence[str],
) -> tuple[tuple[str, int], ...]:
    rows = []
    for action_id in sorted(set(action_ids)):
        if action_id not in action_supports:
            raise ValueError(f"unknown action: {action_id}")
        rows.append(
            (
                action_id,
                robust_target_pair_mask(pairs, action_supports[action_id]),
            )
        )
    return tuple(rows)


def exact_minimum_robust_target_design(
    hypotheses: Sequence[JointAssayHypothesis],
    action_supports: Mapping[
        str,
        Mapping[str, Sequence[str] | set[str] | frozenset[str]],
    ],
    *,
    available_action_ids: Sequence[str] | None = None,
) -> RobustFutureTargetPlan:
    """Solve exact minimum action cover over only target-discordant joint pairs."""

    pairs = target_discordant_pairs(hypotheses)
    ids = tuple(sorted(row.joint_id for row in hypotheses))
    if not pairs:
        return RobustFutureTargetPlan(
            joint_hypothesis_ids=ids,
            target_discordant_pair_count=0,
            rankings=(),
            minimum_action_ids=(),
            minimum_size=0,
            all_target_pairs_separated=True,
            insufficient_action_library=False,
        )

    selected_ids = (
        tuple(sorted(action_supports))
        if available_action_ids is None
        else tuple(sorted(set(str(value) for value in available_action_ids)))
    )
    rows = _canonical_action_masks(pairs, action_supports, selected_ids)
    full_mask = (1 << len(pairs)) - 1

    rankings = tuple(
        sorted(
            (
                RobustTargetActionRanking(
                    action_id=action_id,
                    robust_split_target_pair_count=mask.bit_count(),
                    unresolved_target_pair_count=len(pairs) - mask.bit_count(),
                )
                for action_id, mask in rows
            ),
            key=lambda row: (-row.robust_split_target_pair_count, row.action_id),
        )
    )

    # Equal pair coverage is interchangeable for minimum cardinality; retain the
    # lexicographically first action.  Strictly subset coverage at equal unit cost is
    # dominated and may be removed exactly.
    coverage_to_id: dict[int, str] = {}
    for action_id, mask in rows:
        incumbent = coverage_to_id.get(mask)
        if incumbent is None or action_id < incumbent:
            coverage_to_id[mask] = action_id
    unique_rows = tuple(
        sorted(
            ((action_id, mask) for mask, action_id in coverage_to_id.items()),
            key=lambda row: row[0],
        )
    )
    maximal_rows = []
    for action_id, mask in sorted(
        unique_rows,
        key=lambda row: (-row[1].bit_count(), row[0]),
    ):
        if any(mask | kept_mask == kept_mask for _, kept_mask in maximal_rows):
            continue
        maximal_rows.append((action_id, mask))
    maximal_rows = tuple(sorted(maximal_rows))

    coverable = 0
    for _, mask in maximal_rows:
        coverable |= mask
    if coverable != full_mask:
        return RobustFutureTargetPlan(
            joint_hypothesis_ids=ids,
            target_discordant_pair_count=len(pairs),
            rankings=rankings,
            minimum_action_ids=None,
            minimum_size=None,
            all_target_pairs_separated=False,
            insufficient_action_library=True,
        )

    minimum: tuple[str, ...] | None = None
    for size in range(1, len(maximal_rows) + 1):
        candidates = []
        for combo in combinations(maximal_rows, size):
            covered = 0
            for _, mask in combo:
                covered |= mask
            if covered == full_mask:
                candidates.append(tuple(sorted(action_id for action_id, _ in combo)))
        if candidates:
            minimum = min(candidates)
            break

    return RobustFutureTargetPlan(
        joint_hypothesis_ids=ids,
        target_discordant_pair_count=len(pairs),
        rankings=rankings,
        minimum_action_ids=minimum,
        minimum_size=None if minimum is None else len(minimum),
        all_target_pairs_separated=minimum is not None,
        insufficient_action_library=minimum is None,
    )


def repeat_equivalence_violations(
    hypotheses: Sequence[JointAssayHypothesis],
    action_supports: Mapping[str, Mapping[str, frozenset[str]]],
) -> int:
    pairs = target_discordant_pairs(hypotheses)
    violations = 0
    for field in PARAMETER_FIELDS:
        one = robust_target_pair_mask(
            pairs,
            action_supports[f"assay:{field}"],
        )
        repeated = robust_target_pair_mask(
            pairs,
            action_supports[f"repeat2:{field}"],
        )
        if one != repeated:
            violations += 1
    return violations
