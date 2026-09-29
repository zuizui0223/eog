#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
import argparse
import json
from pathlib import Path

from eog.v2.known_truth_bam_v2_1 import build_v21_system


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "validation/known_truth_bam_v2_2/"
            "parameter_alias_audit_result_v2_2.json"
        ),
    )
    args = parser.parse_args()

    system = build_v21_system()
    axes_by = system.axes_by_world
    classes = defaultdict(list)

    for world in system.worlds:
        key = (
            world.abiotic_mask,
            world.biotic_mask,
            world.movement_mask,
            world.first_arrival_steps,
        )
        classes[key].append(world.world_id)

    alias_patterns = Counter()
    class_rows = []
    noninjective_worlds = 0

    for world_ids in classes.values():
        rows = [axes_by[world_id] for world_id in world_ids]
        varying = []
        if len({row.abiotic_label for row in rows}) > 1:
            varying.append("A")
        if len({row.biotic_mode for row in rows}) > 1:
            varying.append("B")
        if len({row.step_radius for row in rows}) > 1:
            varying.append("D")
        if len({row.barrier_permeable for row in rows}) > 1:
            varying.append("P")
        if len({row.horizon for row in rows}) > 1:
            varying.append("H")

        pattern = "+".join(varying) if varying else "none"
        if len(world_ids) > 1:
            alias_patterns[pattern] += 1
            noninjective_worlds += len(world_ids)

        class_rows.append(
            {
                "world_ids": sorted(world_ids),
                "class_size": len(world_ids),
                "varying_axes": varying,
                "alias_pattern": pattern,
            }
        )

    size_dist = Counter(row["class_size"] for row in class_rows)
    result = {
        "schema": "eog.known_truth_bam_direct_evidence.parameter_alias_audit_result.v2_2",
        "primary_result_fingerprint": "5912231d6b8d04fd1cbb3540bf137562c394aca9fc40069486d6350ee7fff9f0",
        "candidate_world_count": len(system.worlds),
        "number_of_equivalence_classes": len(class_rows),
        "class_size_distribution": {
            str(key): value for key, value in sorted(size_dist.items())
        },
        "alias_axis_pattern_counts": dict(sorted(alias_patterns.items())),
        "world_fraction_in_noninjective_classes": (
            0.0 if not system.worlds else noninjective_worlds / len(system.worlds)
        ),
        "classes": sorted(
            class_rows,
            key=lambda row: (row["class_size"], row["world_ids"]),
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "candidate_world_count": result["candidate_world_count"],
                "number_of_equivalence_classes": result[
                    "number_of_equivalence_classes"
                ],
                "class_size_distribution": result["class_size_distribution"],
                "alias_axis_pattern_counts": result[
                    "alias_axis_pattern_counts"
                ],
                "world_fraction_in_noninjective_classes": result[
                    "world_fraction_in_noninjective_classes"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
