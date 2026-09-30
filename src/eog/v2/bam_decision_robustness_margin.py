"""Exact world-universe robustness margins for finite BAM release decisions.

A decision can be invariant inside a declared finite BAM world universe while remaining
fragile to nearby, currently undeclared A/B/M decompositions that reproduce the same
current distribution G.

This module measures that logical fragility without assigning plausibility or probability
to the undeclared completions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .known_truth_bam import BAMWorld
from .bam_counterfactual_identifiability import release_expands_current


def _all_mask(node_count: int) -> int:
    if node_count < 1:
        raise ValueError("node_count must be positive")
    return (1 << node_count) - 1


def _validate_mask(mask: int, node_count: int, name: str) -> int:
    value = int(mask)
    if value < 0 or value & ~_all_mask(node_count):
        raise ValueError(f"{name} outside declared node universe")
    return value


def realised_mask(A: int, B: int, M: int) -> int:
    return int(A) & int(B) & int(M)


def release_decision_from_masks(
    A: int,
    B: int,
    M: int,
    *,
    axis: str,
    node_count: int,
) -> bool:
    A = _validate_mask(A, node_count, "A")
    B = _validate_mask(B, node_count, "B")
    M = _validate_mask(M, node_count, "M")
    G = A & B & M
    outside = _all_mask(node_count) & ~G
    if axis == "A":
        released = B & M
    elif axis == "B":
        released = A & M
    elif axis == "M":
        released = A & B
    else:
        raise ValueError("axis must be A, B or M")
    return bool(released & outside)


def complete_same_g_release_outcomes(
    G: int,
    *,
    axis: str,
    node_count: int,
) -> frozenset[bool]:
    """Exact possible binary release outcomes over every same-G BAM decomposition."""

    G = _validate_mask(G, node_count, "G")
    if axis not in {"A", "B", "M"}:
        raise ValueError("axis must be A, B or M")
    if G == _all_mask(node_count):
        return frozenset({False})
    return frozenset({False, True})


def _retained_and_released_masks(
    A: int,
    B: int,
    M: int,
    axis: str,
) -> tuple[int, int, int]:
    if axis == "A":
        return B, M, A
    if axis == "B":
        return A, M, B
    if axis == "M":
        return A, B, M
    raise ValueError("axis must be A, B or M")


def single_state_completion_flip_margin(
    A: int,
    B: int,
    M: int,
    *,
    axis: str,
    node_count: int,
) -> int | None:
    """Minimum A/B/M bit flips to a same-G state with the opposite release decision.

    Distance is Hamming distance across all three binary axis-state vectors.

    If the current release decision is True, every outside-G node in the intersection
    of the two retained axes must be broken, requiring exactly one retained-axis flip
    per such node.

    If the current release decision is False, choose one outside-G node and convert its
    local three-axis state to the pattern:
      released axis = 0
      retained axes = 1, 1
    The minimum local mismatch count is the exact flip margin.

    When G occupies the full node universe there is no outside-G node and no opposite
    decision exists under same-G completion; None is returned.
    """

    A = _validate_mask(A, node_count, "A")
    B = _validate_mask(B, node_count, "B")
    M = _validate_mask(M, node_count, "M")
    G = A & B & M
    outside = _all_mask(node_count) & ~G
    if outside == 0:
        return None

    retained1, retained2, released_axis = _retained_and_released_masks(A, B, M, axis)
    extras = retained1 & retained2 & outside
    if extras:
        return int(extras.bit_count())

    best: int | None = None
    for i in range(node_count):
        bit = 1 << i
        if not (outside & bit):
            continue
        cost = 0
        if not (retained1 & bit):
            cost += 1
        if not (retained2 & bit):
            cost += 1
        if released_axis & bit:
            cost += 1
        if best is None or cost < best:
            best = cost
    return best


def brute_force_single_state_completion_flip_margin(
    A: int,
    B: int,
    M: int,
    *,
    axis: str,
    node_count: int,
) -> int | None:
    """Reference exhaustive solver for small finite universes."""

    A = _validate_mask(A, node_count, "A")
    B = _validate_mask(B, node_count, "B")
    M = _validate_mask(M, node_count, "M")
    G = A & B & M
    current = release_decision_from_masks(A, B, M, axis=axis, node_count=node_count)
    limit = 1 << node_count
    best: int | None = None

    for A2 in range(limit):
        for B2 in range(limit):
            for M2 in range(limit):
                if (A2 & B2 & M2) != G:
                    continue
                candidate = release_decision_from_masks(
                    A2, B2, M2, axis=axis, node_count=node_count
                )
                if candidate == current:
                    continue
                distance = (
                    (A ^ A2).bit_count()
                    + (B ^ B2).bit_count()
                    + (M ^ M2).bit_count()
                )
                if best is None or distance < best:
                    best = distance
    return best


@dataclass(frozen=True)
class FiberDecisionMargin:
    axis: str
    survivor_ids: tuple[str, ...]
    current_decision: bool | None
    identified_in_declared_universe: bool
    completion_flip_margin: int | None
    full_completion_outcomes: frozenset[bool]


def survivor_fiber_completion_margin(
    worlds: Sequence[BAMWorld],
    survivor_ids: Sequence[str],
    *,
    axis: str,
) -> FiberDecisionMargin:
    """Compute declared-universe status and nearest opposite-decision completion."""

    by_id = {world.world_id: world for world in worlds}
    ids = tuple(sorted(set(str(value) for value in survivor_ids)))
    if not ids:
        raise ValueError("survivor_ids must be non-empty")
    missing = set(ids).difference(by_id)
    if missing:
        raise ValueError(f"unknown survivor worlds: {sorted(missing)}")

    selected = tuple(by_id[world_id] for world_id in ids)
    node_ids = selected[0].node_ids
    if any(world.node_ids != node_ids for world in selected):
        raise ValueError("all survivors must share node_ids and order")
    G = int(selected[0].occupied_mask)
    if any(int(world.occupied_mask) != G for world in selected):
        raise ValueError("completion margin requires a same-G survivor fiber")

    decisions = {release_expands_current(world, axis) for world in selected}
    full_outcomes = complete_same_g_release_outcomes(
        G, axis=axis, node_count=len(node_ids)
    )
    if len(decisions) != 1:
        return FiberDecisionMargin(
            axis=axis,
            survivor_ids=ids,
            current_decision=None,
            identified_in_declared_universe=False,
            completion_flip_margin=0,
            full_completion_outcomes=full_outcomes,
        )

    decision = next(iter(decisions))
    margins = tuple(
        single_state_completion_flip_margin(
            int(world.abiotic_mask),
            int(world.biotic_mask),
            int(world.movement_mask),
            axis=axis,
            node_count=len(node_ids),
        )
        for world in selected
    )
    finite = tuple(value for value in margins if value is not None)
    margin = min(finite) if finite else None
    return FiberDecisionMargin(
        axis=axis,
        survivor_ids=ids,
        current_decision=decision,
        identified_in_declared_universe=True,
        completion_flip_margin=margin,
        full_completion_outcomes=full_outcomes,
    )
