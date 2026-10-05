#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import itertools
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
    _node_id,
)
from benchmarks.run_eog_original_idea_directed_temporal_flow_v5 import (
    _graphs,
    _outlet_corner,
    _truth_source,
)
from benchmarks.run_eog_original_idea_source_placement_v18 import (
    DESIGNS,
    RULE,
    _candidate_sources,
    _source_sets,
)


PROTOCOL = ROOT / "validation/eog_original_idea_source_history_memory_v21/protocol_v21.json"
TRANSIENT_T = 6
ACTIVATION_HISTORIES = {
    "H_anchor_first": (0, 2, 4),
    "H_second_first": (4, 0, 2),
    "H_third_first": (2, 4, 0),
}


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


def _source_distances(graph, sources):
    return {source: _bfs_distances(graph, source) for source in sources}


def _history_metrics(distances, sources, activation_times):
    if len(sources) != 3 or len(activation_times) != 3:
        raise ValueError("v21 requires exactly three sources and three activation times")

    activation = {
        source: int(time)
        for source, time in zip(sources, activation_times, strict=True)
    }

    static_union = frozenset().union(
        *(frozenset(distances[source]) for source in sources)
    )
    if not static_union:
        raise RuntimeError("empty equilibrium union")

    transient = set()
    earliest_map = {}
    static_origin_map = {}
    minimum_arrival = {}

    for node in sorted(static_union):
        static_origins = tuple(
            source for source in sources if node in distances[source]
        )
        arrivals = {
            source: activation[source] + int(distances[source][node])
            for source in static_origins
        }
        first_time = min(arrivals.values())
        earliest = tuple(
            source
            for source in static_origins
            if arrivals[source] == first_time
        )

        static_origin_map[node] = static_origins
        earliest_map[node] = earliest
        minimum_arrival[node] = first_time
        if first_time <= TRANSIENT_T:
            transient.add(node)

    convergence_time = max(minimum_arrival.values())
    return {
        "equilibrium_union": static_union,
        "transient_occupied": frozenset(transient),
        "static_origin_map": static_origin_map,
        "earliest_origin_map": earliest_map,
        "minimum_arrival": minimum_arrival,
        "equilibrium_convergence_time": convergence_time,
        "post_last_activation_convergence_delay": max(0, convergence_time - 4),
    }


def _jaccard_distance(left, right):
    union = left | right
    if not union:
        return 0.0
    return 1.0 - len(left & right) / len(union)


def _pairwise_mean_distance(sets_by_history):
    names = tuple(sorted(sets_by_history))
    values = []
    for left_name, right_name in itertools.combinations(names, 2):
        values.append(
            _jaccard_distance(
                sets_by_history[left_name],
                sets_by_history[right_name],
            )
        )
    return float(np.mean(values)) if values else 0.0


def _provenance_disagreement_fraction(history_metrics):
    names = tuple(sorted(history_metrics))
    union_sets = {
        history_metrics[name]["equilibrium_union"]
        for name in names
    }
    if len(union_sets) != 1:
        raise RuntimeError("equilibrium occupancy differs across histories")
    union = next(iter(union_sets))

    disagree = 0
    unique_switch = 0
    for node in union:
        earliest_sets = [
            tuple(history_metrics[name]["earliest_origin_map"][node])
            for name in names
        ]
        if len(set(earliest_sets)) > 1:
            disagree += 1
        if (
            all(len(value) == 1 for value in earliest_sets)
            and len({value[0] for value in earliest_sets}) > 1
        ):
            unique_switch += 1

    n = len(union)
    return {
        "provenance_disagreement_node_count": disagree,
        "provenance_disagreement_fraction": disagree / n,
        "unique_earliest_source_switch_node_count": unique_switch,
        "unique_earliest_source_switch_fraction": unique_switch / n,
    }


def _static_ambiguity_fraction(metrics):
    union = metrics["equilibrium_union"]
    count = sum(
        len(metrics["static_origin_map"][node]) >= 2
        for node in union
    )
    return count / len(union)


def _earliest_ambiguity_fraction(metrics):
    union = metrics["equilibrium_union"]
    count = sum(
        len(metrics["earliest_origin_map"][node]) >= 2
        for node in union
    )
    return count / len(union)


