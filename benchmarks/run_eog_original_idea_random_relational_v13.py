#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from functools import lru_cache
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.run_eog_original_idea_random_topology_v12 import (
    ACTIVE_SIZES,
    REPLICATES,
    _evaluate as evaluate_v12,
    _static_state,
)


PROTOCOL = ROOT / "validation/eog_original_idea_random_relational_v13/protocol_v13.json"
TARGETS = (
    "pairwise_relation",
    "first_passage",
    "intervention",
    "critical_node_count",
    "full_topology_identity",
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
    worlds = row["worlds"]
    if target == "pairwise_relation":
        return tuple(world["pairwise_relation_signature"] for world in worlds)
    if target == "first_passage":
        return tuple(world["first_passage_signature"] for world in worlds)
    if target == "intervention":
        return tuple(world["intervention_signature"] for world in worlds)
    if target == "critical_node_count":
        return tuple(world["critical_node_count"] for world in worlds)
    if target == "full_topology_identity":
        return tuple(world["edge_fingerprint"] for world in worlds)
    if target == "joint_relational_suite":
        return tuple(
            (
                world["pairwise_relation_signature"],
                world["first_passage_signature"],
                world["intervention_signature"],
            )
            for world in worlds
        )
    raise ValueError(target)


def _atomic_features(row):
    active_n = int(row["active_node_count"])
    replicate = int(row["replicate"])
    active, _, _, _ = _static_state(active_n, replicate)
    worlds = row["worlds"]
    if len(worlds) != 12:
        raise RuntimeError("v13 requires exactly 12 frozen v12 worlds")

    features = {}

    for index, node in enumerate(active[1:], start=1):
        feature_id = f"FP:{node}"
        features[feature_id] = {
            "family": "FP",
            "values": tuple(
                world["first_passage_signature"][index] for world in worlds
            ),
        }

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
                world["pairwise_relation_signature"][index] for world in worlds
            ),
        }

    for index, removed in enumerate(active[1:]):
        feature_id = f"KO:{removed}"
        features[feature_id] = {
            "family": "KO",
            "values": tuple(
                world["intervention_signature"][index] for world in worlds
            ),
        }

    return features


def _discordant_pairs(target_partition):
    pairs = []
    for i in range(len(target_partition)):
        for j in range(i + 1, len(target_partition)):
            if target_partition[i] != target_partition[j]:
                pairs.append((i, j))
    return tuple(pairs)


def _feature_coverages(features, discordant_pairs):
    rows = []
    for feature_id, spec in sorted(features.items()):
        mask = 0
        for bit, (i, j) in enumerate(discordant_pairs):
            if spec["values"][i] != spec["values"][j]:
                mask |= 1 << bit
        if mask:
            rows.append(
                {
                    "feature_id": feature_id,
                    "family": spec["family"],
                    "mask": mask,
                }
            )
    return tuple(rows)


def _dedup_coverages(rows):
    by_mask = {}
    all_ids_by_mask = {}
    families_by_mask = {}
    for row in rows:
        mask = int(row["mask"])
        all_ids_by_mask.setdefault(mask, []).append(row["feature_id"])
        families_by_mask.setdefault(mask, set()).add(row["family"])
        incumbent = by_mask.get(mask)
        if incumbent is None or row["feature_id"] < incumbent["feature_id"]:
            by_mask[mask] = row
    canonical = tuple(
        sorted(
            (
                {
                    **row,
                    "equivalent_feature_ids": tuple(sorted(all_ids_by_mask[mask])),
                    "equivalent_families": tuple(sorted(families_by_mask[mask])),
                }
                for mask, row in by_mask.items()
            ),
            key=lambda row: row["feature_id"],
        )
    )
    return canonical


def _remove_dominated_for_cardinality(rows):
    # For minimum cardinality only, a coverage mask contained in another single
    # measurement mask can never improve the optimum.
    unique = {}
    for row in rows:
        unique.setdefault(int(row["mask"]), row)
    masks = sorted(unique, key=lambda m: (-m.bit_count(), m))
    kept = []
    for mask in masks:
        if any(mask | other == other for other in kept):
            continue
        kept.append(mask)
    return tuple(unique[mask] for mask in kept)


