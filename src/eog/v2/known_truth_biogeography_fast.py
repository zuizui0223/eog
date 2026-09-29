"""Fast bitset replay of the frozen known-truth witness factorial.

Scientific design, world construction, sampling order, hypothesis rules and output
schema are unchanged.  Only repeated occurrence-compatibility evaluation is replaced
with exact integer bitset subset tests over precomputed reachable sets.
"""
from __future__ import annotations

import hashlib
import math
import time

import numpy as np

from .known_truth_biogeography import (
    _factorial_landscapes,
    _factorial_processes,
    _ordered_subset,
    build_virtual_world,
    exact_minimum_positive_witness_set,
    forward_reachable_configuration,
)


FROZEN_REFERENCE_FINGERPRINT = (
    "b1a2df3a6b1708b533f1f2c2d573eb9802f3a18d8bcada3e55e37124918d533b"
)


def _mask(node_ids: tuple[str, ...], values) -> int:
    index = {node_id: i for i, node_id in enumerate(node_ids)}
    result = 0
    for node_id in values:
        result |= 1 << index[node_id]
    return result


def _subset(left: int, right: int) -> bool:
    return left & ~right == 0


def run_witness_factorial_benchmark_fast() -> dict[str, object]:
    """Replay the frozen factorial with cached reachable-set bitsets."""

    from .known_truth_biogeography import _sha256

    started = time.perf_counter()
    coverages = (0.1, 0.25, 0.5, 1.0)
    replicates = 32
    processes = _factorial_processes()

    eligible_cases = 0
    truth_retention_failures = 0
    f1_mismatches = 0
    f2_monotonicity_violations = 0
    f3_equivalence_violations = 0
    f4_boundary_violations = 0
    exact_identifiable = 0
    equivalent_cases = 0
    omitted_falsified = 0
    omitted_survived = 0
    omitted_with_superset = 0
    omitted_with_superset_survived = 0
    witness_histogram: dict[str, int] = {}
    identification_counts = {str(value): 0 for value in coverages}
    identification_denominators = {str(value): 0 for value in coverages}
    case_rows: list[dict[str, object]] = []

    for landscape_id, landscape in _factorial_landscapes():
        worlds_by_id = {}
        for process in processes:
            try:
                worlds_by_id[process.world_id] = build_virtual_world(landscape, process)
            except ValueError:
                continue
        worlds = tuple(worlds_by_id[key] for key in sorted(worlds_by_id))
        if len(worlds) < 2:
            continue

        reachable_by_world = {
            world.world_id: set(
                forward_reachable_configuration(world, max_steps=8).reachable_ids
            )
            for world in worlds
        }
        masks_by_world = {
            world_id: _mask(landscape.node_ids, ids)
            for world_id, ids in reachable_by_world.items()
        }

        for truth in worlds:
            truth_reach = reachable_by_world[truth.world_id]
            if len(truth_reach) < 2:
                continue
            eligible_cases += 1
            truth_mask = masks_by_world[truth.world_id]
            false_worlds = tuple(
                world for world in worlds if world.world_id != truth.world_id
            )
            equivalent_false = tuple(
                world.world_id
                for world in false_worlds
                if masks_by_world[world.world_id] == truth_mask
            )
            if equivalent_false:
                equivalent_cases += 1

            minimum_witness = exact_minimum_positive_witness_set(
                truth,
                worlds,
                max_steps=8,
            )
            if minimum_witness is None:
                witness_histogram["unidentifiable"] = (
                    witness_histogram.get("unidentifiable", 0) + 1
                )
            else:
                exact_identifiable += 1
                key = str(len(minimum_witness))
                witness_histogram[key] = witness_histogram.get(key, 0) + 1

            full_occurrences = _ordered_subset(landscape.node_ids, truth_reach)
            full_mask = _mask(landscape.node_ids, full_occurrences)
            full_compatible = tuple(
                world.world_id
                for world in worlds
                if _subset(full_mask, masks_by_world[world.world_id])
            )
            expected_full = tuple(
                world.world_id
                for world in worlds
                if set(full_occurrences).issubset(reachable_by_world[world.world_id])
            )
            if full_compatible != expected_full:
                f1_mismatches += 1
            if truth.world_id not in full_compatible:
                truth_retention_failures += 1
            if equivalent_false and not set(equivalent_false).issubset(full_compatible):
                f3_equivalence_violations += 1

            omitted_worlds = false_worlds
            omitted_compatible = tuple(
                world.world_id
                for world in omitted_worlds
                if _subset(full_mask, masks_by_world[world.world_id])
            )
            expected_omitted = tuple(
                world.world_id
                for world in omitted_worlds
                if set(full_occurrences).issubset(reachable_by_world[world.world_id])
            )
            if omitted_compatible != expected_omitted:
                f4_boundary_violations += 1
            if omitted_compatible:
                omitted_survived += 1
            else:
                omitted_falsified += 1
            superset_exists = any(
                _subset(truth_mask, masks_by_world[world.world_id])
                for world in omitted_worlds
            )
            if superset_exists:
                omitted_with_superset += 1
                if omitted_compatible:
                    omitted_with_superset_survived += 1
                else:
                    f4_boundary_violations += 1

            for replicate in range(replicates):
                identified_sequence: list[bool] = []
                seed_prefix = f"{landscape_id}|{truth.world_id}|{replicate}"
                full_non_source = [
                    node
                    for node in full_occurrences
                    if node != truth.source_ids[0]
                ]
                seed = int(
                    hashlib.sha256(seed_prefix.encode("utf-8")).hexdigest()[:16],
                    16,
                )
                rng = np.random.default_rng(seed)
                shuffled = list(full_non_source)
                rng.shuffle(shuffled)

                for coverage in coverages:
                    count = (
                        len(shuffled)
                        if coverage >= 1.0
                        else max(1, int(math.ceil(coverage * len(shuffled))))
                    )
                    sampled = _ordered_subset(
                        landscape.node_ids,
                        (truth.source_ids[0], *shuffled[:count]),
                    )
                    sampled_mask = _mask(landscape.node_ids, sampled)
                    compatible = tuple(
                        world.world_id
                        for world in worlds
                        if _subset(sampled_mask, masks_by_world[world.world_id])
                    )
                    expected = tuple(
                        world.world_id
                        for world in worlds
                        if set(sampled).issubset(reachable_by_world[world.world_id])
                    )
                    if compatible != expected:
                        f1_mismatches += 1
                    if truth.world_id not in compatible:
                        truth_retention_failures += 1
                    identified = compatible == (truth.world_id,)
                    identified_sequence.append(identified)
                    key = str(coverage)
                    identification_denominators[key] += 1
                    if identified:
                        identification_counts[key] += 1

                if any(
                    earlier and not later
                    for earlier, later in zip(
                        identified_sequence,
                        identified_sequence[1:],
                    )
                ):
                    f2_monotonicity_violations += 1

            case_rows.append(
                {
                    "landscape_id": landscape_id,
                    "truth_world_id": truth.world_id,
                    "truth_reachable_count": len(truth_reach),
                    "full_compatible_count": len(full_compatible),
                    "equivalent_false_world_count": len(equivalent_false),
                    "minimum_positive_witness_count": (
                        None
                        if minimum_witness is None
                        else len(minimum_witness)
                    ),
                    "omitted_truth_compatible_count": len(omitted_compatible),
                    "omitted_truth_falsified": len(omitted_compatible) == 0,
                    "omitted_truth_superset_candidate_exists": superset_exists,
                }
            )

    identification_rate = {
        key: (
            0.0
            if identification_denominators[key] == 0
            else identification_counts[key] / identification_denominators[key]
        )
        for key in identification_counts
    }
    runtime_seconds = time.perf_counter() - started
    verdicts = {
        "F1_witness_criterion": (
            "SUPPORTED" if f1_mismatches == 0 else "REFUTED"
        ),
        "F2_sampling_monotonicity": (
            "SUPPORTED"
            if f2_monotonicity_violations == 0
            else "REFUTED"
        ),
        "F3_equivalence_ceiling": (
            "SUPPORTED"
            if f3_equivalence_violations == 0
            else "REFUTED"
        ),
        "F4_omitted_truth_not_guaranteed": (
            "BOUNDARY_CONFIRMED"
            if (
                f4_boundary_violations == 0
                and omitted_survived > 0
                and omitted_falsified > 0
            )
            else "NOT_CONFIRMED"
        ),
    }
    result: dict[str, object] = {
        "schema": "eog.known_truth_biogeography.witness_factorial_result.v1",
        "eligible_exact_cases": eligible_cases,
        "process_worlds_per_landscape": len(processes),
        "sampling_replicates_per_case": replicates,
        "sampling_coverages": list(coverages),
        "truth_retention_failures": truth_retention_failures,
        "f1_criterion_mismatches": f1_mismatches,
        "f2_monotonicity_violations": f2_monotonicity_violations,
        "f3_equivalence_violations": f3_equivalence_violations,
        "f4_boundary_violations": f4_boundary_violations,
        "identifiable_at_full_coverage_fraction": (
            0.0
            if eligible_cases == 0
            else exact_identifiable / eligible_cases
        ),
        "observational_equivalence_fraction": (
            0.0
            if eligible_cases == 0
            else equivalent_cases / eligible_cases
        ),
        "minimum_positive_witness_count_distribution": witness_histogram,
        "identification_rate_by_sampling_coverage": identification_rate,
        "omitted_truth_falsification_fraction": (
            0.0
            if eligible_cases == 0
            else omitted_falsified / eligible_cases
        ),
        "omitted_truth_survival_fraction": (
            0.0
            if eligible_cases == 0
            else omitted_survived / eligible_cases
        ),
        "omitted_truth_survival_with_superset_fraction": (
            0.0
            if omitted_with_superset == 0
            else omitted_with_superset_survived / omitted_with_superset
        ),
        "runtime_seconds": runtime_seconds,
        "verdicts": verdicts,
        "cases": case_rows,
    }
    fingerprint_payload = dict(result)
    fingerprint_payload["runtime_seconds"] = None
    result["fingerprint"] = _sha256(fingerprint_payload)
    result["reference_fingerprint_match"] = (
        result["fingerprint"] == FROZEN_REFERENCE_FINGERPRINT
    )
    return result
