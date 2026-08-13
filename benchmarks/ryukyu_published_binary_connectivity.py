"""Digitize only the published FST<0.1 bold-grid classification from Frontiers Figure 2.

The continuous heatmap colours are deliberately ignored. Response-free predictors must
already have been frozen before this script is run. The result is a retrospective
published-response sensitivity, not raw-genotype replication or blinded confirmation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

EXPECTED_FIGURE_SHA256 = "70d35809ac5e6408b647a920366703aff02b99cab5888ce10744ed3f7b6e9ad1"
EXPECTED_PREDICTOR_MANIFEST_FINGERPRINT = "8bef7a6ab0b804d4ab1d039bc5778944c589115af261b802d7918c2170a87e50"
LABELS = (
    "OKI", "MYKa", "MYKb", "MYKc", "MYKd", "ISGa", "ISGb", "ISGc",
    "ISGd", "IRMa", "IRMb", "IRMc", "IRMd", "IRMe", "IRMf", "IRMg",
)
X_BOUNDS = np.asarray((270, 380, 488, 598, 712, 819, 929, 1039, 1149, 1262, 1371, 1483, 1590, 1701, 1814, 1922, 2032), dtype=int)
Y_BOUNDS = np.asarray((163, 267, 372, 478, 584, 689, 795, 901, 1010, 1116, 1222, 1328, 1433, 1539, 1645, 1748, 1853), dtype=int)
N_BOLD = 25
L2_PENALTY = 1.0
KNOWN_LOW_PAIRS = {
    tuple(sorted(pair))
    for pair in (
        ("IRMe", "IRMf"),
        ("ISGa", "ISGc"),
        ("MYKb", "MYKd"),
        ("MYKc", "IRMd"),
    )
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _border_score(grayscale: np.ndarray, i: int, j: int) -> float:
    row_position = len(LABELS) - 1 - i
    y0, y1 = int(Y_BOUNDS[row_position]), int(Y_BOUNDS[row_position + 1])
    x0, x1 = int(X_BOUNDS[j]), int(X_BOUNDS[j + 1])
    strips = [
        grayscale[max(0, y0 - 2):y0 + 5, x0 + 8:x1 - 8].ravel(),
        grayscale[y1 - 5:y1 + 2, x0 + 8:x1 - 8].ravel(),
        grayscale[y0 + 8:y1 - 8, max(0, x0 - 2):x0 + 5].ravel(),
        grayscale[y0 + 8:y1 - 8, x1 - 5:x1 + 2].ravel(),
    ]
    values = np.concatenate(strips).astype(float)
    if not values.size:
        raise RuntimeError("empty Figure 2 border strip")
    return float(np.quantile(values, 0.20))


def extract_binary_response(figure_path: str | Path) -> tuple[list[dict[str, object]], str]:
    figure_path = Path(figure_path)
    digest = _sha256(figure_path)
    if digest != EXPECTED_FIGURE_SHA256:
        raise ValueError("Ryukyu published Figure 2 SHA-256 does not match frozen asset")
    image = Image.open(figure_path).convert("L")
    if image.size != (2047, 2081):
        raise ValueError("Ryukyu published Figure 2 dimensions changed")
    grayscale = np.asarray(image, dtype=np.uint8)

    rows = []
    for i in range(len(LABELS)):
        for j in range(i + 1, len(LABELS)):
            rows.append(
                {
                    "population_a": LABELS[i],
                    "population_b": LABELS[j],
                    "border_darkness_q20": _border_score(grayscale, i, j),
                }
            )
    rows.sort(
        key=lambda row: (
            float(row["border_darkness_q20"]),
            str(row["population_a"]),
            str(row["population_b"]),
        )
    )
    for rank, row in enumerate(rows, start=1):
        row["bold_rank"] = rank
        row["published_FST_lt_0.1"] = int(rank <= N_BOLD)
    rows.sort(key=lambda row: (LABELS.index(str(row["population_a"])), LABELS.index(str(row["population_b"]))))

    positives = {
        tuple(sorted((str(row["population_a"]), str(row["population_b"]))))
        for row in rows
        if int(row["published_FST_lt_0.1"]) == 1
    }
    if len(positives) != N_BOLD:
        raise RuntimeError("published bold-grid extraction did not produce 25 pairs")
    missing_known = KNOWN_LOW_PAIRS - positives
    if missing_known:
        raise RuntimeError(f"published bold-grid extraction missed article-identified low-FST pairs: {sorted(missing_known)}")
    return rows, digest


def _fit_ridge_logistic(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mean = np.mean(x, axis=0)
    scale = np.where(np.std(x, axis=0) > 1e-12, np.std(x, axis=0), 1.0)
    z = (x - mean) / scale
    design = np.column_stack([np.ones(len(y)), z])
    beta = np.zeros(design.shape[1], dtype=float)
    penalty = np.concatenate([[0.0], np.full(x.shape[1], L2_PENALTY)])

    def objective(value: np.ndarray) -> float:
        eta = design @ value
        return float(np.sum(np.logaddexp(0.0, eta) - y * eta) + 0.5 * L2_PENALTY * np.dot(value[1:], value[1:]))

    current = objective(beta)
    for _ in range(200):
        eta = design @ beta
        probability = 1.0 / (1.0 + np.exp(-np.clip(eta, -40.0, 40.0)))
        weights = probability * (1.0 - probability)
        gradient = design.T @ (probability - y) + penalty * beta
        hessian = design.T @ (design * weights[:, None]) + np.diag(penalty) + np.eye(design.shape[1]) * 1e-12
        step = np.linalg.solve(hessian, gradient)
        step_scale = 1.0
        accepted = False
        while step_scale >= 2.0 ** -20:
            candidate = beta - step_scale * step
            candidate_objective = objective(candidate)
            if candidate_objective <= current + 1e-12:
                improvement = current - candidate_objective
                beta = candidate
                current = candidate_objective
                accepted = True
                break
            step_scale *= 0.5
        if not accepted:
            raise RuntimeError("Ryukyu ridge logistic update failed")
        if np.max(np.abs(step_scale * step)) <= 1e-9 or improvement <= 1e-9:
            break
    return mean, scale, beta


def _predict(model: tuple[np.ndarray, np.ndarray, np.ndarray], x: np.ndarray) -> np.ndarray:
    mean, scale, beta = model
    z = (np.asarray(x, dtype=float) - mean) / scale
    eta = np.column_stack([np.ones(len(z)), z]) @ beta
    return 1.0 / (1.0 + np.exp(-np.clip(eta, -40.0, 40.0)))


def _log_loss(y: np.ndarray, p: np.ndarray) -> float:
    probability = np.clip(np.asarray(p, dtype=float), 1e-9, 1.0 - 1e-9)
    response = np.asarray(y, dtype=float)
    return float(np.mean(-(response * np.log(probability) + (1.0 - response) * np.log(1.0 - probability))))


def _brier(y: np.ndarray, p: np.ndarray) -> float:
    return float(np.mean(np.square(np.asarray(y, dtype=float) - np.asarray(p, dtype=float))))


def _auc(y: np.ndarray, p: np.ndarray) -> float:
    response = np.asarray(y, dtype=int)
    score = np.asarray(p, dtype=float)
    positive = score[response == 1]
    negative = score[response == 0]
    if not len(positive) or not len(negative):
        raise RuntimeError("Ryukyu AUC requires both response classes")
    return float(np.mean(positive[:, None] > negative[None, :]) + 0.5 * np.mean(positive[:, None] == negative[None, :]))


def _load_predictors(path: Path, manifest_path: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("predictor_manifest_fingerprint") != EXPECTED_PREDICTOR_MANIFEST_FINGERPRINT:
        raise ValueError("Ryukyu response-free predictor manifest differs from the frozen artifact")
    if manifest.get("genetic_response_attached") is not False:
        raise ValueError("Ryukyu response-free predictor artifact already contains a genetic response")
    if _sha256(path) != manifest.get("predictors_csv_sha256"):
        raise ValueError("Ryukyu predictor CSV SHA-256 differs from frozen manifest")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for raw in reader:
            rows.append(
                {
                    "population_a": raw["population_a"],
                    "population_b": raw["population_b"],
                    "geographic_distance": float(raw["geographic_distance"]),
                    "eog_continuous_distance": float(raw["eog_continuous_distance"]),
                    "eog_disconnected": float(raw["eog_disconnected"]),
                    "strong_reference_distance": float(raw["strong_reference_distance"]),
                }
            )
    if len(rows) != 120:
        raise ValueError("Ryukyu frozen predictor table must contain 120 pairs")
    return rows, manifest


def evaluate(figure_path: str | Path, predictors_path: str | Path, manifest_path: str | Path) -> dict[str, object]:
    response_rows, figure_sha = extract_binary_response(figure_path)
    predictor_rows, manifest = _load_predictors(Path(predictors_path), Path(manifest_path))
    response_by_pair = {
        (str(row["population_a"]), str(row["population_b"])): int(row["published_FST_lt_0.1"])
        for row in response_rows
    }
    if {(row["population_a"], row["population_b"]) for row in predictor_rows} != set(response_by_pair):
        raise ValueError("Ryukyu response and predictor pair sets do not align")

    y = np.asarray([response_by_pair[(row["population_a"], row["population_b"])] for row in predictor_rows], dtype=int)
    models = {
        "IBD": np.asarray([[row["geographic_distance"]] for row in predictor_rows], dtype=float),
        "currentflow": np.asarray([[row["strong_reference_distance"]] for row in predictor_rows], dtype=float),
        "IBD_EOG": np.asarray(
            [[row["geographic_distance"], row["eog_continuous_distance"], row["eog_disconnected"]] for row in predictor_rows],
            dtype=float,
        ),
        "currentflow_EOG": np.asarray(
            [[row["strong_reference_distance"], row["eog_continuous_distance"], row["eog_disconnected"]] for row in predictor_rows],
            dtype=float,
        ),
    }
    predictions = {name: np.full(len(y), np.nan, dtype=float) for name in models}
    fold_rows = []
    for held_out in LABELS:
        test = np.asarray([held_out in (row["population_a"], row["population_b"]) for row in predictor_rows], dtype=bool)
        train = ~test
        if int(np.sum(test)) != 15:
            raise RuntimeError("Ryukyu leave-one-population-out fold must hold 15 pairs")
        if len(np.unique(y[train])) != 2:
            raise RuntimeError("Ryukyu LOPO training fold lacks both binary response classes")
        fold_record = {"population": held_out, "n_test": int(np.sum(test)), "models": {}}
        for name, matrix in models.items():
            fitted = _fit_ridge_logistic(matrix[train], y[train])
            score = _predict(fitted, matrix[test])
            predictions[name][test] = score
            fold_record["models"][name] = {
                "log_loss": _log_loss(y[test], score),
                "brier": _brier(y[test], score),
            }
        fold_rows.append(fold_record)

    summary = {}
    for name, score in predictions.items():
        if not np.isfinite(score).all():
            raise RuntimeError("Ryukyu LOPO predictions are incomplete")
        summary[name] = {
            "log_loss": _log_loss(y, score),
            "brier": _brier(y, score),
            "auc": _auc(y, score),
        }
    primary_delta = float(summary["currentflow_EOG"]["log_loss"] - summary["currentflow"]["log_loss"])
    secondary_delta = float(summary["IBD_EOG"]["log_loss"] - summary["IBD"]["log_loss"])
    result = {
        "status": "ryukyu-published-binary-fst-connectivity-retrospective",
        "figure_sha256": figure_sha,
        "predictor_manifest_fingerprint": manifest["predictor_manifest_fingerprint"],
        "n_pairs": len(y),
        "n_published_FST_lt_0.1": int(np.sum(y)),
        "models": summary,
        "currentflow_EOG_minus_currentflow_log_loss": primary_delta,
        "IBD_EOG_minus_IBD_log_loss": secondary_delta,
        "folds": fold_rows,
        "interpretation": (
            "retrospective_binary_added_information"
            if primary_delta < 0.0
            else "retrospective_binary_no_added_information"
        ),
        "claim_boundary": (
            "Published Figure 2 bold-grid FST<0.1 classification only; continuous FST colours, "
            "migration direction and raw-genotype inference are not used."
        ),
        "response_rows": response_rows,
    }
    result["fingerprint"] = _canonical_sha256(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--figure", type=Path, required=True)
    parser.add_argument("--predictors", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(args.figure, args.predictors, args.manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
