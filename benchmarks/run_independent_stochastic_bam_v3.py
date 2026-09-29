#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
import argparse
import json
import math
from pathlib import Path
import sys

import numpy as np

from benchmarks.independent_stochastic_bam_generator import (
    abiotic_mask as generator_abiotic_mask,
    candidate_parameter_grid,
    make_landscape,
    simulate_associates,
    simulate_focal,
    truth_scenarios,
)
from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
)
from eog.v2.world_reconstruction import (
    FiniteWorld,
    forward_reachable_configuration,
    reconstruct_compatible_worlds,
)


def _crosses_barrier(landscape, i, j):
    x1, y1 = landscape.coordinates[i]
    x2, y2 = landscape.coordinates[j]
    if not (min(x1, x2) < landscape.barrier_col <= max(x1, x2)):
        return False
    return (
        not (
            int(round(y1)) == int(round(y2)) == landscape.barrier_gap_row
        )
    )


def _evaluator_abiotic_mask(landscape, spec):
    c = np.asarray(spec.niche_center, dtype=float)
    r = np.asarray(spec.niche_radius, dtype=float)
    scaled = (landscape.environment - c) / r
    return np.sum(scaled * scaled, axis=1) <= 1.0 + 1e-12


def _evaluator_biotic_mask(landscape, associates, mode):
    if mode == "none":
        return np.ones(len(landscape.node_ids), dtype=bool)
    if mode == "obligate_partner":
        return associates.partner_mask.copy()
    if mode == "antagonist_exclusion":
        return ~associates.antagonist_mask
    if mode == "partner_and_antagonist":
        return associates.partner_mask & ~associates.antagonist_mask
    raise ValueError(mode)


def _build_eog_world(landscape, associates, spec):
    A = _evaluator_abiotic_mask(landscape, spec)
    B = _evaluator_biotic_mask(landscape, associates, spec.biotic_mode)
    eligible = A & B
    source_index = landscape.node_ids.index(spec.source_id)
    if not bool(eligible[source_index]):
        raise ValueError(f"candidate source invalid: {spec.scenario_id}")

    edges = []
    n = len(landscape.node_ids)
    for i in range(n):
        if not bool(eligible[i]):
            continue
        for j in range(n):
            if i == j or not bool(eligible[j]):
                continue
            distance = float(
                np.linalg.norm(landscape.coordinates[i] - landscape.coordinates[j])
            )
            if distance > spec.step_radius + 1e-12:
                continue
            if not spec.barrier_permeable and _crosses_barrier(landscape, i, j):
                continue
            edges.append(
                DynamicReachabilityEdge(
                    source=i,
                    target=j,
                    geographic_support=1.0,
                )
            )

    operator = build_dynamic_transition_operator(
        landscape.node_ids,
        edges,
        loss_support=1.0,
    )
    return FiniteWorld(
        world_id=spec.scenario_id,
        operator=operator,
        source_ids=(spec.source_id,),
        analytical_variant="independent_stochastic_bam_v3",
    )


