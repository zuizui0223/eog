#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from itertools import combinations
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.run_eog_original_idea_virtual_worlds_v2 import (
    AUTOCORR_LEVELS,
    BARRIER_LEVELS,
    NEIGHBOURHOODS,
    REPLICATES,
    _bfs_distances,
    _generate_base,
)
from benchmarks.run_eog_original_idea_directed_temporal_flow_v5 import (
    _candidate_worlds,
    _graphs,
    _outlet_corner,
    _truth_source,
    _truth_world_id,
)


PROTOCOL = ROOT / "validation/eog_original_idea_evidence_target_boundaries_v6/protocol_v6.json"
CHANNELS = ("T_temporal", "S_source", "B_barrier", "R_analyst")


def _sha256(payload):
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _all_subsets():
    rows = [()]
    for size in range(1, len(CHANNELS) + 1):
        rows.extend(combinations(CHANNELS, size))
    return tuple(rows)


def _subset_id(subset):
    return "+".join(subset) if subset else "baseline"


def _apply_evidence(
    baseline_survivors,
    subset,
    truth_source,
    truth_barrier,
    truth_depth,
):
    rows = []
    for world in baseline_survivors:
        keep = True
        if "T_temporal" in subset:
            keep = keep and all(
                node in world["dist"]
                and int(world["dist"][node]) <= int(depth)
                for node, depth in truth_depth.items()
                if node != truth_source
            )
        if "S_source" in subset:
            keep = keep and world["source"] == truth_source
        if "B_barrier" in subset:
            keep = keep and float(world["barrier_density"]) == float(truth_barrier)
        if "R_analyst" in subset:
            keep = keep and world["rule"] == "relative_edge_q70"
        if keep:
            rows.append(world)
    return tuple(rows)


def _summary(survivors, permissive, truth_reachable, truth_world_id):
    if not survivors:
        raise RuntimeError("truth-consistent evidence eliminated all candidate worlds")
    ids = {world["world_id"] for world in survivors}
    if truth_world_id not in ids:
        raise RuntimeError("truth world eliminated by truth-consistent evidence")

    reachability_classes = {
        tuple(sorted(world["reachable"]))
        for world in survivors
    }
    union_reachable = frozenset().union(
        *(world["reachable"] for world in survivors)
    )
    robust_unreachable = frozenset(permissive.difference(union_reachable))
    truth_unreachable = frozenset(permissive.difference(truth_reachable))
    false_exclusion = robust_unreachable.intersection(truth_reachable)

    return {
        "survivor_world_count": len(survivors),
        "surviving_source_count": len({world["source"] for world in survivors}),
        "reachability_class_count": len(reachability_classes),
        "robustly_unreachable_nodes": tuple(sorted(robust_unreachable)),
        "robustly_unreachable_count": len(robust_unreachable),
        "truth_unreachable_count": len(truth_unreachable),
        "false_robust_exclusion_count": len(false_exclusion),
        "truth_reachability_class_identified": all(
            world["reachable"] == truth_reachable
            for world in survivors
        ),
        "truth_world_identified": (
            len(survivors) == 1
            and survivors[0]["world_id"] == truth_world_id
        ),
    }


def _classify_single_channel(baseline, after):
    if after["survivor_world_count"] == baseline["survivor_world_count"]:
        return "redundant"

    before_robust = set(baseline["robustly_unreachable_nodes"])
    after_robust = set(after["robustly_unreachable_nodes"])
    if not before_robust.issubset(after_robust):
        raise RuntimeError("truth-consistent evidence weakened robust impossibility")

    if after_robust > before_robust:
        return "envelope_changing"
    if after["reachability_class_count"] < baseline["reachability_class_count"]:
        return "target_refining"
    if after["reachability_class_count"] == baseline["reachability_class_count"]:
        return "identity_only"
    raise RuntimeError("reachability class count increased after evidence")


def _minimum_subset(subset_rows, field):
    candidates = [
        row
        for row in subset_rows
        if row["summary"][field]
    ]
    if not candidates:
        return None
    candidates.sort(
        key=lambda row: (
            len(row["subset"]),
            tuple(CHANNELS.index(channel) for channel in row["subset"]),
        )
    )
    return candidates[0]


