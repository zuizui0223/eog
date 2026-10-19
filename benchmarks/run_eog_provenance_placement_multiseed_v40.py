#!/usr/bin/env python3
"""Post-v39-exposure fixed-seed placement robustness under known-truth provenance.

This is a synthetic known-truth test only. Random *placements* are varied,
not biological histories, data sources, fitting hyperparameters, or the v39
observation channel. No 2021 genotype, bird or field-effort data are accessed.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.run_eog_imperfect_provenance_sampling_v39 import (
    AUTOCORR_LEVELS, BARRIER_LEVELS, NEIGHBOURHOODS, REPLICATES,
    DESIGNS, RULE, SEED as OLD_SEED,
    _generate_base, _outlet_corner, _truth_source,
    _candidate_sources, _source_sets, _graphs,
    bayes_information, prepare_design,
)

V39 = ROOT / "validation/eog_original_idea_imperfect_provenance_v39/result_frozen_v39.json"
V23 = ROOT / "validation/eog_original_idea_provenance_observability_v23/result_summary_v23.json"
PROTOCOL = ROOT / "validation/eog_original_idea_provenance_placement_multiseed_v40/protocol_v40.json"
SCHEMA = "eog.original_idea.noisy_provenance_placement_multiseed.result.v40"
PREDECLARED_SHA = "eefbd3c2ef69e532d6efc5fef66fd7ec97def75e6dd6b74d533d042e78aaa865"
SOURCE_SCHEMAS = (
    "eog.original_idea_provenance_observability.result_summary.v23",
    "eog.original_idea.imperfect_source_provenance_sampling.frozen_review_v39",
)
SEED_PREFIX = "eog-v40-20261019-random-seed-"
Q, E = 0.6, 0.1
TOL = 1e-9
BUDGET = 3
SEED_COUNT = 64
HYPOTHESES = (
    "M1_material_targeting_advantage",
    "M2_targeting_outperforms_most_independent_random_placements",
    "M3_per_world_targeting_consistency",
    "M4_random_seed_effect_not_hidden",
    "M5_raw_source_overlap_is_imperfect_information_proxy",
)
BOUNDS = {
    "post_v39_exposure_sensitivity_not_independent_preregistered_conformation": True,
    "random_seeds_not_independent_ecological_replicates": True,
    "sampling_site_budget_is_equal_but_observation_costs_not_calibrated": True,
    "no_empirical_genetic_origin_assignment_accuracy_or_field_effort_estimated": True,
    "no_heldout_genetic_EOG_predictive_endpoint": True,
    "no_unique_true_colonization_history_identified": True,
    "v39_parent_protocol_and_EOG_WF_3_31_3_unchanged": True,
}


def _verify(policy: dict, v39: dict, v23: dict) -> None:
    if (
        policy.get("schema") !=
            "eog.original_idea.noisy_provenance_placement_multiseed.protocol.v40"
        or policy.get("status") !=
            "FROZEN_BEFORE_V40_RANDOM_SEED_ENSEMBLE_EVALUATION__POST_V39_EXPOSURE"
        or v39.get("schema") != SOURCE_SCHEMAS[1]
        or v23.get("schema") != SOURCE_SCHEMAS[0]
        or v23.get("result_fingerprint") !=
            "ab37b83de94fce5e6d35918b9f5730a63364cebf0bb00ec662eececc5ae85244"
    ):
        raise ValueError("Predeclared protocol or v23/v39 source identity changed")
    parent = policy.get("parent", {})
    if not (
        parent.get("base_commit") == "9b15962341594d9936410067706db72a705d39c3"
        and parent.get("full_v39_result_sha256") == PREDECLARED_SHA
        and v39["authority"]["canonical_full_result_sha256"] == PREDECLARED_SHA
        and parent.get("v23_fingerprint") == v23["result_fingerprint"]
        and parent.get("matched_full_design_rows") == 768
        and parent.get("occupancy_ambiguous_rows") == 189
        and parent.get("equal_budget_occupancy_ambiguous_rows") == 88
        and parent.get("old_one_seed_target_bits") ==
            v39["primary_fixed_setting"]["confluence_targeted"]["mean_information_bits"]
        and parent.get("old_one_seed_random_bits") ==
            v39["primary_fixed_setting"]["random_response_blind"]["mean_information_bits"]
    ):
        raise ValueError("Frozen parent original experiment/one-seed result changed")
    c = policy.get("design", {})
    if not (
        c.get("site_budget") == BUDGET
        and c.get("ensemble_count") == SEED_COUNT
        and c.get("seed_prefix") == SEED_PREFIX
        and c.get("original_v39_seed") == OLD_SEED
        and c.get("observation_coverage") == Q
        and c.get("categorical_miscall") == E
        and c.get("sensitivity_setting") ==
            {"coverage": 1.0, "miscall": 0.0,
             "role": "optional separate perfect-tag upper diagnostics ONLY, not a replacement for q=.6/e=.1"}
        and c.get("no_2021_empirical_genetic_data") is True
        and c.get("no_real_field_sampling_costs") is True
    ):
        raise ValueError("Response-blind random seeds or noisy provenance channel changed")
    estimands = policy.get("estimands", {})
    if (
        estimands.get("materiality_threshold_bits") != 0.02
        or estimands.get("no_new_heldout_endpoint") is not True
        or policy.get("scientific_boundaries") != BOUNDS
        or tuple(row.get("id") for row in policy.get("falsifiable_hypotheses", ())) != HYPOTHESES
    ):
        raise ValueError("Primary nontrivial hypothesis threshold or claims changed")


def rank_random_sites(site_names: tuple[str, ...], design_key: str, seed_index: int) -> tuple[str, ...]:
    """Never use actual provenance tag readouts to rank measurement sites."""
    if not 0 <= seed_index < SEED_COUNT:
        raise ValueError("Use exactly the sixty-four frozen seed indices")
    seed = f"{SEED_PREFIX}{seed_index:03d}"
    return tuple(sorted(
        site_names,
        key=lambda node: (
            hashlib.sha256(f"{seed}|{design_key}|{node}".encode("utf-8")).hexdigest(),
            node,
        )
    )[:BUDGET])


def _metric(x: dict, nodes: tuple[str, ...], q=Q, e=E) -> tuple[float, float]:
    result = bayes_information(
        x["occupancy"], x["provenance_tags"], nodes, q, e
    )
    return result["additional_information_bits"], result["bayes_accuracy_gain"]


def _mean(xs):
    if not xs:
        return None
    return sum(xs) / len(xs)


def _quantile(xs, q):
    if not xs:
        return None
    v = sorted(xs)
    i = (len(v) - 1) * q
    lo = int(i)
    hi = min(lo+1, len(v)-1)
    return v[lo] if lo == hi else v[lo] * (hi-i) + v[hi] * (i-lo)


def evaluate(seed_count=SEED_COUNT):
    if seed_count != SEED_COUNT:
        raise ValueError("Exactly 64 seeds are precommitted; subset scoring forbidden")
    policy = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    v39 = json.loads(V39.read_text(encoding="utf-8"))
    v23 = json.loads(V23.read_text(encoding="utf-8"))
    _verify(policy, v39, v23)

    all_count = 0
    occupancy_ident_count = 0
    occ_aliased = 0
    equal_budget = 0
    original_target = []
    original_random = []
    perfect_target = []
    original_target_accuracy = []
    perfect_seed_values = [[] for _ in range(SEED_COUNT)]
    seed_information = [[] for _ in range(SEED_COUNT)]
    seed_accuracy = [[] for _ in range(SEED_COUNT)]
    per_world_advantage = []
    per_world_random_spread = []
    per_world_origin_constant_count = []
    confluence_total_selected = 0
    confluence_history_invariant = 0
    random_confluence_count = 0
    geometry = defaultdict(lambda: {
        "target_info": [], "random_info": [], "target_accuracy": [],
        "random_accuracy": [], "invariant_selected": 0, "selected": 0,
    })
    seed_id_and_hash_unique = set()

    for autocorr in AUTOCORR_LEVELS:
        for neighbourhood in NEIGHBOURHOODS:
            for replicate in range(REPLICATES):
                base = _generate_base(replicate, autocorr, neighbourhood)
                outlet = _outlet_corner(replicate, autocorr, neighbourhood)
                anchor = _truth_source(base, outlet)
                candidates, _ = _candidate_sources(base, outlet, anchor)
                source_sets = _source_sets(candidates, anchor)
                if not source_sets:
                    raise ValueError("Parent design became ineligible")
                for barrier in BARRIER_LEVELS:
                    _, graph = _graphs(base, barrier, RULE, outlet)
                    for design in DESIGNS:
                        all_count += 1
                        sources = source_sets[design][3]
                        key = f"{replicate}|{autocorr}|{neighbourhood}|{barrier}|{design}"
                        x = prepare_design(graph, sources, key)
                        occupancy_ident_count += int(x["occupancy_exact_history_identifiable"])
                        if x["occupancy_exact_history_identifiable"]:
                            continue
                        occ_aliased += 1
                        if not x["equal_budget_eligible"]:
                            continue
                        equal_budget += 1
                        target_nodes = tuple(x["selected"]["confluence_targeted"])
                        random_39_nodes = tuple(x["selected"]["random_response_blind"])
                        if len(target_nodes) != BUDGET or len(random_39_nodes) != BUDGET:
                            raise ValueError("Confluence and original random budgets not equal")
                        target_info, target_accuracy = _metric(x, target_nodes)
                        previous_random_info, _ = _metric(x, random_39_nodes)
                        original_target.append(target_info)
                        original_target_accuracy.append(target_accuracy)
                        original_random.append(previous_random_info)
                        perfect_target.append(_metric(x, target_nodes, 1.0, 0.0)[0])
                        per_seed_world_info = []
                        per_seed_world_accuracy = []
                        for seed in range(SEED_COUNT):
                            random_nodes = rank_random_sites(
                                tuple(sorted(x["provenance_tags"])), key, seed
                            )
                            if len(random_nodes) != BUDGET:
                                raise ValueError("A random budget is missing candidate nodes")
                            seed_id_and_hash_unique.add((key, seed))
                            info, accuracy = _metric(x, random_nodes)
                            seed_information[seed].append(info)
                            seed_accuracy[seed].append(accuracy)
                            perfect_seed_values[seed].append(
                                _metric(x, random_nodes, 1.0, 0.0)[0]
                            )
                            per_seed_world_info.append(info)
                            per_seed_world_accuracy.append(accuracy)
                            random_confluence_count += sum(
                                node in x["selected"]["confluence_targeted"]
                                for node in random_nodes
                            )
                        mean_random_info = _mean(per_seed_world_info)
                        mean_random_accuracy = _mean(per_seed_world_accuracy)
                        per_world_advantage.append(target_info - mean_random_info)
                        per_world_random_spread.append(
                            max(per_seed_world_info) - min(per_seed_world_info)
                        )
                        invariants = sum(
                            len(set(x["provenance_tags"][node].values())) == 1
                            for node in target_nodes
                        )
                        per_world_origin_constant_count.append(invariants)
                        confluence_total_selected += BUDGET
                        confluence_history_invariant += invariants
                        record = geometry[design]
                        record["target_info"].append(target_info)
                        record["random_info"].append(mean_random_info)
                        record["target_accuracy"].append(target_accuracy)
                        record["random_accuracy"].append(mean_random_accuracy)
                        record["invariant_selected"] += invariants
                        record["selected"] += BUDGET

    if (all_count, occupancy_ident_count, occ_aliased, equal_budget) != (
        768, 579, 189, 88
    ):
        raise ValueError("v23/v39 same-world denominator did not reconcile")
    if len(seed_id_and_hash_unique) != 88 * SEED_COUNT:
        raise ValueError("The seed/world placement grid is not complete")
    if len(original_target) != equal_budget or any(
        len(a) != 88 for a in seed_information + seed_accuracy + perfect_seed_values
    ):
        raise ValueError("Missing whole-world placement outcome")
    previous_target_mean = _mean(original_target)
    previous_random_mean = _mean(original_random)
    if not (
        abs(previous_target_mean - policy["parent"]["old_one_seed_target_bits"]) < TOL
        and abs(previous_random_mean - policy["parent"]["old_one_seed_random_bits"]) < TOL
    ):
        raise ValueError("Original v39 selected-target and random-seed results changed")

    seed_means = [_mean(vals) for vals in seed_information]
    seed_accuracy_means = [_mean(vals) for vals in seed_accuracy]
    seed_perfect_means = [_mean(vals) for vals in perfect_seed_values]
    random_ensemble_info = _mean(seed_means)
    random_ensemble_accuracy = _mean(seed_accuracy_means)
    perfect_random = _mean(seed_perfect_means)
    # Recompute the same target Bayes accuracy from every one of the 88
    # fixed designs, and independently reconcile the previous v39 baseline.
    target_average_accuracy = _mean(original_target_accuracy)
    if not abs(target_average_accuracy - 0.33305599621211984) < TOL:
        raise ValueError("v39 correct-history accuracy baseline drifted")

    mean_advantage = previous_target_mean - random_ensemble_info
    seed_differences = [previous_target_mean - x for x in seed_means]
    positive = sum(a > TOL for a in per_world_advantage)
    negative = sum(a < -TOL for a in per_world_advantage)
    tied = len(per_world_advantage) - positive - negative
    seed_positive = sum(d > TOL for d in seed_differences)

    hypotheses = {
        HYPOTHESES[0]: "SUPPORTED" if mean_advantage > 0.02 + TOL else "REFUTED",
        HYPOTHESES[1]: "SUPPORTED" if seed_positive >= 48 else "REFUTED",
        HYPOTHESES[2]: "SUPPORTED" if positive > 44 else "REFUTED",
        HYPOTHESES[3]: "SUPPORTED" if max(seed_means)-min(seed_means) > TOL else "REFUTED",
        HYPOTHESES[4]: "SUPPORTED" if confluence_history_invariant > 0 else "REFUTED",
    }

    geometry_summary = []
    for design in DESIGNS:
        vals = geometry[design]
        n = len(vals["target_info"])
        if n <= 0:
            continue
        geometry_summary.append({
            "source_geometry": design, "n_equal_budget_occupancy_aliased": n,
            "target_mean_information_bits": _mean(vals["target_info"]),
            "seed_mean_random_information_bits": _mean(vals["random_info"]),
            "target_minus_random_information_bits":
                _mean(vals["target_info"]) - _mean(vals["random_info"]),
            "target_mean_bayes_accuracy_gain": _mean(vals["target_accuracy"]),
            "seed_mean_random_bayes_accuracy_gain": _mean(vals["random_accuracy"]),
            "number_invariant_targeted_confluence_sites": vals["invariant_selected"],
            "number_targeted_sites": vals["selected"],
        })

    return {
        "schema": SCHEMA,
        "status": "POST_V39_MULTISEED_RANDOM_PLACEMENT_SENSITIVITY__NO_REAL_GENETIC_VALIDATION",
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "protocol_freeze_before_new_random_ensemble": True,
        "parent_reconciliation": {
            "v39_full_result_sha256": PREDECLARED_SHA,
            "design_rows": all_count,
            "four_snapshot_occupancy_history_identifiable": occupancy_ident_count,
            "four_snapshot_occupancy_aliased": occ_aliased,
            "fair_equal_budget_three_site_aliased": equal_budget,
            "v39_one_seed_confluence_information_bits": previous_target_mean,
            "v39_one_seed_random_information_bits": previous_random_mean,
        },
        "primary": {
            "n_worlds": equal_budget, "new_random_seed_count": SEED_COUNT,
            "coverage": Q, "miscall": E, "site_count_per_policy": BUDGET,
            "confluence_fixed_mean_information_bits": previous_target_mean,
            "random_64_seed_mean_information_bits": random_ensemble_info,
            "target_minus_random_64_seed_information_bits": mean_advantage,
            "materiality_threshold_bits": 0.02,
            "fixed_target_mean_bayes_accuracy_gain": target_average_accuracy,
            "random_64_seed_mean_bayes_accuracy_gain": random_ensemble_accuracy,
            "target_minus_random_64_seed_accuracy_gain":
                target_average_accuracy - random_ensemble_accuracy,
            "mean_perfect_confluence_information_bits": _mean(perfect_target),
            "mean_perfect_random_64_seed_information_bits": perfect_random,
        },
        "seed_ensemble": {
            "all_64_seed_world_averages": [
                {"seed_index":i, "random_mean_information_bits": seed_means[i],
                 "random_mean_accuracy_gain": seed_accuracy_means[i],
                 "confluence_minus_seed_mean_information_bits": seed_differences[i]}
                for i in range(SEED_COUNT)
            ],
            "random_information_mean_min": min(seed_means),
            "random_information_mean_median": statistics.median(seed_means),
            "random_information_mean_max": max(seed_means),
            "random_information_q10": _quantile(seed_means,0.10),
            "random_information_q90": _quantile(seed_means,0.90),
            "random_seed_count_target_outperforms": seed_positive,
            "random_seed_fraction_target_outperforms": seed_positive/SEED_COUNT,
        },
        "world_paired_placement": {
            "strict_target_better_than_64_seed_mean": positive,
            "indistinguishable_within_1e_minus_9": tied,
            "strict_target_worse_than_64_seed_mean": negative,
            "mean_world_level_advantage_bits": _mean(per_world_advantage),
            "median_world_level_advantage_bits": statistics.median(per_world_advantage),
            "median_within_world_seed_information_range_bits":
                statistics.median(per_world_random_spread),
        },
        "mechanism_posthoc_not_assay_selection": {
            "selected_static_potential_confluence_site_count": confluence_total_selected,
            "history_invariant_potential_confluence_site_count": confluence_history_invariant,
            "worlds_with_at_least_one_history_invariant_targeted_confluence_site":
                sum(n>0 for n in per_world_origin_constant_count),
            "random_sites_overlapping_fixed_target_total_over_all_seeds": random_confluence_count,
            "history_specific_labels_used_for_site_placement": False,
        },
        "source_geometry": geometry_summary,
        "predeclared_verdicts": hypotheses,
        "scientific_boundaries": BOUNDS,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    x = evaluate()
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("Refuse to replace existing benchmark evidence")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as fd:
        json.dump(x, fd, ensure_ascii=False, sort_keys=True, indent=2)
        fd.write("\n")
    print(json.dumps({
        "status": x["status"], "target_minus_seed_mean":x["primary"]["target_minus_random_64_seed_information_bits"],
        "verdicts":x["predeclared_verdicts"], "empirical_genetic_data_read":False,
    }))


if __name__ == "__main__":
    main()
