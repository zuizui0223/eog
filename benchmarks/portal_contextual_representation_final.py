from __future__ import annotations

import argparse
import base64
import csv
import io
import json
import math
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import log_loss

from eog.v2.predictive_signature_gate import evaluate_saturated_static_signature
from eog.v2.source_symmetric_predictive_summary import summarize_source_symmetric_support
from eog.v2.worldset_contraction_audit import audit_worldset_contraction

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "validation/contextual_representation_fresh_v1/portal_final_contract.json"
STAGE0_PATH = ROOT / "validation/contextual_representation_fresh_v1/portal_stage0_result.json"
OUTPUT_PATH = ROOT / "build/portal_contextual_representation_final_result.json"
API = "https://api.github.com/repos/weecology/PortalData/git/blobs/{}"
PRE_RESPONSE = {
    "coords": "fa96bd174b28767acb27758fddaca0b51676800f",
    "plots": "d4502de80688bd42b52eee1f9e0b8bc429385178",
    "trapping": "e405c7669c9a25a9111527270cdaec7af26f31c7",
}
RESPONSE_SHA = "daac4615a868339e3c1f77b35ceebf005e1240ad"
EPS = 1e-6


def fetch_blob(expected_sha: str) -> bytes:
    req = urllib.request.Request(API.format(expected_sha), headers={"Accept": "application/vnd.github+json", "User-Agent": "eog-portal-final"})
    with urllib.request.urlopen(req, timeout=60) as r:
        payload = json.load(r)
    if payload.get("sha") != expected_sha or payload.get("encoding") != "base64":
        raise RuntimeError("GitHub blob identity/encoding mismatch")
    return base64.b64decode(payload["content"])


def csv_rows(blob: bytes) -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(blob.decode("utf-8-sig")))
    rows = list(reader)
    return list(reader.fieldnames or []), rows


def load_pre_response() -> tuple[dict[int, tuple[float, float]], dict[tuple[int, int, int], tuple[str, str, str]], dict[tuple[int, int], dict[str, object]], list[int]]:
    _, coords = csv_rows(fetch_blob(PRE_RESPONSE["coords"]))
    _, plots = csv_rows(fetch_blob(PRE_RESPONSE["plots"]))
    _, trapping = csv_rows(fetch_blob(PRE_RESPONSE["trapping"]))

    corners: dict[int, list[tuple[float, float]]] = defaultdict(list)
    for r in coords:
        if r["type"].strip().lower() == "corner":
            p = int(r["plot"])
            if 1 <= p <= 24:
                corners[p].append((float(r["east"]), float(r["north"])))
    centroids = {p: (float(np.mean([v[0] for v in corners[p]])), float(np.mean([v[1] for v in corners[p]]))) for p in range(1, 25)}

    treatment: dict[tuple[int, int, int], tuple[str, str, str]] = {}
    for r in plots:
        treatment[(int(r["year"]), int(r["month"]), int(r["plot"]))] = (r["treatment"], r["resourcetreatment"], r["anttreatment"])

    units: dict[tuple[int, int], dict[str, object]] = {}
    for r in trapping:
        try:
            period, plot = int(r["period"]), int(r["plot"])
            sampled, effort, qcflag = int(r["sampled"]), float(r["effort"]), int(r["qcflag"])
        except (TypeError, ValueError):
            continue
        if period <= 0 or not (1 <= plot <= 24) or sampled != 1 or effort <= 0 or qcflag != 1:
            continue
        key = (period, plot)
        if key in units:
            raise RuntimeError(f"duplicate eligible plot-period in trapping registry: {key}")
        year, month = int(r["year"]), int(r["month"])
        units[key] = {"period": period, "plot": plot, "year": year, "month": month, "effort": effort, "treatment": treatment[(year, month, plot)]}
    periods = sorted({p for p, _ in units})
    return centroids, treatment, units, periods


