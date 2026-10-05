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


PROTOCOL = ROOT / "validation/eog_original_idea_colonization_age_memory_v24/protocol_v24.json"


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


def _first_arrival_target(non_source_nodes, first_arrival):
    return tuple(
        (_node_id(node), int(first_arrival[node]))
        for node in non_source_nodes
    )


def _age_target(non_source_nodes, first_arrival, horizon):
    return tuple(
        (_node_id(node), int(horizon - int(first_arrival[node])))
        for node in non_source_nodes
    )


def _combined_observation_signature(histories, name, non_source_nodes):
    occupancy = tuple(
        histories[name]["snapshots"][time]
        for time in SNAPSHOT_TIMES
    )
    provenance = tuple(
        (
            _node_id(node),
            tuple(
                _node_id(source)
                for source in histories[name]["earliest_map"][node]
            ),
        )
        for node in non_source_nodes
    )
    return (occupancy, provenance)


def _equivalence_class_count(values_by_history):
    return len(set(values_by_history.values()))


def _alias_classes(values_by_history):
    groups = {}
    for history, value in values_by_history.items():
        groups.setdefault(value, []).append(history)
    return tuple(
        tuple(sorted(group))
        for group in groups.values()
        if len(group) > 1
    )


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
    if not non_source_nodes:
        return {
            "design": design,
            "eligible": False,
        }

    common_horizon = max(
        int(histories[name]["first_arrival"][node])
        for name in histories
        for node in non_source_nodes
    )

    provenance_by_history = {
        name: histories[name]["provenance_target"]
        for name in histories
    }
    first_arrival_by_history = {
        name: _first_arrival_target(
            non_source_nodes,
            histories[name]["first_arrival"],
        )
        for name in histories
    }
    age_by_history = {
        name: _age_target(
            non_source_nodes,
            histories[name]["first_arrival"],
            common_horizon,
        )
        for name in histories
    }
    combined_signature_by_history = {
        name: _combined_observation_signature(
            histories,
            name,
            non_source_nodes,
        )
        for name in histories
    }

    combined_class_count = _equivalence_class_count(
        combined_signature_by_history
    )
    provenance_class_count = _equivalence_class_count(
        provenance_by_history
    )
    first_arrival_class_count = _equivalence_class_count(
        first_arrival_by_history
    )
    age_class_count = _equivalence_class_count(age_by_history)

    if age_class_count != first_arrival_class_count:
        raise RuntimeError(
            "common-horizon colonization-age partition differs from first-arrival partition"
        )

    residual_alias_classes = _alias_classes(combined_signature_by_history)
    hidden_age_alias = False
    for group in residual_alias_classes:
        values = {first_arrival_by_history[name] for name in group}
        if len(values) > 1:
            hidden_age_alias = True
            break

    provenance_equivalent_age_different_pairs = 0
    history_names = tuple(sorted(histories))
    for i, left in enumerate(history_names):
        for right in history_names[i + 1 :]:
            if (
                provenance_by_history[left] == provenance_by_history[right]
                and first_arrival_by_history[left] != first_arrival_by_history[right]
            ):
                provenance_equivalent_age_different_pairs += 1

    unique_origin_nodes = 0
    confluence_nodes = 0
    unique_origin_age_memory_nodes = 0
    confluence_age_memory_nodes = 0
    first_arrival_disagreement_nodes = 0

    for node in non_source_nodes:
        static_origins = tuple(
            source for source in sources if node in distances[source]
        )
        times = {
            int(histories[name]["first_arrival"][node])
            for name in histories
        }
        has_age_memory = len(times) > 1
        first_arrival_disagreement_nodes += int(has_age_memory)

        if len(static_origins) == 1:
            unique_origin_nodes += 1
            unique_origin_age_memory_nodes += int(has_age_memory)
        elif len(static_origins) >= 2:
            confluence_nodes += 1
            confluence_age_memory_nodes += int(has_age_memory)

    return {
        "design": design,
        "eligible": True,
        "source_ids": [_node_id(source) for source in sources],
        "equilibrium_non_source_node_count": len(non_source_nodes),
        "combined_observation_class_count": combined_class_count,
        "combined_full_history_unresolved": combined_class_count < len(histories),
        "provenance_class_count": provenance_class_count,
        "first_arrival_class_count": first_arrival_class_count,
        "colonization_age_class_count": age_class_count,
        "first_arrival_exact_history_identified": (
            first_arrival_class_count == len(histories)
        ),
        "hidden_age_difference_inside_combined_alias": hidden_age_alias,
        "provenance_equivalent_age_different_pair_count": (
            provenance_equivalent_age_different_pairs
        ),
        "first_arrival_disagreement_node_count": (
            first_arrival_disagreement_nodes
        ),
        "first_arrival_disagreement_fraction": (
            first_arrival_disagreement_nodes / len(non_source_nodes)
        ),
        "unique_origin_node_count": unique_origin_nodes,
        "confluence_node_count": confluence_nodes,
        "unique_origin_age_memory_node_count": (
            unique_origin_age_memory_nodes
        ),
        "confluence_age_memory_node_count": confluence_age_memory_nodes,
        "common_horizon": common_horizon,
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


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != (
        "frozen_before_colonization_age_benchmark_implementation_and_scoring"
    ):
        raise RuntimeError("v24 protocol is not frozen")

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
        if row["designs"][design].get("eligible")
    ]

    v23_residual = [
        drow for drow in design_rows
        if drow["combined_full_history_unresolved"]
    ]
    if len(v23_residual) != 81:
        raise RuntimeError(
            f"expected to reproduce 81 v23 combined-unresolved design rows, got {len(v23_residual)}"
        )

    hidden_age_residual_rows = sum(
        drow["hidden_age_difference_inside_combined_alias"]
        for drow in v23_residual
    )
    first_arrival_rescued_residual_rows = sum(
        drow["first_arrival_exact_history_identified"]
        for drow in v23_residual
    )
    first_arrival_unresolved_rows = sum(
        not drow["first_arrival_exact_history_identified"]
        for drow in design_rows
    )
    provenance_equivalent_age_pairs = sum(
        drow["provenance_equivalent_age_different_pair_count"]
        for drow in design_rows
    )
    unique_age_rows = sum(
        drow["unique_origin_age_memory_node_count"] > 0
        for drow in design_rows
    )
    confluence_age_rows = sum(
        drow["confluence_age_memory_node_count"] > 0
        for drow in design_rows
    )
    class_count_violations = sum(
        drow["first_arrival_class_count"] > 3
        for drow in design_rows
    )
    occupancy_equal_with_age_memory_rows = sum(
        drow["first_arrival_disagreement_node_count"] > 0
        for drow in design_rows
    )

    by_design = {}
    for design in DESIGNS:
        drows = [
            row["designs"][design]
            for row in eligible
            if row["designs"][design].get("eligible")
        ]
        by_design[design] = {
            "design_rows": len(drows),
            "v23_combined_unresolved_rows": sum(
                drow["combined_full_history_unresolved"] for drow in drows
            ),
            "mean_first_arrival_disagreement_fraction": _mean(
                drow["first_arrival_disagreement_fraction"] for drow in drows
            ),
            "first_arrival_exact_history_identified_rows": sum(
                drow["first_arrival_exact_history_identified"] for drow in drows
            ),
            "rows_with_unique_origin_age_memory": sum(
                drow["unique_origin_age_memory_node_count"] > 0 for drow in drows
            ),
            "rows_with_confluence_age_memory": sum(
                drow["confluence_age_memory_node_count"] > 0 for drow in drows
            ),
        }

    verdicts = {
        "A1_occupancy_and_provenance_can_hide_colonization_age_memory": (
            "SUPPORTED" if hidden_age_residual_rows > 0 else "REFUTED"
        ),
        "A2_first_arrival_rescues_some_v23_residual_histories": (
            "SUPPORTED" if first_arrival_rescued_residual_rows > 0 else "REFUTED"
        ),
        "A3_first_arrival_does_not_always_identify_exact_history": (
            "SUPPORTED" if first_arrival_unresolved_rows > 0 else "REFUTED"
        ),
        "A4_provenance_equivalence_does_not_imply_age_equivalence": (
            "SUPPORTED" if provenance_equivalent_age_pairs > 0 else "REFUTED"
        ),
        "A5_unique_origin_zones_can_retain_age_memory": (
            "SUPPORTED" if unique_age_rows > 0 else "REFUTED"
        ),
        "A6_confluence_zones_can_retain_age_memory": (
            "SUPPORTED" if confluence_age_rows > 0 else "REFUTED"
        ),
        "A7_first_arrival_target_is_no_finer_than_exact_history": (
            "SUPPORTED" if class_count_violations == 0 else "REFUTED"
        ),
        "A8_final_occupancy_can_forget_history_while_age_state_remembers_it": (
            "SUPPORTED" if occupancy_equal_with_age_memory_rows > 0 else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_colonization_age_memory.result.v24",
        "row_count": len(rows),
        "eligible_row_count": len(eligible),
        "design_row_count": len(design_rows),
        "predeclared_verdicts": verdicts,
        "reproduced_v23_combined_unresolved_rows": len(v23_residual),
        "v23_residual_rows_with_hidden_age_difference": hidden_age_residual_rows,
        "v23_residual_rows_rescued_by_complete_first_arrival_map": (
            first_arrival_rescued_residual_rows
        ),
        "full_design_rows_unresolved_by_complete_first_arrival_map": (
            first_arrival_unresolved_rows
        ),
        "provenance_equivalent_age_different_pair_count": (
            provenance_equivalent_age_pairs
        ),
        "design_rows_with_unique_origin_age_memory": unique_age_rows,
        "design_rows_with_confluence_age_memory": confluence_age_rows,
        "first_arrival_class_count_violation_count": class_count_violations,
        "design_rows_with_any_age_memory_after_occupancy_convergence": (
            occupancy_equal_with_age_memory_rows
        ),
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
                "reproduced_v23_combined_unresolved_rows": result[
                    "reproduced_v23_combined_unresolved_rows"
                ],
                "v23_residual_rows_with_hidden_age_difference": result[
                    "v23_residual_rows_with_hidden_age_difference"
                ],
                "v23_residual_rows_rescued_by_complete_first_arrival_map": result[
                    "v23_residual_rows_rescued_by_complete_first_arrival_map"
                ],
                "full_design_rows_unresolved_by_complete_first_arrival_map": result[
                    "full_design_rows_unresolved_by_complete_first_arrival_map"
                ],
                "summary_by_design": result["summary_by_design"],
                "fingerprint": result["fingerprint"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