def _minimum_cardinality(full_mask, rows):
    if full_mask == 0:
        return 0
    reduced = _remove_dominated_for_cardinality(rows)
    current = {0}
    for depth in range(1, len(reduced) + 1):
        next_masks = set()
        for state in current:
            for row in reduced:
                updated = state | int(row["mask"])
                if updated == full_mask:
                    return depth
                next_masks.add(updated)

        # Retain only inclusion-maximal coverage states at this depth.
        ordered = sorted(next_masks, key=lambda m: (-m.bit_count(), m))
        antichain = []
        for mask in ordered:
            if any(mask | other == other for other in antichain):
                continue
            antichain.append(mask)
        current = set(antichain)
    return None


def _canonical_minimum_ids(full_mask, rows, minimum_size):
    if minimum_size == 0:
        return ()
    ordered = tuple(sorted(rows, key=lambda row: row["feature_id"]))
    masks = tuple(int(row["mask"]) for row in ordered)
    ids = tuple(row["feature_id"] for row in ordered)

    suffix_union = [0] * (len(ordered) + 1)
    for i in range(len(ordered) - 1, -1, -1):
        suffix_union[i] = suffix_union[i + 1] | masks[i]

    @lru_cache(maxsize=None)
    def search(start, remaining, covered):
        if remaining == 0:
            return () if covered == full_mask else None
        if len(ordered) - start < remaining:
            return None
        if (covered | suffix_union[start]) != full_mask:
            return None

        max_i = len(ordered) - remaining
        for i in range(start, max_i + 1):
            updated = covered | masks[i]
            tail = search(i + 1, remaining - 1, updated)
            if tail is not None:
                return (ids[i], *tail)
        return None

    result = search(0, int(minimum_size), 0)
    if result is None:
        raise RuntimeError("failed to recover canonical exact minimum")
    return tuple(result)


def _minimum_with_cross_family(full_mask, rows, minimum_size, same_family):
    if minimum_size in (None, 0) or same_family is None:
        return False

    # Exact depth-limited bitmask DP.  The previous combinatorial DFS enumerated
    # feature-ID combinations even when they induced the same coverage state.
    # Here states are only (covered target-discordant pairs, cross-family-used).
    # At a fixed depth, an inclusion-superset state with the same flag dominates a
    # subset state.  A cross-used superset also dominates a non-cross subset because
    # the objective explicitly requires at least one cross-family measurement.
    states_false = {0}
    states_true = set()

    for depth in range(1, int(minimum_size) + 1):
        next_false = set()
        next_true = set()
        for covered in states_false:
            for row in rows:
                updated = covered | int(row["mask"])
                if row["family"] != same_family:
                    next_true.add(updated)
                else:
                    next_false.add(updated)
        for covered in states_true:
            for row in rows:
                next_true.add(covered | int(row["mask"]))

        if full_mask in next_true:
            return depth == int(minimum_size)

        def antichain(masks):
            ordered_masks = sorted(masks, key=lambda m: (-m.bit_count(), m))
            kept = []
            for mask in ordered_masks:
                if any(mask | other == other for other in kept):
                    continue
                kept.append(mask)
            return set(kept)

        next_true = antichain(next_true)
        next_false = antichain(next_false)
        if next_true:
            next_false = {
                mask
                for mask in next_false
                if not any(mask | other == other for other in next_true)
            }

        states_false = next_false
        states_true = next_true

    return False