def _evaluate_design(graph, sources, design):
    distances = _source_distances(graph, sources)
    histories = {
        name: _history_metrics(distances, sources, activation_times)
        for name, activation_times in ACTIVATION_HISTORIES.items()
    }

    equilibrium_sets = {
        histories[name]["equilibrium_union"]
        for name in histories
    }
    if len(equilibrium_sets) != 1:
        raise RuntimeError("same final source set did not converge to same occupancy")

    transient_sets = {
        name: histories[name]["transient_occupied"]
        for name in histories
    }
    provenance = _provenance_disagreement_fraction(histories)
    static_ambiguity = _static_ambiguity_fraction(next(iter(histories.values())))
    earliest_ambiguity_by_history = {
        name: _earliest_ambiguity_fraction(metrics)
        for name, metrics in histories.items()
    }

    return {
        "design": design,
        "source_ids": [_node_id(source) for source in sources],
        "equilibrium_union_node_count": len(next(iter(equilibrium_sets))),
        "equilibrium_occupancy_equal_across_histories": True,
        "transient_occupied_fraction_by_history": {
            name: len(transient_sets[name]) / len(next(iter(equilibrium_sets)))
            for name in histories
        },
        "mean_pairwise_transient_occupancy_jaccard_distance": (
            _pairwise_mean_distance(transient_sets)
        ),
        "static_origin_ambiguity_fraction": static_ambiguity,
        "earliest_origin_ambiguity_fraction_by_history": (
            earliest_ambiguity_by_history
        ),
        "mean_earliest_origin_ambiguity_fraction": float(
            np.mean(tuple(earliest_ambiguity_by_history.values()))
        ),
        "post_last_activation_convergence_delay_by_history": {
            name: histories[name]["post_last_activation_convergence_delay"]
            for name in histories
        },
        **provenance,
        "history_metrics": {
            name: {
                "transient_occupied_node_count": len(
                    histories[name]["transient_occupied"]
                ),
                "equilibrium_convergence_time": histories[name][
                    "equilibrium_convergence_time"
                ],
                "post_last_activation_convergence_delay": histories[name][
                    "post_last_activation_convergence_delay"
                ],
            }
            for name in histories
        },
    }


def _evaluate_row(replicate, autocorr, neighbourhood, barrier_density):
    base = _generate_base(replicate, autocorr, neighbourhood)
    outlet = _outlet_corner(replicate, autocorr, neighbourhood)
    anchor = _truth_source(base, outlet)
    _, graph = _graphs(base, barrier_density, RULE, outlet)
    candidates, _ = _candidate_sources(base, outlet, anchor)
    source_sets = _source_sets(candidates, anchor)

    row = {
        "replicate": replicate,
        "environmental_autocorrelation": autocorr,
        "neighbourhood": neighbourhood,
        "truth_barrier_density": barrier_density,
        "anchor_source": _node_id(anchor),
        "eligible": bool(source_sets),
        "designs": {},
    }
    if not source_sets:
        return row

    for design in DESIGNS:
        row["designs"][design] = _evaluate_design(
            graph,
            source_sets[design][3],
            design,
        )
    return row


