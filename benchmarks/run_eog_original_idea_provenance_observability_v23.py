#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import itertools
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


PROTOCOL = ROOT / "validation/eog_original_idea_provenance_observability_v23/protocol_v23.json"
LIBRARIES = ("occupancy_only", "provenance_only", "combined")


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


def _target_pairs(history_names, target_by_history):
    pairs = []
    for i, left in enumerate(history_names):
        for right in history_names[i + 1 :]:
            if target_by_history[left] != target_by_history[right]:
                pairs.append((left, right))
    return tuple(pairs)


def _minimum_action_design(action_values, target_by_history):
    names = tuple(sorted(target_by_history))
    pairs = _target_pairs(names, target_by_history)
    if not pairs:
        return {
            "identified": True,
            "minimum_size": 0,
            "minimum_action_ids": (),
            "discordant_pair_count": 0,
        }

    pair_index = {pair: i for i, pair in enumerate(pairs)}
    full_mask = (1 << len(pairs)) - 1
    mask_to_action = {}
    for action_id in sorted(action_values):
        values = action_values[action_id]
        mask = 0
        for pair, i in pair_index.items():
            left, right = pair
            if values[left] != values[right]:
                mask |= 1 << i
        if mask == 0:
            continue
        incumbent = mask_to_action.get(mask)
        if incumbent is None or action_id < incumbent:
            mask_to_action[mask] = action_id

    if not mask_to_action:
        return {
            "identified": False,
            "minimum_size": None,
            "minimum_action_ids": None,
            "discordant_pair_count": len(pairs),
        }

    actions = tuple(sorted((aid, mask) for mask, aid in mask_to_action.items()))
    coverable = 0
    for _, mask in actions:
        coverable |= mask
    if coverable != full_mask:
        return {
            "identified": False,
            "minimum_size": None,
            "minimum_action_ids": None,
            "discordant_pair_count": len(pairs),
        }

    for size in range(1, min(len(pairs), len(actions)) + 1):
        for combo in itertools.combinations(actions, size):
            covered = 0
            ids = []
            for action_id, mask in combo:
                covered |= mask
                ids.append(action_id)
            if covered == full_mask:
                return {
                    "identified": True,
                    "minimum_size": size,
                    "minimum_action_ids": tuple(sorted(ids)),
                    "discordant_pair_count": len(pairs),
                }

    raise RuntimeError("coverable target pair universe had no exact cover")


