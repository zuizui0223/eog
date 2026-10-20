#!/usr/bin/env python3
"""v43: minimal PERFECT time/space occupancy readouts for original 12 v42 aliases.

Source+original occupancy can be observationally identical even when a frozen
lag-2 present target differs. Extra timing observations are *synthetic*
perfect binary censuses, not field-validated migration or maturity assays.

The full t=Tstar-2 occupancy census is definitionally EQUAL to the target,
so that control is never presented as an independent predictive success.
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks import run_eog_provenance_ecological_state_v41 as original
from benchmarks.run_eog_provenance_uncertainty_v42 import deterministic_risk
from benchmarks.run_eog_original_idea_virtual_worlds_v2 import _node_id

PROTOCOL = ROOT / "validation/eog_original_idea_temporal_evidence_v43/protocol_v43.json"
PARENT_V42 = ROOT / "validation/eog_provenance_uncertainty_decomposition_v42/result_locked_v42.json"
SOURCE_V41_DIGEST = "34f6f2bd94b9b22854eb699c97607ec2b9408f0ea55bcd6d5103a4019581125d"
SOURCE_V42_DIGEST = "32887217c613ea92fd20e32d60d0a7e93ef8355c628ea955f968bec98436e273"
RESULT_SCHEMA = "eog.original_idea.non_tautological_temporal_evidence.result.v43"
CENSUSES = (4, 5, 6, 8)
CALENDAR = (0, 1, 2, 3, 7, 9, 10, 11, 12)
TARGET = "persistent_threshold_lag2"
EPS = 1e-9
BOUNDS = {
    "new_field_colonization_or_genetic_result": False,
    "perfect_binary_occupancy_or_source_label_assays_calibrated_in_nature": False,
    "v42_12_cases_already_exposed_to_analyst": True,
    "post_v42_analysis_not_independent_replication": True,
    "oracle_design_candidate_histories_assumed_known": True,
    "factual_EOG_WF_3_31_3_modified": False,
    "existing_methods_in_ecology_and_evolution_submission_validation_reopened": False,
}
VERDICTS = (
    "T1_definitionally_direct_target_census_resolves_all",
    "T2_non_tautological_temporal_evidence_resolves_some",
    "T3_one_binary_sentinel_can_replace_full_census_in_some",
    "T4_some_cases_require_multiple_spacetime_probes",
    "T5_original_census_remeasurement_is_not_new_information",
)


def _canonical(x: dict) -> bytes:
    return json.dumps(
        x, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def verify_protocol(p: dict, v42: dict) -> None:
    if (
        p.get("schema") != "eog.original_idea.source_alias_temporal_observability.protocol.v43"
        or p.get("status") !=
        "FROZEN_BEFORE_V43_SITE_TIME_PREDICTION_SCORING__POST_V42_EXPOSURE"
        or p.get("source", {}).get("base_commit") !=
        "f3a3d3a20922af717d48bfd9bf137eefdf67d5f3"
        or p["source"]["v41_source_sha256"] != SOURCE_V41_DIGEST
        or p["source"]["v42_result_sha256"] != SOURCE_V42_DIGEST
        or v42.get("canonical_result_sha256") != SOURCE_V42_DIGEST
        or v42.get("parent_complete_v41_sha256") != SOURCE_V41_DIGEST
    ):
        raise ValueError("Original exact v41/v42 evidence or frozen v43 protocol changed")
    design = p.get("world_design", {})
    if not (
        design.get("original_occupancy_census_times") == list(CENSUSES)
        and design.get("ecological_target") ==
        "same v26 binary persistent_threshold_lag2: mature iff first_arrival<=T*-2; source-site nodes excluded"
        and design.get("time_domain") ==
        "all integer times t from 0 to T* inclusive, do not access t>T*"
        and design.get("no_field_effort_or_selection_cost_estimated") is True
    ):
        raise ValueError("Time grid, synthetic target, or effort scope was changed")
    rules = p.get("contrasts", {})
    nontaut = rules.get("primary_non_tautological", {})
    if not (
        nontaut.get("exclude_original_observed_times") is True
        and nontaut.get("exclude_target_identity_time_tstar_minus_two") is True
        and nontaut.get("exact_minimal_binary_measurement_budget_max") == 3
        and rules.get("positive_tautology_control", {}).get("allowed_identity_time") == "t=T*-2"
        and rules.get("fixed_calendar_census_sensitivity", {}).get("probe_times") ==
        list(CALENDAR)
        and rules.get("control_original_times", {}).get("times") ==
        list(CENSUSES)
    ):
        raise ValueError("Tautological target or original-census exclusion removed")
    if (
        tuple(h["id"] for h in p.get("predeclared_testable_predictions", ())) != VERDICTS
        or p.get("scientific_boundaries") != BOUNDS
        or p["source"]["reviewed_prior_counts"] != {
            "all_worlds":768,
            "occupancy_history_alias":189,
            "maturity_known_from_occupancy":141,
            "maturity_uncertain":48,
            "maturity_resolvable_by_perfect_selected_source_tags":36,
            "maturity_unresolved_even_by_all_perfect_source_tags":12,
        }
    ):
        raise ValueError("Predeclared 12-world hypothesis or ecological limits changed")


def required_pairs(baseline: dict, targets: dict) -> tuple[tuple[str, str], ...]:
    """Only pairs with the SAME baseline signature and DIFFERENT target."""
    names = sorted(baseline)
    if set(names) != set(targets) or len(names) != 3:
        raise ValueError("Exactly three matched synthetic candidate histories are required")
    return tuple(
        (a, b) for a, b in combinations(names, 2)
        if baseline[a] == baseline[b] and targets[a] != targets[b]
    )


def census_at(
    first_arrivals: dict[str, dict[tuple, int]],
    nodes: tuple[tuple, ...],
    time: int,
) -> dict:
    if time < 0:
        raise ValueError("Negative physical time is unsupported")
    return {
        h: tuple((_node_id(node), int(arrivals[node] <= time)) for node in nodes)
        for h, arrivals in first_arrivals.items()
    }


def risk_with_readout(baseline: dict, targets: dict, readout: dict) -> dict:
    return deterministic_risk(
        {h: (baseline[h], readout[h]) for h in baseline}, targets
    )


def _covered_pairs(pairs: tuple, reports: dict) -> int:
    return sum((1 << i) for i, (a, b) in enumerate(pairs) if reports[a] != reports[b])


def smallest_binary_probe_set(
    pairs: tuple[tuple[str, str], ...],
    probes: dict[tuple[int, str], dict],
    *,
    budget: int = 3,
) -> tuple[tuple[int, str], ...] | None:
    """Exact finite set cover of target-discordant baseline-equivalent pairs.

    Up to three histories imply at most three required distinct pairs.
    The chosen target states and candidate predictions may guide this design
    (an explicitly labelled model-aided oracle) but observed true history
    is never read for measurement site/time selection.
    """
    if len(pairs) > 3 or budget > 3 or budget < 0:
        raise ValueError("Invalid three-history probe cover budget")
    if not pairs:
        return ()
    all_bits = (1 << len(pairs)) - 1
    # Retain earliest chronological probe of each distinct pair-separation mask.
    representative = {}
    for key, reports in probes.items():
        mask = _covered_pairs(pairs, reports)
        if mask and (mask not in representative or key < representative[mask]):
            representative[mask] = key
    best = {0: ()}
    for mask, key in sorted(representative.items(), key=lambda x: x[1]):
        prior = list(best.items())
        for covered, events in prior:
            union = covered | mask
            trial = tuple(sorted((*events, key)))
            if len(trial) > budget:
                continue
            previous = best.get(union)
            if previous is None or (len(trial), trial) < (len(previous), previous):
                best[union] = trial
    return best.get(all_bits)


def evaluate_residual(
    baseline: dict, targets: dict,
    first_arrivals: dict[str, dict[tuple, int]],
    nodes: tuple[tuple, ...], present_t: int,
) -> dict:
    """Return full one-world diagnostic, not a field/biological claim."""
    if present_t < 2:
        raise ValueError("Residual lag-2 maturity requires a nontrivial present horizon")
    if any(set(row) != set(nodes) for row in first_arrivals.values()):
        raise ValueError("Only original equilibrium non-source nodes can be observed")
    pairs = required_pairs(baseline, targets)
    if not pairs:
        raise ValueError("Passed world has no source/occupancy-equivalent maturity contrast")
    old = deterministic_risk(baseline, targets)
    if old["entropy_bits"] <= EPS:
        raise ValueError("Residual source-information uncertainty was not positive")
    direct_time = present_t - 2
    direct = census_at(first_arrivals, nodes, direct_time)
    if direct != targets:
        raise ValueError("Full census t=T*-2 is not the declared exact maturity target")
    direct_risk = risk_with_readout(baseline, targets, direct)
    if direct_risk["entropy_bits"] > EPS:
        raise ValueError("Definitional maturity measurement failed to resolve target")
    allowed = tuple(
        t for t in range(present_t + 1)
        if t not in CENSUSES and t != direct_time
    )
    baseline_retest_max = 0.0
    for t in CENSUSES:
        # Already available observations (even if they occur after T* in
        # some worlds) are retained ONLY as baseline equivalence controls,
        # not newly scored physical census outcomes.
        if t <= present_t:
            info = old["entropy_bits"] - risk_with_readout(
                baseline, targets, census_at(first_arrivals, nodes, t)
            )["entropy_bits"]
            baseline_retest_max = max(baseline_retest_max, abs(info))
    census_options = []
    for t in allowed:
        risk = risk_with_readout(
            baseline, targets, census_at(first_arrivals, nodes, t)
        )
        census_options.append({
            "time":t,
            "information_bits": max(0.0, old["entropy_bits"] - risk["entropy_bits"]),
            "target_resolved": risk["entropy_bits"] <= EPS,
        })
    # Highest expected information with chronological ties, only among
    # the fixed candidate worlds; this is an optimistic model-aided design.
    best = (
        min(census_options, key=lambda x: (-x["information_bits"], x["time"]))
        if census_options else None
    )
    probe_predictions = {}
    for t in allowed:
        for node in nodes:
            nid = _node_id(node)
            probe_predictions[(t, nid)] = {
                h: int(first_arrivals[h][node] <= t) for h in first_arrivals
            }
    full_cover = (1 << len(pairs)) - 1
    single = tuple(sorted(
        key for key, report in probe_predictions.items()
        if _covered_pairs(pairs, report) == full_cover
    ))
    minimum = smallest_binary_probe_set(pairs, probe_predictions)
    if minimum is not None and len(minimum) > 3:
        raise ValueError("Measurement budget was silently enlarged")
    fixed = {}
    for t in CALENDAR:
        is_allowed = t in allowed
        rec = next((x for x in census_options if x["time"] == t), None)
        fixed[str(t)] = {
            "applicable": is_allowed,
            "excluded_reason": None if is_allowed else (
                "after_present" if t > present_t else
                "already_observed" if t in CENSUSES else
                "equals_definition_of_target" if t == direct_time else "not_allowed"
            ),
            "resolved":rec["target_resolved"] if rec else None,
            "information_bits":rec["information_bits"] if rec else None,
        }
    return {
        "required_unresolved_history_pairs":len(pairs),
        "common_present_t":present_t,
        "identity_time_t_minus_2":direct_time,
        "baseline_target_conditional_entropy_bits":old["entropy_bits"],
        "baseline_bayes_target_error":old["bayes_error"],
        "definitional_full_census_resolves":True,
        "allowed_non_tautological_census_count":len(allowed),
        "any_non_tautological_full_census_resolves":any(z["target_resolved"] for z in census_options),
        "single_best_non_tautological_full_census":best,
        "earliest_resolving_non_tautological_full_census":next(
            (x["time"] for x in census_options if x["target_resolved"]), None
        ),
        "single_site_time_resolves":bool(single),
        "earliest_resolving_single_site_time":list(single[0]) if single else None,
        "minimum_non_tautological_binary_probe_count":
            len(minimum) if minimum is not None else None,
        "minimum_non_tautological_binary_probes":
            [list(probe) for probe in minimum] if minimum is not None else None,
        "all_non_tautological_binary_events_can_resolve":
            minimum is not None,
        "original_observation_retest_max_information_abs_error":baseline_retest_max,
        "fixed_calendar_one_census":fixed,
    }


def _mean(values):
    return sum(values) / len(values) if values else None


def run() -> tuple[dict, list[dict]]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    frozen_v42 = json.loads(PARENT_V42.read_text(encoding="utf-8"))
    verify_protocol(protocol, frozen_v42)
    v41_actual = original.run()
    if hashlib.sha256(_canonical(v41_actual)).hexdigest() != SOURCE_V41_DIGEST:
        raise ValueError("Canonical original v41 computation changed from reviewed source")
    count = Counter()
    residual = []
    calendar = {t: {"applicable":0, "resolved":0, "information_bits":[]} for t in CALENDAR}
    source_shapes = Counter()
    for autocorr in original.AUTOCORR_LEVELS:
        for neighbourhood in original.NEIGHBOURHOODS:
            for replicate in range(original.REPLICATES):
                base = original._generate_base(replicate, autocorr, neighbourhood)
                outlet = original._outlet_corner(replicate, autocorr, neighbourhood)
                anchor = original._truth_source(base, outlet)
                candidates,_ = original._candidate_sources(base, outlet, anchor)
                sets = original._source_sets(candidates, anchor)
                if not sets:
                    raise ValueError("Previously valid parent world absent")
                for barrier in original.BARRIER_LEVELS:
                    _,graph = original._graphs(base, barrier, original.RULE, outlet)
                    for shape in original.DESIGNS:
                        sources = sets[shape][3]
                        key = f"{replicate}|{autocorr}|{neighbourhood}|{barrier}|{shape}"
                        spec = original.prepare_design(graph, sources, key)
                        targets = original._synthetic_present_targets(graph, sources)[TARGET]
                        occupancy = spec["occupancy"]
                        tag_ids = tuple(sorted(spec["provenance_tags"]))
                        signatures = {
                            h: (occupancy[h], tuple(spec["provenance_tags"][node][h] for node in tag_ids))
                            for h in occupancy
                        }
                        count["all_worlds"] += 1
                        occ_alias = not spec["occupancy_exact_history_identifiable"]
                        count["occupancy_history_alias"] += int(occ_alias)
                        if not occ_alias:
                            continue
                        base_occ_risk = deterministic_risk(occupancy, targets)
                        if base_occ_risk["entropy_bits"] <= EPS:
                            count["maturity_known_from_occupancy"] += 1
                            continue
                        count["maturity_uncertain"] += 1
                        # The same selected perfect source tags as v42.
                        selected = tuple(spec["selected"]["confluence_targeted"])
                        selected_sig = {
                            h:(occupancy[h],tuple(spec["provenance_tags"][s][h] for s in selected))
                            for h in occupancy
                        }
                        full_risk = deterministic_risk(signatures, targets)
                        selected_risk = deterministic_risk(selected_sig, targets)
                        if full_risk["entropy_bits"] <= EPS:
                            if selected_risk["entropy_bits"] > EPS:
                                raise ValueError("v42 zero perfect-site coverage gap changed")
                            count["maturity_resolvable_by_perfect_selected_source_tags"] += 1
                            continue
                        count["maturity_unresolved_even_by_all_perfect_source_tags"] += 1
                        # Rebuild original discrete first-arrival field without changing
                        # selected graph, sources, activation histories or common T*.
                        distances=original._distances(graph, sources)
                        firsts={}
                        equilibria=set()
                        for h,activation in original.ACTIVATION_HISTORIES.items():
                            eq,first,_=original._arrival_structure(distances,sources,activation)
                            equilibria.add(tuple(sorted(eq)))
                            firsts[h]=first
                        if len(equilibria) != 1:
                            raise ValueError("Parent v23 equilibrium occupancy differs across histories")
                        nodes=tuple(n for n in next(iter(equilibria)) if n not in frozenset(sources))
                        present_t=max(firsts[h][n] for h in firsts for n in nodes)
                        first_non_source={h:{n:firsts[h][n] for n in nodes} for h in firsts}
                        v = evaluate_residual(signatures,targets,first_non_source,nodes,present_t)
                        v["design_key"]=key
                        v["source_geometry"]=shape
                        v["neighborhood"]=neighbourhood
                        v["autocorrelation"]=autocorr
                        v["barrier_density"]=barrier
                        v["non_source_node_count"]=len(nodes)
                        residual.append(v)
                        source_shapes[(shape,neighbourhood)] += 1
                        for t in CALENDAR:
                            entry=v["fixed_calendar_one_census"][str(t)]
                            if entry["applicable"]:
                                calendar[t]["applicable"] += 1
                                calendar[t]["resolved"] += int(entry["resolved"])
                                calendar[t]["information_bits"].append(entry["information_bits"])
    expected=protocol["source"]["reviewed_prior_counts"]
    if dict(count) != expected:
        raise ValueError(f"Exact parent 768/189/141/36/12 world populations changed: {dict(count)}")
    if len(residual) != 12:
        raise ValueError("Original v42 12 residual mature-state worlds did not reproduce")
    if any(z["original_observation_retest_max_information_abs_error"] > EPS for z in residual):
        raise ValueError("Existing original census time contained novel information")
    if any(z["definitional_full_census_resolves"] is not True for z in residual):
        raise ValueError("Definitional control failed")
    if any(z["source_geometry"] != "clustered" or z["neighborhood"] != "rook" for z in residual):
        raise ValueError("Previously observed v42 12 source-shape/adjacency pattern changed")
    n=12
    any_census = sum(x["any_non_tautological_full_census_resolves"] for x in residual)
    any_single = sum(x["single_site_time_resolves"] for x in residual)
    budget_dist=Counter(
        str(z["minimum_non_tautological_binary_probe_count"]) for z in residual
    )
    control = sum(x["definitional_full_census_resolves"] for x in residual)
    multi = sum(
        z["minimum_non_tautological_binary_probe_count"] is not None
        and z["minimum_non_tautological_binary_probe_count"] >= 2
        for z in residual
    )
    verdict={
        VERDICTS[0]:"SUPPORTED" if control == 12 else "REFUTED",
        VERDICTS[1]:"SUPPORTED" if any_census > 0 else "REFUTED",
        VERDICTS[2]:"SUPPORTED" if any_single > 0 else "REFUTED",
        VERDICTS[3]:"SUPPORTED" if multi > 0 else "REFUTED",
        VERDICTS[4]:"SUPPORTED" if all(z["original_observation_retest_max_information_abs_error"] <= EPS for z in residual) else "REFUTED",
    }
    report={
        "schema":RESULT_SCHEMA,
        "status":"SOURCE_ALIASED_MATURITY_TIMING_EVIDENCE_KNOWN_TRUTH_ONLY",
        "parent_population":dict(count),
        "fixed_12_geometry":{f"{s}|{n}":v for (s,n),v in sorted(source_shapes.items())},
        "original_12_worlds_scored":n,
        "lag2_identity_census_positive_control_resolved":control,
        "non_tautological_one_extra_full_census_resolves":any_census,
        "non_tautological_one_binary_site_time_resolves":any_single,
        "non_tautological_minimum_binary_probe_count_distribution":dict(budget_dist),
        "non_tautological_two_or_three_binary_probes_required":multi,
        "non_tautological_all_binary_measurement_library_insufficient":sum(
            not z["all_non_tautological_binary_events_can_resolve"] for z in residual
        ),
        "one_census_calendar_sensitivity":{
            str(t):{
                "applicable_worlds":v["applicable"],"resolved_worlds":v["resolved"],
                "mean_additional_information_bits":_mean(v["information_bits"])
            } for t,v in sorted(calendar.items())
        },
        "mean_original_residual_entropy_bits":_mean([v["baseline_target_conditional_entropy_bits"] for v in residual]),
        "mean_optimal_non_tautological_one_census_information_bits":_mean([
            v["single_best_non_tautological_full_census"]["information_bits"] if
            v["single_best_non_tautological_full_census"] else 0.0 for v in residual
        ]),
        # Post-first-result audit, NOT an additional preregistered hypothesis:
        # for these residual cases the original occupancy library's t=8
        # record is already in the *future* relative to the target's Tstar.
        # Therefore this is retrospective smoothing, not prospective forecast.
        "post_exposure_temporal_chronology_audit":{
            "purpose":"Clarify original target-versus-observation chronology, not score a new hypothesis",
            "latest_original_occupancy_snapshot_time":max(CENSUSES),
            "target_present_T_distribution":{
                str(t):sum(row["common_present_t"]==t for row in residual)
                for t in sorted({row["common_present_t"] for row in residual})
            },
            "non_source_equilibrium_node_count_distribution":{
                str(n):sum(row["non_source_node_count"]==n for row in residual)
                for n in sorted({row["non_source_node_count"] for row in residual})
            },
            "worlds_with_last_original_occupancy_snapshot_after_target_T":sum(
                max(CENSUSES)>row["common_present_t"] for row in residual),
            "worlds_with_any_original_occupancy_snapshot_after_target_T":sum(
                any(t>row["common_present_t"] for t in CENSUSES) for row in residual),
            "non_tautological_earliest_resolving_census_time_distribution":{
                str(t):sum(row["earliest_resolving_non_tautological_full_census"]==t
                           for row in residual)
                for t in sorted({row["earliest_resolving_non_tautological_full_census"]
                                 for row in residual
                                 if row["earliest_resolving_non_tautological_full_census"] is not None})
            },
            "claim_of_prospective_maturity_prediction_authorized":False,
            "posthoc_chronology_reported_not_refitted":True
        },
        "frozen_v43_verdicts":verdict,
        "original_v41_complete_canonical_sha256":SOURCE_V41_DIGEST,
        "original_v42_frozen_sha256":SOURCE_V42_DIGEST,
        "scientific_boundaries":protocol["scientific_boundaries"],
        "no_real_source_genetic_or_field_data_read":True,
        "positive_control_direct_target_identity_is_not_prediction":True,
    }
    return report, residual


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir",required=True,type=Path)
    args=parser.parse_args()
    if args.output_dir.exists() or args.output_dir.is_symlink():
        raise ValueError("Refusing to overwrite existing evidence directory")
    report,rows=run()
    args.output_dir.mkdir(parents=True,exist_ok=False)
    path=args.output_dir / "twelve_residual_world_diagnostics.json"
    path.write_text(json.dumps(rows,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    report["twelve_world_diagnostics_sha256"]=hashlib.sha256(_canonical(rows)).hexdigest()
    out=args.output_dir/"result_v43.json"
    out.write_text(json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":report["status"],
        "non_tautological_census_rescue":report["non_tautological_one_extra_full_census_resolves"],
        "non_tautological_sentinel_rescue":report["non_tautological_one_binary_site_time_resolves"],
        "hypotheses":report["frozen_v43_verdicts"],
        "real_field_data":False
    },ensure_ascii=False))


if __name__=="__main__":
    main()
