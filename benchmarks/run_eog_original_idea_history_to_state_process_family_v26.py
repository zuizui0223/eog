#!/usr/bin/env python3
from __future__ import annotations

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
from benchmarks.run_eog_original_idea_source_history_memory_v21 import (
    ACTIVATION_HISTORIES,
)
from benchmarks.run_eog_original_idea_history_observability_v22 import (
    SNAPSHOT_TIMES,
    _arrival_structure,
    _distances,
    _provenance_target,
    _snapshot_signature,
)
from benchmarks.run_eog_original_idea_colonization_age_memory_v24 import (
    _combined_observation_signature,
    _first_arrival_target,
)


PROTOCOL = ROOT / "validation/eog_original_idea_history_to_state_process_family_v26/protocol_v26.json"

PROCESS_IDS = (
    "history_blind_occupancy",
    "persistent_threshold_lag2",
    "transient_window_age1_2",
    "saturating_age_class_cap3",
)


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


def _static_origin_set(distances, sources, node):
    return tuple(source for source in sources if node in distances[source])


def _class_count(values_by_history):
    return len(set(values_by_history.values()))


def _age_map(non_source_nodes, first_arrival, horizon):
    if horizon is None:
        return ()
    return tuple(
        (
            _node_id(node),
            int(horizon) - int(first_arrival[node]),
        )
        for node in non_source_nodes
    )


def _process_map(process_id, ages):
    if process_id == "history_blind_occupancy":
        return tuple((node_id, True) for node_id, _ in ages)
    if process_id == "persistent_threshold_lag2":
        return tuple((node_id, age >= 2) for node_id, age in ages)
    if process_id == "transient_window_age1_2":
        return tuple((node_id, 1 <= age < 3) for node_id, age in ages)
    if process_id == "saturating_age_class_cap3":
        return tuple((node_id, min(int(age), 3)) for node_id, age in ages)
    raise ValueError(f"unknown process {process_id!r}")


