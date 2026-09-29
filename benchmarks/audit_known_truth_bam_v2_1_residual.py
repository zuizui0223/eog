#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import statistics

from eog.v2.known_truth_bam import (
    compatible_positive_only,
    compatible_with_perfect_negatives,
    compatible_with_temporal_arrivals,
)
from eog.v2.known_truth_bam_v2_1 import build_v21_system


def _pattern(a: bool, b: bool, m: bool) -> str:
    text = "".join(axis for axis, flag in (("A", a), ("B", b), ("M", m)) if flag)
    return text or "none"


def _row_for_level(system, truth, compatible_ids, level):
    axes_by = system.axes_by_world
    rows = [axes_by[world_id] for world_id in compatible_ids]
    A = {row.abiotic_label for row in rows}
    B = {row.biotic_mode for row in rows}
    D = {row.step_radius for row in rows}
    P = {row.barrier_permeable for row in rows}
    H = {row.horizon for row in rows}
    M = {(row.step_radius, row.barrier_permeable, row.horizon) for row in rows}
    a_unresolved = len(A) > 1
    b_unresolved = len(B) > 1
    m_unresolved = len(M) > 1
    return {
        "truth_world_id": truth.world_id,
        "evidence_level": level,
        "compatible_world_count": len(compatible_ids),
        "distinct_A_count": len(A),
        "distinct_B_count": len(B),
        "distinct_M_distance_count": len(D),
        "distinct_M_barrier_count": len(P),
        "distinct_M_horizon_count": len(H),
        "distinct_M_joint_count": len(M),
        "A_unresolved": a_unresolved,
        "B_unresolved": b_unresolved,
        "M_unresolved": m_unresolved,
        "residual_axis_pattern": _pattern(a_unresolved, b_unresolved, m_unresolved),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "validation/known_truth_bam_v2_1/"
            "residual_ambiguity_audit_result_v2_1.json"
        ),
    )
    args = parser.parse_args()

    system = build_v21_system()
    rows = []
    for truth in system.worlds:
        positives = truth.occupied_ids
        if len(positives) < 2 or "r1c0" not in positives:
            continue

        positive = compatible_positive_only(system.worlds, positives)
        negatives = tuple(
            node_id for node_id in system.landscape.node_ids if node_id not in set(positives)
        )
        with_neg = compatible_with_perfect_negatives(
            system.worlds,
            positives,
            negatives,
        )
        idx = {node_id: i for i, node_id in enumerate(truth.node_ids)}
        arrivals = {
            node_id: int(truth.first_arrival_steps[idx[node_id]])
            for node_id in positives
            if truth.first_arrival_steps[idx[node_id]] is not None
        }
        with_time = compatible_with_temporal_arrivals(
            system.worlds,
            positives,
            negatives,
            arrivals,
        )

        rows.append(_row_for_level(
            system, truth, positive.compatible_world_ids, "positive_only"
        ))
        rows.append(_row_for_level(
            system, truth, with_neg.compatible_world_ids, "positive_plus_perfect_negative"
        ))
        rows.append(_row_for_level(
            system, truth, with_time.compatible_world_ids, "positive_negative_temporal"
        ))

    levels = (
        "positive_only",
        "positive_plus_perfect_negative",
        "positive_negative_temporal",
    )
    aggregate = {}
    for level in levels:
        subset = [row for row in rows if row["evidence_level"] == level]
        n = len(subset)
        pattern_counts = Counter(row["residual_axis_pattern"] for row in subset)
        aggregate[level] = {
            "truth_count": n,
            "fraction_A_unresolved": 0.0 if n == 0 else sum(row["A_unresolved"] for row in subset) / n,
            "fraction_B_unresolved": 0.0 if n == 0 else sum(row["B_unresolved"] for row in subset) / n,
            "fraction_M_unresolved": 0.0 if n == 0 else sum(row["M_unresolved"] for row in subset) / n,
            "median_compatible_world_count": (
                None if n == 0 else statistics.median(
                    row["compatible_world_count"] for row in subset
                )
            ),
            "residual_axis_pattern_counts": dict(sorted(pattern_counts.items())),
        }

    result = {
        "schema": "eog.known_truth_bam_orthogonal.residual_ambiguity_result.v2_1",
        "primary_result_fingerprint": "dbfd0c09b492c1e53914ddfdfe392c765df6da98a43e105245767c24c75ad9b3",
        "system_fingerprint": system.fingerprint,
        "aggregate": aggregate,
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(aggregate, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
