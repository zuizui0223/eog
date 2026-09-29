#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from independent_stochastic_bam_generator import (
    candidate_parameter_grid,
    make_landscape,
    simulate_associates,
    simulate_focal,
    truth_scenarios,
)
from run_independent_stochastic_bam_v3 import _build_eog_world
from eog.dynamic_island_reachability import propagate_dynamic_reachability
from eog.v2.world_reconstruction import forward_reachable_configuration


def _first_observed_steps(history: np.ndarray, horizon: int) -> dict[int, int]:
    prefix = history[: horizon + 1]
    observed = np.any(prefix, axis=0)
    result = {}
    for node in np.flatnonzero(observed):
        hits = np.flatnonzero(prefix[:, node])
        result[int(node)] = int(hits[0])
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "validation/independent_stochastic_temporal_v3_2/result_v3_2.json"
        ),
    )
    args = parser.parse_args()

    landscape = make_landscape()
    associates = simulate_associates(landscape)
    specs = candidate_parameter_grid()
    specs_by_id = {spec.scenario_id: spec for spec in specs}
    truths = truth_scenarios()

    worlds = tuple(
        sorted(
            (
                _build_eog_world(landscape, associates, spec)
                for spec in specs
            ),
            key=lambda world: world.world_id,
        )
    )
    world_ids = tuple(world.world_id for world in worlds)

    support_by_world = {}
    earliest_by_world = {}
    for world in worlds:
        support = forward_reachable_configuration(
            world,
            max_steps=40,
            support_tolerance=0.0,
        )
        support_by_world[world.world_id] = frozenset(support.reachable_ids)

        propagation = propagate_dynamic_reachability(
            world.operator,
            world.source_weight_mapping,
            max_steps=40,
            arrival_tolerance=0.0,
        )
        earliest_by_world[world.world_id] = tuple(
            None if int(step) < 0 else int(step)
            for step in propagation.first_arrival_step
        )

    static_classes = defaultdict(list)
    temporal_classes = defaultdict(list)
    for world_id in world_ids:
        static_key = support_by_world[world_id]
        static_classes[static_key].append(world_id)
        temporal_key = (
            support_by_world[world_id],
            earliest_by_world[world_id],
        )
        temporal_classes[temporal_key].append(world_id)

    static_m_equivalent_pairs = set()
    for ids in static_classes.values():
        ordered = sorted(ids)
        for i in range(len(ordered)):
            for j in range(i + 1, len(ordered)):
                left, right = ordered[i], ordered[j]
                if specs_by_id[left].movement_label != specs_by_id[right].movement_label:
                    static_m_equivalent_pairs.add((left, right))

    horizons = (5, 10, 20, 40)
    replicates = 64

    truth_retention_failures = 0
    temporal_expansion_violations = 0
    temporal_strict_gain_runs = 0
    realised_temporal_split_pairs = set()
    static_counts = defaultdict(lambda: defaultdict(list))
    temporal_counts = defaultdict(lambda: defaultdict(list))
    static_unique = defaultdict(lambda: defaultdict(int))
    temporal_unique = defaultdict(lambda: defaultdict(int))
    temporal_nonidentified_h40 = defaultdict(int)
    run_rows = []

    for scenario_id, truth_world_id in truths.items():
        spec = specs_by_id[truth_world_id]
        for replicate in range(replicates):
            realization = simulate_focal(
                landscape,
                associates,
                spec,
                replicate=replicate,
            )

            run_has_strict_gain = False
            for horizon in horizons:
                first_observed = _first_observed_steps(
                    realization.occupancy_history,
                    horizon,
                )
                observed_ids = {
                    landscape.node_ids[node]
                    for node in first_observed
                }

                static_compatible = tuple(
                    world_id
                    for world_id in world_ids
                    if observed_ids.issubset(support_by_world[world_id])
                )
                static_set = set(static_compatible)

                temporal_compatible = []
                for world_id in static_compatible:
                    earliest = earliest_by_world[world_id]
                    compatible = True
                    for node, observed_step in first_observed.items():
                        minimum_step = earliest[node]
                        if minimum_step is None or minimum_step > observed_step:
                            compatible = False
                            break
                    if compatible:
                        temporal_compatible.append(world_id)
                temporal_compatible = tuple(temporal_compatible)
                temporal_set = set(temporal_compatible)

                static_counts[scenario_id][horizon].append(
                    len(static_compatible)
                )
                temporal_counts[scenario_id][horizon].append(
                    len(temporal_compatible)
                )

                if truth_world_id not in temporal_set:
                    truth_retention_failures += 1
                if not temporal_set.issubset(static_set):
                    temporal_expansion_violations += 1
                if len(temporal_compatible) < len(static_compatible):
                    run_has_strict_gain = True

                if static_compatible == (truth_world_id,):
                    static_unique[scenario_id][horizon] += 1
                if temporal_compatible == (truth_world_id,):
                    temporal_unique[scenario_id][horizon] += 1

                for pair in static_m_equivalent_pairs:
                    left, right = pair
                    if left in static_set and right in static_set:
                        left_temporal = left in temporal_set
                        right_temporal = right in temporal_set
                        if left_temporal != right_temporal:
                            realised_temporal_split_pairs.add(pair)

                if horizon == 40 and len(temporal_compatible) > 1:
                    temporal_nonidentified_h40[scenario_id] += 1

                run_rows.append(
                    {
                        "scenario_id": scenario_id,
                        "replicate": replicate,
                        "horizon": horizon,
                        "static_compatible_count": len(static_compatible),
                        "temporal_compatible_count": len(temporal_compatible),
                        "observed_node_count": len(observed_ids),
                    }
                )

            if run_has_strict_gain:
                temporal_strict_gain_runs += 1

    static_class_dist = Counter(len(ids) for ids in static_classes.values())
    temporal_class_dist = Counter(len(ids) for ids in temporal_classes.values())

    median_static = {
        scenario_id: {
            str(h): float(np.median(values))
            for h, values in sorted(by_h.items())
        }
        for scenario_id, by_h in static_counts.items()
    }
    median_temporal = {
        scenario_id: {
            str(h): float(np.median(values))
            for h, values in sorted(by_h.items())
        }
        for scenario_id, by_h in temporal_counts.items()
    }
    static_unique_fraction = {
        scenario_id: {
            str(h): static_unique[scenario_id][h] / replicates
            for h in horizons
        }
        for scenario_id in truths
    }
    temporal_unique_fraction = {
        scenario_id: {
            str(h): temporal_unique[scenario_id][h] / replicates
            for h in horizons
        }
        for scenario_id in truths
    }

    verdicts = {
        "T1_temporal_truth_retention": (
            "SUPPORTED" if truth_retention_failures == 0 else "REFUTED"
        ),
        "T2_temporal_refines_static_positive": (
            "SUPPORTED"
            if temporal_expansion_violations == 0
            else "REFUTED"
        ),
        "T3_temporal_strict_gain": (
            "SUPPORTED" if temporal_strict_gain_runs > 0 else "REFUTED"
        ),
        "T4_movement_erasure_is_partly_reversed_by_time": (
            "SUPPORTED" if len(temporal_classes) > len(static_classes) else "REFUTED"
        ),
        "T5_temporal_witness_realization": (
            "SUPPORTED" if realised_temporal_split_pairs else "REFUTED"
        ),
        "T6_temporal_does_not_force_universal_identification": (
            "SUPPORTED"
            if any(value > 0 for value in temporal_nonidentified_h40.values())
            else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.independent_stochastic_temporal.result.v3_2",
        "parent_v3_result_fingerprint": (
            "bc558d10073133510f1b47b5651f6694d53f04771e757e9d8d9716ada72b18bf"
        ),
        "parent_v3_1_audit_fingerprint": (
            "ae797daf732af37740408fd5ca3cb4eb1c02f5345b9ffea651fbec5d05d79b2c"
        ),
        "candidate_world_count": len(worlds),
        "candidate_static_support_class_count": len(static_classes),
        "candidate_static_support_class_size_distribution": {
            str(size): count
            for size, count in sorted(static_class_dist.items())
        },
        "candidate_temporal_signature_class_count": len(temporal_classes),
        "candidate_temporal_signature_class_size_distribution": {
            str(size): count
            for size, count in sorted(temporal_class_dist.items())
        },
        "static_M_equivalent_pair_count": len(static_m_equivalent_pairs),
        "realised_temporal_split_pair_count": len(
            realised_temporal_split_pairs
        ),
        "realised_temporal_split_pairs": [
            list(pair) for pair in sorted(realised_temporal_split_pairs)
        ],
        "truth_retention_failures": truth_retention_failures,
        "temporal_expansion_violations": temporal_expansion_violations,
        "temporal_strict_gain_runs": temporal_strict_gain_runs,
        "planned_runs": len(truths) * replicates,
        "temporal_nonidentified_h40_runs_by_scenario": dict(
            temporal_nonidentified_h40
        ),
        "median_static_compatible_world_count": median_static,
        "median_temporal_compatible_world_count": median_temporal,
        "static_unique_truth_fraction": static_unique_fraction,
        "temporal_unique_truth_fraction": temporal_unique_fraction,
        "verdicts": verdicts,
        "runs": run_rows,
    }

    encoded = json.dumps(
        result,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    result["fingerprint"] = hashlib.sha256(encoded).hexdigest()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "candidate_static_support_class_count": result[
                    "candidate_static_support_class_count"
                ],
                "candidate_temporal_signature_class_count": result[
                    "candidate_temporal_signature_class_count"
                ],
                "static_M_equivalent_pair_count": result[
                    "static_M_equivalent_pair_count"
                ],
                "realised_temporal_split_pair_count": result[
                    "realised_temporal_split_pair_count"
                ],
                "truth_retention_failures": truth_retention_failures,
                "temporal_expansion_violations": temporal_expansion_violations,
                "temporal_strict_gain_runs": temporal_strict_gain_runs,
                "median_static_compatible_world_count": median_static,
                "median_temporal_compatible_world_count": median_temporal,
                "temporal_unique_truth_fraction": temporal_unique_fraction,
                "temporal_nonidentified_h40_runs_by_scenario": dict(
                    temporal_nonidentified_h40
                ),
                "verdicts": verdicts,
                "fingerprint": result["fingerprint"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
