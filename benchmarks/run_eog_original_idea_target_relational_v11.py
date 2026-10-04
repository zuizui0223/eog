#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.run_eog_original_idea_marginal_topology_v10 import (
    ACTIVE_SIZES,
    REPLICATES,
    TOPOLOGIES,
    _evaluate,
)


PROTOCOL = ROOT / "validation/eog_original_idea_target_relational_v11/protocol_v11.json"
TARGETS = (
    "pairwise_relation",
    "first_passage",
    "intervention",
    "critical_node_count",
    "joint_relational_suite",
)


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


def _normalized_partition(values):
    labels = {}
    out = []
    for value in values:
        key = json.dumps(value, sort_keys=True, default=str)
        if key not in labels:
            labels[key] = len(labels)
        out.append(labels[key])
    return tuple(out)


def _target_values(row, target):
    values = []
    for topology in TOPOLOGIES:
        world = row["worlds"][topology]
        if target == "pairwise_relation":
            value = world["pairwise_relation_signature"]
        elif target == "first_passage":
            value = world["first_passage_signature"]
        elif target == "intervention":
            value = world["intervention_signature"]
        elif target == "critical_node_count":
            value = world["critical_node_count"]
        elif target == "joint_relational_suite":
            value = (
                world["pairwise_relation_signature"],
                world["first_passage_signature"],
                world["intervention_signature"],
            )
        else:
            raise ValueError(target)
        values.append(value)
    return tuple(values)


def _atomic_features(row):
    active = tuple(row["active_nodes"])
    features = {}

    # First-passage measurements from the shared source to one active node.
    for index, node in enumerate(active[1:], start=1):
        feature_id = f"FP:{node}"
        features[feature_id] = {
            "family": "FP",
            "values": tuple(
                row["worlds"][topology]["first_passage_signature"][index]
                for topology in TOPOLOGIES
            ),
        }

    # One directed reachability bit for one ordered pair.
    rel_pairs = []
    for source in active:
        for target in active:
            if source == target:
                continue
            rel_pairs.append((source, target))
    for index, (source, target) in enumerate(rel_pairs):
        feature_id = f"REL:{source}->{target}"
        features[feature_id] = {
            "family": "REL",
            "values": tuple(
                row["worlds"][topology]["pairwise_relation_signature"][index]
                for topology in TOPOLOGIES
            ),
        }

    # One single-node knockout retained-count measurement.
    for index, removed in enumerate(active[1:]):
        feature_id = f"KO:{removed}"
        features[feature_id] = {
            "family": "KO",
            "values": tuple(
                row["worlds"][topology]["intervention_signature"][index]
                for topology in TOPOLOGIES
            ),
        }

    return features


def _combined_partition(feature_ids, feature_partitions):
    values = []
    for world_index in range(len(TOPOLOGIES)):
        values.append(
            tuple(feature_partitions[feature_id][world_index] for feature_id in feature_ids)
        )
    return _normalized_partition(values)


def _refines(candidate_partition, target_partition):
    for i in range(len(candidate_partition)):
        for j in range(i + 1, len(candidate_partition)):
            if (
                candidate_partition[i] == candidate_partition[j]
                and target_partition[i] != target_partition[j]
            ):
                return False
    return True


