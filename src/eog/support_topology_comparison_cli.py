"""CLI for audited held-out support-topology comparisons."""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from .support_topology_comparison import (
    HeldoutCandidate,
    SupportTopologyComparisonConfig,
    compare_support_topology_heldout,
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _load_declaration(path: Path) -> tuple[dict[str, Any], SupportTopologyComparisonConfig]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("declaration must be a JSON object")
    analysis_id = str(payload.get("analysis_id", "")).strip()
    if not analysis_id:
        raise ValueError("declaration analysis_id must be non-empty")
    if payload.get("frozen_before_outcomes") is not True:
        raise ValueError("declaration must assert frozen_before_outcomes=true")
    try:
        config = SupportTopologyComparisonConfig(
            thresholds=tuple(float(value) for value in payload["thresholds"]),
            single_threshold=float(payload["single_threshold"]),
            minimum_persistence_steps=int(payload.get("minimum_persistence_steps", 2)),
            neighbourhood=int(payload.get("neighbourhood", 4)),
            support_weight=float(payload.get("support_weight", 0.5)),
        )
    except KeyError as error:
        raise ValueError(f"declaration missing required field: {error.args[0]}") from error
    config.validate()
    return payload, config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--support", type=Path, required=True)
    parser.add_argument("--mask", type=Path, required=True)
    parser.add_argument("--anchors", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--declaration", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    declaration, config = _load_declaration(args.declaration)
    result = compare_support_topology_heldout(
        np.load(args.support, allow_pickle=False),
        np.load(args.mask, allow_pickle=False),
        _load_anchors(args.anchors),
        _load_candidates(args.candidates),
        config,
    )
    input_paths = {
        "support": args.support,
        "mask": args.mask,
        "anchors": args.anchors,
        "candidates": args.candidates,
        "declaration": args.declaration,
    }
    manifest = {
        "analysis_id": declaration["analysis_id"],
        "frozen_before_outcomes": True,
        "input_sha256": {name: _sha256_file(path) for name, path in input_paths.items()},
        "declaration": declaration,
        "comparison_fingerprint": result.fingerprint,
        "audit_note": (
            "The frozen-before-outcomes field is an analyst declaration, not independent proof. "
            "Protocol timestamps and archives must establish temporal precedence."
        ),
    }
    bundle_payload = {
        "manifest": manifest,
        "metrics": {key: asdict(value) for key, value in result.metrics.items()},
        "candidates": list(result.candidates),
        "config": asdict(result.config),
        "claim_limit": result.claim_limit,
    }
    bundle_fingerprint = hashlib.sha256(
        json.dumps(bundle_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    payload = {**bundle_payload, "fingerprint": bundle_fingerprint}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
