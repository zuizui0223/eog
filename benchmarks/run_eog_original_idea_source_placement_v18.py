#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
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
    _node_id,
)
from benchmarks.run_eog_original_idea_directed_temporal_flow_v5 import (
    _graphs,
    _outlet_corner,
    _potential,
    _truth_source,
)


PROTOCOL = ROOT / "validation/eog_original_idea_source_placement_v18/protocol_v18.json"
RULE = "relative_edge_q70"
SOURCE_COUNTS = (1, 2, 3)
DESIGNS = ("clustered", "dispersed")


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


def _euclidean(a, b):
    return float(math.hypot(a[0] - b[0], a[1] - b[1]))


def _candidate_sources(base, outlet, anchor):
    permissive = tuple(sorted(base["permissive"]))
    values = np.asarray([_potential(node, outlet) for node in permissive], dtype=float)
    median = float(np.median(values))
    candidates = tuple(
        sorted(
            node
            for node in permissive
            if node != anchor and _potential(node, outlet) >= median - 1e-15
        )
    )
    return candidates, median


def _clustered_order(candidates, anchor):
    return tuple(
        sorted(
            candidates,
            key=lambda node: (_euclidean(node, anchor), _node_id(node)),
        )
    )


def _dispersed_order(candidates, anchor):
    remaining = set(candidates)
    selected = [anchor]
    out = []
    while remaining:
        def score(node):
            return min(_euclidean(node, chosen) for chosen in selected)

        chosen = sorted(
            remaining,
            key=lambda node: (-score(node), _node_id(node)),
        )[0]
        out.append(chosen)
        selected.append(chosen)
        remaining.remove(chosen)
    return tuple(out)


def _source_sets(candidates, anchor):
    if len(candidates) < 2:
        return {}
    orders = {
        "clustered": _clustered_order(candidates, anchor),
        "dispersed": _dispersed_order(candidates, anchor),
    }
    rows = {}
    for design, order in orders.items():
        rows[design] = {
            1: (anchor,),
            2: (anchor, order[0]),
            3: (anchor, order[0], order[1]),
        }
    return rows


def _metrics(graph, permissive, sources):
    reach_by_source = {
        source: frozenset(_bfs_distances(graph, source))
        for source in sources
    }
    union = frozenset().union(*reach_by_source.values())
    if not union:
        raise RuntimeError("source set has empty reachable union")

    multiplicity = {
        node: sum(node in reach for reach in reach_by_source.values())
        for node in union
    }
    multi_count = sum(value >= 2 for value in multiplicity.values())
    exclusive_count = sum(value == 1 for value in multiplicity.values())

    if len(sources) == 1:
        worst_retention = 0.0
    else:
        retained = []
        for removed in sources:
            remaining = tuple(source for source in sources if source != removed)
            remaining_union = frozenset().union(
                *(reach_by_source[source] for source in remaining)
            )
            retained.append(len(remaining_union) / len(union))
        worst_retention = float(min(retained))

    return {
        "source_ids": [_node_id(source) for source in sources],
        "union_reachable_node_count": len(union),
        "union_reachable_fraction": len(union) / len(permissive),
        "multi_source_node_count": multi_count,
        "multi_source_overlap_fraction": multi_count / len(union),
        "exclusive_source_node_count": exclusive_count,
        "exclusive_source_fraction": exclusive_count / len(union),
        "mean_source_multiplicity": float(np.mean(tuple(multiplicity.values()))),
        "worst_source_loss_retention": worst_retention,
    }


def _evaluate_row(replicate, autocorr, neighbourhood, barrier_density):
    base = _generate_base(replicate, autocorr, neighbourhood)
    outlet = _outlet_corner(replicate, autocorr, neighbourhood)
    anchor = _truth_source(base, outlet)
    _, graph = _graphs(base, barrier_density, RULE, outlet)

    candidates, median_potential = _candidate_sources(base, outlet, anchor)
    source_sets = _source_sets(candidates, anchor)
    row = {
        "replicate": replicate,
        "environmental_autocorrelation": autocorr,
        "neighbourhood": neighbourhood,
        "truth_barrier_density": barrier_density,
        "anchor_source": _node_id(anchor),
        "permissive_node_count": len(base["permissive"]),
        "eligible_additional_source_count": len(candidates),
        "candidate_potential_median": median_potential,
        "eligible": bool(source_sets),
        "designs": {},
    }
    if not source_sets:
        return row

    for design in DESIGNS:
        row["designs"][design] = {}
        previous_union = -1
        previous_multi = -1
        for source_count in SOURCE_COUNTS:
            metrics = _metrics(
                graph,
                base["permissive"],
                source_sets[design][source_count],
            )
            if metrics["union_reachable_node_count"] < previous_union:
                raise RuntimeError("adding sources reduced union reachability")
            if metrics["multi_source_node_count"] < previous_multi:
                raise RuntimeError("adding sources reduced multi-source node count")
            previous_union = metrics["union_reachable_node_count"]
            previous_multi = metrics["multi_source_node_count"]
            row["designs"][design][str(source_count)] = metrics

    return row


