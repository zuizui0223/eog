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
    _graph_from_edges,
    _node_id,
)
from benchmarks.run_eog_original_idea_analyst_worlds_v3 import (
    RULES,
    _rule_threshold,
)


PROTOCOL = ROOT / "validation/eog_original_idea_occurrence_information_v4/protocol_v4.json"
COVERAGE = (0.10, 0.25, 0.50, 1.00)
DESIGNS = ("clustered_near_source", "dispersed_farthest_first")


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


def _distance(left, right):
    return float(math.hypot(left[0] - right[0], left[1] - right[1]))


def _candidate_graph(base, barrier_density, rule):
    threshold = _rule_threshold(base, rule)
    edges = tuple(
        edge
        for edge in base["geo_edges"]
        if base["edge_uniform"][edge] >= barrier_density
        and abs(float(base["env"][edge[0]]) - float(base["env"][edge[1]]))
        <= threshold + 1e-15
    )
    return _graph_from_edges(base["permissive"], edges)


def _candidate_worlds(base):
    rows = []
    for rule in RULES:
        for barrier_density in BARRIER_LEVELS:
            graph = _candidate_graph(base, barrier_density, rule)
            for source in sorted(base["permissive"]):
                reachable = frozenset(_bfs_distances(graph, source))
                rows.append(
                    {
                        "world_id": (
                            f"{_node_id(source)}|b{barrier_density:.2f}|{rule}"
                        ),
                        "source": source,
                        "barrier_density": barrier_density,
                        "rule": rule,
                        "reachable": reachable,
                    }
                )
    expected = len(base["permissive"]) * len(BARRIER_LEVELS) * len(RULES)
    if len(rows) != expected:
        raise RuntimeError("candidate world Cartesian product incomplete")
    return tuple(rows)


def _truth_world_id(base, barrier_density):
    return (
        f"{_node_id(base['source'])}|b{barrier_density:.2f}|"
        "relative_edge_q70"
    )


def _clustered_order(pool, truth_dist, truth_source):
    return tuple(
        sorted(
            pool,
            key=lambda node: (
                int(truth_dist[node]),
                _distance(node, truth_source),
                _node_id(node),
            ),
        )
    )


def _dispersed_order(pool, truth_source):
    remaining = set(pool)
    first = sorted(
        remaining,
        key=lambda node: (-_distance(node, truth_source), _node_id(node)),
    )[0]
    selected = [first]
    remaining.remove(first)

    while remaining:
        def score(node):
            return min(_distance(node, chosen) for chosen in selected)

        nxt = sorted(
            remaining,
            key=lambda node: (-score(node), _node_id(node)),
        )[0]
        selected.append(nxt)
        remaining.remove(nxt)
    return tuple(selected)


def _coverage_count(pool_size, fraction):
    return max(1, int(math.ceil(float(fraction) * pool_size)))


def _survivor_summary(
    worlds,
    anchors,
    permissive,
    truth_reachable,
    truth_world_id,
):
    anchor_set = frozenset(anchors)
    survivors = tuple(
        world
        for world in worlds
        if anchor_set.issubset(world["reachable"])
    )
    if not survivors:
        raise RuntimeError("truth-generated positive anchors eliminated all worlds")

    survivor_ids = {world["world_id"] for world in survivors}
    if truth_world_id not in survivor_ids:
        raise RuntimeError("truth world was eliminated by truth-positive evidence")

    union_reachable = frozenset().union(
        *(world["reachable"] for world in survivors)
    )
    robust_unreachable = frozenset(permissive.difference(union_reachable))
    truth_unreachable = frozenset(permissive.difference(truth_reachable))
    false_exclusions = robust_unreachable.intersection(truth_reachable)

    recovery = (
        None
        if not truth_unreachable
        else len(robust_unreachable) / len(truth_unreachable)
    )
    return {
        "anchor_count": len(anchor_set),
        "survivor_world_count": len(survivors),
        "survivor_world_fraction": len(survivors) / len(worlds),
        "surviving_source_count": len({world["source"] for world in survivors}),
        "surviving_barrier_level_count": len(
            {world["barrier_density"] for world in survivors}
        ),
        "surviving_analyst_rule_count": len(
            {world["rule"] for world in survivors}
        ),
        "robustly_unreachable_count": len(robust_unreachable),
        "truth_unreachable_count": len(truth_unreachable),
        "robust_impossibility_recovery_fraction": recovery,
        "false_robust_exclusion_count": len(false_exclusions),
        "truth_world_survives": True,
    }


