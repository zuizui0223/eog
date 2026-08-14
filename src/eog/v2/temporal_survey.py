"""Positive temporal survey discrimination for finite EOG worlds.

This module ranks candidate ``(node, time)`` positive observations by how a positive
detection would partition the temporal worlds that remain compatible with the current
positive evidence.  It deliberately does not score non-detections, call the result
expected information gain, or introduce a detection probability model.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal, Sequence

from .temporal_reachability import TemporalWorld, build_temporal_flow_set
from .temporal_reconstruction import TemporalWorldReconstruction


TemporalCandidateStatus = Literal[
    "discriminating",
    "non_discriminating",
    "unsupported_by_compatible_worlds",
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
class _PositiveTemporalCandidate:
    node_id: str
    time_label: str
    reachable_world_ids: tuple[str, ...]
    unreachable_world_ids: tuple[str, ...]
    positive_elimination_fraction: float
    split_balance: float
    status: TemporalCandidateStatus


@dataclass(frozen=True)
class PositiveTemporalSurveyRanking:
    """Candidate positive observations ranked by compatible-world discrimination."""

    rows: tuple[_PositiveTemporalCandidate, ...]
    compatible_world_ids: tuple[str, ...]
    reconstruction_fingerprint: str
    fingerprint: str


def _canonical_candidates(
    node_ids: tuple[str, ...],
    time_labels: tuple[str, ...],
    candidates: Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    declared = tuple((str(node).strip(), str(time).strip()) for node, time in candidates)
    if not declared:
        raise ValueError("at least one positive temporal survey candidate is required")
    if any(not node or not time for node, time in declared):
        raise ValueError("candidate node/time labels must be non-empty")
    if len(set(declared)) != len(declared):
        raise ValueError("positive temporal survey candidates must be unique")

    node_index = {node_id: i for i, node_id in enumerate(node_ids)}
    time_index = {time_label: i for i, time_label in enumerate(time_labels)}
    missing_nodes = sorted({node for node, _ in declared if node not in node_index})
    if missing_nodes:
        raise ValueError(f"candidates contain nodes outside the temporal world universe: {missing_nodes}")
    missing_times = sorted({time for _, time in declared if time not in time_index})
    if missing_times:
        raise ValueError(f"candidates contain undeclared time labels: {missing_times}")
    return tuple(sorted(declared, key=lambda row: (time_index[row[1]], node_index[row[0]])))


def rank_positive_temporal_occurrence_candidates(
    reconstruction: TemporalWorldReconstruction,
    worlds: Sequence[TemporalWorld],
    candidates: Sequence[tuple[str, str]],
) -> PositiveTemporalSurveyRanking:
    """Rank candidate positive observations without assigning value to non-detection.

    A candidate is ``discriminating`` when some compatible temporal worlds have reached
    the node by the candidate time and others have not.  It is
    ``non_discriminating`` when every compatible world has reached it.  A candidate
    unsupported by every compatible world is reported separately because observing it
    would challenge the declared compatible-world universe rather than choose among its
    members.
    """

    if not reconstruction.compatible_world_ids:
        raise ValueError("temporal survey discrimination requires at least one compatible world")

    flow_set = build_temporal_flow_set(worlds, support_tolerance=reconstruction.support_tolerance)
    if flow_set.world_fingerprints != reconstruction.world_fingerprints:
        raise ValueError("survey ranking must use the same frozen temporal world universe")

    canonical = _canonical_candidates(flow_set.node_ids, flow_set.time_labels, candidates)
    overlap = set(canonical).intersection(reconstruction.observations)
    if overlap:
        raise ValueError(f"candidates already contain observed positive occurrences: {sorted(overlap)}")

    node_index = {node_id: i for i, node_id in enumerate(flow_set.node_ids)}
    time_index = {time_label: i for i, time_label in enumerate(flow_set.time_labels)}
    reached_by_world = {
        world_id: reached
        for world_id, reached in zip(flow_set.world_ids, flow_set.reached_by_world, strict=True)
    }

    total = len(reconstruction.compatible_world_ids)
    rows: list[_PositiveTemporalCandidate] = []
    for node_id, time_label in canonical:
        node = node_index[node_id]
        time = time_index[time_label]
        reachable = tuple(
            world_id
            for world_id in reconstruction.compatible_world_ids
            if bool(reached_by_world[world_id][time, node])
        )
        unreachable = tuple(
            world_id
            for world_id in reconstruction.compatible_world_ids
            if world_id not in set(reachable)
        )
        if not reachable:
            status: TemporalCandidateStatus = "unsupported_by_compatible_worlds"
        elif not unreachable:
            status = "non_discriminating"
        else:
            status = "discriminating"
        rows.append(
            _PositiveTemporalCandidate(
                node_id=node_id,
                time_label=time_label,
                reachable_world_ids=reachable,
                unreachable_world_ids=unreachable,
                positive_elimination_fraction=float(len(unreachable) / total),
                split_balance=float(min(len(reachable), len(unreachable)) / total),
                status=status,
            )
        )

    priority = {
        "discriminating": 0,
        "unsupported_by_compatible_worlds": 1,
        "non_discriminating": 2,
    }
    rows.sort(
        key=lambda row: (
            priority[row.status],
            -row.positive_elimination_fraction,
            -row.split_balance,
            time_index[row.time_label],
            node_index[row.node_id],
        )
    )
    payload = {
        "reconstruction_fingerprint": reconstruction.fingerprint,
        "rows": [
            {
                "node_id": row.node_id,
                "time_label": row.time_label,
                "reachable_world_ids": list(row.reachable_world_ids),
                "unreachable_world_ids": list(row.unreachable_world_ids),
                "positive_elimination_fraction": row.positive_elimination_fraction,
                "split_balance": row.split_balance,
                "status": row.status,
            }
            for row in rows
        ],
    }
    return PositiveTemporalSurveyRanking(
        rows=tuple(rows),
        compatible_world_ids=reconstruction.compatible_world_ids,
        reconstruction_fingerprint=reconstruction.fingerprint,
        fingerprint=_canonical_sha256(payload),
    )