def conventional_encoder(units: dict[tuple[int, int], dict[str, object]], centroids: dict[int, tuple[float, float]]):
    treat = sorted({str(v["treatment"][0]) for v in units.values()})
    resource = sorted({str(v["treatment"][1]) for v in units.values()})
    ant = sorted({str(v["treatment"][2]) for v in units.values()})
    tmap, rmap, amap = {v: i for i, v in enumerate(treat)}, {v: i for i, v in enumerate(resource)}, {v: i for i, v in enumerate(ant)}
    years = [int(v["year"]) for v in units.values()]
    ymin, ymax = min(years), max(years)

    def encode(unit: dict[str, object]) -> np.ndarray:
        month = int(unit["month"])
        phase = 2.0 * math.pi * (month - 1) / 12.0
        year_scaled = (int(unit["year"]) - ymin) / max(1, ymax - ymin)
        east, north = centroids[int(unit["plot"])]
        vec = [float(unit["effort"]), math.sin(phase), math.cos(phase), year_scaled, east, north]
        for value, mapping in ((str(unit["treatment"][0]), tmap), (str(unit["treatment"][1]), rmap), (str(unit["treatment"][2]), amap)):
            onehot = [0.0] * len(mapping)
            onehot[mapping[value]] = 1.0
            vec.extend(onehot)
        return np.asarray(vec, dtype=float)
    return encode


def summarize_no_source(surviving_local: list[int], external_alive: bool, node_count: int, declared: int = 5) -> np.ndarray:
    world_count = len(surviving_local) + int(external_alive)
    values = np.asarray(([0.0] * len(surviving_local)) + ([1.0] if external_alive else []), dtype=float)
    rows = []
    for _ in range(node_count):
        mn, mx = float(np.min(values)), float(np.max(values))
        rows.append([
            world_count / declared,
            float(np.mean(values)),
            float(np.std(values)),
            mn,
            mx,
            float(np.quantile(values, 0.25, method="linear")),
            float(np.quantile(values, 0.50, method="linear")),
            float(np.quantile(values, 0.75, method="linear")),
            float(np.mean(values > 0.0)),
            mx - mn,
        ])
    return np.asarray(rows, dtype=float)


def contextual_matrix(source_plots: set[int], surviving_local: list[int], thresholds: list[float], centroids: dict[int, tuple[float, float]]) -> np.ndarray:
    nodes = list(range(1, 25))
    if not source_plots:
        return summarize_no_source(surviving_local, True, len(nodes))
    worlds = [f"local_{i}" for i in surviving_local] + ["external_open"]
    tensor = np.zeros((len(source_plots), len(worlds), len(nodes)), dtype=float)
    sources = sorted(source_plots)
    for si, source in enumerate(sources):
        sx, sy = centroids[source]
        for wi, local_index in enumerate(surviving_local):
            threshold = thresholds[local_index]
            for ni, node in enumerate(nodes):
                nx, ny = centroids[node]
                tensor[si, wi, ni] = 1.0 if math.hypot(sx - nx, sy - ny) <= threshold else 0.0
        tensor[si, len(worlds) - 1, :] = 1.0
    summary = summarize_source_symmetric_support(
        tensor,
        source_ids=[f"plot_{p}" for p in sources],
        world_ids=worlds,
        node_ids=[f"plot_{p}" for p in nodes],
        declared_world_count=5,
    )
    return summary.feature_matrix


def update_state(positives: set[int], source_plots: set[int], surviving_local: list[int], thresholds: list[float], centroids: dict[int, tuple[float, float]]) -> tuple[set[int], list[int]]:
    keep = list(surviving_local)
    if source_plots and positives:
        next_keep: list[int] = []
        for idx in surviving_local:
            threshold = thresholds[idx]
            compatible = True
            for target in positives:
                tx, ty = centroids[target]
                if not any(math.hypot(centroids[s][0] - tx, centroids[s][1] - ty) <= threshold for s in source_plots):
                    compatible = False
                    break
            if compatible:
                next_keep.append(idx)
        keep = next_keep
    return source_plots | positives, keep


def rf(contract: dict[str, object]) -> RandomForestClassifier:
    hp = contract["learner"]
    return RandomForestClassifier(
        n_estimators=int(hp["n_estimators"]),
        min_samples_leaf=int(hp["min_samples_leaf"]),
        max_features=str(hp["max_features"]),
        class_weight=None,
        random_state=int(hp["random_state"]),
        n_jobs=int(hp["n_jobs"]),
    )


def proba(model: RandomForestClassifier, x: np.ndarray) -> np.ndarray:
    if list(model.classes_) != [0, 1]:
        raise RuntimeError(f"unexpected model classes {model.classes_}")
    return np.clip(model.predict_proba(x)[:, 1], EPS, 1 - EPS)


