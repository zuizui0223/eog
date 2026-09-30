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


def _singleton_outcome(
    support: Sequence[str] | set[str] | frozenset[str],
) -> str:
    values = tuple(support)
    if len(values) != 1:
        raise ValueError("deterministic fast path requires singleton action supports")
    return str(values[0])


def _normalized_singleton_partition(
    action_support: Mapping[str, Sequence[str] | set[str] | frozenset[str]],
    joint_ids: Sequence[str],
) -> tuple[int, ...]:
    labels: dict[str, int] = {}
    signature: list[int] = []
    for joint_id in joint_ids:
        value = _singleton_outcome(action_support[joint_id])
        if value not in labels:
            labels[value] = len(labels)
        signature.append(labels[value])
    return tuple(signature)


def repeat_equivalence_violations_deterministic(
    hypotheses: Sequence[JointAssayHypothesis],
    action_supports: Mapping[str, Mapping[str, frozenset[str]]],
) -> int:
    """Fast exact H1 audit for deterministic assay outcomes.

    Two actions have identical robust pair coverage iff they induce the same partition
    of the joint-hypothesis set.  The repeated assay maps code -> code|code, which is a
    one-to-one recoding under the frozen systematic observation world.
    """

    joint_ids = tuple(sorted(row.joint_id for row in hypotheses))
    violations = 0
    for field in PARAMETER_FIELDS:
        one = _normalized_singleton_partition(
            action_supports[f"assay:{field}"],
            joint_ids,
        )
        repeated = _normalized_singleton_partition(
            action_supports[f"repeat2:{field}"],
            joint_ids,
        )
        if one != repeated:
            violations += 1
    return violations


def exact_minimum_deterministic_target_design(
    hypotheses: Sequence[JointAssayHypothesis],
    action_supports: Mapping[
        str,
        Mapping[str, Sequence[str] | set[str] | frozenset[str]],
    ],
    *,
    available_action_ids: Sequence[str] | None = None,
) -> RobustFutureTargetPlan:
    """Exact minimum target design for deterministic singleton action outcomes.

    This is mathematically equivalent to covering all target-discordant hypothesis
    pairs, but avoids explicitly materializing O(n^2) pairs.  A selected action set is
    sufficient iff every joint hypothesis sharing the same combined observed signature
    also shares the same future target.

    Actions that induce exactly the same hypothesis partition are interchangeable for
    every possible combination; only the lexicographically first representative is
    retained.  In the frozen Phase-VII library this removes repeat2 duplicates while
    preserving the exact minimum cardinality and lexicographic tie rule.
    """

    rows = tuple(hypotheses)
    if not rows:
        raise ValueError("hypotheses must be non-empty")
    by_id = {row.joint_id: row for row in rows}
    if len(by_id) != len(rows):
        raise ValueError("joint hypothesis IDs must be unique")
    joint_ids = tuple(sorted(by_id))

    selected_ids = (
        tuple(sorted(action_supports))
        if available_action_ids is None
        else tuple(sorted(set(str(value) for value in available_action_ids)))
    )
    missing_actions = set(selected_ids).difference(action_supports)
    if missing_actions:
        raise ValueError(f"unknown actions: {sorted(missing_actions)}")

    # Validate singleton deterministic supports and exact hypothesis coverage.
    outcome_by_action: dict[str, dict[str, str]] = {}
    for action_id in selected_ids:
        support = action_supports[action_id]
        if set(support) != set(joint_ids):
            raise ValueError(
                f"action {action_id!r} must cover exact joint hypothesis universe"
            )
        outcome_by_action[action_id] = {
            joint_id: _singleton_outcome(support[joint_id])
            for joint_id in joint_ids
        }

    target_counts = Counter(by_id[joint_id].future_target for joint_id in joint_ids)
    n = len(joint_ids)
    total_pairs = n * (n - 1) // 2
    same_target_pairs = sum(count * (count - 1) // 2 for count in target_counts.values())
    discordant_pair_count = total_pairs - same_target_pairs

    if discordant_pair_count == 0:
        return RobustFutureTargetPlan(
            joint_hypothesis_ids=joint_ids,
            target_discordant_pair_count=0,
            rankings=(),
            minimum_action_ids=(),
            minimum_size=0,
            all_target_pairs_separated=True,
            insufficient_action_library=False,
        )

    rankings_list: list[RobustTargetActionRanking] = []
    for action_id in selected_ids:
        grouped: dict[str, Counter[Hashable]] = {}
        for joint_id in joint_ids:
            outcome = outcome_by_action[action_id][joint_id]
            grouped.setdefault(outcome, Counter())[
                by_id[joint_id].future_target
            ] += 1

        unresolved = 0
        for counts in grouped.values():
            group_n = sum(counts.values())
            group_pairs = group_n * (group_n - 1) // 2
            same = sum(count * (count - 1) // 2 for count in counts.values())
            unresolved += group_pairs - same
        split = discordant_pair_count - unresolved
        rankings_list.append(
            RobustTargetActionRanking(
                action_id=action_id,
                robust_split_target_pair_count=split,
                unresolved_target_pair_count=unresolved,
            )
        )
    rankings = tuple(
        sorted(
            rankings_list,
            key=lambda row: (-row.robust_split_target_pair_count, row.action_id),
        )
    )

    # Deduplicate actions by the exact partition they induce.  Partition labels are
    # normalized so one-to-one recodings such as code -> code|code collapse exactly.
    partition_to_id: dict[tuple[int, ...], str] = {}
    for action_id in selected_ids:
        partition = _normalized_singleton_partition(
            action_supports[action_id],
            joint_ids,
        )
        incumbent = partition_to_id.get(partition)
        if incumbent is None or action_id < incumbent:
            partition_to_id[partition] = action_id
    canonical_ids = tuple(sorted(partition_to_id.values()))

    def sufficient(combo: Sequence[str]) -> bool:
        signature_targets: dict[tuple[str, ...], Hashable] = {}
        for joint_id in joint_ids:
            signature = tuple(
                outcome_by_action[action_id][joint_id]
                for action_id in combo
            )
            target = by_id[joint_id].future_target
            incumbent = signature_targets.get(signature)
            if incumbent is None:
                signature_targets[signature] = target
            elif incumbent != target:
                return False
        return True

    minimum: tuple[str, ...] | None = None
    for size in range(1, len(canonical_ids) + 1):
        for combo in combinations(canonical_ids, size):
            if sufficient(combo):
                minimum = tuple(combo)
                break
        if minimum is not None:
            break

    return RobustFutureTargetPlan(
        joint_hypothesis_ids=joint_ids,
        target_discordant_pair_count=discordant_pair_count,
        rankings=rankings,
        minimum_action_ids=minimum,
        minimum_size=None if minimum is None else len(minimum),
        all_target_pairs_separated=minimum is not None,
        insufficient_action_library=minimum is None,
    )