def _minimum_design(row, target):
    features = _atomic_features(row)
    target_values = _target_values(row, target)
    target_partition = _normalized_partition(target_values)

    partition_to_features = {}
    feature_partitions = {}
    for feature_id, spec in sorted(features.items()):
        partition = _normalized_partition(spec["values"])
        feature_partitions[feature_id] = partition
        partition_to_features.setdefault(partition, []).append(feature_id)

    # Features constant across all worlds never help.
    informative_partitions = [
        partition
        for partition in sorted(partition_to_features)
        if len(set(partition)) > 1
    ]

    canonical_by_partition = {
        partition: sorted(partition_to_features[partition])[0]
        for partition in informative_partitions
    }

    if len(set(target_partition)) == 1:
        return {
            "target_class_count": 1,
            "minimum_size": 0,
            "canonical_measurement_ids": [],
            "canonical_families": [],
            "cross_family_minimum_exists": False,
            "all_features_sufficient": True,
        }

    chosen_partitions = None
    for size in range(1, len(informative_partitions) + 1):
        candidates = []
        for combo in itertools.combinations(informative_partitions, size):
            ids = tuple(canonical_by_partition[partition] for partition in combo)
            partition = _combined_partition(ids, feature_partitions)
            if _refines(partition, target_partition):
                candidates.append((ids, combo))
        if candidates:
            candidates.sort(key=lambda item: item[0])
            chosen_ids, chosen_partitions = candidates[0]
            break

    if chosen_partitions is None:
        minimum_size = None
        canonical_ids = None
        canonical_families = None
        cross_family_exists = False
    else:
        minimum_size = len(chosen_partitions)
        canonical_ids = tuple(
            canonical_by_partition[partition] for partition in chosen_partitions
        )
        canonical_families = tuple(
            features[feature_id]["family"] for feature_id in canonical_ids
        )

        same_family = {
            "pairwise_relation": "REL",
            "first_passage": "FP",
            "intervention": "KO",
        }.get(target)
        cross_family_exists = False
        if same_family is not None:
            # Each selected partition can be represented by any feature inducing that
            # partition.  If a minimum partition combo contains a cross-family
            # representative, a cross-family minimum design exists.
            cross_family_exists = any(
                any(
                    features[feature_id]["family"] != same_family
                    for feature_id in partition_to_features[partition]
                )
                for partition in chosen_partitions
            )

    all_ids = tuple(sorted(features))
    all_partition = _combined_partition(all_ids, feature_partitions)
    return {
        "target_class_count": len(set(target_partition)),
        "minimum_size": minimum_size,
        "canonical_measurement_ids": (
            None if canonical_ids is None else list(canonical_ids)
        ),
        "canonical_families": (
            None if canonical_families is None else list(canonical_families)
        ),
        "cross_family_minimum_exists": cross_family_exists,
        "all_features_sufficient": _refines(all_partition, target_partition),
    }


def _evaluate_row(active_n, replicate):
    row = _evaluate(active_n, replicate)
    features = _atomic_features(row)
    target_rows = {
        target: _minimum_design(row, target)
        for target in TARGETS
    }
    first_measurements = {
        target: (
            None
            if target_rows[target]["canonical_measurement_ids"] in (None, [])
            else target_rows[target]["canonical_measurement_ids"][0]
        )
        for target in TARGETS
    }

    return {
        "active_node_count": active_n,
        "replicate": replicate,
        "atomic_feature_count": len(features),
        "family_feature_counts": {
            family: sum(spec["family"] == family for spec in features.values())
            for family in ("REL", "FP", "KO")
        },
        "full_topology_class_count": 4,
        "targets": target_rows,
        "canonical_first_measurements": first_measurements,
    }


def _dist(values):
    return {
        str(key): int(value)
        for key, value in sorted(Counter(values).items(), key=lambda item: str(item[0]))
    }


