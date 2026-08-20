#!/usr/bin/env python3
"""Assynt 69-patch response-blind Gate 1 structural audit.

This runner is deliberately incapable of reading the ecological response table.  It
uses only the separately released 69-patch British National Grid coordinate file,
then applies the existing generic structural-scale ladder and the generic prospective
estimability screen using published aggregate counts.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from eog.v2.prospective_estimability import (
    AggregateCountInterval,
    AggregateEstimabilityEvidence,
    ProspectiveEstimabilityDeclaration,
    evaluate_prospective_estimability,
)
from eog.v2.world_scale_ladder import (
    StructuralScaleLadderDeclaration,
    build_structural_scale_ladder,
)

EXPECTED_GEOMETRY_MD5 = "9174c10342b9d0d1d94397fa6ce5d4be"
EXPECTED_GEOMETRY_SIZE = 1397
EXPECTED_NODE_COUNT = 69


def digest(path: Path, algorithm: str) -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def parse_geometry(path: Path) -> tuple[tuple[str, ...], np.ndarray]:
    rows: list[tuple[str, float, float]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(
            (line for line in handle if line.strip() and not line.startswith("#")),
            delimiter="\t",
        )
        header = next(reader)
        if header != ["ID", "X_coord", "Y_coord"]:
            raise ValueError(f"unexpected geometry header: {header!r}")
        for row in reader:
            if len(row) != 3:
                raise ValueError(f"unexpected geometry row: {row!r}")
            rows.append((str(row[0]).strip(), float(row[1]), float(row[2])))

    if len(rows) != EXPECTED_NODE_COUNT:
        raise ValueError(f"expected {EXPECTED_NODE_COUNT} nodes, observed {len(rows)}")
    ids = tuple(row[0] for row in rows)
    if ids != tuple(str(i) for i in range(1, EXPECTED_NODE_COUNT + 1)):
        raise ValueError("geometry IDs are not the complete canonical 1..69 registry")

    # British National Grid coordinates are metres; divide by 1000 for km distances,
    # as documented in the released geometry file itself.
    xy_km = np.asarray([(row[1] / 1000.0, row[2] / 1000.0) for row in rows], dtype=float)
    delta = xy_km[:, None, :] - xy_km[None, :, :]
    distance_km = np.sqrt(np.sum(delta * delta, axis=2))
    return ids, distance_km


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geometry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    if args.geometry.stat().st_size != EXPECTED_GEOMETRY_SIZE:
        raise ValueError("geometry size differs from frozen Figshare metadata")
    md5 = digest(args.geometry, "md5")
    if md5 != EXPECTED_GEOMETRY_MD5:
        raise ValueError("geometry MD5 differs from frozen Figshare metadata")

    node_ids, distance_km = parse_geometry(args.geometry)
    declaration = StructuralScaleLadderDeclaration(
        axis_id="assynt69_geo",
        target_largest_component_fractions=(0.25, 0.50, 0.75, 0.90),
    )
    ladder = build_structural_scale_ladder(node_ids, distance_km, declaration)

    distinct_positive_thresholds = sorted({
        round(level.distance_threshold, 12)
        for level in ladder.levels
        if level.distance_threshold > 0.0
    })
    broad = ladder.levels[-1]
    structural_pass = (
        len(distinct_positive_thresholds) >= 3
        and broad.achieved_largest_component_fraction >= 0.90
        and broad.isolated_node_fraction <= 0.05
    )

    # Published pre-response evidence gives at least five observed colonisation events
    # in every annual transition.  With three transitions in calibration and three in
    # heldout, event lower bounds are therefore 15 in each block.  The paper does not
    # provide a response-blind lower bound for the corresponding remained-empty rows,
    # so those quantities stay unresolved rather than being reconstructed from the
    # response file.
    prospective = evaluate_prospective_estimability(
        ProspectiveEstimabilityDeclaration(
            calibration_events=10,
            calibration_non_events=40,
            heldout_events=10,
            heldout_non_events=40,
            heldout_outer_units_with_both_classes=1,
        ),
        AggregateEstimabilityEvidence(
            source_label="Sutherland et al. 2012 published aggregate transition counts",
            endpoint_definition_matches=True,
            response_rows_opened=False,
            intervals={
                "calibration_events": AggregateCountInterval(lower=15),
                "heldout_events": AggregateCountInterval(lower=15),
                # Non-event and both-class-unit lower bounds are intentionally omitted.
            },
            note=(
                "1999-2005; colonisation defined as empty-to-occupied; published annual "
                "colonisation range 5-27. Published text does not establish blockwise "
                "remained-empty lower bounds required by the frozen 10/40 gate."
            ),
        ),
    )

    result = {
        "status": (
            "stop_uncertain_pre_response_non_event_bounds"
            if prospective.status != "plausibly_eligible_pre_response"
            else "gate1_structural_pass_pending_next_freeze"
        ),
        "candidate": "Assynt water vole 69-patch 1999-2005 system",
        "response_rows_opened": False,
        "response_file_downloaded": False,
        "geometry": {
            "node_count": len(node_ids),
            "md5": md5,
            "sha256": digest(args.geometry, "sha256"),
            "size_bytes": args.geometry.stat().st_size,
            "crs_semantics": "British National Grid coordinates; Euclidean km after /1000",
        },
        "structural_gate": {
            "pass": structural_pass,
            "distinct_positive_threshold_count": len(distinct_positive_thresholds),
            "distinct_positive_thresholds_km": distinct_positive_thresholds,
            "levels": [
                {
                    "level_id": level.level_id,
                    "target_lcc": level.target_largest_component_fraction,
                    "distance_threshold_km": level.distance_threshold,
                    "achieved_lcc": level.achieved_largest_component_fraction,
                    "component_count": level.weak_component_count,
                    "isolated_fraction": level.isolated_node_fraction,
                    "directed_edge_count": level.directed_edge_count,
                    "fingerprint": level.fingerprint,
                }
                for level in ladder.levels
            ],
            "ladder_fingerprint": ladder.fingerprint,
        },
        "prospective_estimability": {
            "status": prospective.status,
            "failing_keys": list(prospective.failing_keys),
            "unresolved_keys": list(prospective.unresolved_keys),
            "fingerprint": prospective.fingerprint,
        },
        "decision": (
            "STOP before ecological response access: event lower bounds pass, but the "
            "frozen prospective gate cannot certify calibration/heldout non-event counts "
            "or a heldout unit with both classes from published aggregate evidence alone."
        ),
    }
    if not structural_pass:
        result["status"] = "gate1_stop_structural_adequacy_failed"
        result["decision"] = "STOP before response access: structural adequacy failed."

    out = args.output / "assynt69_gate1_result.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))

    # Gate 1 must be scientifically adequate; prospective uncertainty is an expected
    # candidate STOP, not a CI failure.
    if not structural_pass:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