def _minimum_design(row, target):
    features = _atomic_features(row)
    target_partition = _normalized_partition(_target_values(row, target))
    discordant = _discordant_pairs(target_partition)
    full_mask = (1 << len(discordant)) - 1

    if not discordant:
        return {
            "target_class_count": 1,
            "target_discordant_pair_count": 0,
            "minimum_size": 0,
            "canonical_measurement_ids": [],
            "canonical_families": [],
            "cross_family_minimum_exists": False,
            "complete_library_sufficient": True,
        }

    coverage_rows = _feature_coverages(features, discordant)
    union_mask = 0
    for item in coverage_rows:
        union_mask |= int(item["mask"])
    sufficient = union_mask == full_mask
    if not sufficient:
        return {
            "target_class_count": len(set(target_partition)),
            "target_discordant_pair_count": len(discordant),
            "minimum_size": None,
            "canonical_measurement_ids": None,
            "canonical_families": None,
            "cross_family_minimum_exists": False,
            "complete_library_sufficient": False,
        }

    dedup = _dedup_coverages(coverage_rows)
    minimum = _minimum_cardinality(full_mask, dedup)
    ids = _canonical_minimum_ids(full_mask, dedup, minimum)
    families = tuple(features[feature_id]["family"] for feature_id in ids)

    same_family = {
        "pairwise_relation": "REL",
        "first_passage": "FP",
        "intervention": "KO",
        "critical_node_count": "KO",
    }.get(target)
    cross_exists = _minimum_with_cross_family(
        full_mask,
        dedup,
        minimum,
        same_family,
    )

    return {
        "target_class_count": len(set(target_partition)),
        "target_discordant_pair_count": len(discordant),
        "minimum_size": minimum,
        "canonical_measurement_ids": list(ids),
        "canonical_families": list(families),
        "cross_family_minimum_exists": cross_exists,
        "complete_library_sufficient": True,
    }


def _evaluate_row(active_n, replicate):
    row = evaluate_v12(active_n, replicate)
    features = _atomic_features(row)
    targets = {
        target: _minimum_design(row, target)
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
        "distinct_edge_topology_count": row["distinct_edge_topology_count"],
        "mean_edge_count": float(
            np.mean([world["edge_count"] for world in row["worlds"]])
        ),
        "targets": targets,
    }


def _dist(values):
    return {
        str(key): int(value)
        for key, value in sorted(Counter(values).items(), key=lambda item: str(item[0]))
    }


def _mean(values):
    vals = [float(v) for v in values]
    return None if not vals else float(np.mean(vals))


def _median(values):
    vals = [float(v) for v in values]
    return None if not vals else float(np.median(vals))


def _rankdata(values):
    values = np.asarray(values, dtype=float)
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and values[order[end]] == values[order[start]]:
            end += 1
        ranks[order[start:end]] = (start + 1 + end) / 2.0
        start = end
    return ranks