def _evaluate_design(graph, sources, design):
    distances = _distances(graph, sources)
    source_set = frozenset(sources)
    histories = {}

    for name, activation_times in ACTIVATION_HISTORIES.items():
        equilibrium_union, first_arrival, earliest_map = _arrival_structure(
            distances,
            sources,
            activation_times,
        )
        histories[name] = {
            "equilibrium_union": equilibrium_union,
            "first_arrival": first_arrival,
            "earliest_map": earliest_map,
            "provenance_target": _provenance_target(
                equilibrium_union,
                earliest_map,
            ),
            "snapshots": {
                time: _snapshot_signature(
                    equilibrium_union,
                    first_arrival,
                    source_set,
                    time,
                )
                for time in SNAPSHOT_TIMES
            },
        }

    equilibrium_sets = {row["equilibrium_union"] for row in histories.values()}
    if len(equilibrium_sets) != 1:
        raise RuntimeError("equilibrium occupancy differs across histories")
    equilibrium_union = next(iter(equilibrium_sets))
    non_source_nodes = tuple(
        node for node in sorted(equilibrium_union)
        if node not in source_set
    )

    common_horizon = (
        max(
            int(histories[name]["first_arrival"][node])
            for name in histories
            for node in non_source_nodes
        )
        if non_source_nodes
        else None
    )

    combined_signature = {
        name: _combined_observation_signature(
            histories,
            name,
            non_source_nodes,
        )
        for name in histories
    }
    exact_age = {
        name: _first_arrival_target(
            non_source_nodes,
            histories[name]["first_arrival"],
        )
        for name in histories
    }
    colonization_age = {
        name: _age_map(
            non_source_nodes,
            histories[name]["first_arrival"],
            common_horizon,
        )
        for name in histories
    }
    process_targets = {
        process_id: {
            name: _process_map(process_id, colonization_age[name])
            for name in histories
        }
        for process_id in PROCESS_IDS
    }

    exact_age_class_count = _class_count(exact_age)
    class_counts = {
        process_id: _class_count(targets)
        for process_id, targets in process_targets.items()
    }

    if class_counts["history_blind_occupancy"] != 1:
        raise RuntimeError("history-blind control retained age information")
    if class_counts["saturating_age_class_cap3"] > exact_age_class_count:
        raise RuntimeError("cap3 target finer than exact age")
    if (
        class_counts["persistent_threshold_lag2"]
        > class_counts["saturating_age_class_cap3"]
    ):
        raise RuntimeError("threshold target finer than cap3")
    if (
        class_counts["transient_window_age1_2"]
        > class_counts["saturating_age_class_cap3"]
    ):
        raise RuntimeError("transient target finer than cap3")

    combined_groups = {}
    for history, signature in combined_signature.items():
        combined_groups.setdefault(signature, []).append(history)
    residual_groups = tuple(
        tuple(sorted(group))
        for group in combined_groups.values()
        if len(group) > 1
    )

    hidden_age_inside_v23_alias = False
    memory_inside_v23_alias = {
        process_id: False for process_id in PROCESS_IDS
    }
    for group in residual_groups:
        age_values = {exact_age[name] for name in group}
        hidden_age_inside_v23_alias |= len(age_values) > 1
        for process_id in PROCESS_IDS:
            values = {
                process_targets[process_id][name]
                for name in group
            }
            memory_inside_v23_alias[process_id] |= len(values) > 1

    node_memory = {
        process_id: {
            "total": 0,
            "unique_origin": 0,
            "confluence": 0,
        }
        for process_id in PROCESS_IDS
    }
    node_count_by_zone = {"unique_origin": 0, "confluence": 0}

    for node in non_source_nodes:
        static_origins = _static_origin_set(distances, sources, node)
        if len(static_origins) == 1:
            zone = "unique_origin"
        elif len(static_origins) >= 2:
            zone = "confluence"
        else:
            continue
        node_count_by_zone[zone] += 1

        node_id = _node_id(node)
        for process_id in PROCESS_IDS:
            values = {
                dict(process_targets[process_id][name])[node_id]
                for name in histories
            }
            if len(values) > 1:
                node_memory[process_id]["total"] += 1
                node_memory[process_id][zone] += 1

    process_memory = {
        process_id: class_counts[process_id] > 1
        for process_id in PROCESS_IDS
    }

    exact_age_memory = exact_age_class_count > 1
    threshold_hidden = (
        exact_age_memory
        and class_counts["persistent_threshold_lag2"] == 1
    )
    cap3_hidden = (
        exact_age_memory
        and class_counts["saturating_age_class_cap3"] == 1
    )

    return {
        "design": design,
        "source_ids": [_node_id(source) for source in sources],
        "equilibrium_non_source_node_count": len(non_source_nodes),
        "common_horizon": common_horizon,
        "v23_combined_full_history_unresolved": (
            _class_count(combined_signature) < len(histories)
        ),
        "v24_hidden_age_difference_inside_v23_alias": (
            hidden_age_inside_v23_alias
        ),
        "exact_age_class_count": exact_age_class_count,
        "process_class_counts": class_counts,
        "process_history_memory": process_memory,
        "process_memory_inside_v23_alias": memory_inside_v23_alias,
        "threshold_hidden_exact_age": threshold_hidden,
        "cap3_hidden_exact_age": cap3_hidden,
        "node_memory_counts": node_memory,
        "zone_node_counts": node_count_by_zone,
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


def _jaccard(left, right):
    left = set(left)
    right = set(right)
    union = left | right
    return 1.0 if not union else len(left & right) / len(union)


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != (
        "frozen_before_process_family_benchmark_implementation_and_scoring"
    ):
        raise RuntimeError("v26 protocol is not frozen")

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
    design_rows = [
        row["designs"][design]
        for row in eligible
        for design in DESIGNS
    ]
    if len(design_rows) != 768:
        raise RuntimeError(
            f"expected 768 design rows, got {len(design_rows)}"
        )

    v23_residual = [
        drow for drow in design_rows
        if drow["v23_combined_full_history_unresolved"]
    ]
    if len(v23_residual) != 81:
        raise RuntimeError(
            f"expected 81 v23 residual rows, got {len(v23_residual)}"
        )
    v24_hidden_age = [
        drow for drow in v23_residual
        if drow["v24_hidden_age_difference_inside_v23_alias"]
    ]
    if len(v24_hidden_age) != 45:
        raise RuntimeError(
            f"expected 45 v24 hidden-age residual rows, got {len(v24_hidden_age)}"
        )

    process_memory_sets = {}
    for process_id in PROCESS_IDS:
        process_memory_sets[process_id] = {
            index
            for index, drow in enumerate(design_rows)
            if drow["process_history_memory"][process_id]
        }

    hidden_age_process_sets = {}
    for process_id in PROCESS_IDS:
        hidden_age_process_sets[process_id] = {
            index
            for index, drow in enumerate(v24_hidden_age)
            if drow["process_memory_inside_v23_alias"][process_id]
        }

    p1_violations = sum(
        drow["process_class_counts"]["history_blind_occupancy"] != 1
        for drow in design_rows
    )
    p2_violations = sum(
        drow["process_class_counts"]["saturating_age_class_cap3"]
        > drow["exact_age_class_count"]
        for drow in design_rows
    )
    p3_violations = sum(
        (
            drow["process_class_counts"]["saturating_age_class_cap3"]
            < drow["process_class_counts"]["persistent_threshold_lag2"]
        )
        or (
            drow["process_class_counts"]["saturating_age_class_cap3"]
            < drow["process_class_counts"]["transient_window_age1_2"]
        )
        for drow in design_rows
    )

    threshold_only = (
        process_memory_sets["persistent_threshold_lag2"]
        - process_memory_sets["transient_window_age1_2"]
    )
    transient_only = (
        process_memory_sets["transient_window_age1_2"]
        - process_memory_sets["persistent_threshold_lag2"]
    )

    threshold_hidden_rows = [
        index for index, drow in enumerate(design_rows)
        if drow["threshold_hidden_exact_age"]
    ]
    richer_rescues = [
        index for index in threshold_hidden_rows
        if (
            design_rows[index]["process_history_memory"][
                "transient_window_age1_2"
            ]
            or design_rows[index]["process_history_memory"][
                "saturating_age_class_cap3"
            ]
        )
    ]

    cap3_hidden_rows = [
        index for index, drow in enumerate(design_rows)
        if drow["cap3_hidden_exact_age"]
    ]

    non_control_hidden_sets = {
        key: hidden_age_process_sets[key]
        for key in (
            "persistent_threshold_lag2",
            "transient_window_age1_2",
            "saturating_age_class_cap3",
        )
    }
    hidden_sets_differ = len(
        {
            tuple(sorted(value))
            for value in non_control_hidden_sets.values()
        }
    ) > 1

    by_process = {}
    for process_id in PROCESS_IDS:
        memory_rows = process_memory_sets[process_id]
        node_memory_total = sum(
            drow["node_memory_counts"][process_id]["total"]
            for drow in design_rows
        )
        total_nodes = sum(
            drow["equilibrium_non_source_node_count"]
            for drow in design_rows
        )
        by_process[process_id] = {
            "design_rows_with_history_memory": len(memory_rows),
            "fraction_of_design_rows_with_history_memory": (
                len(memory_rows) / len(design_rows)
            ),
            "history_dependent_node_count": node_memory_total,
            "history_dependent_node_fraction": (
                0.0 if total_nodes == 0 else node_memory_total / total_nodes
            ),
            "v24_hidden_age_residual_rows_detected": len(
                hidden_age_process_sets[process_id]
            ),
            "unique_origin_memory_rows": sum(
                drow["node_memory_counts"][process_id]["unique_origin"] > 0
                for drow in design_rows
            ),
            "confluence_memory_rows": sum(
                drow["node_memory_counts"][process_id]["confluence"] > 0
                for drow in design_rows
            ),
        }

    pairwise_jaccard = {}
    non_control = (
        "persistent_threshold_lag2",
        "transient_window_age1_2",
        "saturating_age_class_cap3",
    )
    for i, left in enumerate(non_control):
        for right in non_control[i + 1 :]:
            pairwise_jaccard[f"{left}__{right}"] = _jaccard(
                process_memory_sets[left],
                process_memory_sets[right],
            )

    by_design = {}
    for design in DESIGNS:
        drows = [row["designs"][design] for row in eligible]
        by_design[design] = {}
        for process_id in PROCESS_IDS:
            by_design[design][process_id] = {
                "rows_with_history_memory": sum(
                    drow["process_history_memory"][process_id]
                    for drow in drows
                ),
                "mean_history_dependent_node_fraction": _mean(
                    (
                        drow["node_memory_counts"][process_id]["total"]
                        / drow["equilibrium_non_source_node_count"]
                        if drow["equilibrium_non_source_node_count"] > 0
                        else 0.0
                    )
                    for drow in drows
                ),
            }

    verdicts = {
        "P1_history_blind_control_erases_all_age_history": (
            "SUPPORTED" if p1_violations == 0 else "REFUTED"
        ),
        "P2_saturating_process_is_no_finer_than_exact_age": (
            "SUPPORTED" if p2_violations == 0 else "REFUTED"
        ),
        "P3_saturating_process_is_at_least_as_informative_as_both_binary_processes": (
            "SUPPORTED" if p3_violations == 0 else "REFUTED"
        ),
        "P4_transient_age_memory_exists": (
            "SUPPORTED"
            if process_memory_sets["transient_window_age1_2"]
            else "REFUTED"
        ),
        "P5_process_choice_changes_whether_history_is_ecologically_visible": (
            "SUPPORTED"
            if threshold_only and transient_only
            else "REFUTED"
        ),
        "P6_a_richer_age_process_recovers_some_threshold_hidden_history": (
            "SUPPORTED" if richer_rescues else "REFUTED"
        ),
        "P7_finite_saturation_can_still_erase_exact_age_history": (
            "SUPPORTED" if cap3_hidden_rows else "REFUTED"
        ),
        "P8_present_state_memory_is_target_specific_within_v24_hidden_age_aliases": (
            "SUPPORTED" if hidden_sets_differ else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_history_to_state_process_family.result.v26",
        "row_count": len(rows),
        "eligible_row_count": len(eligible),
        "design_row_count": len(design_rows),
        "predeclared_verdicts": verdicts,
        "theory_violation_counts": {
            "history_blind_control": p1_violations,
            "cap3_finer_than_exact_age": p2_violations,
            "binary_finer_than_cap3": p3_violations,
        },
        "process_summary": by_process,
        "process_specific_memory": {
            "threshold_only_row_count": len(threshold_only),
            "transient_only_row_count": len(transient_only),
            "threshold_hidden_exact_age_row_count": len(threshold_hidden_rows),
            "threshold_hidden_rows_recovered_by_transient_or_cap3": len(
                richer_rescues
            ),
            "cap3_hidden_exact_age_row_count": len(cap3_hidden_rows),
            "pairwise_memory_row_jaccard": pairwise_jaccard,
        },
        "v24_hidden_age_process_detection": {
            key: len(value)
            for key, value in hidden_age_process_sets.items()
        },
        "summary_by_design": by_design,
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
                "process_summary": result["process_summary"],
                "process_specific_memory": result[
                    "process_specific_memory"
                ],
                "v24_hidden_age_process_detection": result[
                    "v24_hidden_age_process_detection"
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