def _static_origin_set(distances, sources, node):
    return tuple(
        source
        for source in sources
        if node in distances[source]
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
        raise RuntimeError("equilibrium union differs across histories")
    equilibrium_union = next(iter(equilibrium_sets))
    non_source_nodes = tuple(
        node for node in sorted(equilibrium_union)
        if node not in source_set
    )

    occupancy_actions = {
        f"O_t{time}": {
            name: histories[name]["snapshots"][time]
            for name in histories
        }
        for time in SNAPSHOT_TIMES
    }
    provenance_actions = {
        f"P_{_node_id(node)}": {
            name: tuple(
                _node_id(source)
                for source in histories[name]["earliest_map"][node]
            )
            for name in histories
        }
        for node in non_source_nodes
    }
    combined_actions = {**occupancy_actions, **provenance_actions}
    libraries = {
        "occupancy_only": occupancy_actions,
        "provenance_only": provenance_actions,
        "combined": combined_actions,
    }

    full_target = {name: name for name in histories}
    provenance_target = {
        name: histories[name]["provenance_target"]
        for name in histories
    }

    plans = {}
    for library_name, actions in libraries.items():
        plans[library_name] = {
            "full_history": _minimum_action_design(actions, full_target),
            "provenance_class": _minimum_action_design(actions, provenance_target),
        }

    unique_origin_nodes = []
    confluence_nodes = []
    informative_unique = 0
    informative_confluence = 0
    for node in non_source_nodes:
        static_origins = _static_origin_set(distances, sources, node)
        action_id = f"P_{_node_id(node)}"
        values = set(provenance_actions[action_id].values())
        informative = len(values) > 1
        if len(static_origins) == 1:
            unique_origin_nodes.append(node)
            informative_unique += int(informative)
        elif len(static_origins) >= 2:
            confluence_nodes.append(node)
            informative_confluence += int(informative)

    return {
        "design": design,
        "source_ids": [_node_id(source) for source in sources],
        "history_count": len(histories),
        "non_source_equilibrium_node_count": len(non_source_nodes),
        "static_unique_origin_node_count": len(unique_origin_nodes),
        "static_confluence_node_count": len(confluence_nodes),
        "informative_unique_origin_provenance_action_count": informative_unique,
        "informative_confluence_provenance_action_count": informative_confluence,
        "provenance_class_count": len(set(provenance_target.values())),
        "plans": plans,
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
    vals = [float(v) for v in values]
    return None if not vals else float(np.mean(vals))


def _burden(value):
    return math.inf if value is None else float(value)


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != (
        "frozen_before_provenance_observability_benchmark_implementation_and_scoring"
    ):
        raise RuntimeError("v23 protocol is not frozen")

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
        raise RuntimeError("no eligible v23 rows")

    design_rows = [
        row["designs"][design]
        for row in eligible
        for design in DESIGNS
    ]

    summary_by_library = {}
    for library in LIBRARIES:
        full_rows = [drow["plans"][library]["full_history"] for drow in design_rows]
        prov_rows = [drow["plans"][library]["provenance_class"] for drow in design_rows]
        summary_by_library[library] = {
            "full_history_identifiable_rows": sum(row["identified"] for row in full_rows),
            "full_history_unresolved_rows": sum(not row["identified"] for row in full_rows),
            "mean_full_history_minimum_burden_among_identifiable": _mean(
                row["minimum_size"] for row in full_rows
                if row["minimum_size"] is not None
            ),
            "provenance_identifiable_rows": sum(row["identified"] for row in prov_rows),
            "mean_provenance_minimum_burden_among_identifiable": _mean(
                row["minimum_size"] for row in prov_rows
                if row["minimum_size"] is not None
            ),
        }

    occupancy_only_ident = []
    provenance_only_ident = []
    combined_ident = []
    occupancy_only_not_provenance = 0
    provenance_only_not_occupancy = 0
    provenance_rescues_occupancy_unresolved = 0
    combined_rescues_occupancy_unresolved = 0
    combined_unresolved = 0
    target_burden_violations = 0
    strict_target_savings = 0
    unique_origin_info_violations = 0
    informative_confluence_actions = 0

    for drow in design_rows:
        occ = drow["plans"]["occupancy_only"]["full_history"]
        prov = drow["plans"]["provenance_only"]["full_history"]
        comb = drow["plans"]["combined"]["full_history"]
        occupancy_only_ident.append(bool(occ["identified"]))
        provenance_only_ident.append(bool(prov["identified"]))
        combined_ident.append(bool(comb["identified"]))

        occupancy_only_not_provenance += int(occ["identified"] and not prov["identified"])
        provenance_only_not_occupancy += int(prov["identified"] and not occ["identified"])
        provenance_rescues_occupancy_unresolved += int(
            (not occ["identified"]) and prov["identified"]
        )
        combined_rescues_occupancy_unresolved += int(
            (not occ["identified"]) and comb["identified"]
        )
        combined_unresolved += int(not comb["identified"])

        unique_origin_info_violations += int(
            drow["informative_unique_origin_provenance_action_count"] != 0
        )
        informative_confluence_actions += int(
            drow["informative_confluence_provenance_action_count"] > 0
        )

        for library in LIBRARIES:
            full = drow["plans"][library]["full_history"]
            provenance = drow["plans"][library]["provenance_class"]
            if _burden(provenance["minimum_size"]) > _burden(full["minimum_size"]):
                target_burden_violations += 1
            if _burden(provenance["minimum_size"]) < _burden(full["minimum_size"]):
                strict_target_savings += 1

    occ_count = sum(occupancy_only_ident)
    prov_count = sum(provenance_only_ident)
    comb_count = sum(combined_ident)

    verdicts = {
        "R1_provenance_rescues_some_occupancy_unresolved_histories": (
            "SUPPORTED" if provenance_rescues_occupancy_unresolved > 0 else "REFUTED"
        ),
        "R2_occupancy_and_provenance_are_complementary": (
            "SUPPORTED"
            if occupancy_only_not_provenance > 0 and provenance_only_not_occupancy > 0
            else "REFUTED"
        ),
        "R3_combined_library_identifies_strictly_more_histories": (
            "SUPPORTED"
            if comb_count > occ_count and comb_count > prov_count
            else "REFUTED"
        ),
        "R4_provenance_target_is_never_harder_than_full_history": (
            "SUPPORTED" if target_burden_violations == 0 else "REFUTED"
        ),
        "R5_unique_origin_provenance_tags_have_zero_history_information": (
            "SUPPORTED" if unique_origin_info_violations == 0 else "REFUTED"
        ),
        "R6_confluence_provenance_tags_can_reveal_history": (
            "SUPPORTED" if informative_confluence_actions > 0 else "REFUTED"
        ),
        "R7_full_combined_evidence_can_still_leave_history_unresolved": (
            "SUPPORTED" if combined_unresolved > 0 else "REFUTED"
        ),
        "R8_provenance_evidence_is_target_compressible": (
            "SUPPORTED" if strict_target_savings > 0 else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_provenance_observability.result.v23",
        "row_count": len(rows),
        "eligible_row_count": len(eligible),
        "design_row_count": len(design_rows),
        "predeclared_verdicts": verdicts,
        "summary_by_library": summary_by_library,
        "occupancy_only_not_provenance_full_history_rows": occupancy_only_not_provenance,
        "provenance_only_not_occupancy_full_history_rows": provenance_only_not_occupancy,
        "provenance_rescued_v22_unresolved_rows": provenance_rescues_occupancy_unresolved,
        "combined_rescued_v22_unresolved_rows": combined_rescues_occupancy_unresolved,
        "combined_full_history_unresolved_rows": combined_unresolved,
        "target_burden_violation_count": target_burden_violations,
        "strict_provenance_target_saving_count": strict_target_savings,
        "unique_origin_information_violation_count": unique_origin_info_violations,
        "design_rows_with_informative_confluence_provenance_action": (
            informative_confluence_actions
        ),
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
                "summary_by_library": result["summary_by_library"],
                "occupancy_only_not_provenance_full_history_rows": result[
                    "occupancy_only_not_provenance_full_history_rows"
                ],
                "provenance_only_not_occupancy_full_history_rows": result[
                    "provenance_only_not_occupancy_full_history_rows"
                ],
                "combined_full_history_unresolved_rows": result[
                    "combined_full_history_unresolved_rows"
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