def run_live() -> dict[str, object]:
    contract = json.loads(CONTRACT_PATH.read_text())
    stage0 = json.loads(STAGE0_PATH.read_text())
    if not stage0.get("stage0_pass"):
        raise RuntimeError("Stage0 did not pass")
    centroids, _, units, periods = load_pre_response()
    if periods != list(range(1, 541)):
        raise RuntimeError("frozen eligible period calendar drift")

    # Sole full biological-response access for this attempt.
    response_blob = fetch_blob(RESPONSE_SHA)
    header, response_rows = csv_rows(response_blob)
    required = set(contract["authoritative_response"]["required_columns"])
    if not required.issubset(set(header)):
        result = {"schema": "eog.contextual_representation_fresh_v1.portal_final_result", "terminal_class": "stop_response_schema_mismatch", "response_consumed": True, "required_columns": sorted(required), "observed_columns": header, "changes_closed_eog_wf": False}
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True); OUTPUT_PATH.write_text(json.dumps(result, indent=2) + "\n"); return result

    positives_by_period: dict[int, set[int]] = defaultdict(set)
    for r in response_rows:
        try:
            period, plot = int(r["period"]), int(r["plot"])
        except (TypeError, ValueError):
            continue
        if period <= 0 or not (1 <= plot <= 24):
            continue
        if r["species"].strip() == "DM" and (period, plot) in units:
            positives_by_period[period].add(plot)

    y_by_key = {(period, plot): int(plot in positives_by_period.get(period, set())) for period, plot in units}
    train_keys = [(p, plot) for p in range(2, 406) for plot in range(1, 25) if (p, plot) in units]
    heldout_keys = [(p, plot) for p in range(406, 541) for plot in range(1, 25) if (p, plot) in units]
    train_y = np.asarray([y_by_key[k] for k in train_keys], dtype=int)
    heldout_y = np.asarray([y_by_key[k] for k in heldout_keys], dtype=int)
    both_class_periods = sum(len({y_by_key[(p, plot)] for plot in range(1, 25) if (p, plot) in units}) == 2 for p in range(406, 541))
    minima = contract["estimability_minima"]
    estimability = {
        "calibration_positive_plot_periods": int(np.sum(train_y == 1)),
        "calibration_negative_plot_periods": int(np.sum(train_y == 0)),
        "heldout_positive_plot_periods": int(np.sum(heldout_y == 1)),
        "heldout_negative_plot_periods": int(np.sum(heldout_y == 0)),
        "heldout_periods_with_both_classes": int(both_class_periods),
    }
    if any(estimability[k] < int(minima[k]) for k in minima):
        result = {"schema": "eog.contextual_representation_fresh_v1.portal_final_result", "terminal_class": "stop_response_estimability", "response_consumed": True, "estimability": estimability, "minima": minima, "changes_closed_eog_wf": False}
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True); OUTPUT_PATH.write_text(json.dumps(result, indent=2) + "\n"); return result

    encode = conventional_encoder(units, centroids)
    thresholds = [float(v) for v in contract["worlds"]["local_threshold_m"]]
    source_plots: set[int] = set()
    surviving_local = [0, 1, 2, 3]
    contextual_by_key: dict[tuple[int, int], np.ndarray] = {}
    surviving_counts_before: list[int] = []
    contraction_events: list[dict[str, object]] = []

    # Period 1 initializes state only.
    source_plots, surviving_local = update_state(positives_by_period.get(1, set()), source_plots, surviving_local, thresholds, centroids)
    for period in range(2, 541):
        matrix = contextual_matrix(source_plots, surviving_local, thresholds, centroids)
        surviving_counts_before.append(len(surviving_local) + 1)
        for plot in range(1, 25):
            if (period, plot) in units:
                contextual_by_key[(period, plot)] = matrix[plot - 1]
        old = list(surviving_local)
        source_plots, surviving_local = update_state(positives_by_period.get(period, set()), source_plots, surviving_local, thresholds, centroids)
        if old != surviving_local:
            contraction_events.append({"period": period, "before_local": old, "after_local": list(surviving_local)})

    x_train_base = np.vstack([encode(units[k]) for k in train_keys])
    x_train_ctx = np.vstack([contextual_by_key[k] for k in train_keys])
    x_test_base = np.vstack([encode(units[k]) for k in heldout_keys])
    x_test_ctx = np.vstack([contextual_by_key[k] for k in heldout_keys])

    contraction_audit = audit_worldset_contraction(5, surviving_counts_before[:404])
    signature_gate = evaluate_saturated_static_signature(x_train_ctx, [f"plot_{k[1]}" for k in train_keys], contraction_audit)
    if not signature_gate.predictive_use_allowed:
        result = {"schema": "eog.contextual_representation_fresh_v1.portal_final_result", "terminal_class": "stop_saturated_static_identity_signature", "response_consumed": True, "signature_gate": signature_gate.__dict__, "changes_closed_eog_wf": False}
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True); OUTPUT_PATH.write_text(json.dumps(result, indent=2, default=list) + "\n"); return result

    baseline = rf(contract); augmented = rf(contract)
    baseline.fit(x_train_base, train_y)
    augmented.fit(np.column_stack([x_train_base, x_train_ctx]), train_y)

    baseline_prob = proba(baseline, x_test_base)
    augmented_prob = proba(augmented, np.column_stack([x_test_base, x_test_ctx]))

    period_metrics = []
    offset = 0
    for period in range(406, 541):
        keys = [(period, plot) for plot in range(1, 25) if (period, plot) in units]
        n = len(keys)
        yy = heldout_y[offset:offset+n]
        pb = baseline_prob[offset:offset+n]
        pa = augmented_prob[offset:offset+n]
        bl = float(log_loss(yy, pb, labels=[0, 1]))
        al = float(log_loss(yy, pa, labels=[0, 1]))
        bb = float(np.mean((pb - yy) ** 2)); ab = float(np.mean((pa - yy) ** 2))
        period_metrics.append({"period": period, "n": n, "baseline_log_loss": bl, "augmented_log_loss": al, "delta": al - bl, "baseline_brier": bb, "augmented_brier": ab})
        offset += n

    macro_base = float(np.mean([r["baseline_log_loss"] for r in period_metrics]))
    macro_aug = float(np.mean([r["augmented_log_loss"] for r in period_metrics]))
    delta = macro_aug - macro_base
    macro_brier_base = float(np.mean([r["baseline_brier"] for r in period_metrics]))
    macro_brier_aug = float(np.mean([r["augmented_brier"] for r in period_metrics]))
    terminal = "favorable_contextual_added_value" if delta < 0 else ("adverse_contextual_added_value" if delta > 0 else "tie_contextual_added_value")
    result = {
        "schema": "eog.contextual_representation_fresh_v1.portal_final_result",
        "terminal_class": terminal,
        "response_consumed": True,
        "counts_as_fourth_closed_endpoint": False,
        "changes_closed_eog_wf": False,
        "known_truth_translation_supported": bool(delta < 0),
        "estimability": estimability,
        "primary": {"baseline_macro_log_loss": macro_base, "augmented_macro_log_loss": macro_aug, "augmented_minus_baseline": delta, "relative_change": delta / macro_base},
        "secondary": {"baseline_macro_brier": macro_brier_base, "augmented_macro_brier": macro_brier_aug, "augmented_minus_baseline_brier": macro_brier_aug - macro_brier_base, "augmented_period_wins": sum(r["delta"] < 0 for r in period_metrics), "heldout_period_count": len(period_metrics)},
        "layer_a": {"contraction_events": contraction_events, "final_surviving_local_worlds": surviving_local, "external_open_survives": True},
        "signature_gate": {"status": signature_gate.status, "predictive_use_allowed": signature_gate.predictive_use_allowed, "worldset_fully_saturated": signature_gate.worldset_fully_saturated, "all_repeated_entities_static": signature_gate.all_repeated_entities_static, "entity_signature_injective": signature_gate.entity_signature_injective},
        "period_metrics": period_metrics,
        "interpretation": "This once-only post-closure validation tests whether source-symmetric sequentially refreshed contextual EOG state adds heldout predictive information beyond the unchanged strong conventional RF baseline. It does not alter the closed EOG-WF three-endpoint synthesis."
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "period_metrics"}, indent=2, sort_keys=True))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if not args.live:
        print("proposal-safe: live response access not executed")
        return
    run_live()


if __name__ == "__main__":
    main()
