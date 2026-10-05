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
from benchmarks.run_eog_original_idea_source_history_memory_v21 import (
    ACTIVATION_HISTORIES,
)


PROTOCOL = ROOT / "validation/eog_original_idea_history_observability_v22/protocol_v22.json"
SNAPSHOT_TIMES = (4, 5, 6, 8)


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


def _distances(graph, sources):
    return {source: _bfs_distances(graph, source) for source in sources}


def _arrival_structure(distances, sources, activation_times):
    activation = {
        source: int(time)
        for source, time in zip(sources, activation_times, strict=True)
    }
    equilibrium_union = frozenset().union(
        *(frozenset(distances[source]) for source in sources)
    )
    earliest_map = {}
    first_arrival = {}
    for node in sorted(equilibrium_union):
        arrivals = {
            source: activation[source] + int(distances[source][node])
            for source in sources
            if node in distances[source]
        }
        first = min(arrivals.values())
        earliest = tuple(
            source
            for source in sources
            if source in arrivals and arrivals[source] == first
        )
        first_arrival[node] = first
        earliest_map[node] = earliest
    return equilibrium_union, first_arrival, earliest_map


def _snapshot_signature(
    equilibrium_union,
    first_arrival,
    source_set,
    time,
):
    return tuple(
        _node_id(node)
        for node in sorted(equilibrium_union)
        if node not in source_set
        and int(first_arrival[node]) <= int(time)
    )


def _provenance_target(equilibrium_union, earliest_map):
    return tuple(
        (
            _node_id(node),
            tuple(_node_id(source) for source in earliest_map[node]),
        )
        for node in sorted(equilibrium_union)
    )


def _minimum_snapshot_design(histories, target_by_history):
    names = tuple(sorted(histories))
    target_values = {target_by_history[name] for name in names}
    if len(target_values) == 1:
        return {
            "minimum_size": 0,
            "minimum_times": (),
            "identified": True,
        }

    def sufficient(times):
        signatures = {}
        for name in names:
            signature = tuple(
                histories[name]["snapshots"][time]
                for time in times
            )
            incumbent = signatures.get(signature)
            target = target_by_history[name]
            if incumbent is None:
                signatures[signature] = target
            elif incumbent != target:
                return False
        return True

    for size in range(1, len(SNAPSHOT_TIMES) + 1):
        for combo in itertools.combinations(SNAPSHOT_TIMES, size):
            if sufficient(combo):
                return {
                    "minimum_size": size,
                    "minimum_times": tuple(combo),
                    "identified": True,
                }
    return {
        "minimum_size": None,
        "minimum_times": None,
        "identified": False,
    }