def _spearman(x, y):
    rx = _rankdata(x)
    ry = _rankdata(y)
    if np.std(rx) == 0 or np.std(ry) == 0:
        return 0.0
    return float(np.corrcoef(rx, ry)[0, 1])


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != (
        "frozen_before_random_relational_sufficiency_implementation_and_scoring"
    ):
        raise RuntimeError("v13 protocol is not frozen")

    rows = [
        _evaluate_row(active_n, replicate)
        for active_n in ACTIVE_SIZES
        for replicate in range(REPLICATES)
    ]
    if len(rows) != 144:
        raise RuntimeError("expected 144 frozen v12 rows")

    unresolved = {
        target: sum(
            not row["targets"][target]["complete_library_sufficient"]
            or row["targets"][target]["minimum_size"] is None
            for row in rows
        )
        for target in TARGETS
    }

    medians = {
        target: _median(
            row["targets"][target]["minimum_size"]
            for row in rows
            if row["targets"][target]["minimum_size"] is not None
        )
        for target in TARGETS
    }
    means = {
        target: _mean(
            row["targets"][target]["minimum_size"]
            for row in rows
            if row["targets"][target]["minimum_size"] is not None
        )
        for target in TARGETS
    }

    class_counts = []
    burdens = []
    for row in rows:
        for target in ("pairwise_relation", "first_passage", "intervention"):
            spec = row["targets"][target]
            if spec["minimum_size"] is not None:
                class_counts.append(spec["target_class_count"])
                burdens.append(spec["minimum_size"])
    rho_class_burden = _spearman(class_counts, burdens)

    s5_violations = 0
    for row in rows:
        joint = row["targets"]["joint_relational_suite"]["minimum_size"]
        for target in ("pairwise_relation", "first_passage", "intervention"):
            value = row["targets"][target]["minimum_size"]
            if joint is None or value is None or joint < value:
                s5_violations += 1

    cross_family_rows = {
        target: sum(
            row["targets"][target]["cross_family_minimum_exists"]
            for row in rows
        )
        for target in (
            "pairwise_relation",
            "first_passage",
            "intervention",
            "critical_node_count",
        )
    }

    canonical_first_ids = {
        ids[0]
        for row in rows
        for target in TARGETS
        for ids in [row["targets"][target]["canonical_measurement_ids"]]
        if ids
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
            "mean_minimum_size": means[target],
            "median_minimum_size": medians[target],
            "cross_family_minimum_exists_rows": (
                cross_family_rows.get(target, 0)
            ),
        }

    by_size = {}
    for active_n in ACTIVE_SIZES:
        subset = [row for row in rows if row["active_node_count"] == active_n]
        by_size[str(active_n)] = {
            target: {
                "minimum_size_distribution": _dist(
                    row["targets"][target]["minimum_size"] for row in subset
                ),
                "mean_minimum_size": _mean(
                    row["targets"][target]["minimum_size"] for row in subset
                ),
                "median_minimum_size": _median(
                    row["targets"][target]["minimum_size"] for row in subset
                ),
            }
            for target in TARGETS
        }

    verdicts = {
        "S1_all_declared_targets_are_resolvable": (
            "SUPPORTED"
            if all(value == 0 for value in unresolved.values())
            else "REFUTED"
        ),
        "S2_random_worlds_break_the_v11_one_measurement_shortcut": (
            "SUPPORTED"
            if medians["first_passage"] > 1 and medians["intervention"] > 1
            else "REFUTED"
        ),
        "S3_intervention_is_informationally_coarser_than_pairwise_relation": (
            "SUPPORTED"
            if means["intervention"] < means["pairwise_relation"]
            else "REFUTED"
        ),
        "S4_target_class_count_predicts_measurement_burden": (
            "SUPPORTED" if rho_class_burden > 0 else "REFUTED"
        ),
        "S5_joint_target_requires_at_least_as_much_information_as_each_component": (
            "SUPPORTED" if s5_violations == 0 else "REFUTED"
        ),
        "S6_cross_family_measurements_remain_useful_in_random_topologies": (
            "SUPPORTED"
            if any(value > 0 for value in cross_family_rows.values())
            else "REFUTED"
        ),
        "S7_full_topology_can_be_identified_without_raw_edge_queries": (
            "SUPPORTED" if unresolved["full_topology_identity"] == 0 else "REFUTED"
        ),
        "S8_no_single_relational_measurement_is_universally_first": (
            "SUPPORTED" if len(canonical_first_ids) > 1 else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_random_relational_sufficiency.result.v13",
        "row_count": len(rows),
        "predeclared_verdicts": verdicts,
        "unresolved_by_target": unresolved,
        "mean_minimum_size_by_target": means,
        "median_minimum_size_by_target": medians,
        "target_class_count_vs_burden_spearman": rho_class_burden,
        "joint_burden_monotonicity_violation_count": s5_violations,
        "cross_family_minimum_rows": cross_family_rows,
        "distinct_canonical_first_measurement_count": len(canonical_first_ids),
        "distinct_canonical_first_measurements": sorted(canonical_first_ids),
        "by_target": by_target,
        "by_active_node_count": by_size,
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
                "mean_minimum_size_by_target": result[
                    "mean_minimum_size_by_target"
                ],
                "median_minimum_size_by_target": result[
                    "median_minimum_size_by_target"
                ],
                "target_class_count_vs_burden_spearman": result[
                    "target_class_count_vs_burden_spearman"
                ],
                "cross_family_minimum_rows": result[
                    "cross_family_minimum_rows"
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