def _mean(values):
    vals = [float(value) for value in values]
    return None if not vals else float(np.mean(vals))


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != (
        "frozen_before_source_placement_benchmark_implementation_and_scoring"
    ):
        raise RuntimeError("v18 protocol is not frozen")

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
        raise RuntimeError("no eligible source-placement rows")

    arrangement_difference_rows = sum(
        row["designs"]["clustered"]["2"]["union_reachable_node_count"]
        != row["designs"]["dispersed"]["2"]["union_reachable_node_count"]
        for row in eligible
    )

    c2 = (
        _mean(
            row["designs"]["dispersed"]["2"]["union_reachable_fraction"]
            for row in eligible
        )
        - _mean(
            row["designs"]["clustered"]["2"]["union_reachable_fraction"]
            for row in eligible
        )
    )
    c3 = (
        _mean(
            row["designs"]["clustered"]["2"]["multi_source_overlap_fraction"]
            for row in eligible
        )
        - _mean(
            row["designs"]["dispersed"]["2"]["multi_source_overlap_fraction"]
            for row in eligible
        )
    )
    c4 = (
        _mean(
            row["designs"]["clustered"]["2"]["worst_source_loss_retention"]
            for row in eligible
        )
        - _mean(
            row["designs"]["dispersed"]["2"]["worst_source_loss_retention"]
            for row in eligible
        )
    )

    two_dispersed_beats_three_clustered_rows = sum(
        row["designs"]["dispersed"]["2"]["union_reachable_node_count"]
        > row["designs"]["clustered"]["3"]["union_reachable_node_count"]
        for row in eligible
    )

    monotonic_union_violations = 0
    monotonic_multi_violations = 0
    tradeoff_rows = 0
    for row in eligible:
        for design in DESIGNS:
            unions = [
                row["designs"][design][str(k)]["union_reachable_node_count"]
                for k in SOURCE_COUNTS
            ]
            multis = [
                row["designs"][design][str(k)]["multi_source_node_count"]
                for k in SOURCE_COUNTS
            ]
            monotonic_union_violations += sum(
                a > b for a, b in zip(unions[:-1], unions[1:], strict=True)
            )
            monotonic_multi_violations += sum(
                a > b for a, b in zip(multis[:-1], multis[1:], strict=True)
            )

        dispersed = row["designs"]["dispersed"]["2"]
        clustered = row["designs"]["clustered"]["2"]
        if (
            dispersed["union_reachable_fraction"]
            > clustered["union_reachable_fraction"]
            and clustered["worst_source_loss_retention"]
            > dispersed["worst_source_loss_retention"]
        ):
            tradeoff_rows += 1

    summary_by_design_count = {}
    for design in DESIGNS:
        summary_by_design_count[design] = {}
        for k in SOURCE_COUNTS:
            key = str(k)
            summary_by_design_count[design][key] = {
                "mean_union_reachable_fraction": _mean(
                    row["designs"][design][key]["union_reachable_fraction"]
                    for row in eligible
                ),
                "mean_multi_source_overlap_fraction": _mean(
                    row["designs"][design][key]["multi_source_overlap_fraction"]
                    for row in eligible
                ),
                "mean_source_multiplicity": _mean(
                    row["designs"][design][key]["mean_source_multiplicity"]
                    for row in eligible
                ),
                "mean_worst_source_loss_retention": _mean(
                    row["designs"][design][key]["worst_source_loss_retention"]
                    for row in eligible
                ),
                "mean_exclusive_source_fraction": _mean(
                    row["designs"][design][key]["exclusive_source_fraction"]
                    for row in eligible
                ),
            }

    verdicts = {
        "S1_same_source_count_different_placement_changes_coverage": (
            "SUPPORTED" if arrangement_difference_rows > 0 else "REFUTED"
        ),
        "S2_dispersed_sources_expand_coverage": (
            "SUPPORTED" if c2 > 0 else "REFUTED"
        ),
        "S3_clustered_sources_increase_route_overlap": (
            "SUPPORTED" if c3 > 0 else "REFUTED"
        ),
        "S4_clustered_sources_increase_source_loss_insurance": (
            "SUPPORTED" if c4 > 0 else "REFUTED"
        ),
        "S5_two_well_placed_sources_can_outperform_three_clustered_sources": (
            "SUPPORTED"
            if two_dispersed_beats_three_clustered_rows > 0
            else "REFUTED"
        ),
        "S6_more_sources_never_reduce_union_reachability": (
            "SUPPORTED" if monotonic_union_violations == 0 else "REFUTED"
        ),
        "S7_more_sources_never_reduce_multi_source_node_count": (
            "SUPPORTED" if monotonic_multi_violations == 0 else "REFUTED"
        ),
        "S8_source_placement_creates_coverage_insurance_tradeoff": (
            "SUPPORTED" if tradeoff_rows > 0 else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_source_placement.result.v18",
        "row_count": len(rows),
        "eligible_row_count": len(eligible),
        "non_estimable_row_count": len(rows) - len(eligible),
        "predeclared_verdicts": verdicts,
        "summary_by_design_and_source_count": summary_by_design_count,
        "two_source_contrasts": {
            "dispersed_minus_clustered_union_reachable_fraction": c2,
            "clustered_minus_dispersed_multi_source_overlap_fraction": c3,
            "clustered_minus_dispersed_worst_source_loss_retention": c4,
        },
        "arrangement_difference_row_count": arrangement_difference_rows,
        "two_dispersed_beats_three_clustered_row_count": (
            two_dispersed_beats_three_clustered_rows
        ),
        "coverage_insurance_tradeoff_row_count": tradeoff_rows,
        "monotonic_union_violation_count": monotonic_union_violations,
        "monotonic_multi_source_count_violation_count": monotonic_multi_violations,
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
                "two_source_contrasts": result["two_source_contrasts"],
                "arrangement_difference_row_count": result[
                    "arrangement_difference_row_count"
                ],
                "two_dispersed_beats_three_clustered_row_count": result[
                    "two_dispersed_beats_three_clustered_row_count"
                ],
                "coverage_insurance_tradeoff_row_count": result[
                    "coverage_insurance_tradeoff_row_count"
                ],
                "summary_by_design_and_source_count": result[
                    "summary_by_design_and_source_count"
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