def _single_snapshot_identifies_full_history(histories, time):
    signatures = [
        histories[name]["snapshots"][time]
        for name in sorted(histories)
    ]
    return len(set(signatures)) == len(signatures)


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

    equilibrium_sets = {
        histories[name]["equilibrium_union"]
        for name in histories
    }
    if len(equilibrium_sets) != 1:
        raise RuntimeError("equilibrium occupancy differs across activation histories")

    full_target = {name: name for name in histories}
    provenance_target = {
        name: histories[name]["provenance_target"]
        for name in histories
    }
    full_plan = _minimum_snapshot_design(histories, full_target)
    provenance_plan = _minimum_snapshot_design(histories, provenance_target)

    one_snapshot = {
        time: _single_snapshot_identifies_full_history(histories, time)
        for time in SNAPSHOT_TIMES
    }

    equilibrium_signature = tuple(
        _node_id(node)
        for node in sorted(next(iter(equilibrium_sets)))
        if node not in source_set
    )
    equilibrium_signatures = {
        name: equilibrium_signature for name in histories
    }

    return {
        "design": design,
        "source_ids": [_node_id(source) for source in sources],
        "history_count": len(histories),
        "equilibrium_snapshot_identical": (
            len(set(equilibrium_signatures.values())) == 1
        ),
        "full_history": full_plan,
        "provenance_class": provenance_plan,
        "single_snapshot_identifies_full_history": {
            str(time): bool(value)
            for time, value in one_snapshot.items()
        },
        "provenance_class_count": len(set(provenance_target.values())),
        "snapshot_class_counts": {
            str(time): len(
                {
                    histories[name]["snapshots"][time]
                    for name in histories
                }
            )
            for time in SNAPSHOT_TIMES
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


def _burden_value(value):
    return math.inf if value is None else float(value)


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != (
        "frozen_before_history_observability_benchmark_implementation_and_scoring"
    ):
        raise RuntimeError("v22 protocol is not frozen")

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
        raise RuntimeError("no eligible v22 rows")

    equilibrium_violations = sum(
        not row["designs"][design]["equilibrium_snapshot_identical"]
        for row in eligible
        for design in DESIGNS
    )

    summary = {}
    for design in DESIGNS:
        drows = [row["designs"][design] for row in eligible]
        finite_full = [
            int(drow["full_history"]["minimum_size"])
            for drow in drows
            if drow["full_history"]["minimum_size"] is not None
        ]
        finite_prov = [
            int(drow["provenance_class"]["minimum_size"])
            for drow in drows
            if drow["provenance_class"]["minimum_size"] is not None
        ]
        summary[design] = {
            "full_history_identifiable_rows": sum(
                drow["full_history"]["identified"] for drow in drows
            ),
            "full_history_unresolved_rows": sum(
                not drow["full_history"]["identified"] for drow in drows
            ),
            "mean_full_history_minimum_snapshots_among_identifiable": (
                _mean(finite_full)
            ),
            "provenance_identifiable_rows": sum(
                drow["provenance_class"]["identified"] for drow in drows
            ),
            "mean_provenance_minimum_snapshots_among_identifiable": (
                _mean(finite_prov)
            ),
            "one_snapshot_full_history_rows": sum(
                drow["full_history"]["minimum_size"] == 1
                for drow in drows
            ),
            "zero_snapshot_provenance_rows": sum(
                drow["provenance_class"]["minimum_size"] == 0
                for drow in drows
            ),
            "canonical_full_history_minimum_time_counts": {
                str(time): sum(
                    drow["full_history"]["minimum_times"] is not None
                    and len(drow["full_history"]["minimum_times"]) == 1
                    and drow["full_history"]["minimum_times"][0] == time
                    for drow in drows
                )
                for time in SNAPSHOT_TIMES
            },
        }

    q3_contrast = (
        summary["dispersed"][
            "mean_full_history_minimum_snapshots_among_identifiable"
        ]
        - summary["clustered"][
            "mean_full_history_minimum_snapshots_among_identifiable"
        ]
        if (
            summary["dispersed"][
                "mean_full_history_minimum_snapshots_among_identifiable"
            ]
            is not None
            and summary["clustered"][
                "mean_full_history_minimum_snapshots_among_identifiable"
            ]
            is not None
        )
        else None
    )

    q4_violations = 0
    strict_target_savings = 0
    earlier_resolves_t8_fails = 0
    for row in eligible:
        for design in DESIGNS:
            drow = row["designs"][design]
            full = _burden_value(drow["full_history"]["minimum_size"])
            prov = _burden_value(drow["provenance_class"]["minimum_size"])
            if prov > full:
                q4_violations += 1
            if prov < full:
                strict_target_savings += 1

            if (
                any(
                    drow["single_snapshot_identifies_full_history"][str(time)]
                    for time in (4, 5, 6)
                )
                and not drow["single_snapshot_identifies_full_history"]["8"]
            ):
                earlier_resolves_t8_fails += 1

    q2_rows = sum(
        row["designs"][design]["full_history"]["identified"]
        for row in eligible
        for design in DESIGNS
    )
    q6_rows = sum(
        row["designs"][design]["full_history"]["minimum_size"] == 1
        for row in eligible
        for design in DESIGNS
    )
    q7_rows = sum(
        not row["designs"][design]["full_history"]["identified"]
        for row in eligible
        for design in DESIGNS
    )

    verdicts = {
        "Q1_equilibrium_occupancy_snapshot_has_zero_history_information": (
            "SUPPORTED" if equilibrium_violations == 0 else "REFUTED"
        ),
        "Q2_post_activation_transients_can_identify_history": (
            "SUPPORTED" if q2_rows > 0 else "REFUTED"
        ),
        "Q3_dispersed_sources_make_history_more_observable": (
            "SUPPORTED"
            if q3_contrast is not None and q3_contrast < 0
            else "REFUTED"
        ),
        "Q4_provenance_target_is_never_harder_than_full_history_identity": (
            "SUPPORTED" if q4_violations == 0 else "REFUTED"
        ),
        "Q5_target_compression_saves_snapshots_somewhere": (
            "SUPPORTED" if strict_target_savings > 0 else "REFUTED"
        ),
        "Q6_one_post_activation_snapshot_is_sometimes_sufficient": (
            "SUPPORTED" if q6_rows > 0 else "REFUTED"
        ),
        "Q7_history_can_remain_observationally_unresolved": (
            "SUPPORTED" if q7_rows > 0 else "REFUTED"
        ),
        "Q8_later_snapshots_are_not_monotonically_more_informative": (
            "SUPPORTED" if earlier_resolves_t8_fails > 0 else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_history_observability.result.v22",
        "row_count": len(rows),
        "eligible_row_count": len(eligible),
        "predeclared_verdicts": verdicts,
        "summary_by_design": summary,
        "equilibrium_snapshot_violation_count": equilibrium_violations,
        "Q3_dispersed_minus_clustered_mean_minimum_snapshot_count": q3_contrast,
        "Q4_target_burden_violation_count": q4_violations,
        "Q5_strict_target_saving_design_row_count": strict_target_savings,
        "Q6_one_snapshot_history_identification_design_row_count": q6_rows,
        "Q7_full_history_unresolved_design_row_count": q7_rows,
        "Q8_earlier_resolves_while_t8_fails_design_row_count": (
            earlier_resolves_t8_fails
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
                "summary_by_design": result["summary_by_design"],
                "Q3_dispersed_minus_clustered_mean_minimum_snapshot_count": result[
                    "Q3_dispersed_minus_clustered_mean_minimum_snapshot_count"
                ],
                "Q5_strict_target_saving_design_row_count": result[
                    "Q5_strict_target_saving_design_row_count"
                ],
                "Q7_full_history_unresolved_design_row_count": result[
                    "Q7_full_history_unresolved_design_row_count"
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
