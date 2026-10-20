#!/usr/bin/env python3
"""v44: finite-world information about future maturity with a HARD data cutoff.

Do not confuse conditional Bayes information under a perfectly known synthetic
process with held-out field forecast accuracy. All observed occupancy/tag
readouts here are cutoff-time only, with no future tag for an empty site.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
from itertools import product
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks import run_eog_provenance_ecological_state_v41 as original
from benchmarks.run_eog_imperfect_provenance_sampling_v39 import (
    SEED as HISTORIC_RANDOM_SEED,
)
from benchmarks.run_eog_original_idea_virtual_worlds_v2 import _node_id

PROTOCOL = ROOT / "validation/eog_original_idea_asof_time_source_v44/protocol_v44.json"
V43 = ROOT / "validation/eog_original_idea_temporal_evidence_v43/result_locked_v43.json"
RESULT_SCHEMA = "eog.original_idea.asof_time_source_tag_information.result.v44"
PANEL_PAIRS = (
    ("primary_early", 2, 5),
    ("secondary_near", 4, 5),
    ("identity_control", 4, 6),
    ("secondary_late", 4, 7),
)
TARGETS = ("persistent_threshold_lag2", "transient_window_age1_2")
POLICIES = (
    "static_confluence_top3", "static_sha256_random_top3",
    "cutoff_occupied_confluence_top3",
)
Q, ERROR = 0.6, 0.1
BUDGET = 3
TOL = 1e-9
EXPECTED_HISTORIES = {
    "H_anchor_first": (0, 2, 4),
    "H_second_first": (4, 0, 2),
    "H_third_first": (2, 4, 0),
}
BASE_SHA = "8d9b83888be491764a51978802ccafd2fda3e3d1"
V41_SHA = "34f6f2bd94b9b22854eb699c97607ec2b9408f0ea55bcd6d5103a4019581125d"
V43_SHA = "04f24a88911b76da4c112a827dd4df4694152ff92dd350d413056f007ef05446"
BOUNDARIES = {
    "same_known_truth_simulator_not_independent_heldout_ecological_empirics": True,
    "source_network_and_potential_source_coordinates_assumed_known_at_cutoff": True,
    "perfect_cutoff_occupancy_is_an_optimistic_assumption": True,
    "synthetic_noisy_tag_is_not_empirical_SNP_ancestry": True,
    "maturation_is_abstract_v26_arrival_age_status_not_actual_survival_or_reproduction": True,
    "no_original_2021_genetic_or_bird_data_fetched": True,
    "no_real_world_island_year_detection_effort_or_predictive_performance_estimated": True,
    "original_EOG_WF_3_31_3_unchanged": True,
}
HYPOTHESES = (
    "A1_primary_has_uncertain_future_maturity_cases",
    "A2_available_noisy_provenance_improves_some_future_maturity_predictions",
    "A3_future_unoccupied_sites_cannot_supply_current_labels",
    "A4_lag2_maturity_at_t6_is_already_known_from_full_t4_occupancy",
    "A5_cutoff_aware_site_selection_outperforms_static_confluence",
    "A6_perfect_cutoff_available_tags_bound_noisy_tags",
)


def canonical(data: dict) -> bytes:
    return json.dumps(
        data, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")


def _entropy(weights: dict) -> float:
    total = sum(weights.values())
    if total <= 0:
        return 0.0
    return -sum(value / total * math.log2(value / total)
                for value in weights.values() if value > 0)


def verify_contract(p: dict, parent: dict) -> None:
    if (
        p.get("schema") !=
            "eog.original_idea.asof_time_source_tag_information.protocol.v44"
        or p.get("status") !=
            "FROZEN_BEFORE_ANY_ASOF_TIME_PROSPECTIVE_TARGET_SCORING__POST_V43_EXPOSURE"
        or p.get("parent", {}).get("main_commit") != BASE_SHA
        or p["parent"]["v41_complete_result_sha256"] != V41_SHA
        or p["parent"]["v43_complete_result_sha256"] != V43_SHA
        or parent.get("authority", {}).get("complete_result_sha256") != V43_SHA
        or p.get("world_and_information_contract", {}).get("design_rows") != 768
        or p.get("world_and_information_contract", {}).get(
            "three_source_activation_histories") != {
                key: list(val) for key, val in EXPECTED_HISTORIES.items()
            }
    ):
        raise ValueError("Original v23-v43 prior known truth or v44 contract changed")
    if (
        [(x["id"], x["cutoff_t"], x["target_t"]) for x in p["fixed_forecast_pairs"]]
        != list(PANEL_PAIRS)
        or tuple(p["targets"]) != TARGETS
        or tuple(p["measurement"]["policies"]) != POLICIES
        or p["measurement"]["q_observation_given_occupied"] != Q
        or p["measurement"]["e_miscall_given_observed"] != ERROR
        or p["measurement"]["max_sites"] != BUDGET
        or p["measurement"]["static_random"] !=
            "same v39 one fixed seed eog-v39-20261019-fixed-rank, topology/node IDs only"
        or p["world_and_information_contract"]["future_label_leakage_prohibited"] is not True
        or p["world_and_information_contract"]["unknown_by_cutoff"] !=
            ["true activation order", "future actual node first-arrival times",
             "future occupancy readouts", "later genetic measurements"]
        or tuple(x["id"] for x in p["predeclared_hypotheses"]) != HYPOTHESES
        or p["scientific_boundaries"] != BOUNDARIES
    ):
        raise ValueError("Predeclared target, no-future source channel, or claim scope changed")
    if not all(target > cutoff for _, cutoff, target in PANEL_PAIRS):
        raise ValueError("Forecast must always target a strictly later clock time")


def static_selection(
    sites: tuple[str, ...], source_cover: dict[str, int], design_key: str,
) -> dict[str, tuple[str, ...]]:
    """Select by source-potential geometry / names ONLY, never future tags."""
    if set(sites) != set(source_cover):
        raise ValueError("Every non-source site needs a static source count")
    confluence = tuple(sorted(
        (node for node in sites if source_cover[node] >= 2),
        key=lambda node: (-source_cover[node], node),
    ))[:BUDGET]
    random = tuple(sorted(
        sites,
        key=lambda node: (
            hashlib.sha256(
                f"{HISTORIC_RANDOM_SEED}|{design_key}|{node}".encode()
            ).hexdigest(), node,
        ),
    ))[:BUDGET]
    return {
        "static_confluence_top3": confluence,
        "static_sha256_random_top3": random,
    }


def occupied_confluence_selection(
    occ_signature: tuple, source_cover: dict[str, int],
) -> tuple[str, ...]:
    """Uses ONLY observed cutoff-time occupancy, plus fixed static geography."""
    if not all(isinstance(node, str) and type(present) is bool
               for node, present in occ_signature):
        raise ValueError("Expected exact cutoff-only binary observations")
    return tuple(sorted(
        (node for node, present in occ_signature
         if present and source_cover[node] >= 2),
        key=lambda node: (-source_cover[node], node),
    ))[:BUDGET]


def make_asof_world(graph, sources: tuple, design_key: str) -> dict:
    """Static source network known; actual source activation order unknown."""
    distances = original._distances(graph, sources)
    equilibrium = None
    histories = {}
    for history, schedule in original.ACTIVATION_HISTORIES.items():
        union, first, earliest = original._arrival_structure(
            distances, sources, schedule
        )
        if equilibrium is None:
            equilibrium = union
        if union != equilibrium:
            raise ValueError("Same fixed source graph has different equilibrium union")
        histories[history] = {
            "first": first,
            "earliest": earliest,
        }
    nodes = tuple(sorted(equilibrium - frozenset(sources)))
    site_ids = tuple(_node_id(node) for node in nodes)
    source_cover = {
        _node_id(node): sum(node in distances[source] for source in sources)
        for node in nodes
    }
    return {
        "nodes": nodes,
        "site_ids": site_ids,
        "source_cover": source_cover,
        "histories": histories,
        "fixed_selections": static_selection(site_ids, source_cover, design_key),
    }


def make_cutoff_inputs(world: dict, cutoff: int) -> tuple[dict, dict]:
    """Do not ever inspect future source tags for unoccupied nodes."""
    occupancy = {}
    available = {}
    for h, record in world["histories"].items():
        bits = []
        by_site = {}
        for node in world["nodes"]:
            site = _node_id(node)
            present = bool(record["first"][node] <= cutoff)
            bits.append((site, present))
            # Only if physically occupied by cutoff could an ideal source
            # label have been acquired. No future label in a missing record.
            if present:
                by_site[site] = tuple(sorted(
                    _node_id(s) for s in record["earliest"][node]
                ))
            else:
                by_site[site] = None
        occupancy[h] = tuple(bits)
        available[h] = by_site
    if any(
        available[h][site] is not None and not present
        for h in occupancy
        for site, present in occupancy[h]
    ):
        raise ValueError("Future source tag leaked at unoccupied site")
    return occupancy, available


def future_state(world: dict, horizon: int, target: str) -> dict:
    """v26 synthetic state map at an EXOGENOUS clock, not target-derived Tstar."""
    if target not in TARGETS:
        raise ValueError("Unsupported future ecological state target")
    result = {}
    for h, record in world["histories"].items():
        ages = original._age_map(world["nodes"], record["first"], horizon)
        result[h] = original._process_map(target, ages)
    return result


def risk_given_cutoff(
    occupancy: dict, target: dict, available_tags: dict,
    *,
    policy: str,
    fixed_selection: dict[str, tuple[str, ...]],
    source_cover: dict[str, int],
    coverage: float = Q,
    miscall: float = ERROR,
) -> dict:
    """Exact expectation over hidden histories, cutoff O, and tag reports.

    The selected measurement locations depend on static geography, and for
    the adaptive policy on the ALREADY OBSERVED cutoff occupancy alone.
    The tag channel cannot supply future labels at sites not occupied yet.
    """
    histories = tuple(sorted(occupancy))
    if (
        len(histories) != 3 or set(target) != set(histories)
        or set(available_tags) != set(histories)
        or policy not in POLICIES
        or not (0 <= coverage <= 1 and 0 <= miscall <= .25)
    ):
        raise ValueError("Three-history cutoff source likelihood invalid")
    groups = defaultdict(list)
    for h in histories:
        groups[occupancy[h]].append(h)

    baseline_entropy = 0.0
    baseline_correct = 0.0
    after_entropy = 0.0
    after_correct = 0.0
    effective_sites_expected = 0.0
    nominal_sites_expected = 0.0
    unoccupied_tag_violations = 0

    for signature, members in groups.items():
        prior_target = Counter(target[h] for h in members)
        baseline_entropy += len(members) / 3 * _entropy(prior_target)
        baseline_correct += max(prior_target.values()) / 3

        if policy == "cutoff_occupied_confluence_top3":
            selected = occupied_confluence_selection(signature, source_cover)
        else:
            selected = tuple(fixed_selection[policy])
        if len(selected) > BUDGET or len(set(selected)) != len(selected):
            raise ValueError("Cutoff source-tag budget or unique sites violated")
        observed_by_node = dict(signature)
        for node in selected:
            if node not in observed_by_node:
                raise ValueError("Selected site not in the observable site universe")
        effective = sum(observed_by_node[n] for n in selected)
        effective_sites_expected += len(members) / 3 * effective
        nominal_sites_expected += len(members) / 3 * len(selected)

        domains = []
        likelihood = {}
        for node in selected:
            if not observed_by_node[node]:
                # The node was not occupied in this cutoff-occupancy class;
                # its future origin must NEVER be read or used.
                domains.append((None,))
                for h in members:
                    if available_tags[h][node] is not None:
                        unoccupied_tag_violations += 1
                    likelihood[(node, h)] = {None: 1.0}
                continue
            truth = {h: available_tags[h][node] for h in members}
            if any(not isinstance(value, tuple) for value in truth.values()):
                raise ValueError("An occupied cutoff site lacks its available origin tag")
            labels = tuple(sorted(set(truth.values())))
            unseen = ("__synthetic_unseen__",)
            if unseen in labels:
                raise ValueError("Synthetic miscall tag collided with actual source")
            catalog = labels + (unseen,)
            domains.append((None,) + catalog)
            for h in members:
                likelihood[(node, h)] = {
                    **{None: 1.0 - coverage},
                    **{
                        tag: coverage * (
                            (1.0 - miscall) if tag == truth[h]
                            else (miscall / (len(catalog) - 1))
                        )
                        for tag in catalog
                    },
                }
                if abs(sum(likelihood[(node, h)].values()) - 1.0) > 1e-12:
                    raise ValueError("As-of tag channel is not a probability distribution")

        for reports in product(*domains):
            joint_by_target = defaultdict(float)
            for h in members:
                weight = 1 / 3
                for node, tag in zip(selected, reports, strict=True):
                    weight *= likelihood[(node, h)][tag]
                joint_by_target[target[h]] += weight
            mass = sum(joint_by_target.values())
            if mass <= 0:
                continue
            after_entropy += mass * _entropy(joint_by_target)
            after_correct += max(joint_by_target.values())
    gain_info = baseline_entropy - after_entropy
    gain_correct = after_correct - baseline_correct
    if gain_info < -1e-8 or gain_correct < -1e-8:
        raise ValueError("Expected Bayes risk grew under correctly modeled cutoff observations")
    return {
        "baseline_target_conditional_entropy_bits": baseline_entropy,
        "baseline_target_bayes_accuracy": baseline_correct,
        "added_source_information_bits": max(0.0, gain_info),
        "added_target_bayes_accuracy_gain": max(0.0, gain_correct),
        "mean_nominal_selected_sites": nominal_sites_expected,
        "mean_cutoff_occupied_selected_sites": effective_sites_expected,
        "unoccupied_future_source_tag_violations": unoccupied_tag_violations,
        "ambiguous_target_under_cutoff_occupancy": baseline_entropy > TOL,
    }


def _mean(rows, field):
    return sum(x[field] for x in rows) / len(rows) if rows else None


def aggregate(results: list[dict], panel: str, target: str,
              policy: str, subset: str) -> dict:
    group = [
        r for r in results if r["panel"] == panel
        and r["target"] == target and r["policy"] == policy
        and (subset == "all" or r["target_ambiguous_from_cutoff_occupancy"])
    ]
    out = {
        "panel": panel, "target": target,
        "policy": policy, "subset": subset,
        "n_world_designs": len(group),
    }
    for name in (
        "baseline_target_conditional_entropy_bits",
        "baseline_target_bayes_accuracy",
        "added_source_information_bits",
        "added_target_bayes_accuracy_gain",
        "perfect_cutoff_tag_information_bits",
        "perfect_cutoff_tag_accuracy_gain",
        "mean_nominal_selected_sites",
        "mean_cutoff_occupied_selected_sites",
    ):
        out["mean_"+name] = _mean(group, name)
    out["worlds_with_positive_source_info"] = sum(
        r["added_source_information_bits"] > TOL for r in group
    )
    return out


def run() -> tuple[dict, list[dict]]:
    p = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    parent_v43 = json.loads(V43.read_text(encoding="utf-8"))
    verify_contract(p, parent_v43)
    if dict(original.ACTIVATION_HISTORIES) != EXPECTED_HISTORIES:
        raise ValueError("Activation histories changed from originally frozen source")
    original_v41 = original.run()
    if hashlib.sha256(canonical(original_v41)).hexdigest() != V41_SHA:
        raise ValueError("Original 768-world v41 complete result no longer reproduces")
    rows = []
    population = Counter()
    blocked_future = 0
    perfect_bound_violations = 0
    zero_information_cutoff4_target6 = 0
    asof_source_tag_gain = Counter()
    total_sites = 0
    for autocorr in original.AUTOCORR_LEVELS:
        for neighborhood in original.NEIGHBOURHOODS:
            for replicate in range(original.REPLICATES):
                base = original._generate_base(replicate, autocorr, neighborhood)
                outlet = original._outlet_corner(replicate, autocorr, neighborhood)
                anchor = original._truth_source(base, outlet)
                candidates, _ = original._candidate_sources(base, outlet, anchor)
                source_sets = original._source_sets(candidates, anchor)
                if not source_sets:
                    raise ValueError("Original source-geometry world not available")
                for barrier in original.BARRIER_LEVELS:
                    _, graph = original._graphs(base, barrier, original.RULE, outlet)
                    for geometry in original.DESIGNS:
                        key = f"{replicate}|{autocorr}|{neighborhood}|{barrier}|{geometry}"
                        world = make_asof_world(graph, source_sets[geometry][3], key)
                        population["designs"] += 1
                        total_sites += len(world["site_ids"])
                        for panel, cutoff, future in PANEL_PAIRS:
                            if future <= cutoff:
                                raise ValueError("Prospective horizon not strictly later than input cutoff")
                            occupancy, tags = make_cutoff_inputs(world, cutoff)
                            population[panel] += 1
                            for target_name in TARGETS:
                                target = future_state(world, future, target_name)
                                if panel == "identity_control" and target_name == "persistent_threshold_lag2":
                                    # Mat_6(>=2 years) is identical to presence_4,
                                    # so no future target uncertainty is possible.
                                    if any(
                                        target[h] != occupancy[h] for h in occupancy
                                    ):
                                        raise ValueError("T+2 lag2 maturity is not exactly cutoff occupancy")
                                    zero_information_cutoff4_target6 += 1
                                for policy in POLICIES:
                                    observed = risk_given_cutoff(
                                        occupancy, target, tags, policy=policy,
                                        fixed_selection=world["fixed_selections"],
                                        source_cover=world["source_cover"],
                                    )
                                    perfect = risk_given_cutoff(
                                        occupancy, target, tags, policy=policy,
                                        fixed_selection=world["fixed_selections"],
                                        source_cover=world["source_cover"],
                                        coverage=1.0, miscall=0.0,
                                    )
                                    if (
                                        observed["added_source_information_bits"] >
                                            perfect["added_source_information_bits"] + TOL
                                        or observed["added_target_bayes_accuracy_gain"] >
                                            perfect["added_target_bayes_accuracy_gain"] + TOL
                                    ):
                                        perfect_bound_violations += 1
                                    blocked_future += observed["unoccupied_future_source_tag_violations"]
                                    if observed["ambiguous_target_under_cutoff_occupancy"] and (
                                        observed["added_source_information_bits"] > TOL
                                    ):
                                        asof_source_tag_gain[(panel,target_name,policy)] += 1
                                    rows.append({
                                        "design_key": key,
                                        "source_geometry": geometry,
                                        "panel": panel, "cutoff_time": cutoff,
                                        "future_target_time": future, "target": target_name,
                                        "policy": policy,
                                        "target_ambiguous_from_cutoff_occupancy":
                                            observed["ambiguous_target_under_cutoff_occupancy"],
                                        "baseline_target_conditional_entropy_bits":
                                            observed["baseline_target_conditional_entropy_bits"],
                                        "baseline_target_bayes_accuracy":
                                            observed["baseline_target_bayes_accuracy"],
                                        "added_source_information_bits":
                                            observed["added_source_information_bits"],
                                        "added_target_bayes_accuracy_gain":
                                            observed["added_target_bayes_accuracy_gain"],
                                        "perfect_cutoff_tag_information_bits":
                                            perfect["added_source_information_bits"],
                                        "perfect_cutoff_tag_accuracy_gain":
                                            perfect["added_target_bayes_accuracy_gain"],
                                        "mean_nominal_selected_sites":
                                            observed["mean_nominal_selected_sites"],
                                        "mean_cutoff_occupied_selected_sites":
                                            observed["mean_cutoff_occupied_selected_sites"],
                                    })
    if population["designs"] != 768 or any(population[panel] != 768 for panel, _, _ in PANEL_PAIRS):
        raise ValueError("Original source worlds or as-of panel universes drifted")
    if len(rows) != 768 * len(PANEL_PAIRS) * len(TARGETS) * len(POLICIES):
        raise ValueError("As-of-time future target/policy grid incomplete")
    if blocked_future or perfect_bound_violations or zero_information_cutoff4_target6 != 768:
        raise ValueError("Future-input leakage or target-data-processing control failed")
    summaries = [
        aggregate(rows, panel, target, policy, subset)
        for panel, _, _ in PANEL_PAIRS
        for target in TARGETS
        for policy in POLICIES
        for subset in ("all", "target_ambiguous")
    ]
    primary = {
        policy: next(
            row for row in summaries
            if row["panel"] == "primary_early"
            and row["target"] == "persistent_threshold_lag2"
            and row["policy"] == policy
            and row["subset"] == "target_ambiguous"
        ) for policy in POLICIES
    }
    criterion = primary["cutoff_occupied_confluence_top3"]
    static = primary["static_confluence_top3"]
    count_uncertain = criterion["n_world_designs"]
    control = next(
        row for row in summaries
        if row["panel"] == "identity_control"
        and row["target"] == "persistent_threshold_lag2"
        and row["policy"] == "cutoff_occupied_confluence_top3"
        and row["subset"] == "all"
    )
    hypothesis = {
        HYPOTHESES[0]: "SUPPORTED" if count_uncertain > 0 else "REFUTED",
        HYPOTHESES[1]: "SUPPORTED" if criterion["worlds_with_positive_source_info"] > 0
                      else "REFUTED",
        HYPOTHESES[2]: "SUPPORTED" if blocked_future == 0 else "REFUTED",
        HYPOTHESES[3]: "SUPPORTED" if (
            zero_information_cutoff4_target6 == 768
            and abs(control["mean_baseline_target_conditional_entropy_bits"]) <= TOL
            and abs(control["mean_added_source_information_bits"]) <= TOL
        ) else "REFUTED",
        HYPOTHESES[4]: "SUPPORTED" if (
            count_uncertain > 0 and
            criterion["mean_added_source_information_bits"] >
                static["mean_added_source_information_bits"] + TOL
        ) else "REFUTED",
        HYPOTHESES[5]: "SUPPORTED" if perfect_bound_violations == 0 else "REFUTED",
    }
    return {
        "schema": RESULT_SCHEMA,
        "status": "CUTOFF_ONLY_SYNTHETIC_SOURCE_INFORMATION_FOR_FUTURE_STATE__NO_EMPIRICAL_SCORE",
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "parent_v41_full_canonical_sha256_reproduced": V41_SHA,
        "parent_v43_retrospective_result_sha256_attested": V43_SHA,
        "populations": {
            "base_worlds": 768,
            "world_panel_target_policy_rows": len(rows),
            "future_target_t6_exact_t4_occupancy_identity_worlds":
                zero_information_cutoff4_target6,
            "total_non_source_sites_over_768_worlds": total_sites,
        },
        "summary_by_panel_target_policy": summaries,
        "primary_early_t2_to_t5_maturity": primary,
        "eligible_policy_positive_information_worlds": {
            "|".join(key): value
            for key, value in sorted(asof_source_tag_gain.items())
        },
        "controls": {
            "unoccupied_future_source_tag_leakage_violations": blocked_future,
            "perfect_tag_data_processing_violations": perfect_bound_violations,
            "future_occupancy_snapshot_in_observation_model": False,
            "post_cutoff_source_tag_used_as_observed": False,
            "no_original_full_v23_t4_t5_t6_t8_snapshot_if_after_cutoff": True,
            "original_v43_12_of_12_retrospective_rescue_rescored": False,
        },
        "predeclared_hypothesis_verdicts": hypothesis,
        "scientific_boundaries": BOUNDARIES,
    }, rows


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", required=True, type=Path)
    args = p.parse_args()
    if args.output_dir.exists() or args.output_dir.is_symlink():
        raise ValueError("Refuse overwrite of existing evidence output")
    result, rows = run()
    args.output_dir.mkdir(parents=True)
    csv_path = args.output_dir / "per_world_asof_v44.csv"
    with csv_path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    result["full_csv_sha256"] = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    (args.output_dir / "result_v44.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False,
                   allow_nan=False)+"\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": result["status"],
        "primary": result["primary_early_t2_to_t5_maturity"],
        "verdicts": result["predeclared_hypothesis_verdicts"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
