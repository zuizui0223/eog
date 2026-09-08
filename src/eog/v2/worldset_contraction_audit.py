"""Auditable contraction/saturation summaries for finite EOG world sets.

The audit separates epistemic contraction from support geometry.  A prediction-facing
support block may vary even when the compatible world set never contracts; this module
makes that distinction explicit instead of inferring contraction from support features.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence



def _sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class WorldSetContractionAudit:
    declared_world_count: int
    context_count: int
    surviving_world_counts: tuple[int, ...]
    contraction_event_count: int
    total_worlds_eliminated: int
    ever_contracted: bool
    fully_saturated_context_count: int
    fully_saturated_context_fraction: float
    final_surviving_world_fraction: float
    terminal_universe_falsified: bool
    fingerprint: str


def audit_worldset_contraction(
    declared_world_count: int,
    surviving_world_counts: Sequence[int],
) -> WorldSetContractionAudit:
    """Summarize monotone contraction across an ordered sequence of contexts.

    Counts are the exact compatible/surviving world-set sizes *before or after* evidence
    updates according to one declared convention; callers must use the same convention
    across the sequence.  Expansion is rejected because eliminated frozen Layer-A worlds
    are not allowed to return.
    """

    declared = int(declared_world_count)
    if declared <= 0:
        raise ValueError("declared_world_count must be positive")
    counts = tuple(int(value) for value in surviving_world_counts)
    if not counts:
        raise ValueError("surviving_world_counts must not be empty")
    if any(value < 0 or value > declared for value in counts):
        raise ValueError("surviving world counts must lie in [0, declared_world_count]")
    if any(right > left for left, right in zip(counts, counts[1:])):
        raise ValueError("surviving world set must contract monotonically; eliminated worlds cannot return")

    contraction_events = sum(right < left for left, right in zip(counts, counts[1:]))
    saturated = sum(value == declared for value in counts)
    total_eliminated = declared - counts[-1]
    terminal_falsified = counts[-1] == 0
    payload = {
        "declared_world_count": declared,
        "context_count": len(counts),
        "surviving_world_counts": list(counts),
        "contraction_event_count": contraction_events,
        "total_worlds_eliminated": total_eliminated,
        "ever_contracted": any(value < declared for value in counts),
        "fully_saturated_context_count": saturated,
        "fully_saturated_context_fraction": saturated / len(counts),
        "final_surviving_world_fraction": counts[-1] / declared,
        "terminal_universe_falsified": terminal_falsified,
    }
    return WorldSetContractionAudit(
        declared_world_count=declared,
        context_count=len(counts),
        surviving_world_counts=counts,
        contraction_event_count=contraction_events,
        total_worlds_eliminated=total_eliminated,
        ever_contracted=bool(payload["ever_contracted"]),
        fully_saturated_context_count=saturated,
        fully_saturated_context_fraction=float(payload["fully_saturated_context_fraction"]),
        final_surviving_world_fraction=float(payload["final_surviving_world_fraction"]),
        terminal_universe_falsified=terminal_falsified,
        fingerprint=_sha256(payload),
    )
