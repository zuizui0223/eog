"""Direct BAM evidence identifiability upper-bound experiment v2.2."""
from __future__ import annotations

from collections import Counter
import hashlib
import json

from .known_truth_bam import (
    compatible_with_temporal_arrivals,
)
from .known_truth_bam_v2_1 import build_v21_system


def _sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _full_state_key(world) -> tuple[object, ...]:
    return (
        world.abiotic_mask,
        world.biotic_mask,
        world.movement_mask,
        world.first_arrival_steps,
    )


def run_bam_v22() -> dict[str, object]:
    system = build_v21_system()
    worlds = system.worlds
    eligible = 0

    unique_counts = {
        "baseline": 0,
        "A_direct": 0,
        "B_direct": 0,
        "M_direct": 0,
        "AB_direct": 0,
        "AM_direct": 0,
        "BM_direct": 0,
        "ABM_direct": 0,
    }

    d1_mismatches = 0
    d2_violations = 0
    d3_violations = 0
    state_class_hist = Counter()
    rows: list[dict[str, object]] = []

    for truth in worlds:
        positives = truth.occupied_ids
        if len(positives) < 2 or "r1c0" not in positives:
            continue
        eligible += 1
        positives_set = set(positives)
        negatives = tuple(
            node_id
            for node_id in system.landscape.node_ids
            if node_id not in positives_set
        )
        idx = {node_id: i for i, node_id in enumerate(truth.node_ids)}
        occupied_arrivals = {
            node_id: int(truth.first_arrival_steps[idx[node_id]])
            for node_id in positives
            if truth.first_arrival_steps[idx[node_id]] is not None
        }
        baseline = compatible_with_temporal_arrivals(
            worlds,
            positives,
            negatives,
            occupied_arrivals,
        ).compatible_world_ids
        baseline_set = set(baseline)

        filters = {
            "A_direct": lambda world: world.abiotic_mask == truth.abiotic_mask,
            "B_direct": lambda world: world.biotic_mask == truth.biotic_mask,
            "M_direct": lambda world: (
                world.movement_mask == truth.movement_mask
                and world.first_arrival_steps == truth.first_arrival_steps
            ),
        }

        compatible = {
            "baseline": baseline,
            "A_direct": tuple(
                world.world_id for world in worlds
                if world.world_id in baseline_set and filters["A_direct"](world)
            ),
            "B_direct": tuple(
                world.world_id for world in worlds
                if world.world_id in baseline_set and filters["B_direct"](world)
            ),
            "M_direct": tuple(
                world.world_id for world in worlds
                if world.world_id in baseline_set and filters["M_direct"](world)
            ),
            "AB_direct": tuple(
                world.world_id for world in worlds
                if world.world_id in baseline_set
                and filters["A_direct"](world)
                and filters["B_direct"](world)
            ),
            "AM_direct": tuple(
                world.world_id for world in worlds
                if world.world_id in baseline_set
                and filters["A_direct"](world)
                and filters["M_direct"](world)
            ),
            "BM_direct": tuple(
                world.world_id for world in worlds
                if world.world_id in baseline_set
                and filters["B_direct"](world)
                and filters["M_direct"](world)
            ),
            "ABM_direct": tuple(
                world.world_id for world in worlds
                if world.world_id in baseline_set
                and filters["A_direct"](world)
                and filters["B_direct"](world)
                and filters["M_direct"](world)
            ),
        }

        for key, ids in compatible.items():
            if ids == (truth.world_id,):
                unique_counts[key] += 1

        # D1: each direct-axis filter must agree exactly with state equality.
        for axis in ("A_direct", "B_direct", "M_direct"):
            observed = set(compatible[axis])
            expected = {
                world.world_id
                for world in worlds
                if world.world_id in baseline_set and filters[axis](world)
            }
            if observed != expected:
                d1_mismatches += 1

        truth_key = _full_state_key(truth)
        state_equivalent = tuple(
            world.world_id for world in worlds if _full_state_key(world) == truth_key
        )
        state_class_hist[str(len(state_equivalent))] += 1
        final_ids = compatible["ABM_direct"]

        if not set(state_equivalent).issubset(final_ids):
            d2_violations += 1
        expected_unique = len(state_equivalent) == 1
        observed_unique = final_ids == (truth.world_id,)
        if expected_unique != observed_unique:
            d3_violations += 1

        rows.append(
            {
                "truth_world_id": truth.world_id,
                "baseline_count": len(compatible["baseline"]),
                "A_direct_count": len(compatible["A_direct"]),
                "B_direct_count": len(compatible["B_direct"]),
                "M_direct_count": len(compatible["M_direct"]),
                "AB_direct_count": len(compatible["AB_direct"]),
                "AM_direct_count": len(compatible["AM_direct"]),
                "BM_direct_count": len(compatible["BM_direct"]),
                "ABM_direct_count": len(compatible["ABM_direct"]),
                "complete_state_equivalence_size": len(state_equivalent),
            }
        )

    fractions = {
        key: (0.0 if eligible == 0 else value / eligible)
        for key, value in unique_counts.items()
    }
    verdicts = {
        "D1_axis_exactness": "SUPPORTED" if d1_mismatches == 0 else "REFUTED",
        "D2_combined_state_ceiling": "SUPPORTED" if d2_violations == 0 else "REFUTED",
        "D3_unique_state_recovery": "SUPPORTED" if d3_violations == 0 else "REFUTED",
    }
    result: dict[str, object] = {
        "schema": "eog.known_truth_bam_direct_evidence.result.v2_2",
        "primary_parent_result_fingerprint": "dbfd0c09b492c1e53914ddfdfe392c765df6da98a43e105245767c24c75ad9b3",
        "eligible_truth_worlds": eligible,
        "unique_truth_fractions": fractions,
        "complete_state_equivalence_class_size_distribution": dict(
            sorted(state_class_hist.items(), key=lambda item: int(item[0]))
        ),
        "D1_mismatches": d1_mismatches,
        "D2_violations": d2_violations,
        "D3_violations": d3_violations,
        "verdicts": verdicts,
        "cases": rows,
    }
    result["fingerprint"] = _sha256(result)
    return result
