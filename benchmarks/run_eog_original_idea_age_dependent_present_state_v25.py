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


PROTOCOL = ROOT / "validation/eog_original_idea_age_dependent_present_state_v25/protocol_v25.json"
MATURATION_LAG = 2


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


def _mature_target(non_source_nodes, first_arrival, horizon):
    if horizon is None:
        return ()
    return tuple(
        (
            _node_id(node),
            bool(int(horizon) - int(first_arrival[node]) >= MATURATION_LAG),
        )
        for node in non_source_nodes
    )


def _class_count(values_by_history):
    return len(set(values_by_history.values()))


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
    first_arrival = {
        name: _first_arrival_target(
            non_source_nodes,
            histories[name]["first_arrival"],
        )
        for name in histories
    }
    mature = {
        name: _mature_target(
            non_source_nodes,
            histories[name]["first_arrival"],
            common_horizon,
        )
        for name in histories
    }

    combined_class_count = _class_count(combined_signature)
    first_arrival_class_count = _class_count(first_arrival)
    mature_class_count = _class_count(mature)
    if mature_class_count > first_arrival_class_count:
        raise RuntimeError(
            "mature-state target is finer than first-arrival target"
        )

    # Residual aliases under complete v23 occupancy + provenance evidence.
    combined_groups = {}
    for history, signature in combined_signature.items():
        combined_groups.setdefault(signature, []).append(history)
    residual_groups = tuple(
        tuple(sorted(group))
        for group in combined_groups.values()
        if len(group) > 1
    )

    hidden_age_inside_residual = False
    mature_difference_inside_residual = False
    for group in residual_groups:
        age_values = {first_arrival[name] for name in group}
        mature_values = {mature[name] for name in group}
        hidden_age_inside_residual |= len(age_values) > 1
        mature_difference_inside_residual |= len(mature_values) > 1

    unique_nodes = 0
    confluence_nodes = 0
    unique_mature_memory_nodes = 0
    confluence_mature_memory_nodes = 0
    mature_disagreement_nodes = 0
    age_disagreement_nodes = 0

    for node in non_source_nodes:
        static_origins = _static_origin_set(distances, sources, node)
        mature_values = {
            dict(mature[name])[ _node_id(node) ]
            for name in histories
        }
        age_values = {
            int(histories[name]["first_arrival"][node])
            for name in histories
        }
        mature_memory = len(mature_values) > 1
        age_memory = len(age_values) > 1
        mature_disagreement_nodes += int(mature_memory)
        age_disagreement_nodes += int(age_memory)

        if len(static_origins) == 1:
            unique_nodes += 1
            unique_mature_memory_nodes += int(mature_memory)
        elif len(static_origins) >= 2:
            confluence_nodes += 1
            confluence_mature_memory_nodes += int(mature_memory)

    return {
        "design": design,
        "source_ids": [_node_id(source) for source in sources],
        "equilibrium_non_source_node_count": len(non_source_nodes),
        "common_horizon": common_horizon,
        "combined_observation_class_count": combined_class_count,
        "v23_combined_full_history_unresolved": combined_class_count < len(histories),
        "first_arrival_class_count": first_arrival_class_count,
        "first_arrival_exact_history_identified": (
            first_arrival_class_count == len(histories)
        ),
        "mature_state_class_count": mature_class_count,
        "mature_state_exact_history_identified": (
            mature_class_count == len(histories)
        ),
        "mature_state_identified_target": mature_class_count == 1,
        "hidden_age_difference_inside_v23_alias": hidden_age_inside_residual,
        "mature_state_difference_inside_v23_alias": (
            mature_difference_inside_residual
        ),
        "age_difference_but_mature_state_invariant": (
            first_arrival_class_count > 1 and mature_class_count == 1
        ),
        "age_disagreement_node_count": age_disagreement_nodes,
        "mature_disagreement_node_count": mature_disagreement_nodes,
        "mature_disagreement_fraction": (
            mature_disagreement_nodes / len(non_source_nodes)
            if non_source_nodes else 0.0
        ),
        "unique_origin_node_count": unique_nodes,
        "confluence_node_count": confluence_nodes,
        "unique_origin_mature_memory_node_count": (
            unique_mature_memory_nodes
        ),
        "confluence_mature_memory_node_count": (
            confluence_mature_memory_nodes
        ),
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
        "frozen_before_age_dependent_present_state_benchmark_implementation_and_scoring"
    ):
        raise RuntimeError("v25 protocol is not frozen")
    if int(protocol["frozen_age_dependent_process"]["maturation_lag"]) != MATURATION_LAG:
        raise RuntimeError("v25 maturation lag drift")

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
        if drow["hidden_age_difference_inside_v23_alias"]
    ]
    if len(v24_hidden_age) != 45:
        raise RuntimeError(
            f"expected 45 v24 hidden-age residual rows, got {len(v24_hidden_age)}"
        )

    hidden_age_with_mature_difference = sum(
        drow["mature_state_difference_inside_v23_alias"]
        for drow in v24_hidden_age
    )
    v23_residual_with_mature_difference = sum(
        drow["mature_state_difference_inside_v23_alias"]
        for drow in v23_residual
    )
    class_count_violations = sum(
        drow["mature_state_class_count"] > drow["first_arrival_class_count"]
        for drow in design_rows
    )
    exact_history_unresolved_but_mature_identified = sum(
        drow["first_arrival_class_count"] < 3
        and drow["mature_state_class_count"] == 1
        for drow in design_rows
    )
    unique_mature_rows = sum(
        drow["unique_origin_mature_memory_node_count"] > 0
        for drow in design_rows
    )
    confluence_mature_rows = sum(
        drow["confluence_mature_memory_node_count"] > 0
        for drow in design_rows
    )
    age_without_mature_rows = sum(
        drow["age_difference_but_mature_state_invariant"]
        for drow in design_rows
    )
    mature_memory_rows = sum(
        drow["mature_disagreement_node_count"] > 0
        for drow in design_rows
    )

    by_design = {}
    for design in DESIGNS:
        drows = [row["designs"][design] for row in eligible]
        by_design[design] = {
            "design_rows": len(drows),
            "mean_mature_disagreement_fraction": _mean(
                drow["mature_disagreement_fraction"] for drow in drows
            ),
            "rows_with_any_mature_state_memory": sum(
                drow["mature_disagreement_node_count"] > 0
                for drow in drows
            ),
            "rows_with_unique_origin_mature_memory": sum(
                drow["unique_origin_mature_memory_node_count"] > 0
                for drow in drows
            ),
            "rows_with_confluence_mature_memory": sum(
                drow["confluence_mature_memory_node_count"] > 0
                for drow in drows
            ),
            "rows_with_age_difference_but_mature_invariance": sum(
                drow["age_difference_but_mature_state_invariant"]
                for drow in drows
            ),
        }

    verdicts = {
        "F1_hidden_age_can_change_present_mature_state": (
            "SUPPORTED"
            if hidden_age_with_mature_difference > 0
            else "REFUTED"
        ),
        "F2_same_occupancy_and_provenance_can_hide_present_state_difference": (
            "SUPPORTED"
            if v23_residual_with_mature_difference > 0
            else "REFUTED"
        ),
        "F3_mature_state_is_coarser_than_first_arrival_state": (
            "SUPPORTED" if class_count_violations == 0 else "REFUTED"
        ),
        "F4_exact_history_can_be_unresolved_while_present_mature_state_is_identified": (
            "SUPPORTED"
            if exact_history_unresolved_but_mature_identified > 0
            else "REFUTED"
        ),
        "F5_unique_origin_zones_can_show_history_dependent_maturation": (
            "SUPPORTED" if unique_mature_rows > 0 else "REFUTED"
        ),
        "F6_confluence_zones_can_show_history_dependent_maturation": (
            "SUPPORTED" if confluence_mature_rows > 0 else "REFUTED"
        ),
        "F7_age_memory_need_not_be_present_state_memory": (
            "SUPPORTED" if age_without_mature_rows > 0 else "REFUTED"
        ),
        "F8_final_occupancy_can_be_identical_while_present_mature_state_differs": (
            "SUPPORTED" if mature_memory_rows > 0 else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_age_dependent_present_state.result.v25",
        "row_count": len(rows),
        "eligible_row_count": len(eligible),
        "design_row_count": len(design_rows),
        "maturation_lag": MATURATION_LAG,
        "predeclared_verdicts": verdicts,
        "reproduced_v23_combined_unresolved_rows": len(v23_residual),
        "reproduced_v24_hidden_age_residual_rows": len(v24_hidden_age),
        "v24_hidden_age_rows_with_mature_state_difference": (
            hidden_age_with_mature_difference
        ),
        "v23_residual_rows_with_mature_state_difference": (
            v23_residual_with_mature_difference
        ),
        "mature_vs_first_arrival_class_count_violation_count": (
            class_count_violations
        ),
        "exact_history_unresolved_but_mature_state_identified_rows": (
            exact_history_unresolved_but_mature_identified
        ),
        "design_rows_with_unique_origin_mature_memory": unique_mature_rows,
        "design_rows_with_confluence_mature_memory": confluence_mature_rows,
        "design_rows_with_age_difference_but_mature_state_invariant": (
            age_without_mature_rows
        ),
        "design_rows_with_any_mature_state_memory": mature_memory_rows,
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
                "v24_hidden_age_rows_with_mature_state_difference": result[
                    "v24_hidden_age_rows_with_mature_state_difference"
                ],
                "v23_residual_rows_with_mature_state_difference": result[
                    "v23_residual_rows_with_mature_state_difference"
                ],
                "exact_history_unresolved_but_mature_state_identified_rows": result[
                    "exact_history_unresolved_but_mature_state_identified_rows"
                ],
                "design_rows_with_age_difference_but_mature_state_invariant": result[
                    "design_rows_with_age_difference_but_mature_state_invariant"
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
