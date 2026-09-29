#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from itertools import combinations
import argparse
import json
from pathlib import Path

from eog.v2.falsification_driven_design import (
    build_v23_intervention_library,
    plan_v24,
)
from eog.v2.generic_evidence_design import (
    equivalence_classes,
    plan_finite_evidence_design,
)
from eog.v2.known_truth_bam_v2_1 import build_v21_system


def _p_only_contracted_active_worlds(passive):
    system = build_v21_system()
    axes_by = system.axes_by_world
    placeholder = {"x": {world_id: 0 for world_id in passive}}
    classes = equivalence_classes(passive, placeholder)

    keep = set(passive)
    for group in classes:
        if len(group) != 2:
            continue
        left, right = group
        l = axes_by[left]
        r = axes_by[right]
        varying = []
        if l.abiotic_label != r.abiotic_label:
            varying.append("A")
        if l.biotic_mode != r.biotic_mode:
            varying.append("B")
        if l.step_radius != r.step_radius:
            varying.append("D")
        if l.barrier_permeable != r.barrier_permeable:
            varying.append("P")
        if l.horizon != r.horizon:
            varying.append("H")
        if varying == ["P"]:
            keep.remove(max(group))
    return tuple(sorted(keep))


def _monotone_violations(passive, interventions):
    ids = tuple(sorted(interventions))
    partitions = {}
    for size in range(len(ids) + 1):
        for subset in combinations(ids, size):
            classes = equivalence_classes(
                passive,
                interventions,
                selected_evidence_ids=subset,
            )
            partitions[subset] = {
                world_id: frozenset(group)
                for group in classes
                for world_id in group
            }

    violations = 0
    for subset, before in partitions.items():
        for evidence_id in ids:
            if evidence_id in subset:
                continue
            after_subset = tuple(sorted((*subset, evidence_id)))
            after = partitions[after_subset]
            for world_id in passive:
                if not after[world_id].issubset(before[world_id]):
                    violations += 1
    return violations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "validation/generic_finite_evidence_design_v2_5/result_v2_5.json"
        ),
    )
    args = parser.parse_args()

    passive, interventions = build_v23_intervention_library()
    frozen = plan_v24()
    generic = plan_finite_evidence_design(passive, interventions)

    generic_rank = {
        row.evidence_id: row.split_unresolved_pairs
        for row in generic.rankings
    }
    frozen_rank = {
        row["intervention_id"]: row["split_unresolved_pairs"]
        for row in frozen["ranked_interventions"]
    }
    g1 = (
        len(generic.active_world_ids) == frozen["world_count"]
        and len(generic.unresolved_world_pairs)
        == frozen["passive_unresolved_pair_count"]
        and generic_rank == frozen_rank
        and list(generic.minimum_separating_set or ())
        == frozen["minimum_separating_set"]
        and generic.minimum_set_size == frozen["minimum_set_size"]
        and generic.all_active_worlds_separated
        == frozen["all_worlds_separated"]
    )

    limited = {
        key: interventions[key]
        for key in ("P_barrier_challenge", "repeat_passive_state")
    }
    insufficient = plan_finite_evidence_design(passive, limited)
    insufficient_sizes = Counter(
        len(group) for group in insufficient.final_equivalence_classes
    )
    g2 = (
        insufficient.minimum_separating_set is None
        and insufficient.insufficient_library
        and not insufficient.all_active_worlds_separated
        and insufficient_sizes == Counter({1: 48, 2: 8})
    )

    active = _p_only_contracted_active_worlds(passive)
    contracted = plan_finite_evidence_design(
        passive,
        interventions,
        active_world_ids=active,
    )
    g3 = (
        len(active) == 56
        and len(contracted.unresolved_world_pairs) == 8
        and contracted.minimum_separating_set
        == ("H_long_corridor_challenge",)
        and contracted.all_active_worlds_separated
    )

    monotone_violations = _monotone_violations(passive, interventions)
    g4 = monotone_violations == 0

    verdicts = {
        "G1_reproduce_v2_4": "SUPPORTED" if g1 else "REFUTED",
        "G2_fail_closed_when_library_insufficient": (
            "SUPPORTED" if g2 else "REFUTED"
        ),
        "G3_replan_after_world_contraction": (
            "SUPPORTED" if g3 else "REFUTED"
        ),
        "G4_monotone_evidence_addition": "SUPPORTED" if g4 else "REFUTED",
    }

    result = {
        "schema": "eog.generic_finite_evidence_design.result.v2_5",
        "parent_v2_4_result_fingerprint": (
            "c7107f1511fd7b5542da3f7c501d99f0b8cebe00feec0348ca4d60d510a75b12"
        ),
        "world_count": len(passive),
        "full_unresolved_pair_count": len(generic.unresolved_world_pairs),
        "full_split_counts": generic_rank,
        "full_minimum_separating_set": list(
            generic.minimum_separating_set or ()
        ),
        "full_minimum_set_size": generic.minimum_set_size,
        "insufficient_library": {
            "evidence_ids": sorted(limited),
            "minimum_separating_set": None,
            "unresolved_pair_count_before": len(
                insufficient.unresolved_world_pairs
            ),
            "final_class_size_distribution": {
                str(size): count
                for size, count in sorted(insufficient_sizes.items())
            },
            "insufficient_library": insufficient.insufficient_library,
        },
        "contracted_world_set": {
            "active_world_count": len(active),
            "unresolved_pair_count": len(contracted.unresolved_world_pairs),
            "minimum_separating_set": list(
                contracted.minimum_separating_set or ()
            ),
            "minimum_set_size": contracted.minimum_set_size,
            "all_worlds_separated": contracted.all_active_worlds_separated,
        },
        "monotone_evidence_addition_violations": monotone_violations,
        "coverage_certificate": generic.coverage_certificate,
        "generic_plan_fingerprint": generic.fingerprint,
        "verdicts": verdicts,
    }

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
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