def _evaluate_row(replicate, autocorr, neighbourhood, barrier_density):
    base = _generate_base(replicate, autocorr, neighbourhood)
    outlet = _outlet_corner(replicate, autocorr, neighbourhood)
    truth_source = _truth_source(base, outlet)
    _, truth_graph = _graphs(
        base,
        barrier_density,
        "relative_edge_q70",
        outlet,
    )
    truth_depth = _bfs_distances(truth_graph, truth_source)
    truth_reachable = frozenset(truth_depth)
    positive_pool = tuple(
        sorted(node for node in truth_reachable if node != truth_source)
    )

    row = {
        "replicate": replicate,
        "environmental_autocorrelation": autocorr,
        "neighbourhood": neighbourhood,
        "truth_barrier_density": barrier_density,
        "truth_source": f"r{truth_source[0]}c{truth_source[1]}",
        "truth_positive_pool_size": len(positive_pool),
        "eligible": len(positive_pool) >= 4,
    }
    if not row["eligible"]:
        return {**row, "subsets": {}, "single_channels": {}}

    worlds = _candidate_worlds(base, outlet, "directed")
    truth_id = _truth_world_id(truth_source, barrier_density)
    positive_set = frozenset(positive_pool)
    baseline_survivors = tuple(
        world
        for world in worlds
        if positive_set.issubset(world["reachable"])
    )
    baseline = _summary(
        baseline_survivors,
        base["permissive"],
        truth_reachable,
        truth_id,
    )

    subset_rows = []
    by_id = {}
    for subset in _all_subsets():
        survivors = _apply_evidence(
            baseline_survivors,
            subset,
            truth_source,
            barrier_density,
            truth_depth,
        )
        summary = _summary(
            survivors,
            base["permissive"],
            truth_reachable,
            truth_id,
        )
        record = {
            "subset": tuple(subset),
            "subset_id": _subset_id(subset),
            "summary": summary,
        }
        subset_rows.append(record)
        by_id[record["subset_id"]] = record

    direct_world = by_id["S_source+B_barrier+R_analyst"]["summary"]
    if not direct_world["truth_world_identified"]:
        raise RuntimeError(
            "direct source+barrier+analyst evidence did not identify truth world"
        )

    target_min = _minimum_subset(
        subset_rows,
        "truth_reachability_class_identified",
    )
    world_min = _minimum_subset(
        subset_rows,
        "truth_world_identified",
    )
    if target_min is None or world_min is None:
        raise RuntimeError("frozen evidence library failed finite target/world identification")
    if len(target_min["subset"]) > len(world_min["subset"]):
        raise RuntimeError("target evidence burden exceeded world burden")

    single_channels = {}
    for channel in CHANNELS:
        summary = by_id[channel]["summary"]
        single_channels[channel] = {
            "classification": _classify_single_channel(baseline, summary),
            "world_contraction": (
                baseline["survivor_world_count"]
                - summary["survivor_world_count"]
            ),
            "reachability_class_contraction": (
                baseline["reachability_class_count"]
                - summary["reachability_class_count"]
            ),
            "robust_impossibility_gain": (
                summary["robustly_unreachable_count"]
                - baseline["robustly_unreachable_count"]
            ),
            "survivor_world_count": summary["survivor_world_count"],
            "reachability_class_count": summary["reachability_class_count"],
            "robustly_unreachable_count": summary["robustly_unreachable_count"],
        }

    return {
        **row,
        "baseline": baseline,
        "single_channels": single_channels,
        "minimum_reachability_target_burden": len(target_min["subset"]),
        "minimum_reachability_target_subset": list(target_min["subset"]),
        "minimum_full_world_burden": len(world_min["subset"]),
        "minimum_full_world_subset": list(world_min["subset"]),
        "strict_target_saving": (
            len(target_min["subset"]) < len(world_min["subset"])
        ),
        "subsets": {
            record["subset_id"]: record["summary"]
            for record in subset_rows
        },
    }


def _mean(values):
    values = [float(value) for value in values]
    return None if not values else float(np.mean(values))


