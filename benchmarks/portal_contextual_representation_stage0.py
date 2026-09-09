from __future__ import annotations

import base64
import csv
import io
import json
import math
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "validation/contextual_representation_fresh_v1/portal_stage0_contract.json"
OUTPUT_PATH = ROOT / "build/portal_contextual_representation_stage0_result.json"
API = "https://api.github.com/repos/weecology/PortalData/git/blobs/{}"


def fetch_blob(expected_sha: str) -> bytes:
    req = urllib.request.Request(API.format(expected_sha), headers={"Accept": "application/vnd.github+json", "User-Agent": "eog-response-blind-stage0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if payload.get("sha") != expected_sha:
        raise RuntimeError(f"external blob identity mismatch: {payload.get('sha')} != {expected_sha}")
    if payload.get("encoding") != "base64":
        raise RuntimeError("unexpected GitHub blob encoding")
    return base64.b64decode(payload["content"])


def rows_from(blob: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(blob.decode("utf-8-sig"))))


def q(values: np.ndarray, p: float) -> float:
    return float(np.quantile(values, p, method="linear"))


def run() -> dict[str, object]:
    contract = json.loads(CONTRACT_PATH.read_text())
    allowed = contract["dataset"]["allowed_pre_response_files"]
    blobs = {path: fetch_blob(sha) for path, sha in allowed.items() if path.endswith(".csv")}

    coords = rows_from(blobs["SiteandMethods/Portal_UTMCoords.csv"])
    plots = rows_from(blobs["SiteandMethods/Portal_plots.csv"])
    trapping = rows_from(blobs["Rodents/Portal_rodent_trapping.csv"])
    species = rows_from(blobs["Rodents/Portal_rodent_species.csv"])

    # Plot centroids are reconstructed only from corner coordinates.
    corners: dict[int, list[tuple[float, float]]] = defaultdict(list)
    for r in coords:
        if r["type"].strip().lower() != "corner":
            continue
        plot = int(r["plot"])
        if 1 <= plot <= 24:
            corners[plot].append((float(r["east"]), float(r["north"])))
    centroids = {
        p: (float(np.mean([x for x, _ in pts])), float(np.mean([y for _, y in pts])))
        for p, pts in corners.items()
        if pts
    }
    centroid_pass = len(centroids) == 24 and all(len(corners[p]) >= 4 for p in range(1, 25))

    # Response-blind geometry ladder.
    dists: list[float] = []
    for i in range(1, 25):
        for j in range(i + 1, 25):
            xi, yi = centroids[i]
            xj, yj = centroids[j]
            d = math.hypot(xi - xj, yi - yj)
            if d > 0:
                dists.append(d)
    arr = np.asarray(dists, dtype=float)
    thresholds = [q(arr, p) for p in (0.25, 0.50, 0.75, 0.90)]
    geometry_pass = len(set(round(v, 9) for v in thresholds)) == 4 and all(v > 0 for v in thresholds)

    # Eligible sampled plot-period rows; response remains unopened.
    eligible: list[dict[str, object]] = []
    for r in trapping:
        try:
            period = int(r["period"])
            plot = int(r["plot"])
            sampled = int(r["sampled"])
            effort = float(r["effort"])
            qcflag = int(r["qcflag"])
        except (TypeError, ValueError):
            continue
        if period <= 0 or not (1 <= plot <= 24) or sampled != 1 or effort <= 0 or qcflag != 1:
            continue
        eligible.append({"period": period, "plot": plot, "year": int(r["year"]), "month": int(r["month"]), "effort": effort})
    periods = sorted({int(r["period"]) for r in eligible})
    cut = int(math.floor(0.75 * len(periods)))
    train_periods = periods[:cut]
    heldout_periods = periods[cut:]
    split_pass = len(train_periods) > 0 and len(heldout_periods) >= 20 and max(train_periods) < min(heldout_periods)

    # Treatment join is part of the frozen conventional baseline and must be fully materializable.
    treatment_by_key: dict[tuple[int, int, int], tuple[str, str, str]] = {}
    for r in plots:
        key = (int(r["year"]), int(r["month"]), int(r["plot"]))
        treatment_by_key[key] = (r["treatment"], r["resourcetreatment"], r["anttreatment"])
    missing_treatment = 0
    missing_centroid = 0
    for r in eligible:
        key = (int(r["year"]), int(r["month"]), int(r["plot"]))
        if key not in treatment_by_key:
            missing_treatment += 1
        if int(r["plot"]) not in centroids:
            missing_centroid += 1
    baseline_pass = missing_treatment == 0 and missing_centroid == 0

    dm_rows = [r for r in species if r.get("species", "").strip() == "DM"]
    if not dm_rows:
        # Current schema uses species code in the first column; fall back without inspecting response.
        first_field = list(species[0].keys())[0] if species else ""
        dm_rows = [r for r in species if r.get(first_field, "").strip() == "DM"]
    species_metadata_pass = bool(dm_rows) and any("merriami" in " ".join(r.values()).lower() for r in dm_rows)

    # Response-free placeholder proves the chosen v2 representation is invariant to arbitrary source/world labels.
    from eog.v2.source_symmetric_predictive_summary import summarize_source_symmetric_support
    tensor = np.asarray([
        [[0.1, 0.3, 0.6], [0.2, 0.4, 0.7]],
        [[0.5, 0.2, 0.8], [0.4, 0.6, 0.9]],
    ], dtype=float)
    a = summarize_source_symmetric_support(tensor, source_ids=["s1", "s2"], world_ids=["w1", "w2"], node_ids=["n1", "n2", "n3"], declared_world_count=2)
    b = summarize_source_symmetric_support(tensor[::-1, ::-1, :], source_ids=["banana", "saffron"], world_ids=["right", "left"], node_ids=["n1", "n2", "n3"], declared_world_count=2)
    invariance_pass = bool(np.array_equal(a.feature_matrix, b.feature_matrix))

    checks = {
        "exact_24_plot_centroids": centroid_pass,
        "four_distinct_positive_geometry_worlds": geometry_pass,
        "ordered_75_25_split_with_20plus_heldout_periods": split_pass,
        "baseline_materializable_without_response": baseline_pass,
        "focal_taxon_metadata_matches_dm": species_metadata_pass,
        "source_world_label_invariance_placeholder": invariance_pass,
    }
    result = {
        "schema": "eog.contextual_representation_fresh_v1.portal_stage0_result",
        "uses_biological_response": False,
        "response_blob_requested": False,
        "counts_as_fourth_closed_endpoint": False,
        "checks": checks,
        "stage0_pass": all(checks.values()),
        "plot_count": len(centroids),
        "corner_counts": {str(p): len(corners[p]) for p in sorted(corners)},
        "geometry_threshold_m": {"q25": thresholds[0], "q50": thresholds[1], "q75": thresholds[2], "q90": thresholds[3]},
        "eligible_plot_period_rows": len(eligible),
        "eligible_period_count": len(periods),
        "train_period_count": len(train_periods),
        "heldout_period_count": len(heldout_periods),
        "train_period_minmax": [min(train_periods), max(train_periods)] if train_periods else None,
        "heldout_period_minmax": [min(heldout_periods), max(heldout_periods)] if heldout_periods else None,
        "split_cut_period": heldout_periods[0] if heldout_periods else None,
        "missing_treatment_rows": missing_treatment,
        "missing_centroid_rows": missing_centroid,
        "next_gate": "freeze exact response parser, class-count estimability minima and once-only outcome access" if all(checks.values()) else "STOP before response",
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    run()
