"""Finite target-sufficient quotient partitions for BAM survivor fibers.

This module is a mathematical organization layer over already frozen finite worlds.
It introduces no new ecological or observation model.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, Mapping, Sequence


@dataclass(frozen=True)
class FinitePartition:
    world_ids: tuple[str, ...]
    blocks: tuple[tuple[str, ...], ...]

    @property
    def block_count(self) -> int:
        return len(self.blocks)

    @property
    def world_count(self) -> int:
        return len(self.world_ids)

    @property
    def compression_factor(self) -> float:
        return self.world_count / self.block_count


def partition_from_values(
    world_ids: Sequence[str],
    value_by_world: Mapping[str, Hashable],
) -> FinitePartition:
    ids = tuple(sorted(set(str(value) for value in world_ids)))
    if not ids:
        raise ValueError("world_ids must be non-empty")
    missing = set(ids).difference(value_by_world)
    if missing:
        raise ValueError(f"value mapping missing worlds: {sorted(missing)}")

    groups: dict[Hashable, list[str]] = {}
    for world_id in ids:
        groups.setdefault(value_by_world[world_id], []).append(world_id)

    blocks = tuple(
        sorted(
            (tuple(sorted(group)) for group in groups.values()),
            key=lambda block: (block[0], len(block), block),
        )
    )
    flattened = tuple(sorted(world_id for block in blocks for world_id in block))
    if flattened != ids:
        raise RuntimeError("partition blocks do not cover exact world universe")
    return FinitePartition(world_ids=ids, blocks=blocks)


def _block_index(partition: FinitePartition) -> dict[str, int]:
    out: dict[str, int] = {}
    for i, block in enumerate(partition.blocks):
        for world_id in block:
            if world_id in out:
                raise RuntimeError("partition world occurs in multiple blocks")
            out[world_id] = i
    if set(out) != set(partition.world_ids):
        raise RuntimeError("partition index does not cover world universe")
    return out


def refines(finer: FinitePartition, coarser: FinitePartition) -> bool:
    """Whether every finer block is contained in one coarser block."""

    if finer.world_ids != coarser.world_ids:
        raise ValueError("partitions must share exact world universe")
    coarse_index = _block_index(coarser)
    for block in finer.blocks:
        labels = {coarse_index[world_id] for world_id in block}
        if len(labels) != 1:
            return False
    return True


def partition_relation(
    left: FinitePartition,
    right: FinitePartition,
    *,
    left_label: str = "left",
    right_label: str = "right",
) -> str:
    """Return equality, one-way refinement, or incomparability."""

    left_refines = refines(left, right)
    right_refines = refines(right, left)
    if left_refines and right_refines:
        return "equal"
    if left_refines:
        return f"{left_label}_refines"
    if right_refines:
        return f"{right_label}_refines"
    return "incomparable"


def singleton_parameter_partition(world_ids: Sequence[str]) -> FinitePartition:
    ids = tuple(sorted(set(str(value) for value in world_ids)))
    return partition_from_values(ids, {world_id: world_id for world_id in ids})


def joint_value_partition(
    world_ids: Sequence[str],
    mappings: Sequence[Mapping[str, Hashable]],
) -> FinitePartition:
    ids = tuple(sorted(set(str(value) for value in world_ids)))
    if not mappings:
        raise ValueError("mappings must be non-empty")
    for mapping in mappings:
        missing = set(ids).difference(mapping)
        if missing:
            raise ValueError(f"joint mapping missing worlds: {sorted(missing)}")
    values = {
        world_id: tuple(mapping[world_id] for mapping in mappings)
        for world_id in ids
    }
    return partition_from_values(ids, values)


def target_sufficient(
    representation: FinitePartition,
    target: FinitePartition,
) -> bool:
    """Whether representation identity always determines target identity."""

    return refines(representation, target)