def _mean(values):
    vals = [float(value) for value in values]
    return None if not vals else float(np.mean(vals))


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != (
        "frozen_before_source_history_benchmark_implementation_and_scoring"
    ):
        raise RuntimeError("v21 protocol is not frozen")

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
        raise RuntimeError("no eligible v21 rows")

    transient_difference_design_rows = 0
    occupancy_equality_violations = 0
    provenance_difference_design_rows = 0
    history_memory_design_rows = 0
    residual_ambiguity_any = False

    summary = {}
    for design in DESIGNS:
        drows = [row["designs"][design] for row in eligible]

        for drow in drows:
            fractions = tuple(drow["transient_occupied_fraction_by_history"].values())
            if max(fractions) - min(fractions) > 1e-15:
                transient_difference_design_rows += 1
            if not drow["equilibrium_occupancy_equal_across_histories"]:
                occupancy_equality_violations += 1
            if drow["provenance_disagreement_fraction"] > 0:
                provenance_difference_design_rows += 1
                history_memory_design_rows += 1
            if any(
                value > 0
                for value in drow["earliest_origin_ambiguity_fraction_by_history"].values()
            ):
                residual_ambiguity_any = True

        summary[design] = {
            "mean_pairwise_transient_occupancy_jaccard_distance": _mean(
                drow["mean_pairwise_transient_occupancy_jaccard_distance"]
                for drow in drows
            ),
            "mean_static_origin_ambiguity_fraction": _mean(
                drow["static_origin_ambiguity_fraction"]
                for drow in drows
            ),
            "mean_earliest_origin_ambiguity_fraction": _mean(
                drow["mean_earliest_origin_ambiguity_fraction"]
                for drow in drows
            ),
            "mean_provenance_disagreement_fraction": _mean(
                drow["provenance_disagreement_fraction"]
                for drow in drows
            ),
            "mean_unique_earliest_source_switch_fraction": _mean(
                drow["unique_earliest_source_switch_fraction"]
                for drow in drows
            ),
            "mean_post_last_activation_convergence_delay": _mean(
                delay
                for drow in drows
                for delay in drow[
                    "post_last_activation_convergence_delay_by_history"
                ].values()
            ),
            "rows_with_transient_occupancy_difference": sum(
                (
                    max(drow["transient_occupied_fraction_by_history"].values())
                    - min(drow["transient_occupied_fraction_by_history"].values())
                )
                > 1e-15
                for drow in drows
            ),
            "rows_with_provenance_disagreement": sum(
                drow["provenance_disagreement_fraction"] > 0
                for drow in drows
            ),
        }

    m4_contrast = (
        summary["dispersed"][
            "mean_pairwise_transient_occupancy_jaccard_distance"
        ]
        - summary["clustered"][
            "mean_pairwise_transient_occupancy_jaccard_distance"
        ]
    )
    m5_contrast = (
        summary["clustered"]["mean_provenance_disagreement_fraction"]
        - summary["dispersed"]["mean_provenance_disagreement_fraction"]
    )

    m6_by_design = {}
    m6_supported = True
    for design in DESIGNS:
        static = summary[design]["mean_static_origin_ambiguity_fraction"]
        earliest = summary[design]["mean_earliest_origin_ambiguity_fraction"]
        strict = earliest < static
        m6_by_design[design] = {
            "mean_static_origin_ambiguity_fraction": static,
            "mean_earliest_origin_ambiguity_fraction": earliest,
            "strict_reduction": strict,
        }
        m6_supported = m6_supported and strict

    verdicts = {
        "M1_activation_order_changes_transient_distribution": (
            "SUPPORTED" if transient_difference_design_rows > 0 else "REFUTED"
        ),
        "M2_equilibrium_occupancy_forgets_activation_order": (
            "SUPPORTED" if occupancy_equality_violations == 0 else "REFUTED"
        ),
        "M3_provenance_can_remember_history_after_occupancy_converges": (
            "SUPPORTED" if provenance_difference_design_rows > 0 else "REFUTED"
        ),
        "M4_dispersed_sources_increase_transient_order_sensitivity": (
            "SUPPORTED" if m4_contrast > 0 else "REFUTED"
        ),
        "M5_clustered_sources_increase_provenance_order_sensitivity": (
            "SUPPORTED" if m5_contrast > 0 else "REFUTED"
        ),
        "M6_timing_reduces_but_does_not_eliminate_static_source_ambiguity": (
            "SUPPORTED"
            if m6_supported and residual_ambiguity_any
            else "REFUTED"
        ),
        "M7_same_final_source_set_can_encode_multiple_histories": (
            "SUPPORTED" if provenance_difference_design_rows > 0 else "REFUTED"
        ),
        "M8_history_memory_is_not_occupancy_memory": (
            "SUPPORTED"
            if history_memory_design_rows > 0
            and occupancy_equality_violations == 0
            else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_source_history_memory.result.v21",
        "row_count": len(rows),
        "eligible_row_count": len(eligible),
        "non_estimable_row_count": len(rows) - len(eligible),
        "predeclared_verdicts": verdicts,
        "summary_by_design": summary,
        "M1_transient_difference_design_row_count": (
            transient_difference_design_rows
        ),
        "M2_equilibrium_occupancy_equality_violation_count": (
            occupancy_equality_violations
        ),
        "M3_provenance_difference_design_row_count": (
            provenance_difference_design_rows
        ),
        "M4_dispersed_minus_clustered_transient_jaccard": m4_contrast,
        "M5_clustered_minus_dispersed_provenance_disagreement": m5_contrast,
        "M6_detail": m6_by_design,
        "M8_history_memory_design_row_count": history_memory_design_rows,
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
                "summary_by_design": result["summary_by_design"],
                "M4_dispersed_minus_clustered_transient_jaccard": result[
                    "M4_dispersed_minus_clustered_transient_jaccard"
                ],
                "M5_clustered_minus_dispersed_provenance_disagreement": result[
                    "M5_clustered_minus_dispersed_provenance_disagreement"
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
