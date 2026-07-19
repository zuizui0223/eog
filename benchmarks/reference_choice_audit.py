"""Frozen audit of comparative-EOG reference choices."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from eog import (
    ReferenceDeclaration,
    fit_robust_reference,
    infer_comparative_geometry,
    validate_reference_declaration,
)


def auc(negative: np.ndarray, positive: np.ndarray) -> float:
    return float(np.mean(positive[:, None] > negative[None, :]) + 0.5 * np.mean(positive[:, None] == negative[None, :]))


def simulate(seed: int, n: int, contaminated: bool = False):
    rng = np.random.default_rng(seed)
    compact = rng.normal(0.0, 1.0, size=(n, 2))
    broad = rng.normal(0.0, 2.0, size=(n, 2))
    external = rng.normal(0.0, 1.25, size=(max(300, n), 2))
    if contaminated:
        outliers = rng.normal(0.0, 12.0, size=(max(6, n // 20), 2))
        external = np.vstack([external, outliers])
    return compact, broad, external


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("reference_choice_results.csv"))
    parser.add_argument("--decision", type=Path, default=Path("reference_choice_decision.json"))
    args = parser.parse_args()

    rows = []
    repeats = 40
    for n in (60, 120, 240):
        values = {mode: {"compact": [], "broad": []} for mode in ("external", "training-only", "pooled-descriptive", "external-contaminated")}
        for repeat in range(repeats):
            compact, broad, external = simulate(10000 + n * 10 + repeat, n)
            _, _, contaminated = simulate(20000 + n * 10 + repeat, n, contaminated=True)
            references = {
                "external": fit_robust_reference(external, provenance="external archived background"),
                "training-only": fit_robust_reference(compact, provenance="training-only compact baseline"),
                "pooled-descriptive": fit_robust_reference(np.vstack([compact, broad]), provenance="pooled retrospective groups"),
                "external-contaminated": fit_robust_reference(contaminated, provenance="external background with declared outliers"),
            }
            for mode, reference in references.items():
                values[mode]["compact"].append(infer_comparative_geometry(compact, reference).span)
                values[mode]["broad"].append(infer_comparative_geometry(broad, reference).span)
        for mode, groups in values.items():
            compact_values = np.asarray(groups["compact"])
            broad_values = np.asarray(groups["broad"])
            rows.append({
                "n": n,
                "reference_mode": mode,
                "compact_median_span": float(np.median(compact_values)),
                "broad_median_span": float(np.median(broad_values)),
                "broad_vs_compact_auc": auc(compact_values, broad_values),
                "median_span_ratio": float(np.median(broad_values / compact_values)),
            })

    declarations = [
        ReferenceDeclaration("external", "prospective", "archived background", True, False),
        ReferenceDeclaration("training-only", "prospective", "baseline group", True, False),
        ReferenceDeclaration("pooled-descriptive", "retrospective", "all compared groups", False, True),
    ]
    for declaration in declarations:
        validate_reference_declaration(declaration)
    invalid_rejected = False
    try:
        validate_reference_declaration(
            ReferenceDeclaration("pooled-descriptive", "prospective", "selected after viewing outcomes", True, True, True)
        )
    except ValueError:
        invalid_rejected = True

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    valid_rows = [row for row in rows if row["reference_mode"] in {"external", "training-only", "pooled-descriptive"}]
    contaminated = [row for row in rows if row["reference_mode"] == "external-contaminated"]
    decision = {
        "minimum_valid_reference_auc": min(row["broad_vs_compact_auc"] for row in valid_rows),
        "minimum_contaminated_reference_auc": min(row["broad_vs_compact_auc"] for row in contaminated),
        "invalid_outcome_informed_reference_rejected": invalid_rejected,
        "passes_gate": min(row["broad_vs_compact_auc"] for row in valid_rows) >= 0.95 and invalid_rejected,
        "interpretation": "reference modes are predeclared; pooled-descriptive is retrospective only; contamination is reported, not optimized away",
    }
    args.decision.write_text(json.dumps(decision, indent=2), encoding="utf-8")
    print(json.dumps(decision, indent=2))
    if not decision["passes_gate"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
