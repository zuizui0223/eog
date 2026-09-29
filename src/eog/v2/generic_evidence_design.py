"""Generic exact evidence design over a declared finite world universe.

The planner is intentionally domain-agnostic. It receives:
- a current evidence signature for every declared world;
- a finite, predeclared evidence/intervention library whose outcome is specified
  for every world;
- optionally, a subset of currently active/surviving worlds.

It returns unresolved world pairs, per-evidence discrimination, and an exact
minimum separating evidence set when the supplied library is sufficient.

If the library cannot separate all active worlds, the planner fails closed by
returning minimum_separating_set=None while retaining unresolved classes.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations
import hashlib
import json
from typing import Hashable, Mapping, Sequence


def _sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_world_signatures(
    current_signature_by_world: Mapping[str, Hashable],
) -> tuple[str, ...]:
    if not current_signature_by_world:
        raise ValueError("current_signature_by_world must be non-empty")
    world_ids = tuple(sorted(str(world_id) for world_id in current_signature_by_world))
    if any(not world_id.strip() for world_id in world_ids):
        raise ValueError("world IDs must be non-empty")
    if len(set(world_ids)) != len(world_ids):
        raise ValueError("world IDs must be unique")
    return world_ids


def _validate_active_worlds(
    all_world_ids: Sequence[str],
    active_world_ids: Sequence[str] | None,
) -> tuple[str, ...]:
    all_set = set(all_world_ids)
    if active_world_ids is None:
        return tuple(all_world_ids)
    requested = tuple(str(world_id) for world_id in active_world_ids)
    if not requested or len(set(requested)) != len(requested):
        raise ValueError("active_world_ids must contain unique declared world IDs")
    missing = set(requested).difference(all_set)
    if missing:
        raise ValueError(f"active_world_ids contains undeclared worlds: {sorted(missing)}")
    requested_set = set(requested)
    return tuple(world_id for world_id in all_world_ids if world_id in requested_set)


def _validate_evidence_library(
    all_world_ids: Sequence[str],
    evidence_outcomes: Mapping[str, Mapping[str, Hashable]],
) -> tuple[str, ...]:
    if not evidence_outcomes:
        raise ValueError("evidence_outcomes must be non-empty")
    all_set = set(all_world_ids)
    evidence_ids = tuple(sorted(str(evidence_id) for evidence_id in evidence_outcomes))
    if any(not evidence_id.strip() for evidence_id in evidence_ids):
        raise ValueError("evidence IDs must be non-empty")
    if len(set(evidence_ids)) != len(evidence_ids):
        raise ValueError("evidence IDs must be unique")
    for evidence_id in evidence_ids:
        outcome_worlds = set(evidence_outcomes[evidence_id])
        if outcome_worlds != all_set:
            missing = sorted(all_set.difference(outcome_worlds))
            extra = sorted(outcome_worlds.difference(all_set))
            raise ValueError(
                f"evidence {evidence_id!r} must define exactly one outcome for every world; "
                f"missing={missing}, extra={extra}"
            )
    return evidence_ids


def _signature(
    world_id: str,
    current_signature_by_world: Mapping[str, Hashable],
    evidence_outcomes: Mapping[str, Mapping[str, Hashable]],
    selected_evidence_ids: Sequence[str],
) -> tuple[Hashable, ...]:
    return (
        current_signature_by_world[world_id],
        *(
            evidence_outcomes[evidence_id][world_id]
            for evidence_id in selected_evidence_ids
        ),
    )


def equivalence_classes(
    current_signature_by_world: Mapping[str, Hashable],
    evidence_outcomes: Mapping[str, Mapping[str, Hashable]],
    *,
    active_world_ids: Sequence[str] | None = None,
    selected_evidence_ids: Sequence[str] = (),
) -> tuple[tuple[str, ...], ...]:
    """Return exact equivalence classes after appending selected evidence channels."""

    all_world_ids = _validate_world_signatures(current_signature_by_world)
    active = _validate_active_worlds(all_world_ids, active_world_ids)
    evidence_ids = _validate_evidence_library(all_world_ids, evidence_outcomes)
    selected = tuple(str(value) for value in selected_evidence_ids)
    if len(set(selected)) != len(selected):
        raise ValueError("selected_evidence_ids must be unique")
    missing = set(selected).difference(evidence_ids)
    if missing:
        raise ValueError(f"selected evidence IDs are not in the library: {sorted(missing)}")

    groups: dict[tuple[Hashable, ...], list[str]] = defaultdict(list)
    for world_id in active:
        groups[
            _signature(
                world_id,
                current_signature_by_world,
                evidence_outcomes,
                selected,
            )
        ].append(world_id)
    return tuple(
        sorted(
            (tuple(sorted(ids)) for ids in groups.values()),
            key=lambda ids: (len(ids), ids),
        )
    )


def unresolved_pairs_from_classes(
    classes: Sequence[Sequence[str]],
) -> tuple[tuple[str, str], ...]:
    pairs: list[tuple[str, str]] = []
    for values in classes:
        ids = tuple(sorted(values))
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                pairs.append((ids[i], ids[j]))
    return tuple(sorted(pairs))


def evidence_split_count(
    unresolved_pairs: Sequence[tuple[str, str]],
    outcome_by_world: Mapping[str, Hashable],
) -> int:
    return sum(
        1
        for left, right in unresolved_pairs
        if outcome_by_world[left] != outcome_by_world[right]
    )


def evidence_set_covers_pairs(
    unresolved_pairs: Sequence[tuple[str, str]],
    evidence_outcomes: Mapping[str, Mapping[str, Hashable]],
    selected_evidence_ids: Sequence[str],
) -> bool:
    selected = tuple(selected_evidence_ids)
    for left, right in unresolved_pairs:
        if not any(
            evidence_outcomes[evidence_id][left]
            != evidence_outcomes[evidence_id][right]
            for evidence_id in selected
        ):
            return False
    return True


def exact_minimum_separating_set(
    current_signature_by_world: Mapping[str, Hashable],
    evidence_outcomes: Mapping[str, Mapping[str, Hashable]],
    *,
    active_world_ids: Sequence[str] | None = None,
) -> tuple[str, ...] | None:
    """Return the lexicographically first exact minimum separating set, or None."""

    all_world_ids = _validate_world_signatures(current_signature_by_world)
    active = _validate_active_worlds(all_world_ids, active_world_ids)
    evidence_ids = _validate_evidence_library(all_world_ids, evidence_outcomes)
    current_classes = equivalence_classes(
        current_signature_by_world,
        evidence_outcomes,
        active_world_ids=active,
    )
    unresolved = unresolved_pairs_from_classes(current_classes)
    if not unresolved:
        return ()

    for size in range(1, len(evidence_ids) + 1):
        candidates: list[tuple[str, ...]] = []
        for subset in combinations(evidence_ids, size):
            if evidence_set_covers_pairs(unresolved, evidence_outcomes, subset):
                candidates.append(tuple(subset))
        if candidates:
            return min(candidates)
    return None


@dataclass(frozen=True)
class EvidenceRanking:
    evidence_id: str
    split_unresolved_pairs: int
    unresolved_pairs_remaining: int
    residual_class_size_distribution: tuple[tuple[int, int], ...]
    largest_residual_class: int


@dataclass(frozen=True)
class FiniteEvidenceDesignPlan:
    active_world_ids: tuple[str, ...]
    current_equivalence_classes: tuple[tuple[str, ...], ...]
    unresolved_world_pairs: tuple[tuple[str, str], ...]
    rankings: tuple[EvidenceRanking, ...]
    minimum_separating_set: tuple[str, ...] | None
    minimum_set_size: int | None
    final_equivalence_classes: tuple[tuple[str, ...], ...]
    all_active_worlds_separated: bool
    insufficient_library: bool
    coverage_certificate: str
    fingerprint: str


def plan_finite_evidence_design(
    current_signature_by_world: Mapping[str, Hashable],
    evidence_outcomes: Mapping[str, Mapping[str, Hashable]],
    *,
    active_world_ids: Sequence[str] | None = None,
) -> FiniteEvidenceDesignPlan:
    """Plan exact evidence acquisition inside one finite declared world universe."""

    all_world_ids = _validate_world_signatures(current_signature_by_world)
    active = _validate_active_worlds(all_world_ids, active_world_ids)
    evidence_ids = _validate_evidence_library(all_world_ids, evidence_outcomes)

    current_classes = equivalence_classes(
        current_signature_by_world,
        evidence_outcomes,
        active_world_ids=active,
    )
    unresolved = unresolved_pairs_from_classes(current_classes)

    rankings: list[EvidenceRanking] = []
    for evidence_id in evidence_ids:
        classes = equivalence_classes(
            current_signature_by_world,
            evidence_outcomes,
            active_world_ids=active,
            selected_evidence_ids=(evidence_id,),
        )
        size_dist = Counter(len(group) for group in classes)
        split = evidence_split_count(unresolved, evidence_outcomes[evidence_id])
        rankings.append(
            EvidenceRanking(
                evidence_id=evidence_id,
                split_unresolved_pairs=split,
                unresolved_pairs_remaining=len(unresolved) - split,
                residual_class_size_distribution=tuple(sorted(size_dist.items())),
                largest_residual_class=max(len(group) for group in classes),
            )
        )
    rankings.sort(
        key=lambda row: (
            -row.split_unresolved_pairs,
            row.largest_residual_class,
            row.evidence_id,
        )
    )

    minimum = exact_minimum_separating_set(
        current_signature_by_world,
        evidence_outcomes,
        active_world_ids=active,
    )
    if minimum is None:
        final_classes = equivalence_classes(
            current_signature_by_world,
            evidence_outcomes,
            active_world_ids=active,
            selected_evidence_ids=evidence_ids,
        )
    else:
        final_classes = equivalence_classes(
            current_signature_by_world,
            evidence_outcomes,
            active_world_ids=active,
            selected_evidence_ids=minimum,
        )
    all_separated = all(len(group) == 1 for group in final_classes)
    insufficient = bool(unresolved) and minimum is None
    certificate = "exact_exhaustive_finite_evidence_subset_search"

    payload = {
        "all_declared_world_ids": list(all_world_ids),
        "active_world_ids": list(active),
        "current_classes": [list(group) for group in current_classes],
        "unresolved_pairs": [list(pair) for pair in unresolved],
        "evidence_ids": list(evidence_ids),
        "rankings": [
            {
                "evidence_id": row.evidence_id,
                "split_unresolved_pairs": row.split_unresolved_pairs,
                "unresolved_pairs_remaining": row.unresolved_pairs_remaining,
                "residual_class_size_distribution": list(
                    row.residual_class_size_distribution
                ),
                "largest_residual_class": row.largest_residual_class,
            }
            for row in rankings
        ],
        "minimum_separating_set": None if minimum is None else list(minimum),
        "final_classes": [list(group) for group in final_classes],
        "all_active_worlds_separated": all_separated,
        "insufficient_library": insufficient,
        "coverage_certificate": certificate,
    }

    return FiniteEvidenceDesignPlan(
        active_world_ids=active,
        current_equivalence_classes=current_classes,
        unresolved_world_pairs=unresolved,
        rankings=tuple(rankings),
        minimum_separating_set=minimum,
        minimum_set_size=None if minimum is None else len(minimum),
        final_equivalence_classes=final_classes,
        all_active_worlds_separated=all_separated,
        insufficient_library=insufficient,
        coverage_certificate=certificate,
        fingerprint=_sha256(payload),
    )