def _compatible_from_cached_support(observed_ids, reachable_by_world):
    observed = set(observed_ids)
    return tuple(
        world_id
        for world_id in sorted(reachable_by_world)
        if observed.issubset(reachable_by_world[world_id])
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "validation/independent_stochastic_bam_v3/result_v3.json"
        ),
    )
    args = parser.parse_args()

    landscape = make_landscape()
    associates = simulate_associates(landscape)
    n_nodes = len(landscape.node_ids)
    focal_source = "r4c0"
    source_index = landscape.node_ids.index(focal_source)

    design_stop_reasons = []
    partner_count = int(np.sum(associates.partner_mask))
    antagonist_count = int(np.sum(associates.antagonist_mask))
    if partner_count in (0, n_nodes):
        design_stop_reasons.append("partner_degenerate")
    if antagonist_count in (0, n_nodes):
        design_stop_reasons.append("antagonist_degenerate")
    if not bool(associates.partner_mask[source_index]):
        design_stop_reasons.append("partner_missing_focal_source")
    if bool(associates.antagonist_mask[source_index]):
        design_stop_reasons.append("antagonist_blocks_focal_source")

    specs = candidate_parameter_grid()
    specs_by_id = {spec.scenario_id: spec for spec in specs}
    truths = truth_scenarios()

    worlds = []
    candidate_build_failures = []
    for spec in specs:
        try:
            worlds.append(_build_eog_world(landscape, associates, spec))
        except ValueError as exc:
            candidate_build_failures.append(
                {"world_id": spec.scenario_id, "reason": str(exc)}
            )
    worlds = tuple(sorted(worlds, key=lambda world: world.world_id))
    world_ids = tuple(world.world_id for world in worlds)

    if candidate_build_failures:
        design_stop_reasons.append("candidate_build_failure")
    if len(worlds) != 32:
        design_stop_reasons.append("candidate_world_count_not_32")
    for truth_id in truths.values():
        if truth_id not in world_ids:
            design_stop_reasons.append(f"truth_world_missing:{truth_id}")

    reachable_by_world = {}
    for world in worlds:
        forward = forward_reachable_configuration(
            world,
            max_steps=40,
            support_tolerance=0.0,
        )
        reachable_by_world[world.world_id] = set(forward.reachable_ids)

    structural_truth_parity_failures = []
    for scenario_id, truth_world_id in truths.items():
        if truth_world_id not in specs_by_id or truth_world_id not in reachable_by_world:
            continue
        spec = specs_by_id[truth_world_id]
        A = generator_abiotic_mask(
            landscape,
            spec.niche_center,
            spec.niche_radius,
        )
        B = _evaluator_biotic_mask(
            landscape,
            associates,
            spec.biotic_mode,
        )
        # independent generator BFS is exercised through simulate_focal below; here
        # compare the truth reachable set returned by the generator with EOG support.
        realization = simulate_focal(
            landscape,
            associates,
            spec,
            replicate=-1,
        )
        generator_reach = set(realization.structural_reachable_ids)
        eog_reach = reachable_by_world[truth_world_id]
        if generator_reach != eog_reach:
            structural_truth_parity_failures.append(
                {
                    "scenario_id": scenario_id,
                    "generator_only": sorted(generator_reach - eog_reach),
                    "eog_only": sorted(eog_reach - generator_reach),
                }
            )
    if structural_truth_parity_failures:
        design_stop_reasons.append("generator_evaluator_structural_mismatch")

    result = {
        "schema": "eog.independent_stochastic_bam.result.v3",
        "status": "DESIGN_STOP" if design_stop_reasons else "SCORED",
        "design_stop_reasons": design_stop_reasons,
        "landscape_node_count": n_nodes,
        "partner_occupied_count": partner_count,
        "antagonist_occupied_count": antagonist_count,
        "candidate_world_count": len(worlds),
        "candidate_build_failures": candidate_build_failures,
        "structural_truth_parity_failures": structural_truth_parity_failures,
    }

    if design_stop_reasons:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    horizons = (5, 10, 20, 40)
    replicates = 64

    truth_retention_failures = 0
    sequential_expansion_violations = 0
    superset_ceiling_violations = 0
    omitted_truth_criterion_mismatches = 0
    api_parity_mismatches = 0
    api_parity_audits = 0
    history_worse_than_snapshot = 0
    history_strict_improvements = 0

    scenario_strict_contraction = {scenario_id: 0 for scenario_id in truths}
    scenario_nonidentified_h40 = {scenario_id: 0 for scenario_id in truths}
    compatible_counts = defaultdict(lambda: defaultdict(list))
    unique_counts = defaultdict(lambda: defaultdict(int))
    run_rows = []

    for scenario_id, truth_world_id in truths.items():
        spec = specs_by_id[truth_world_id]
        truth_reach = reachable_by_world[truth_world_id]
        superset_false_worlds = tuple(
            world_id
            for world_id, support in reachable_by_world.items()
            if world_id != truth_world_id and truth_reach.issubset(support)
        )

        for replicate in range(replicates):
            realization = simulate_focal(
                landscape,
                associates,
                spec,
                replicate=replicate,
            )
            previous_compatible = set(world_ids)
            h40_compatible = None

            for horizon, observed_ids in realization.accumulated_occurrence_ids_by_horizon:
                compatible = _compatible_from_cached_support(
                    observed_ids,
                    reachable_by_world,
                )
                compatible_set = set(compatible)
                compatible_counts[scenario_id][horizon].append(len(compatible))

                if truth_world_id not in compatible_set:
                    truth_retention_failures += 1
                if not compatible_set.issubset(previous_compatible):
                    sequential_expansion_violations += 1
                previous_compatible = compatible_set

                for world_id in superset_false_worlds:
                    if world_id not in compatible_set:
                        superset_ceiling_violations += 1

                omitted_candidates = tuple(
                    world_id for world_id in world_ids if world_id != truth_world_id
                )
                omitted_compatible = tuple(
                    world_id for world_id in compatible if world_id != truth_world_id
                )
                observed = set(observed_ids)
                every_candidate_has_witness = all(
                    not observed.issubset(reachable_by_world[world_id])
                    for world_id in omitted_candidates
                )
                universe_falsified = len(omitted_compatible) == 0
                if universe_falsified != every_candidate_has_witness:
                    omitted_truth_criterion_mismatches += 1

                if compatible == (truth_world_id,):
                    unique_counts[scenario_id][horizon] += 1

                # Actual EOG inverse-reconstruction API audit for one replicate per
                # scenario at every frozen horizon.
                if replicate == 0 and len(observed_ids) >= 2:
                    reconstruction = reconstruct_compatible_worlds(
                        worlds,
                        observed_ids,
                        max_steps=40,
                        support_tolerance=0.0,
                    )
                    api_parity_audits += 1
                    if reconstruction.compatible_world_ids != compatible:
                        api_parity_mismatches += 1

                if horizon == 40:
                    h40_compatible = compatible

            assert h40_compatible is not None
            if len(h40_compatible) < len(world_ids):
                scenario_strict_contraction[scenario_id] += 1
            if len(h40_compatible) > 1:
                scenario_nonidentified_h40[scenario_id] += 1

            final_compatible = _compatible_from_cached_support(
                realization.final_snapshot_ids,
                reachable_by_world,
            )
            if len(h40_compatible) > len(final_compatible):
                history_worse_than_snapshot += 1
            if len(h40_compatible) < len(final_compatible):
                history_strict_improvements += 1

            run_rows.append(
                {
                    "scenario_id": scenario_id,
                    "truth_world_id": truth_world_id,
                    "replicate": replicate,
                    "h40_compatible_count": len(h40_compatible),
                    "final_snapshot_compatible_count": len(final_compatible),
                    "truth_structural_reachable_count": len(truth_reach),
                    "h40_accumulated_occurrence_count": len(
                        dict(realization.accumulated_occurrence_ids_by_horizon)[40]
                    ),
                    "final_snapshot_occurrence_count": len(
                        realization.final_snapshot_ids
                    ),
                }
            )

    s4_failures = [
        scenario_id
        for scenario_id, count in scenario_strict_contraction.items()
        if count == 0
    ]
    any_nonidentified = any(
        count > 0 for count in scenario_nonidentified_h40.values()
    )

    medians = {
        scenario_id: {
            str(horizon): float(np.median(values))
            for horizon, values in sorted(by_horizon.items())
        }
        for scenario_id, by_horizon in compatible_counts.items()
    }
    unique_fraction = {
        scenario_id: {
            str(horizon): unique_counts[scenario_id][horizon] / replicates
            for horizon in horizons
        }
        for scenario_id in truths
    }

    verdicts = {
        "S1_true_world_retention": (
            "SUPPORTED" if truth_retention_failures == 0 else "REFUTED"
        ),
        "S2_sequential_contraction_monotonicity": (
            "SUPPORTED" if sequential_expansion_violations == 0 else "REFUTED"
        ),
        "S3_positive_superset_ceiling": (
            "SUPPORTED" if superset_ceiling_violations == 0 else "REFUTED"
        ),
        "S4_stochastic_witness_realization": (
            "SUPPORTED" if not s4_failures else "REFUTED"
        ),
        "S5_nonidentification_persists": (
            "SUPPORTED" if any_nonidentified else "REFUTED"
        ),
        "S6_omitted_truth_witness_criterion": (
            "SUPPORTED"
            if omitted_truth_criterion_mismatches == 0
            else "REFUTED"
        ),
        "S7_history_not_worse_than_final_snapshot": (
            "SUPPORTED"
            if history_worse_than_snapshot == 0
            and history_strict_improvements > 0
            else "REFUTED"
        ),
    }

    result.update(
        {
            "planned_runs": len(truths) * replicates,
            "eligible_runs": len(run_rows),
            "design_stops": 0,
            "truth_retention_failures": truth_retention_failures,
            "sequential_expansion_violations": sequential_expansion_violations,
            "superset_ceiling_violations": superset_ceiling_violations,
            "omitted_truth_criterion_mismatches": omitted_truth_criterion_mismatches,
            "eog_api_parity_audits": api_parity_audits,
            "eog_api_parity_mismatches": api_parity_mismatches,
            "history_worse_than_snapshot": history_worse_than_snapshot,
            "history_strict_improvements": history_strict_improvements,
            "strict_contraction_runs_by_scenario": scenario_strict_contraction,
            "nonidentified_h40_runs_by_scenario": scenario_nonidentified_h40,
            "median_compatible_world_count": medians,
            "unique_truth_fraction": unique_fraction,
            "S4_scenarios_without_strict_contraction": s4_failures,
            "verdicts": verdicts,
            "runs": run_rows,
        }
    )

    encoded = json.dumps(
        result,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    import hashlib
    result["fingerprint"] = hashlib.sha256(encoded).hexdigest()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "partner_occupied_count": partner_count,
                "antagonist_occupied_count": antagonist_count,
                "truth_retention_failures": truth_retention_failures,
                "sequential_expansion_violations": sequential_expansion_violations,
                "superset_ceiling_violations": superset_ceiling_violations,
                "omitted_truth_criterion_mismatches": omitted_truth_criterion_mismatches,
                "eog_api_parity_audits": api_parity_audits,
                "eog_api_parity_mismatches": api_parity_mismatches,
                "history_worse_than_snapshot": history_worse_than_snapshot,
                "history_strict_improvements": history_strict_improvements,
                "strict_contraction_runs_by_scenario": scenario_strict_contraction,
                "nonidentified_h40_runs_by_scenario": scenario_nonidentified_h40,
                "median_compatible_world_count": medians,
                "unique_truth_fraction": unique_fraction,
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