def _median(values):
    values = [float(value) for value in values]
    return None if not values else float(np.median(values))


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != (
        "frozen_before_evidence_boundary_benchmark_implementation_and_scoring"
    ):
        raise RuntimeError("v6 protocol is not frozen")

    rows = []
    for autocorr in AUTOCORR_LEVELS:
        for neighbourhood in NEIGHBOURHOODS:
            for replicate in range(REPLICATES):
                for barrier_density in BARRIER_LEVELS:
                    rows.append(
                        _evaluate_row(
                            replicate,
                            autocorr,
                            neighbourhood,
                            barrier_density,
                        )
                    )
    if len(rows) != 384:
        raise RuntimeError(f"expected 384 rows, got {len(rows)}")

    eligible = [row for row in rows if row["eligible"]]
    if not eligible:
        raise RuntimeError("no v6 eligible rows")

    target_world_burden_violations = sum(
        row["minimum_reachability_target_burden"]
        > row["minimum_full_world_burden"]
        for row in eligible
    )
    strict_saving_rows = sum(row["strict_target_saving"] for row in eligible)

    category_counts = {
        channel: Counter(
            row["single_channels"][channel]["classification"]
            for row in eligible
        )
        for channel in CHANNELS
    }
    global_categories = {
        category
        for counter in category_counts.values()
        for category, count in counter.items()
        if count > 0
    }

    temporal_identity_without_envelope = sum(
        row["single_channels"]["T_temporal"]["world_contraction"] > 0
        and row["single_channels"]["T_temporal"]["robust_impossibility_gain"] == 0
        for row in eligible
    )
    source_envelope_change = sum(
        row["single_channels"]["S_source"]["robust_impossibility_gain"] > 0
        for row in eligible
    )
    barrier_envelope_change = sum(
        row["single_channels"]["B_barrier"]["robust_impossibility_gain"] > 0
        for row in eligible
    )
    analyst_envelope_change = sum(
        row["single_channels"]["R_analyst"]["robust_impossibility_gain"] > 0
        for row in eligible
    )

    direct_world_failures = sum(
        not row["subsets"]["S_source+B_barrier+R_analyst"][
            "truth_world_identified"
        ]
        for row in eligible
    )

    baseline_target_identified = sum(
        row["baseline"]["truth_reachability_class_identified"]
        for row in eligible
    )

    target_burdens = [
        row["minimum_reachability_target_burden"] for row in eligible
    ]
    world_burdens = [
        row["minimum_full_world_burden"] for row in eligible
    ]

    verdicts = {
        "E1_target_burden_never_exceeds_world_burden": (
            "SUPPORTED"
            if target_world_burden_violations == 0
            else "REFUTED"
        ),
        "E2_strict_target_specific_saving_exists": (
            "SUPPORTED" if strict_saving_rows > 0 else "REFUTED"
        ),
        "E3_temporal_identity_without_envelope_change_exists": (
            "SUPPORTED"
            if temporal_identity_without_envelope > 0
            else "REFUTED"
        ),
        "E4_source_evidence_can_cross_envelope_boundary": (
            "SUPPORTED" if source_envelope_change > 0 else "REFUTED"
        ),
        "E5_barrier_or_analyst_evidence_can_cross_envelope_boundary": (
            "SUPPORTED"
            if barrier_envelope_change > 0 or analyst_envelope_change > 0
            else "REFUTED"
        ),
        "E6_direct_world_coordinates_identify_the_world": (
            "SUPPORTED" if direct_world_failures == 0 else "REFUTED"
        ),
        "E7_evidence_channels_are_target_heterogeneous": (
            "SUPPORTED" if len(global_categories) >= 3 else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_evidence_target_boundaries.result.v6",
        "row_count": len(rows),
        "eligible_row_count": len(eligible),
        "non_estimable_row_count": len(rows) - len(eligible),
        "predeclared_verdicts": verdicts,
        "baseline": {
            "reachability_target_already_identified_count": (
                baseline_target_identified
            ),
            "reachability_target_already_identified_fraction": (
                baseline_target_identified / len(eligible)
            ),
        },
        "burdens": {
            "target_burden_distribution": dict(
                sorted(Counter(target_burdens).items())
            ),
            "world_burden_distribution": dict(
                sorted(Counter(world_burdens).items())
            ),
            "median_target_burden": _median(target_burdens),
            "median_world_burden": _median(world_burdens),
            "strict_target_saving_rows": strict_saving_rows,
            "target_gt_world_violation_count": (
                target_world_burden_violations
            ),
        },
        "single_channel_classification_counts": {
            channel: dict(sorted(counter.items()))
            for channel, counter in category_counts.items()
        },
        "single_channel_target_effects": {
            "temporal_world_contraction_without_robust_gain_rows": (
                temporal_identity_without_envelope
            ),
            "source_envelope_change_rows": source_envelope_change,
            "barrier_envelope_change_rows": barrier_envelope_change,
            "analyst_envelope_change_rows": analyst_envelope_change,
            "global_categories_observed": sorted(global_categories),
        },
        "direct_world_coordinate_failure_count": direct_world_failures,
        "rows": rows,
    }
    result["fingerprint"] = _sha256(result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "row_count": result["row_count"],
                "eligible_row_count": result["eligible_row_count"],
                "predeclared_verdicts": result["predeclared_verdicts"],
                "baseline": result["baseline"],
                "burdens": result["burdens"],
                "single_channel_classification_counts": result[
                    "single_channel_classification_counts"
                ],
                "single_channel_target_effects": result[
                    "single_channel_target_effects"
                ],
                "fingerprint": result["fingerprint"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