def _evaluate_row(replicate, autocorr, neighbourhood, barrier_density):
    base = _generate_base(replicate, autocorr, neighbourhood)
    truth_graph = _candidate_graph(
        base,
        barrier_density,
        "relative_edge_q70",
    )
    truth_dist = _bfs_distances(truth_graph, base["source"])
    truth_reachable = frozenset(truth_dist)
    pool = tuple(
        sorted(node for node in truth_reachable if node != base["source"])
    )

    base_row = {
        "replicate": replicate,
        "environmental_autocorrelation": autocorr,
        "neighbourhood": neighbourhood,
        "truth_barrier_density": barrier_density,
        "truth_source": _node_id(base["source"]),
        "permissive_node_count": len(base["permissive"]),
        "truth_reachable_node_count": len(truth_reachable),
        "truth_positive_pool_size": len(pool),
        "eligible": len(pool) >= 4,
    }
    if len(pool) < 4:
        return {
            **base_row,
            "candidate_world_count": None,
            "designs": {},
        }

    worlds = _candidate_worlds(base)
    truth_id = _truth_world_id(base, barrier_density)
    world_ids = {world["world_id"] for world in worlds}
    if truth_id not in world_ids:
        raise RuntimeError("truth world missing from candidate universe")

    orders = {
        "clustered_near_source": _clustered_order(
            pool,
            truth_dist,
            base["source"],
        ),
        "dispersed_farthest_first": _dispersed_order(
            pool,
            base["source"],
        ),
    }
    if set(orders["clustered_near_source"]) != set(pool):
        raise RuntimeError("clustered order lost truth-positive nodes")
    if set(orders["dispersed_farthest_first"]) != set(pool):
        raise RuntimeError("dispersed order lost truth-positive nodes")

    design_rows = {}
    for design in DESIGNS:
        order = orders[design]
        previous_count = len(worlds)
        fraction_rows = {}
        for fraction in COVERAGE:
            count = _coverage_count(len(pool), fraction)
            anchors = order[:count]
            summary = _survivor_summary(
                worlds,
                anchors,
                base["permissive"],
                truth_reachable,
                truth_id,
            )
            if summary["survivor_world_count"] > previous_count:
                raise RuntimeError(
                    "nested positive evidence increased survivor world count"
                )
            previous_count = summary["survivor_world_count"]
            fraction_rows[f"{fraction:.2f}"] = {
                **summary,
                "anchors": [_node_id(node) for node in anchors],
            }
        design_rows[design] = fraction_rows

    return {
        **base_row,
        "candidate_world_count": len(worlds),
        "local_viability_only_survivor_world_count": len(worlds),
        "local_viability_only_survivor_fraction": 1.0,
        "designs": design_rows,
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
        "frozen_before_occurrence_information_benchmark_implementation_and_scoring"
    ):
        raise RuntimeError("v4 protocol is not frozen")

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
        raise RuntimeError("no v4 eligible rows")

    survivor_means = {}
    recovery_means = {}
    for design in DESIGNS:
        survivor_means[design] = {}
        recovery_means[design] = {}
        for fraction in COVERAGE:
            key = f"{fraction:.2f}"
            survivor_means[design][key] = _mean(
                row["designs"][design][key]["survivor_world_fraction"]
                for row in eligible
            )
            recovery_values = [
                row["designs"][design][key][
                    "robust_impossibility_recovery_fraction"
                ]
                for row in eligible
                if row["designs"][design][key][
                    "robust_impossibility_recovery_fraction"
                ]
                is not None
            ]
            recovery_means[design][key] = _mean(recovery_values)

    monotonicity_violations = 0
    false_exclusion_count = 0
    arrangement_difference_rows = 0
    for row in eligible:
        for design in DESIGNS:
            counts = [
                row["designs"][design][f"{fraction:.2f}"][
                    "survivor_world_count"
                ]
                for fraction in COVERAGE
            ]
            if any(a < b for a, b in zip(counts[:-1], counts[1:], strict=True)):
                monotonicity_violations += 1
            false_exclusion_count += sum(
                row["designs"][design][f"{fraction:.2f}"][
                    "false_robust_exclusion_count"
                ]
                for fraction in COVERAGE
            )

        if any(
            row["designs"]["clustered_near_source"][f"{fraction:.2f}"][
                "survivor_world_count"
            ]
            != row["designs"]["dispersed_farthest_first"][f"{fraction:.2f}"][
                "survivor_world_count"
            ]
            for fraction in COVERAGE
        ):
            arrangement_difference_rows += 1

    o1_by_design_coverage = {
        design: {
            f"{fraction:.2f}": survivor_means[design][f"{fraction:.2f}"] < 1.0
            for fraction in COVERAGE
        }
        for design in DESIGNS
    }

    o4_contrasts = {}
    for fraction in (0.25, 0.50):
        key = f"{fraction:.2f}"
        contrast = (
            survivor_means["dispersed_farthest_first"][key]
            - survivor_means["clustered_near_source"][key]
        )
        o4_contrasts[key] = contrast

    o5_details = {}
    o5_supported = True
    for design in DESIGNS:
        values = [
            recovery_means[design][f"{fraction:.2f}"]
            for fraction in COVERAGE
        ]
        usable = [value for value in values if value is not None]
        nondecreasing = (
            len(usable) == len(values)
            and all(
                a <= b + 1e-15
                for a, b in zip(values[:-1], values[1:], strict=True)
            )
        )
        strict_endpoint = (
            values[0] is not None
            and values[-1] is not None
            and values[-1] > values[0]
        )
        o5_supported = o5_supported and nondecreasing and strict_endpoint
        o5_details[design] = {
            "means_by_coverage": {
                f"{fraction:.2f}": value
                for fraction, value in zip(COVERAGE, values, strict=True)
            },
            "nondecreasing": nondecreasing,
            "full_gt_10pct": strict_endpoint,
        }

    full_key = "1.00"
    full_medians = {}
    for design in DESIGNS:
        full_medians[design] = {
            "survivor_world_count": _median(
                row["designs"][design][full_key]["survivor_world_count"]
                for row in eligible
            ),
            "surviving_source_count": _median(
                row["designs"][design][full_key]["surviving_source_count"]
                for row in eligible
            ),
        }

    exact_world_recovery = {
        design: sum(
            row["designs"][design][full_key]["survivor_world_count"] == 1
            for row in eligible
        )
        for design in DESIGNS
    }
    exact_source_recovery = {
        design: sum(
            row["designs"][design][full_key]["surviving_source_count"] == 1
            for row in eligible
        )
        for design in DESIGNS
    }

    verdicts = {
        "O1_reachability_evidence_adds_information_beyond_local_viability": (
            "SUPPORTED"
            if all(
                all(by_coverage.values())
                for by_coverage in o1_by_design_coverage.values()
            )
            else "REFUTED"
        ),
        "O2_more_positive_anchors_contract_worlds_monotonically": (
            "SUPPORTED" if monotonicity_violations == 0 else "REFUTED"
        ),
        "O3_spatial_arrangement_changes_information": (
            "SUPPORTED" if arrangement_difference_rows > 0 else "REFUTED"
        ),
        "O4_dispersed_anchors_are_more_discriminating_on_average": (
            "SUPPORTED"
            if all(value < 0 for value in o4_contrasts.values())
            else "REFUTED"
        ),
        "O5_robust_impossibility_recovery_increases_with_occurrence_coverage": (
            "SUPPORTED" if o5_supported else "REFUTED"
        ),
        "O6_robust_impossibility_is_sound_when_truth_world_is_retained": (
            "SUPPORTED" if false_exclusion_count == 0 else "REFUTED"
        ),
        "O7_full_positive_occurrences_need_not_identify_one_history": (
            "SUPPORTED"
            if any(
                row["survivor_world_count"] > 1
                and row["surviving_source_count"] > 1
                for row in full_medians.values()
            )
            else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_occurrence_information.result.v4",
        "row_count": len(rows),
        "eligible_row_count": len(eligible),
        "non_estimable_row_count": len(rows) - len(eligible),
        "predeclared_verdicts": verdicts,
        "survivor_fraction_means": survivor_means,
        "robust_impossibility_recovery_means": recovery_means,
        "O1_detail": o1_by_design_coverage,
        "O2_monotonicity_violation_count": monotonicity_violations,
        "O3_arrangement_difference_row_count": arrangement_difference_rows,
        "O4_dispersed_minus_clustered_survivor_fraction": o4_contrasts,
        "O5_detail": o5_details,
        "O6_false_robust_exclusion_count": false_exclusion_count,
        "O7_full_coverage_medians": full_medians,
        "full_coverage_exact_world_recovery_count": exact_world_recovery,
        "full_coverage_exact_source_recovery_count": exact_source_recovery,
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
                "survivor_fraction_means": result["survivor_fraction_means"],
                "robust_impossibility_recovery_means": result[
                    "robust_impossibility_recovery_means"
                ],
                "O3_arrangement_difference_row_count": result[
                    "O3_arrangement_difference_row_count"
                ],
                "O4_dispersed_minus_clustered_survivor_fraction": result[
                    "O4_dispersed_minus_clustered_survivor_fraction"
                ],
                "O6_false_robust_exclusion_count": result[
                    "O6_false_robust_exclusion_count"
                ],
                "O7_full_coverage_medians": result["O7_full_coverage_medians"],
                "fingerprint": result["fingerprint"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
