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
    truth_scenarios,
)
from run_independent_stochastic_bam_v3 import _build_eog_world
from eog.v2.world_reconstruction import forward_reachable_configuration


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "validation/restrictiveness_ambiguity_v3_1/audit_result_v3_1.json"
        ),
    )
    args = parser.parse_args()

    landscape = make_landscape()
    associates = simulate_associates(landscape)
    specs = candidate_parameter_grid()
    worlds = tuple(
        sorted(
            (
                _build_eog_world(landscape, associates, spec)
                for spec in specs
            ),
            key=lambda world: world.world_id,
        )
    )

    support_by_world = {}
    for world in worlds:
        support_by_world[world.world_id] = frozenset(
            forward_reachable_configuration(
                world,
                max_steps=40,
                support_tolerance=0.0,
            ).reachable_ids
        )

    compatible_by_truth = {
        truth_id: tuple(
            world_id
            for world_id in sorted(support_by_world)
            if truth_support.issubset(support_by_world[world_id])
        )
        for truth_id, truth_support in support_by_world.items()
    }

    nesting_pairs = []
    monotonicity_violations = 0
    for left_id, left_support in support_by_world.items():
        for right_id, right_support in support_by_world.items():
            if left_id == right_id:
                continue
            if left_support < right_support:
                nesting_pairs.append((left_id, right_id))
                if len(compatible_by_truth[left_id]) < len(
                    compatible_by_truth[right_id]
                ):
                    monotonicity_violations += 1

    eq = defaultdict(list)
    for world_id, support in support_by_world.items():
        eq[support].append(world_id)
    eq_size_dist = Counter(len(ids) for ids in eq.values())

    rows = []
    support_sizes = []
    ambiguity_counts = []
    for world_id in sorted(support_by_world):
        support_size = len(support_by_world[world_id])
        compatible_count = len(compatible_by_truth[world_id])
        support_sizes.append(float(support_size))
        ambiguity_counts.append(float(compatible_count))
        rows.append(
            {
                "world_id": world_id,
                "reachable_support_size": support_size,
                "complete_positive_compatible_world_count": compatible_count,
                "compatible_world_ids": list(compatible_by_truth[world_id]),
            }
        )

    if np.std(support_sizes) > 0 and np.std(ambiguity_counts) > 0:
        correlation = float(
            np.corrcoef(
                np.asarray(support_sizes),
                np.asarray(ambiguity_counts),
            )[0, 1]
        )
    else:
        correlation = None

    max_ambiguity = max(len(values) for values in compatible_by_truth.values())
    min_ambiguity = min(len(values) for values in compatible_by_truth.values())
    maximally_ambiguous = tuple(
        world_id
        for world_id in sorted(compatible_by_truth)
        if len(compatible_by_truth[world_id]) == max_ambiguity
    )
    minimally_ambiguous = tuple(
        world_id
        for world_id in sorted(compatible_by_truth)
        if len(compatible_by_truth[world_id]) == min_ambiguity
    )

    scenarios = truth_scenarios()
    scenario_rows = {
        scenario_id: {
            "world_id": world_id,
            "reachable_support_size": len(support_by_world[world_id]),
            "complete_positive_compatible_world_count": len(
                compatible_by_truth[world_id]
            ),
        }
        for scenario_id, world_id in scenarios.items()
    }

    result = {
        "schema": "eog.restrictiveness_ambiguity_audit.result.v3_1",
        "parent_v3_result_fingerprint": (
            "bc558d10073133510f1b47b5651f6694d53f04771e757e9d8d9716ada72b18bf"
        ),
        "candidate_world_count": len(worlds),
        "strict_support_inclusion_pair_count": len(nesting_pairs),
        "nesting_monotonicity_violations": monotonicity_violations,
        "support_equivalence_class_count": len(eq),
        "support_equivalence_class_size_distribution": {
            str(size): count
            for size, count in sorted(eq_size_dist.items())
        },
        "max_ambiguity_count": max_ambiguity,
        "maximally_ambiguous_worlds": list(maximally_ambiguous),
        "min_ambiguity_count": min_ambiguity,
        "minimally_ambiguous_worlds": list(minimally_ambiguous),
        "support_size_vs_ambiguity_pearson_r": correlation,
        "frozen_truth_scenarios": scenario_rows,
        "world_rows": rows,
        "theorem_audit": {
            "statement": (
                "If R1 is a subset of R2, then every candidate supporting R2 also "
                "supports R1; therefore complete-positive compatible-world count "
                "for R1 cannot be smaller than for R2."
            ),
            "supported_in_all_strict_inclusion_pairs": (
                monotonicity_violations == 0
            ),
        },
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
                "candidate_world_count": result["candidate_world_count"],
                "strict_support_inclusion_pair_count": result[
                    "strict_support_inclusion_pair_count"
                ],
                "nesting_monotonicity_violations": result[
                    "nesting_monotonicity_violations"
                ],
                "support_equivalence_class_size_distribution": result[
                    "support_equivalence_class_size_distribution"
                ],
                "max_ambiguity_count": result["max_ambiguity_count"],
                "maximally_ambiguous_worlds": result[
                    "maximally_ambiguous_worlds"
                ],
                "min_ambiguity_count": result["min_ambiguity_count"],
                "support_size_vs_ambiguity_pearson_r": result[
                    "support_size_vs_ambiguity_pearson_r"
                ],
                "frozen_truth_scenarios": result["frozen_truth_scenarios"],
                "fingerprint": result["fingerprint"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
