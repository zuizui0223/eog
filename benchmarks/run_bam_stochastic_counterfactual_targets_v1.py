#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str((Path(__file__).resolve().parent)))

from independent_stochastic_bam_generator import (
    abiotic_mask,
    biotic_mask,
    candidate_parameter_grid,
    make_landscape,
    simulate_associates,
    simulate_focal,
    structural_reachable_mask,
    truth_scenarios,
)
from independent_stochastic_counterfactual_generator_v1 import (
    stochastic_counterfactual_forecast,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/bam_stochastic_counterfactual_targets_v1/protocol_v1.json"
PARENT_STOCHASTIC = ROOT / "validation/independent_stochastic_bam_v3/result_summary_v3.json"
PARENT_STRUCTURED = ROOT / "validation/bam_structured_counterfactuals_v1/result_summary_v1.json"
EXPECTED_STOCHASTIC = "bc558d10073133510f1b47b5651f6694d53f04771e757e9d8d9716ada72b18bf"
EXPECTED_STRUCTURED = "f502fb647ba4666f5c40ddbd5639123f3e0296fe492dd97a1ec19ec246531cb1"


def _sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _structural_support(landscape, associates, spec):
    A = abiotic_mask(landscape, spec.niche_center, spec.niche_radius)
    B = biotic_mask(
        spec.biotic_mode,
        partner_mask=associates.partner_mask,
        antagonist_mask=associates.antagonist_mask,
    )
    eligible = A & B
    return structural_reachable_mask(
        landscape,
        source_id=spec.source_id,
        eligible_mask=eligible,
        step_radius=spec.step_radius,
        barrier_permeable=spec.barrier_permeable,
    )


def _compatible_ids(observed_ids, supports):
    observed = set(observed_ids)
    return tuple(
        world_id
        for world_id in sorted(supports)
        if observed.issubset(supports[world_id])
    )


def run() -> dict[str, object]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_implementation_and_scoring":
        raise RuntimeError("Phase-VI protocol is not frozen")

    parent_stochastic = json.loads(PARENT_STOCHASTIC.read_text(encoding="utf-8"))
    parent_structured = json.loads(PARENT_STRUCTURED.read_text(encoding="utf-8"))
    if parent_stochastic.get("result_fingerprint") != EXPECTED_STOCHASTIC:
        raise RuntimeError("independent stochastic parent fingerprint mismatch")
    if parent_structured.get("result_fingerprint") != EXPECTED_STRUCTURED:
        raise RuntimeError("structured counterfactual parent fingerprint mismatch")

    landscape = make_landscape()
    associates = simulate_associates(landscape)
    specs = candidate_parameter_grid()
    specs_by_id = {spec.scenario_id: spec for spec in specs}
    truths = truth_scenarios()

    supports = {}
    for spec in specs:
        mask = _structural_support(landscape, associates, spec)
        supports[spec.scenario_id] = {
            node_id
            for node_id, present in zip(landscape.node_ids, mask, strict=True)
            if bool(present)
        }

    transformations = ("climate_shift", "biotic_stress", "barrier_restoration")
    run_rows = []
    truth_retention_failures = 0
    hierarchy_violations = 0
    truth_consistency_failures = 0

    totals = {
        t: {
            "parameter_world_identified": 0,
            "exact_forecast_identified": 0,
            "binary_decision_identified": 0,
            "decision_without_world_identification": 0,
            "exact_forecast_without_world_identification": 0,
            "binary_decision_unresolved": 0,
        }
        for t in transformations
    }
    by_scenario = {
        scenario: {
            t: defaultdict(int)
            for t in transformations
        }
        for scenario in truths
    }

    for scenario_id, truth_world_id in truths.items():
        truth_spec = specs_by_id[truth_world_id]
        for replicate in range(64):
            realization = simulate_focal(
                landscape,
                associates,
                truth_spec,
                replicate=replicate,
            )
            observed_h40 = dict(realization.accumulated_occurrence_ids_by_horizon)[40]
            survivor_ids = _compatible_ids(observed_h40, supports)
            if truth_world_id not in survivor_ids:
                truth_retention_failures += 1

            current_snapshot = realization.occupancy_history[-1].copy()
            parameter_identified = len(survivor_ids) == 1
            targets = {}

            for transformation in transformations:
                forecasts = {}
                decisions = {}
                for world_id in survivor_ids:
                    forecast = stochastic_counterfactual_forecast(
                        landscape,
                        associates,
                        specs_by_id[world_id],
                        current_snapshot=current_snapshot,
                        transformation=transformation,
                    )
                    forecasts[world_id] = forecast.counterfactual_probability
                    decisions[world_id] = forecast.binary_decision

                truth_forecast = stochastic_counterfactual_forecast(
                    landscape,
                    associates,
                    truth_spec,
                    current_snapshot=current_snapshot,
                    transformation=transformation,
                )

                exact_values = set(forecasts.values())
                decision_values = set(decisions.values())
                exact_identified = len(exact_values) == 1
                decision_identified = len(decision_values) == 1

                if parameter_identified:
                    totals[transformation]["parameter_world_identified"] += 1
                    by_scenario[scenario_id][transformation]["parameter_world_identified"] += 1
                if exact_identified:
                    totals[transformation]["exact_forecast_identified"] += 1
                    by_scenario[scenario_id][transformation]["exact_forecast_identified"] += 1
                if decision_identified:
                    totals[transformation]["binary_decision_identified"] += 1
                    by_scenario[scenario_id][transformation]["binary_decision_identified"] += 1
                else:
                    totals[transformation]["binary_decision_unresolved"] += 1
                    by_scenario[scenario_id][transformation]["binary_decision_unresolved"] += 1

                if not parameter_identified and decision_identified:
                    totals[transformation]["decision_without_world_identification"] += 1
                    by_scenario[scenario_id][transformation]["decision_without_world_identification"] += 1
                if not parameter_identified and exact_identified:
                    totals[transformation]["exact_forecast_without_world_identification"] += 1
                    by_scenario[scenario_id][transformation]["exact_forecast_without_world_identification"] += 1

                if parameter_identified and not exact_identified:
                    hierarchy_violations += 1
                if exact_identified and not decision_identified:
                    hierarchy_violations += 1

                if exact_identified:
                    identified_forecast = next(iter(exact_values))
                    if identified_forecast != truth_forecast.counterfactual_probability:
                        truth_consistency_failures += 1
                if decision_identified:
                    identified_decision = next(iter(decision_values))
                    if identified_decision != truth_forecast.binary_decision:
                        truth_consistency_failures += 1

                targets[transformation] = {
                    "survivor_count": len(survivor_ids),
                    "parameter_world_identified": parameter_identified,
                    "exact_forecast_class_count": len(exact_values),
                    "exact_forecast_identified": exact_identified,
                    "binary_decision_class_count": len(decision_values),
                    "binary_decision_identified": decision_identified,
                    "truth_binary_decision": truth_forecast.binary_decision,
                    "truth_expected_delta": truth_forecast.expected_count_delta,
                }

            run_rows.append(
                {
                    "scenario_id": scenario_id,
                    "truth_world_id": truth_world_id,
                    "replicate": replicate,
                    "observed_h40_count": len(observed_h40),
                    "current_snapshot_count": int(np.sum(current_snapshot)),
                    "survivor_ids": list(survivor_ids),
                    "survivor_count": len(survivor_ids),
                    "targets": targets,
                }
            )

    if len(run_rows) != 384:
        raise RuntimeError(f"expected 384 runs, got {len(run_rows)}")

    H2 = {
        t: totals[t]["decision_without_world_identification"] > 0
        for t in transformations
    }
    H3 = any(
        totals[t]["exact_forecast_without_world_identification"] > 0
        for t in transformations
    )
    H4 = {
        t: totals[t]["binary_decision_unresolved"] > 0
        for t in transformations
    }

    verdicts = {
        "H1_target_hierarchy": "SUPPORTED" if hierarchy_violations == 0 else "REFUTED",
        "H2_decision_without_world_identification": {
            t: "SUPPORTED" if H2[t] else "REFUTED"
            for t in transformations
        },
        "H3_exact_forecast_without_world_identification": (
            "SUPPORTED" if H3 else "REFUTED"
        ),
        "H4_counterfactual_disagreement_exists": {
            t: "SUPPORTED" if H4[t] else "REFUTED"
            for t in transformations
        },
        "H5_truth_consistency": (
            "SUPPORTED" if truth_consistency_failures == 0 else "REFUTED"
        ),
    }

    by_scenario_serializable = {
        scenario: {
            t: dict(sorted(values.items()))
            for t, values in rows.items()
        }
        for scenario, rows in by_scenario.items()
    }

    result = {
        "schema": "eog.bam_stochastic_counterfactual_targets.result.v1",
        "parent_stochastic_fingerprint": EXPECTED_STOCHASTIC,
        "parent_structured_fingerprint": EXPECTED_STRUCTURED,
        "run_count": len(run_rows),
        "candidate_world_count": len(specs),
        "truth_scenario_count": len(truths),
        "truth_retention_failures": truth_retention_failures,
        "target_hierarchy_violations": hierarchy_violations,
        "truth_consistency_failures": truth_consistency_failures,
        "totals": totals,
        "by_scenario": by_scenario_serializable,
        "verdicts": verdicts,
        "runs": run_rows,
    }
    result["fingerprint"] = _sha256(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "run_count": result["run_count"],
        "truth_retention_failures": result["truth_retention_failures"],
        "target_hierarchy_violations": result["target_hierarchy_violations"],
        "truth_consistency_failures": result["truth_consistency_failures"],
        "totals": result["totals"],
        "verdicts": result["verdicts"],
        "fingerprint": result["fingerprint"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
