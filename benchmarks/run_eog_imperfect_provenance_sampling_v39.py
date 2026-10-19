#!/usr/bin/env python3
"""v39: exact-information test of noisy/missing source tags at confluence sites.

All latent landscapes, directed graphs, three activation histories and four
occupancy snapshots are reused from fixed v23. This is *synthetic* provenance,
NOT true SNP ancestry or empirically calibrated genetic assignment error.
No new EOG-WF model, empirical endpoint or 2021 Dryad bird rows are used.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from itertools import product
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.run_eog_original_idea_virtual_worlds_v2 import (
    AUTOCORR_LEVELS, BARRIER_LEVELS, NEIGHBOURHOODS,
    REPLICATES, _generate_base, _node_id,
)
from benchmarks.run_eog_original_idea_directed_temporal_flow_v5 import (
    _graphs, _outlet_corner, _truth_source,
)
from benchmarks.run_eog_original_idea_source_placement_v18 import (
    DESIGNS, RULE, _candidate_sources, _source_sets,
)
from benchmarks.run_eog_original_idea_source_history_memory_v21 import (
    ACTIVATION_HISTORIES,
)
from benchmarks.run_eog_original_idea_history_observability_v22 import (
    SNAPSHOT_TIMES, _arrival_structure, _distances, _snapshot_signature,
)

PROTOCOL = ROOT / "validation/eog_original_idea_imperfect_provenance_v39/protocol_v39.json"
PARENT = ROOT / "validation/eog_original_idea_provenance_observability_v23/result_summary_v23.json"
RESULT_SCHEMA = "eog.original_idea.imperfect_source_provenance_sampling.result.v39"
POLICIES = ("confluence_targeted", "random_response_blind", "unique_origin_negative_control")
COVERAGE = (0.0, 0.25, 0.6, 1.0)
ERRORS = (0.0, 0.1, 0.25)
K = 3
SEED = "eog-v39-20261019-fixed-rank"


def _verify(p: dict, parent: dict) -> None:
    if (
        p.get("schema") != "eog.original_idea.imperfect_source_provenance_sampling.protocol.v39"
        or p.get("status") !=
            "FROZEN_BEFORE_IMPERFECT_SOURCE_TAG_MISSINGNESS_AND_ERROR_SCORING"
        or p.get("parent", {}).get("v23_result_fingerprint") !=
            "ab37b83de94fce5e6d35918b9f5730a63364cebf0bb00ec662eececc5ae85244"
        or p.get("parent", {}).get("parent_design_rows") != 768
        or p.get("parent", {}).get("parent_occupancy_exact_identifiable") != 579
        or p.get("parent", {}).get("parent_full_perfect_provenance_plus_occupancy_identifiable") != 687
        or parent.get("result_fingerprint") !=
            p["parent"]["v23_result_fingerprint"]
        or parent.get("design_row_count") != 768
        or parent["summary_by_library"]["occupancy_only"]["full_history_identifiable_rows"] != 579
        or parent["summary_by_library"]["combined"]["full_history_identifiable_rows"] != 687
    ):
        raise ValueError("Predeclared v23 source and baseline cannot be reproduced")
    design = p["fixed_stochastic_world_design"]
    if not (
        design["base_rows"] == 384
        and design["source_geometries"] == list(DESIGNS)
        and design["ecological_autocorrelation"] == list(AUTOCORR_LEVELS)
        and design["neighbourhood"] == list(NEIGHBOURHOODS)
        and design["barrier_densities"] == list(BARRIER_LEVELS)
        and design["replicates_per_ecological_factor_cell"] == REPLICATES == 32
        and design["full_occupancy_snapshots"] == list(SNAPSHOT_TIMES)
        and design["exact_three_activation_histories"] is True
    ):
        raise ValueError("The frozen v23 latent design changed")
    a = p["provenance_assay"]
    if not (
        a["selection_budget"] == K
        and a["coverage_probabilities"] == list(COVERAGE)
        and a["misassignment_probabilities"] == list(ERRORS)
        and a["random_selection_seed"] == SEED
        and a["noise_model_is_synthetic_not_saatoglu_empirically_calibrated"] is True
        and a["no_outcome_dependent_assay_placement"] is True
        and set(a["policies"]) == set(POLICIES)
        and len(p.get("predeclared_hypotheses", [])) == 5
    ):
        raise ValueError("Frozen source-tag observation model or predictions altered")
    if p.get("scientific_boundaries") != {
        "new_EOG_WF_endpoint_scored": False,
        "empirical_genotype_snp_data_read": False,
        "genetic_assignments_or_parentage_modeled_as_truth": False,
        "real_world_survey_effort_or_2021_error_rates_estimated": False,
        "original_v23_v38_results_changed": False,
        "site_selection_uses_truth_origin_labels": False,
        "inference_limited_to_fixed_declared_synthetic_worlds": True,
        "nonzero_information_is_not_measured_actual_colonization": True,
    }:
        raise ValueError("Biological claim boundary was widened")


def _entropy(probs):
    return -sum(p * math.log2(p) for p in probs if p > 0)


def bayes_information(
    occupancy: dict[str, object],
    action_values: dict[str, dict[str, object]],
    chosen: tuple[str, ...],
    coverage: float,
    error: float,
) -> dict:
    """Exact observation-distribution enumeration; no random response draws.

    Each of 3 possible activation histories has prior 1/3. Occupancy is
    exact and deterministic; noisy categorical reports are conditionally
    independent with a synthetically declared confusion channel.
    """
    names = tuple(sorted(occupancy))
    if len(names) != 3:
        raise ValueError("Exactly three declared activation histories required")
    if not (0 <= coverage <= 1 and 0 <= error <= 0.25):
        raise ValueError("Noise parameters outside frozen model range")
    if len(chosen) > K or any(node not in action_values for node in chosen):
        raise ValueError("Assay choice not in the available library")

    by_occupancy = defaultdict(list)
    for h in names:
        by_occupancy[occupancy[h]].append(h)
    base_entropy = sum(len(h) / 3 * math.log2(len(h)) for h in by_occupancy.values())
    base_accuracy = len(by_occupancy) / 3

    if not chosen or coverage == 0:
        return {
            "additional_information_bits": 0.0,
            "bayes_accuracy_gain": 0.0,
            "baseline_conditional_entropy_bits": base_entropy,
            "baseline_bayes_accuracy": base_accuracy,
        }

    report_domains = []
    probabilities = {}
    for node in chosen:
        true_values = action_values[node]
        if set(true_values) != set(names):
            raise ValueError("All three latent histories require an ideal provenance tag")
        # Include an unobserved outside-model label. This creates a nonzero
        # synthetic wrong-report channel even at single-label (uninformative)
        # sites without inventing a new biological source population.
        actual_tags = tuple(sorted(set(true_values.values())))
        unseen = ("__synthetic_unseen__",)
        if unseen in actual_tags:
            raise ValueError("Synthetic UNSEEN category collides with a source tag")
        catalog = actual_tags + (unseen,)
        domain = (None,) + catalog
        report_domains.append(domain)
        Kcats = len(catalog)
        for h in names:
            d = {None: 1.0 - coverage}
            for report in catalog:
                d[report] = coverage * (
                    1.0 - error if report == true_values[h]
                    else error / (Kcats - 1)
                )
            if abs(sum(d.values()) - 1.0) > 1e-12:
                raise RuntimeError("Synthetic misassignment channel is not normalized")
            probabilities[(node, h)] = d

    expected_conditional_entropy = 0.0
    observed_bayes_accuracy = 0.0

    for reports in product(*report_domains):
        for histclass in by_occupancy.values():
            weights = []
            for h in histclass:
                likelihood = 1.0
                for node, report in zip(chosen, reports, strict=True):
                    likelihood *= probabilities[(node, h)][report]
                weights.append(likelihood / 3.0)
            p_outcome = sum(weights)
            if p_outcome <= 0:
                continue
            observed_bayes_accuracy += max(weights)
            expected_conditional_entropy -= sum(
                w * math.log2(w / p_outcome) for w in weights if w > 0
            )

    info = base_entropy - expected_conditional_entropy
    gain = observed_bayes_accuracy - base_accuracy
    if info < -1e-8 or gain < -1e-8:
        raise ValueError("Correct Bayesian evidence cannot increase expected uncertainty/risk")
    if abs(info) < 1e-11:
        info = 0.0
    if abs(gain) < 1e-11:
        gain = 0.0
    return {
        "additional_information_bits": max(0.0, info),
        "bayes_accuracy_gain": max(0.0, gain),
        "baseline_conditional_entropy_bits": base_entropy,
        "baseline_bayes_accuracy": base_accuracy,
    }


def prepare_design(graph, sources, design_key: str) -> dict:
    """Recreate v23 truth worlds WITHOUT consulting answers to select sites."""
    distances = _distances(graph, sources)
    source_set = frozenset(sources)
    histories = {}
    for h, activation_times in ACTIVATION_HISTORIES.items():
        equilibrium_union, first_arrival, earliest_map = _arrival_structure(
            distances, sources, activation_times
        )
        histories[h] = {
            "equilibrium_union": equilibrium_union,
            "snapshots": tuple(
                _snapshot_signature(equilibrium_union, first_arrival, source_set, time)
                for time in SNAPSHOT_TIMES
            ),
            "tags": {
                node: tuple(sorted(_node_id(s) for s in earliest_map[node]))
                for node in equilibrium_union if node not in source_set
            },
        }
    unions = {tuple(sorted(x["equilibrium_union"])) for x in histories.values()}
    if len(unions) != 1:
        raise RuntimeError("Parent v23 histories have distinct equilibrium unions")
    nodes = tuple(sorted(n for n in next(iter(histories.values()))["equilibrium_union"] if n not in source_set))
    obs = {h: item["snapshots"] for h, item in histories.items()}
    action_values = {
        _node_id(node): {h: histories[h]["tags"][node] for h in histories}
        for node in nodes
    }
    source_cover = {
        _node_id(node): sum(int(node in distances[s]) for s in sources)
        for node in nodes
    }
    confluence = tuple(sorted(
        (node for node in action_values if source_cover[node] >= 2),
        key=lambda node: (-source_cover[node], node),
    ))
    unique = tuple(sorted(node for node in action_values if source_cover[node] == 1))
    response_blind = tuple(sorted(
        action_values,
        key=lambda node: (
            hashlib.sha256(f"{SEED}|{design_key}|{node}".encode()).hexdigest(), node
        )
    ))
    chosen = {
        "confluence_targeted": confluence[:K],
        "random_response_blind": response_blind[:K],
        "unique_origin_negative_control": unique[:K],
    }
    ideal_complete_sig = {
        h: (obs[h], tuple(action_values[node][h] for node in sorted(action_values)))
        for h in histories
    }
    return {
        "occupancy": obs,
        "provenance_tags": action_values,
        "selected": chosen,
        "occupancy_exact_history_identifiable": len(set(obs.values())) == len(histories),
        "complete_ideal_occupancy_provenance_identifiable":
            len(set(ideal_complete_sig.values())) == len(histories),
        "static_confluence_site_count": len(confluence),
        "static_unique_origin_site_count": len(unique),
        "equal_budget_eligible": len(confluence) >= K and len(response_blind) >= K,
    }


def _mean(x):
    return None if not x else sum(x) / len(x)


def _get(stats, policy, q, e, subset):
    return stats[(policy, q, e, subset)]


def run() -> dict:
    p = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    parent = json.loads(PARENT.read_text(encoding="utf-8"))
    _verify(p, parent)
    stats = defaultdict(list)
    selected_n = defaultdict(list)
    count_design = 0
    occupancy_ident = 0
    ideal_combined_ident = 0
    aliased_count = 0
    equal_aliased_count = 0
    max_unique_info = 0.0
    max_negative_gain = 0.0
    zero_coverage_violations = 0
    by_design = defaultdict(list)
    for autocorr in AUTOCORR_LEVELS:
        for neighbourhood in NEIGHBOURHOODS:
            for replicate in range(REPLICATES):
                base = _generate_base(replicate, autocorr, neighbourhood)
                outlet = _outlet_corner(replicate, autocorr, neighbourhood)
                anchor = _truth_source(base, outlet)
                candidates, _ = _candidate_sources(base, outlet, anchor)
                source_sets = _source_sets(candidates, anchor)
                for density in BARRIER_LEVELS:
                    _, graph = _graphs(base, density, RULE, outlet)
                    if not source_sets:
                        raise RuntimeError("Parent v23 row unexpectedly ineligible")
                    for design in DESIGNS:
                        sources = source_sets[design][3]
                        key = f"{replicate}|{autocorr}|{neighbourhood}|{density}|{design}"
                        x = prepare_design(graph, sources, key)
                        count_design += 1
                        ident = x["occupancy_exact_history_identifiable"]
                        occupancy_ident += int(ident)
                        ideal_combined_ident += int(
                            x["complete_ideal_occupancy_provenance_identifiable"]
                        )
                        if not ident:
                            aliased_count += 1
                            if x["equal_budget_eligible"]:
                                equal_aliased_count += 1
                        for policy in POLICIES:
                            actions = x["selected"][policy]
                            for q in COVERAGE:
                                for e in ERRORS:
                                    metric = bayes_information(
                                        x["occupancy"], x["provenance_tags"],
                                        actions, q, e
                                    )
                                    for subset in (
                                        ("all",) +
                                        (("occupancy_aliased",) if not ident else ()) +
                                        (("equal_budget_aliased",)
                                         if not ident and x["equal_budget_eligible"] else ())
                                    ):
                                        stats[(policy, q, e, subset)].append(metric)
                                        selected_n[(policy, q, e, subset)].append(len(actions))
                                    if policy == "unique_origin_negative_control":
                                        max_unique_info = max(max_unique_info, metric["additional_information_bits"])
                                        max_negative_gain = max(max_negative_gain, metric["bayes_accuracy_gain"])
                                    if q == 0 and (metric["additional_information_bits"] > 1e-9 or
                                                   metric["bayes_accuracy_gain"] > 1e-9):
                                        zero_coverage_violations += 1
                                    if not ident and q == 0.6 and e == 0.1:
                                        by_design[(design, policy)].append(metric)

    if count_design != 768 or occupancy_ident != 579 or ideal_combined_ident != 687:
        raise ValueError(
            f"v23 parent landscape identifiability drifted: {count_design}, "
            f"{occupancy_ident}, {ideal_combined_ident}"
        )
    if aliased_count != 189:
        raise ValueError("v23 exact four-snapshot occupancy alias count changed")

    summary = []
    for policy in POLICIES:
        for q in COVERAGE:
            for e in ERRORS:
                for subset in ("all", "occupancy_aliased", "equal_budget_aliased"):
                    vals = _get(stats, policy, q, e, subset)
                    summary.append({
                        "policy": policy, "coverage": q, "miscall": e, "subset": subset,
                        "n_design_rows": len(vals),
                        "mean_additional_information_bits": _mean(
                            [v["additional_information_bits"] for v in vals]),
                        "mean_bayes_accuracy_gain": _mean(
                            [v["bayes_accuracy_gain"] for v in vals]),
                        "mean_selected_site_count": _mean(
                            selected_n[(policy, q, e, subset)]),
                    })

    def s(policy, q, e, subset):
        x = next(
            v for v in summary
            if v["policy"] == policy and v["coverage"] == q and
               v["miscall"] == e and v["subset"] == subset
        )
        return x["mean_additional_information_bits"], x["mean_bayes_accuracy_gain"], x["n_design_rows"]

    def nzero(value, tol=1e-9):
        return value is not None and abs(value) <= tol

    monotone_violations = 0
    for policy in POLICIES:
        values = [s(policy, 0.6, e, "all")[0] for e in ERRORS]
        if any(values[i] + 1e-9 < values[i + 1] for i in range(len(values)-1)):
            monotone_violations += 1
        values = [s(policy, q, 0.1, "all")[0] for q in COVERAGE]
        if any(values[i] > values[i + 1] + 1e-9 for i in range(len(values)-1)):
            monotone_violations += 1

    cf = s("confluence_targeted", 0.6, 0.1, "equal_budget_aliased")
    rd = s("random_response_blind", 0.6, 0.1, "equal_budget_aliased")
    perfect = s("confluence_targeted", 1.0, 0.0, "equal_budget_aliased")
    verdicts = {
        "P1_confluence_positive_information_under_perfect_assay":
            "SUPPORTED" if perfect[2] > 0 and perfect[0] > 1e-9 else "REFUTED",
        "P2_unique_origin_site_tags_never_resolve_history":
            "SUPPORTED" if nzero(max_unique_info) and nzero(max_negative_gain) else "REFUTED",
        "P3_targeted_confluence_beats_random_under_noisy_assay":
            "SUPPORTED" if cf[2] > 0 and cf[0] > rd[0] + 1e-9 else "REFUTED",
        "P4_noise_and_missingness_reduce_information":
            "SUPPORTED" if monotone_violations == 0 else "REFUTED",
        "P5_imperfect_genetic_analogue_retains_positive_information":
            "SUPPORTED" if cf[2] > 0 and cf[1] > 1e-9 else "REFUTED",
    }

    by_geometry = []
    for design in DESIGNS:
        for policy in POLICIES:
            vals = by_design[(design, policy)]
            by_geometry.append({
                "source_geometry": design,
                "policy": policy, "coverage": 0.6, "miscall": 0.1,
                "n_aliased": len(vals),
                "mean_additional_information_bits": _mean(
                    [v["additional_information_bits"] for v in vals]),
                "mean_bayes_accuracy_gain": _mean(
                    [v["bayes_accuracy_gain"] for v in vals]),
            })

    return {
        "schema": RESULT_SCHEMA,
        "status": "FROZEN_SIMULATED_NOISY_PROVENANCE_EVIDENCE__NO_REAL_GENETIC_VALIDATION",
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "original_v23_fingerprint": parent["result_fingerprint"],
        "parent_reconciled": {
            "design_rows": count_design,
            "occupancy_exact_identified": occupancy_ident,
            "ideal_full_provenance_plus_occupancy_exact_identified": ideal_combined_ident,
            "occupancy_alias_count": aliased_count,
            "equal_budget_occupancy_aliased_designs": equal_aliased_count,
        },
        "predeclared_hypothesis_verdicts": verdicts,
        "summary": summary,
        "noisy_design_by_source_geometry": by_geometry,
        "negative_controls": {
            "max_unique_origin_additional_information_bits": max_unique_info,
            "max_unique_origin_bayes_accuracy_gain": max_negative_gain,
            "zero_coverage_violations": zero_coverage_violations,
            "aggregate_noise_monotonicity_violations": monotone_violations,
        },
        "scientific_boundaries": p["scientific_boundaries"],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    result = run()
    if args.output.exists():
        raise ValueError("Refuse to overwrite frozen source result")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    print(json.dumps({
        "status": result["status"],
        "parent": result["parent_reconciled"],
        "verdicts": result["predeclared_hypothesis_verdicts"],
        "EOG_WF_changed": False,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