def _mean(values):
    values = [float(value) for value in values]
    return None if not values else float(np.mean(values))


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != (
        "frozen_before_minimal_relational_synthesis_implementation_and_scoring"
    ):
        raise RuntimeError("v11 protocol is not frozen")

    rows = [
        _evaluate_row(active_n, replicate)
        for active_n in ACTIVE_SIZES
        for replicate in range(REPLICATES)
    ]
    if len(rows) != len(ACTIVE_SIZES) * REPLICATES:
        raise RuntimeError("unexpected v11 row count")

    unresolved_by_target = {
        target: sum(
            not row["targets"][target]["all_features_sufficient"]
            or row["targets"][target]["minimum_size"] is None
            for row in rows
        )
        for target in TARGETS
    }

    compression_failures = {
        target: sum(
            row["targets"][target]["minimum_size"] is None
            or row["targets"][target]["minimum_size"] >= row["atomic_feature_count"]
            for row in rows
        )
        for target in ("pairwise_relation", "first_passage", "intervention")
    }

    q3_first_passage_failures = sum(
        row["targets"]["first_passage"]["target_class_count"] >= 4 for row in rows
    )
    q3_intervention_failures = sum(
        row["targets"]["intervention"]["target_class_count"] >= 4 for row in rows
    )

    q4_rows = 0
    for row in rows:
        triple = (
            (
                row["targets"]["pairwise_relation"]["minimum_size"],
                tuple(row["targets"]["pairwise_relation"]["canonical_measurement_ids"] or ()),
            ),
            (
                row["targets"]["first_passage"]["minimum_size"],
                tuple(row["targets"]["first_passage"]["canonical_measurement_ids"] or ()),
            ),
            (
                row["targets"]["intervention"]["minimum_size"],
                tuple(row["targets"]["intervention"]["canonical_measurement_ids"] or ()),
            ),
        )
        if len(set(triple)) > 1:
            q4_rows += 1

    cross_family_rows = {
        target: sum(
            row["targets"][target]["cross_family_minimum_exists"]
            for row in rows
        )
        for target in ("pairwise_relation", "first_passage", "intervention")
    }

    joint_unresolved = unresolved_by_target["joint_relational_suite"]
    joint_leaves_topology_unresolved = sum(
        row["targets"]["joint_relational_suite"]["target_class_count"] < 4
        for row in rows
    )

    first_ids = {
        feature_id
        for row in rows
        for feature_id in row["canonical_first_measurements"].values()
        if feature_id is not None
    }

    by_target = {}
    for target in TARGETS:
        by_target[target] = {
            "target_class_count_distribution": _dist(
                row["targets"][target]["target_class_count"] for row in rows
            ),
            "minimum_size_distribution": _dist(
                row["targets"][target]["minimum_size"] for row in rows
            ),
            "mean_minimum_size": _mean(
                row["targets"][target]["minimum_size"] for row in rows
            ),
            "cross_family_minimum_exists_rows": sum(
                row["targets"][target]["cross_family_minimum_exists"]
                for row in rows
            ),
        }

    verdicts = {
        "Q1_each_target_is_resolvable_by_declared_relational_measurements": (
            "SUPPORTED"
            if all(value == 0 for value in unresolved_by_target.values())
            else "REFUTED"
        ),
        "Q2_target_specific_minima_are_strict_compressions": (
            "SUPPORTED"
            if all(value == 0 for value in compression_failures.values())
            else "REFUTED"
        ),
        "Q3_full_topology_identity_is_not_required_for_first_passage_or_intervention": (
            "SUPPORTED"
            if q3_first_passage_failures == 0 and q3_intervention_failures == 0
            else "REFUTED"
        ),
        "Q4_relational_targets_have_different_information_requirements": (
            "SUPPORTED" if q4_rows > 0 else "REFUTED"
        ),
        "Q5_cross_family_measurements_can_be_sufficient": (
            "SUPPORTED" if any(value > 0 for value in cross_family_rows.values()) else "REFUTED"
        ),
        "Q6_joint_relational_suite_is_resolvable_without_edge_identity": (
            "SUPPORTED" if joint_unresolved == 0 else "REFUTED"
        ),
        "Q7_joint_target_can_leave_full_topology_unresolved": (
            "SUPPORTED" if joint_leaves_topology_unresolved > 0 else "REFUTED"
        ),
        "Q8_no_single_fixed_measurement_is_universally_optimal": (
            "SUPPORTED" if len(first_ids) > 1 else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_target_relational_sufficiency.result.v11",
        "row_count": len(rows),
        "predeclared_verdicts": verdicts,
        "unresolved_by_target": unresolved_by_target,
        "compression_failure_count": compression_failures,
        "Q3_first_passage_full_topology_class_failures": q3_first_passage_failures,
        "Q3_intervention_full_topology_class_failures": q3_intervention_failures,
        "Q4_rows_with_different_target_minima": q4_rows,
        "cross_family_minimum_rows": cross_family_rows,
        "joint_target_rows_leaving_topology_unresolved": joint_leaves_topology_unresolved,
        "distinct_canonical_first_measurement_count": len(first_ids),
        "distinct_canonical_first_measurements": sorted(first_ids),
        "by_target": by_target,
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
                "predeclared_verdicts": result["predeclared_verdicts"],
                "unresolved_by_target": result["unresolved_by_target"],
                "Q4_rows_with_different_target_minima": result[
                    "Q4_rows_with_different_target_minima"
                ],
                "cross_family_minimum_rows": result["cross_family_minimum_rows"],
                "joint_target_rows_leaving_topology_unresolved": result[
                    "joint_target_rows_leaving_topology_unresolved"
                ],
                "by_target": result["by_target"],
                "fingerprint": result["fingerprint"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
