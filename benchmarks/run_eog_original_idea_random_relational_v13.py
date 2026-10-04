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


def _pair_cover_solver(full_mask, rows):
    rows = tuple(sorted(rows, key=lambda row: row["feature_id"]))
    if full_mask == 0:
        return rows, lambda covered: 0

    bit_to_indices = {}
    bit = 0
    while (1 << bit) <= full_mask:
        if full_mask & (1 << bit):
            bit_to_indices[bit] = tuple(
                i
                for i, row in enumerate(rows)
                if int(row["mask"]) & (1 << bit)
            )
            if not bit_to_indices[bit]:
                raise RuntimeError("uncovered target-discordant pair")
        bit += 1

    @lru_cache(maxsize=None)
    def min_additional(covered):
        if covered == full_mask:
            return 0
        uncovered_bits = [
            bit
            for bit in bit_to_indices
            if not (covered & (1 << bit))
        ]
        chosen_bit = min(
            uncovered_bits,
            key=lambda b: (len(bit_to_indices[b]), b),
        )
        best = None
        for i in bit_to_indices[chosen_bit]:
            updated = covered | int(rows[i]["mask"])
            value = 1 + min_additional(updated)
            if best is None or value < best:
                best = value
        if best is None:
            raise RuntimeError("target cover unexpectedly infeasible")
        return best

    return rows, min_additional


def _canonical_minimum_ids(
    full_mask,
    ordered,
    min_additional,
    minimum_size,
):
    if minimum_size == 0:
        return ()

    @lru_cache(maxsize=None)
    def search(start, remaining, covered):
        if remaining == 0:
            return () if covered == full_mask else None
        if len(ordered) - start < remaining:
            return None

        for i in range(start, len(ordered) - remaining + 1):
            updated = covered | int(ordered[i]["mask"])
            if updated == covered:
                continue
            if min_additional(updated) > remaining - 1:
                continue
            tail = search(i + 1, remaining - 1, updated)
            if tail is not None:
                return (ordered[i]["feature_id"], *tail)
        return None

    result = search(0, int(minimum_size), 0)
    if result is None:
        raise RuntimeError("failed to recover canonical exact minimum")
    return tuple(result)


def _cross_family_minimum_exists(
    ordered,
    min_additional,
    minimum_size,
    same_family,
):
    if minimum_size in (None, 0) or same_family is None:
        return False
    # If one cross-family feature is fixed first, the same exact DP gives the
    # minimum additional measurements needed.  Because the unrestricted optimum is
    # already minimum_size, equality identifies an exact minimum containing a
    # cross-family measurement.
    return any(
        row["family"] != same_family
        and 1 + int(min_additional(int(row["mask"]))) == int(minimum_size)
        for row in ordered
    )


def _minimum_design(row, target, features, partition_cache):
    target_partition = _normalized_partition(_target_values(row, target))
    cache_key = target_partition

    if cache_key not in partition_cache:
        discordant = _discordant_pairs(target_partition)
        full_mask = (1 << len(discordant)) - 1

        if not discordant:
            partition_cache[cache_key] = {
                "target_class_count": 1,
                "target_discordant_pair_count": 0,
                "minimum_size": 0,
                "canonical_measurement_ids": (),
                "canonical_families": (),
                "complete_library_sufficient": True,
                "ordered": (),
                "min_additional": None,
            }
        else:
            coverage_rows = _feature_coverages(features, discordant)
            union_mask = 0
            for item in coverage_rows:
                union_mask |= int(item["mask"])
            sufficient = union_mask == full_mask

            if not sufficient:
                partition_cache[cache_key] = {
                    "target_class_count": len(set(target_partition)),
                    "target_discordant_pair_count": len(discordant),
                    "minimum_size": None,
                    "canonical_measurement_ids": None,
                    "canonical_families": None,
                    "complete_library_sufficient": False,
                    "ordered": (),
                    "min_additional": None,
                }
            else:
                dedup = _dedup_coverages(coverage_rows)
                ordered, min_additional = _pair_cover_solver(full_mask, dedup)
                minimum = int(min_additional(0))
                ids = _canonical_minimum_ids(
                    full_mask,
                    ordered,
                    min_additional,
                    minimum,
                )
                families = tuple(
                    features[feature_id]["family"] for feature_id in ids
                )
                partition_cache[cache_key] = {
                    "target_class_count": len(set(target_partition)),
                    "target_discordant_pair_count": len(discordant),
                    "minimum_size": minimum,
                    "canonical_measurement_ids": ids,
                    "canonical_families": families,
                    "complete_library_sufficient": True,
                    "ordered": ordered,
                    "min_additional": min_additional,
                }

    base = partition_cache[cache_key]
    if not base["complete_library_sufficient"]:
        cross_exists = False
    else:
        same_family = {
            "pairwise_relation": "REL",
            "first_passage": "FP",
            "intervention": "KO",
            "critical_node_count": "KO",
        }.get(target)
        cross_exists = _cross_family_minimum_exists(
            base["ordered"],
            base["min_additional"],
            base["minimum_size"],
            same_family,
        )

    return {
        "target_class_count": base["target_class_count"],
        "target_discordant_pair_count": base["target_discordant_pair_count"],
        "minimum_size": base["minimum_size"],
        "canonical_measurement_ids": (
            None
            if base["canonical_measurement_ids"] is None
            else list(base["canonical_measurement_ids"])
        ),
        "canonical_families": (
            None
            if base["canonical_families"] is None
            else list(base["canonical_families"])
        ),
        "cross_family_minimum_exists": cross_exists,
        "complete_library_sufficient": base["complete_library_sufficient"],
    }


def _evaluate_row(active_n, replicate):
    row = evaluate_v12(active_n, replicate)
    features = _atomic_features(row)
    partition_cache = {}
    targets = {
        target: _minimum_design(
            row,
            target,
            features,
            partition_cache,
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
