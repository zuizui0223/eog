"""CLI for audited held-out support-topology comparisons."""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import json
from pathlib import Path

import numpy as np

from .support_topology_comparison import (
    HeldoutCandidate,
    SupportTopologyComparisonConfig,
    compare_support_topology_heldout,
)


def _load_anchors(path: Path) -> dict[str, tuple[int, int]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    anchors: dict[str, tuple[int, int]] = {}
    for row in rows:
        anchor_id = row["anchor_id"]
        if anchor_id in anchors:
            raise ValueError(f"duplicate anchor_id: {anchor_id}")
        anchors[anchor_id] = (int(row["row"]), int(row["column"]))
    return anchors


def _load_candidates(path: Path) -> tuple[HeldoutCandidate, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return tuple(
        HeldoutCandidate(
            candidate_id=row["candidate_id"],
            row=int(row["row"]),
            column=int(row["column"]),
            detected=int(row["detected"]),
        )
        for row in rows
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--support", type=Path, required=True)
    parser.add_argument("--mask", type=Path, required=True)
    parser.add_argument("--anchors", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--thresholds", type=float, nargs="+", required=True)
    parser.add_argument("--single-threshold", type=float, required=True)
    parser.add_argument("--minimum-persistence-steps", type=int, default=2)
    parser.add_argument("--neighbourhood", type=int, default=4)
    parser.add_argument("--support-weight", type=float, default=0.5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = compare_support_topology_heldout(
        np.load(args.support, allow_pickle=False),
        np.load(args.mask, allow_pickle=False),
        _load_anchors(args.anchors),
        _load_candidates(args.candidates),
        SupportTopologyComparisonConfig(
            thresholds=tuple(args.thresholds),
            single_threshold=args.single_threshold,
            minimum_persistence_steps=args.minimum_persistence_steps,
            neighbourhood=args.neighbourhood,
            support_weight=args.support_weight,
        ),
    )
    payload = {
        "metrics": {key: asdict(value) for key, value in result.metrics.items()},
        "candidates": list(result.candidates),
        "config": asdict(result.config),
        "fingerprint": result.fingerprint,
        "claim_limit": result.claim_limit,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
