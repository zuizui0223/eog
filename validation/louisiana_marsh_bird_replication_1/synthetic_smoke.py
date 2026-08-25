from __future__ import annotations

from datetime import date, timedelta
import hashlib
import json
from pathlib import Path

from eog.v2.predictive_complementarity import PredictiveComplementarityDeclaration

from runner_core import (
    CONVENTIONAL_FEATURE_NAMES,
    build_prepared_rows,
    canonical_sha256,
    exact_count_gate,
    fit_and_score,
)

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "full_freeze_spec.json").read_text(encoding="utf-8"))
OUT = Path("build/louisiana_marsh_bird_replication_1/synthetic_smoke.json")
OUT.parent.mkdir(parents=True, exist_ok=True)


def section_fp(name: str) -> str:
    return canonical_sha256(FREEZE[name])


def declaration() -> PredictiveComplementarityDeclaration:
    runtime = FREEZE["preprocessing_model_fit"]["runtime"]
    learner_fp = canonical_sha256({
        "learner": FREEZE["preprocessing_model_fit"]["learner"],
        "hyperparameters": FREEZE["preprocessing_model_fit"]["hyperparameters"],
        "fit_policy": FREEZE["preprocessing_model_fit"]["fit_policy"],
        "runtime": runtime,
    })
    external_fp = canonical_sha256({
        "feature_names": list(FREEZE["comparators"]["conventional_feature_names"]),
        "definitions": FREEZE["preprocessing_model_fit"],
    })
    layer = FREEZE["layer_b_representation"]
    eog_fp = canonical_sha256({
        "representation_name": layer["representation_name"],
        "feature_names": layer["feature_names"],
        "support_value": layer["support_value"],
    })
    metrics = FREEZE["metrics_decision"]
    return PredictiveComplementarityDeclaration(
        metric_name=metrics["primary_metric"],
        lower_is_better=metrics["lower_is_better"],
        expected_outer_unit_count=metrics["primary_outer_unit_count"],
        favorable_min_augmented_wins=metrics["favorable_min_augmented_wins"],
        adverse_min_baseline_wins=metrics["adverse_min_baseline_wins"],
        learner_fit_fingerprint=learner_fp,
        response_endpoint_fingerprint=section_fp("response_semantics"),
        split_fingerprint=section_fp("temporal_split"),
        external_feature_fingerprint=external_fp,
        eog_feature_fingerprint=eog_fp,
    )


def main() -> None:
    frozen_names = tuple(FREEZE["comparators"]["conventional_feature_names"])
    if frozen_names != CONVENTIONAL_FEATURE_NAMES:
        raise RuntimeError("runner conventional feature identity differs from freeze")

    sites = tuple(f"S{index:02d}" for index in range(1, 34))
    coordinates = {}
    marsh = {}
    habitat = {}
    marsh_cycle = ("Brackish", "Fresh", "Intermediate", "Salt")
    for index, site in enumerate(sites):
        cluster = 0 if index < 22 else 1
        within = index if cluster == 0 else index - 22
        coordinates[site] = (
            29.60 + cluster * 0.22 + (within % 6) * 0.018,
            -92.82 + cluster * 0.22 + (within // 6) * 0.021,
        )
        category = marsh_cycle[index % len(marsh_cycle)]
        marsh[site] = category
        habitat[site] = (
            "Brackish-Salt Marsh"
            if category in {"Brackish", "Salt"}
            else "Fresh-Intermediate Marsh"
        )

    periods = tuple(FREEZE["temporal_split"]["chronological_sample_period_order"])
    samples = {}
    start = date(2012, 2, 13)
    for chronological_index, period in enumerate(periods):
        current = start + timedelta(days=7 * chronological_index)
        samples[int(period)] = {
            "date": current.isoformat(),
            "precipitation": float((chronological_index * 7) % 23) / 3.0,
            "min_air_temp": 5.0 + float((chronological_index * 11) % 20),
        }

    labels = {}
    for chronological_index, period in enumerate(periods):
        for site_index, site in enumerate(sites):
            value = 1 if ((site_index * 3 + chronological_index * 5 + site_index // 7) % 13) < 3 else 0
            labels[(int(period), site)] = value

    count = exact_count_gate(
        labels,
        calibration_periods=FREEZE["temporal_split"]["scored_calibration_sample_periods"],
        heldout_periods=FREEZE["temporal_split"]["heldout_sample_periods_chronological"],
        primary_outer_units=FREEZE["temporal_split"]["heldout_sample_periods_chronological"],
        minima=FREEZE["count_gate"],
    )
    if not count.passed:
        raise RuntimeError(f"synthetic count gate unexpectedly failed: {count}")

    feature_result = build_prepared_rows(
        sites=sites,
        site_coordinates=coordinates,
        site_marsh=marsh,
        site_habitat=habitat,
        samples=samples,
        chronological_periods=periods,
        initialization_period=FREEZE["temporal_split"]["initialization_only_sample_period"],
        labels=labels,
        thresholds=FREEZE["world_scale"]["geometry_thresholds_km"],
        structural_gate_fingerprint=FREEZE["structural_adequacy"]["gate1_fingerprint"],
    )

    score = fit_and_score(
        rows=feature_result.rows,
        calibration_periods=FREEZE["temporal_split"]["scored_calibration_sample_periods"],
        heldout_periods=FREEZE["temporal_split"]["heldout_sample_periods_chronological"],
        rf_hyperparameters=FREEZE["preprocessing_model_fit"]["hyperparameters"],
        complementarity_declaration=declaration(),
        probability_clip=FREEZE["metrics_decision"]["probability_clip"],
        tie_tolerance=FREEZE["metrics_decision"]["tie_tolerance"],
    )

    payload = {
        "schema": "eog.louisiana_marsh_bird_synthetic_smoke.v1",
        "attempt_id": FREEZE["attempt_id"],
        "status": "synthetic_end_to_end_smoke_pass",
        "scientific_evidential_value": false,
        "synthetic_site_count": len(sites),
        "synthetic_label_count": len(labels),
        "prepared_row_count": len(feature_result.rows),
        "count_gate": {
            "calibration_events": count.calibration_events,
            "calibration_non_events": count.calibration_non_events,
            "heldout_events": count.heldout_events,
            "heldout_non_events": count.heldout_non_events,
            "primary_outer_units_with_both_classes": count.primary_outer_units_with_both_classes,
            "passed": count.passed,
        },
        "final_surviving_world_ids": list(feature_result.final_surviving_world_ids),
        "local_worlds_eliminated": list(feature_result.local_worlds_eliminated),
        "paired_smoke_status": score["status"],
        "paired_outer_unit_count": score["heldout_outer_units_scored"],
        "model_fit_count": score["model_fit_count"],
        "runner_conventional_feature_count": len(CONVENTIONAL_FEATURE_NAMES),
        "layer_b_feature_count": len(FREEZE["layer_b_representation"]["feature_names"]),
        "response_audit": {
            "response_payload_requests": 0,
            "response_payload_bytes_opened": 0,
            "response_rows_opened": false,
            "response_values_opened": false
        }
    }
    payload["fingerprint"] = canonical_sha256(payload)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
