from __future__ import annotations

from datetime import date, timedelta
import json
from pathlib import Path

from eog.v2.predictive_complementarity import PredictiveComplementarityDeclaration

from validation.azores_yellow_eel_paired_complementarity.pre_response_finalize import canonical_sha256
from validation.azores_yellow_eel_paired_complementarity.runner_core import (
    CONVENTIONAL_FEATURE_NAMES,
    build_prepared_rows,
    exact_count_gate,
    fit_and_score_paired,
)

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "validation/azores_yellow_eel_paired_complementarity"
OUT_DIR = ROOT / "build/azores_yellow_eel_pre_response"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / "synthetic_smoke.json"


def main() -> None:
    spec = json.loads((HERE / "full_freeze_spec.json").read_text(encoding="utf-8"))
    stations = [f"{value} FLO CRUZ" for value in range(148, 158)]
    coordinates = {
        "148 FLO CRUZ": (39.43512, -31.1458),
        "149 FLO CRUZ": (39.43551, -31.1477),
        "150 FLO CRUZ": (39.43572, -31.1487),
        "151 FLO CRUZ": (39.4366, -31.1544),
        "152 FLO CRUZ": (39.43845, -31.157),
        "153 FLO CRUZ": (39.43924, -31.1586),
        "154 FLO CRUZ": (39.43899, -31.1637),
        "155 FLO CRUZ": (39.4418, -31.1701),
        "156 FLO CRUZ": (39.43787, -31.1664),
        "157 FLO CRUZ": (39.43759, -31.1688),
    }
    thresholds = tuple(float(value) for value in spec["world_scale"]["geometry_thresholds_km"])
    first = date.fromisoformat(spec["temporal_split"]["first_scored_week_start"])
    week_starts = [(first + timedelta(days=7 * index)).isoformat() for index in range(49)]

    eligible_active_days = {
        (week, station): 7
        for week in week_starts
        for station in stations
    }
    labels = {}
    for week_index, week in enumerate(week_starts):
        for station in stations:
            positive = station == "148 FLO CRUZ" or (
                station == "151 FLO CRUZ" and week_index % 2 == 0
            )
            labels[(week, station)] = int(positive)

    release_anchors = [
        "148 FLO CRUZ",
        "149 FLO CRUZ",
        "150 FLO CRUZ",
        "151 FLO CRUZ",
        "152 FLO CRUZ",
        "155 FLO CRUZ",
        "156 FLO CRUZ",
        "157 FLO CRUZ",
    ]
    release_anchor_by_tag = {
        f"synthetic_tag_{index:02d}": release_anchors[index % len(release_anchors)]
        for index in range(36)
    }

    calibration_weeks = week_starts[:26]
    heldout_weeks = week_starts[26:]
    primary_outer_units = spec["temporal_split"]["primary_outer_units"]
    gate = exact_count_gate(
        labels,
        calibration_weeks=calibration_weeks,
        heldout_weeks=heldout_weeks,
        primary_outer_units=primary_outer_units,
        minima=spec["count_gate"],
    )
    if not gate.passed:
        raise SystemExit(f"synthetic exact count gate unexpectedly failed: {gate}")

    rows = build_prepared_rows(
        stations=stations,
        week_starts=week_starts,
        eligible_active_days=eligible_active_days,
        labels=labels,
        coordinates=coordinates,
        thresholds=thresholds,
        release_anchor_by_tag=release_anchor_by_tag,
        structural_gate_fingerprint=spec["structural_adequacy"]["structural_gate_fingerprint"],
    )
    if len(rows) != 490:
        raise SystemExit(f"synthetic row count drift: {len(rows)}")
    if any(len(row.conventional) != len(CONVENTIONAL_FEATURE_NAMES) for row in rows):
        raise SystemExit("synthetic conventional feature width drift")
    if any(len(row.layer_b) != 10 for row in rows):
        raise SystemExit("synthetic Layer-B feature width drift")

    declaration = PredictiveComplementarityDeclaration(
        metric_name=spec["metrics_decision"]["primary_metric"],
        lower_is_better=spec["metrics_decision"]["lower_is_better"],
        expected_outer_unit_count=spec["metrics_decision"]["primary_outer_unit_count"],
        favorable_min_augmented_wins=spec["metrics_decision"]["favorable_min_augmented_wins"],
        adverse_min_baseline_wins=spec["metrics_decision"]["adverse_min_baseline_wins"],
        learner_fit_fingerprint=canonical_sha256(spec["preprocessing_model_fit"]),
        response_endpoint_fingerprint=canonical_sha256(spec["response_semantics"]),
        split_fingerprint=canonical_sha256(spec["temporal_split"]),
        external_feature_fingerprint=canonical_sha256(spec["comparators"]["conventional_feature_names"]),
        eog_feature_fingerprint=canonical_sha256(spec["layer_b_representation"]),
    )
    result, scores, supplementary = fit_and_score_paired(
        rows,
        calibration_week_count=26,
        primary_outer_units=primary_outer_units,
        hyperparameters=spec["preprocessing_model_fit"]["hyperparameters"],
        probability_clip=float(spec["metrics_decision"]["probability_clip"]),
        declaration=declaration,
    )
    if result.outer_unit_count != 5 or len(scores) != 5:
        raise SystemExit("synthetic paired endpoint did not produce exactly five primary blocks")

    payload = {
        "schema": "eog.azores_yellow_eel_synthetic_smoke.v1",
        "status": "synthetic_pre_response_runner_pass",
        "synthetic_only": True,
        "prepared_rows": len(rows),
        "conventional_feature_count": len(CONVENTIONAL_FEATURE_NAMES),
        "layer_b_feature_count": len(rows[0].layer_b),
        "count_gate": gate.__dict__,
        "paired_status": result.status,
        "paired_outer_unit_count": result.outer_unit_count,
        "paired_result_fingerprint": result.fingerprint,
        "supplementary": supplementary,
        "response_rows_opened": False,
        "response_values_opened": False,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
