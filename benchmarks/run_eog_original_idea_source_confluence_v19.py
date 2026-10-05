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
from benchmarks.run_eog_original_idea_source_placement_v18 import (
    DESIGNS,
    _candidate_sources,
    _source_sets,
)


PROTOCOL = ROOT / "validation/eog_original_idea_source_confluence_v19/protocol_v19.json"
RULE = "relative_edge_q70"
SOURCE_COUNTS = (2, 3)


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


def _normalized_potential_map(permissive, outlet):
    values = {node: float(_potential(node, outlet)) for node in permissive}
    lo = min(values.values())
    hi = max(values.values())
    if hi <= lo:
        raise RuntimeError("flow-potential range collapsed")
    return {
        node: (value - lo) / (hi - lo)
        for node, value in values.items()
    }


def _source_set_metrics(graph, sources, potential_norm):
    distances = {
        source: _bfs_distances(graph, source)
        for source in sources
    }
    union = frozenset().union(
        *(frozenset(dist) for dist in distances.values())
    )
    if not union:
        raise RuntimeError("empty source-reachable union")

    node_rows = []
    earliest_subset_violations = 0
    for node in sorted(union):
        static_origins = tuple(
            source for source in sources if node in distances[source]
        )
        if not static_origins:
            raise RuntimeError("union node has no static source")
        min_depth = min(int(distances[source][node]) for source in static_origins)
        earliest_origins = tuple(
            source
            for source in static_origins
            if int(distances[source][node]) == min_depth
        )
        if (
            not earliest_origins
            or not set(earliest_origins).issubset(static_origins)
        ):
            earliest_subset_violations += 1

        node_rows.append(
            {
                "node_id": _node_id(node),
                "static_origin_count": len(static_origins),
                "earliest_origin_count": len(earliest_origins),
                "static_ambiguous": len(static_origins) >= 2,
                "temporally_resolved": (
                    len(static_origins) >= 2 and len(earliest_origins) == 1
                ),
                "residual_first_passage_ambiguous": len(earliest_origins) >= 2,
                "first_passage_depth": min_depth,
                "normalized_flow_potential": float(potential_norm[node]),
            }
        )

    static_ambiguous = [row for row in node_rows if row["static_ambiguous"]]
    static_unique = [row for row in node_rows if not row["static_ambiguous"]]
    temporally_resolved = [
        row for row in node_rows if row["temporally_resolved"]
    ]
    residual = [
        row for row in node_rows
        if row["residual_first_passage_ambiguous"]
    ]

    return {
        "source_ids": [_node_id(source) for source in sources],
        "union_reachable_node_count": len(node_rows),
        "static_ambiguous_node_count": len(static_ambiguous),
        "static_ambiguous_fraction": len(static_ambiguous) / len(node_rows),
        "static_unique_node_count": len(static_unique),
        "temporally_resolved_node_count": len(temporally_resolved),
        "temporally_resolved_fraction_of_static_ambiguity": (
            None
            if not static_ambiguous
            else len(temporally_resolved) / len(static_ambiguous)
        ),
        "residual_ambiguous_node_count": len(residual),
        "residual_ambiguity_fraction": len(residual) / len(node_rows),
        "mean_normalized_potential_static_ambiguous": (
            None
            if not static_ambiguous
            else float(
                np.mean(
                    [row["normalized_flow_potential"] for row in static_ambiguous]
                )
            )
        ),
        "mean_normalized_potential_static_unique": (
            None
            if not static_unique
            else float(
                np.mean(
                    [row["normalized_flow_potential"] for row in static_unique]
                )
            )
        ),
        "confluence_front_potential": (
            None
            if not static_ambiguous
            else max(
                row["normalized_flow_potential"] for row in static_ambiguous
            )
        ),
        "earliest_origin_subset_violation_count": earliest_subset_violations,
        "node_rows": node_rows,
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

    potential_norm = _normalized_potential_map(
        base["permissive"],
        outlet,
    )

    for design in DESIGNS:
        row["designs"][design] = {}
        previous_ambiguous = -1
        for k in SOURCE_COUNTS:
            metrics = _source_set_metrics(
                graph,
                source_sets[design][k],
                potential_norm,
            )
            if metrics["static_ambiguous_node_count"] < previous_ambiguous:
                raise RuntimeError(
                    "adding a source reduced static ambiguous-node count"
                )
            previous_ambiguous = metrics["static_ambiguous_node_count"]
            row["designs"][design][str(k)] = metrics

    return row


def _mean(values):
    vals = [float(value) for value in values]
    return None if not vals else float(np.mean(vals))


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != (
        "frozen_before_source_confluence_benchmark_implementation_and_scoring"
    ):
        raise RuntimeError("v19 protocol is not frozen")

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
        raise RuntimeError("no eligible v19 rows")

    any_static_ambiguity = any(
        row["designs"][design][str(k)]["static_ambiguous_node_count"] > 0
        for row in eligible
        for design in DESIGNS
        for k in SOURCE_COUNTS
    )

    p2_contrasts = {}
    p3_detail = {}
    for k in SOURCE_COUNTS:
        key = str(k)
        p2_contrasts[key] = (
            _mean(
                row["designs"]["clustered"][key]["static_ambiguous_fraction"]
                for row in eligible
            )
            - _mean(
                row["designs"]["dispersed"][key]["static_ambiguous_fraction"]
                for row in eligible
            )
        )

    p3_supported = True
    for design in DESIGNS:
        p3_detail[design] = {}
        for k in SOURCE_COUNTS:
            key = str(k)
            static_mean = _mean(
                row["designs"][design][key]["static_ambiguous_fraction"]
                for row in eligible
            )
            residual_mean = _mean(
                row["designs"][design][key]["residual_ambiguity_fraction"]
                for row in eligible
            )
            rows_with_resolution = sum(
                row["designs"][design][key]["temporally_resolved_node_count"] > 0
                for row in eligible
            )
            strict = (
                rows_with_resolution > 0
                and residual_mean is not None
                and static_mean is not None
                and residual_mean < static_mean
            )
            p3_supported = p3_supported and strict
            p3_detail[design][key] = {
                "mean_static_ambiguous_fraction": static_mean,
                "mean_residual_ambiguity_fraction": residual_mean,
                "rows_with_positive_temporal_resolution": rows_with_resolution,
                "strict_reduction": strict,
            }

    residual_any = any(
        row["designs"][design][str(k)][
            "residual_ambiguous_node_count"
        ] > 0
        for row in eligible
        for design in DESIGNS
        for k in SOURCE_COUNTS
    )

    # P5 pools node-level potential values only from source-sets that contain both
    # unique and ambiguous static provenance classes.
    ambiguous_potential = []
    unique_potential = []
    p5_source_sets = 0
    subset_violations = 0
    monotonic_ambiguous_violations = 0
    for row in eligible:
        for design in DESIGNS:
            counts = []
            for k in SOURCE_COUNTS:
                metrics = row["designs"][design][str(k)]
                counts.append(metrics["static_ambiguous_node_count"])
                subset_violations += metrics[
                    "earliest_origin_subset_violation_count"
                ]
                node_rows = metrics["node_rows"]
                if (
                    metrics["static_ambiguous_node_count"] > 0
                    and metrics["static_unique_node_count"] > 0
                ):
                    p5_source_sets += 1
                    ambiguous_potential.extend(
                        node["normalized_flow_potential"]
                        for node in node_rows
                        if node["static_ambiguous"]
                    )
                    unique_potential.extend(
                        node["normalized_flow_potential"]
                        for node in node_rows
                        if not node["static_ambiguous"]
                    )
            monotonic_ambiguous_violations += sum(
                a > b for a, b in zip(counts[:-1], counts[1:], strict=True)
            )

    p5_ambiguous_mean = _mean(ambiguous_potential)
    p5_unique_mean = _mean(unique_potential)
    p5_contrast = (
        None
        if p5_ambiguous_mean is None or p5_unique_mean is None
        else p5_ambiguous_mean - p5_unique_mean
    )

    front_differences = []
    rows_with_both_two_source_confluence = 0
    for row in eligible:
        clustered = row["designs"]["clustered"]["2"][
            "confluence_front_potential"
        ]
        dispersed = row["designs"]["dispersed"]["2"][
            "confluence_front_potential"
        ]
        if clustered is not None and dispersed is not None:
            rows_with_both_two_source_confluence += 1
            front_differences.append(clustered - dispersed)
    p8_contrast = _mean(front_differences)

    summary = {}
    for design in DESIGNS:
        summary[design] = {}
        for k in SOURCE_COUNTS:
            key = str(k)
            summary[design][key] = {
                "mean_static_ambiguous_fraction": _mean(
                    row["designs"][design][key]["static_ambiguous_fraction"]
                    for row in eligible
                ),
                "mean_temporally_resolved_fraction_of_static_ambiguity": _mean(
                    row["designs"][design][key][
                        "temporally_resolved_fraction_of_static_ambiguity"
                    ]
                    for row in eligible
                    if row["designs"][design][key][
                        "temporally_resolved_fraction_of_static_ambiguity"
                    ]
                    is not None
                ),
                "mean_residual_ambiguity_fraction": _mean(
                    row["designs"][design][key]["residual_ambiguity_fraction"]
                    for row in eligible
                ),
                "rows_with_static_confluence": sum(
                    row["designs"][design][key]["static_ambiguous_node_count"] > 0
                    for row in eligible
                ),
                "rows_with_irreducible_first_passage_ambiguity": sum(
                    row["designs"][design][key][
                        "residual_ambiguous_node_count"
                    ] > 0
                    for row in eligible
                ),
            }

    verdicts = {
        "P1_static_distribution_loses_source_provenance": (
            "SUPPORTED" if any_static_ambiguity else "REFUTED"
        ),
        "P2_clustered_sources_create_more_static_provenance_ambiguity": (
            "SUPPORTED"
            if all(value > 0 for value in p2_contrasts.values())
            else "REFUTED"
        ),
        "P3_first_passage_timing_recovers_source_information": (
            "SUPPORTED" if p3_supported else "REFUTED"
        ),
        "P4_first_passage_does_not_always_restore_unique_source_identity": (
            "SUPPORTED" if residual_any else "REFUTED"
        ),
        "P5_confluence_is_downstream_biased": (
            "SUPPORTED"
            if p5_contrast is not None and p5_contrast < 0
            else "REFUTED"
        ),
        "P6_more_sources_never_reduce_static_ambiguous_node_count": (
            "SUPPORTED"
            if monotonic_ambiguous_violations == 0
            else "REFUTED"
        ),
        "P7_earliest_origin_set_is_nested_inside_static_origin_set": (
            "SUPPORTED" if subset_violations == 0 else "REFUTED"
        ),
        "P8_clustered_sources_converge_earlier_upstream": (
            "SUPPORTED"
            if (
                rows_with_both_two_source_confluence > 0
                and p8_contrast is not None
                and p8_contrast > 0
            )
            else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_source_confluence.result.v19",
        "row_count": len(rows),
        "eligible_row_count": len(eligible),
        "non_estimable_row_count": len(rows) - len(eligible),
        "predeclared_verdicts": verdicts,
        "summary_by_design_and_source_count": summary,
        "clustered_minus_dispersed_static_ambiguity_fraction": p2_contrasts,
        "temporal_resolution_detail": p3_detail,
        "P5_pooled_potential": {
            "qualifying_source_set_count": p5_source_sets,
            "mean_ambiguous_normalized_potential": p5_ambiguous_mean,
            "mean_unique_normalized_potential": p5_unique_mean,
            "ambiguous_minus_unique": p5_contrast,
        },
        "P6_monotonic_static_ambiguity_violation_count": (
            monotonic_ambiguous_violations
        ),
        "P7_earliest_subset_violation_count": subset_violations,
        "P8_two_source_confluence_front": {
            "rows_with_both_designs_confluent": rows_with_both_two_source_confluence,
            "mean_clustered_minus_dispersed_front_potential": p8_contrast,
        },
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
                "summary_by_design_and_source_count": result[
                    "summary_by_design_and_source_count"
                ],
                "clustered_minus_dispersed_static_ambiguity_fraction": result[
                    "clustered_minus_dispersed_static_ambiguity_fraction"
                ],
                "P5_pooled_potential": result["P5_pooled_potential"],
                "P8_two_source_confluence_front": result[
                    "P8_two_source_confluence_front"
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
