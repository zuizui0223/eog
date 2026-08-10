"""Aggregate complete outcome-free Tanzania current-flow candidate shards."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from scipy.stats import pearsonr, spearmanr

from eog.tanzania_current_flow_solver import canonical_sha256


def _read_jsonl(paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(paths):
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if line.strip():
                    value = json.loads(line)
                    if not isinstance(value, dict):
                        raise ValueError(f"non-object JSON row in {path}:{line_number}")
                    rows.append(value)
    return rows


def _row_key(row: dict[str, Any]) -> tuple[int, str, int]:
    return int(row["coarsening_factor"]), str(row["region"]), int(row["combination_index"])


def _upper(row: dict[str, Any]) -> np.ndarray:
    value = np.asarray(row["matrix_upper_triangle"], dtype=float)
    if value.ndim != 1 or len(value) != 861 or not np.isfinite(value).all():
        raise ValueError("expected 42-patch upper triangle with 861 finite values")
    return value


def _isolation(row: dict[str, Any], field: str) -> np.ndarray:
    value = np.asarray(row[field], dtype=float)
    if value.shape != (42,) or not np.isfinite(value).all():
        raise ValueError(f"expected 42 finite isolation values for {field}")
    return value


def _correlation(a: np.ndarray, b: np.ndarray) -> dict[str, float]:
    log_a = np.log1p(a)
    log_b = np.log1p(b)
    return {
        "spearman": float(spearmanr(log_a, log_b).statistic),
        "pearson_log1p": float(pearsonr(log_a, log_b).statistic),
    }


def _verify_expected_manifest(manifest: dict[str, Any], expected_path: Path) -> dict[str, Any]:
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    if not isinstance(expected, dict) or expected.get("expected_contract_verified") is not True:
        raise ValueError("invalid Tanzania current-flow expected contract")
    frozen = {key: value for key, value in expected.items() if key != "expected_contract_verified"}
    if manifest != frozen:
        raise ValueError(
            "Tanzania current-flow candidate grid drifted from the frozen expected contract. "
            f"expected_sha={canonical_sha256(frozen)}, actual_sha={canonical_sha256(manifest)}"
        )
    verified = dict(manifest)
    verified["expected_contract_verified"] = True
    return verified


def aggregate(*, input_dir: Path, output_dir: Path, expected_contract: Path | None = None) -> dict[str, Any]:
    paths = [path for path in input_dir.rglob("*.jsonl") if path.is_file()]
    if not paths:
        raise ValueError("no current-flow shard JSONL files found")
    rows = _read_jsonl(paths)
    rows.sort(key=_row_key)
    keys = [_row_key(row) for row in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate current-flow candidate keys across shards")
    expected = {(factor, region, index) for factor in (4, 8) for region in ("E", "W") for index in range(512)}
    missing = sorted(expected - set(keys))
    extra = sorted(set(keys) - expected)
    if missing or extra:
        raise ValueError(f"candidate grid incomplete; missing={missing[:5]}, extra={extra[:5]}")
    if any(
        row.get("species_outcomes_inspected") is not False
        or row.get("resistance_selected") is not False
        or row.get("occurrence_model_fitted") is not False
        or row.get("performance_metric_computed") is not False
        or row.get("eog_performance_inspected") is not False
        for row in rows
    ):
        raise ValueError("candidate artifact crossed the pre-outcome boundary")

    lookup = {_row_key(row): row for row in rows}
    comparisons: list[dict[str, Any]] = []
    for region in ("E", "W"):
        for index in range(512):
            fine = lookup[(4, region, index)]
            coarse = lookup[(8, region, index)]
            matrix_corr = _correlation(_upper(fine), _upper(coarse))
            primary_corr = _correlation(
                _isolation(fine, "weighted_isolation_primary"),
                _isolation(coarse, "weighted_isolation_primary"),
            )
            sensitivity_corr = _correlation(
                _isolation(fine, "weighted_isolation_sensitivity"),
                _isolation(coarse, "weighted_isolation_sensitivity"),
            )
            comparisons.append(
                {
                    "region": region,
                    "combination_index": index,
                    "matrix": matrix_corr,
                    "weighted_isolation_primary": primary_corr,
                    "weighted_isolation_sensitivity": sensitivity_corr,
                }
            )

    def summarize(path: tuple[str, ...]) -> dict[str, float]:
        values = []
        for row in comparisons:
            current: Any = row
            for key in path:
                current = current[key]
            values.append(float(current))
        array = np.asarray(values, dtype=float)
        return {
            "minimum": float(np.min(array)),
            "q05": float(np.quantile(array, 0.05)),
            "median": float(np.median(array)),
            "mean": float(np.mean(array)),
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_path = output_dir / "current_flow_candidates.jsonl"
    with candidate_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
    comparison_path = output_dir / "resolution_comparisons.jsonl"
    with comparison_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in comparisons:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")

    rows_projection = [
        {
            "key": list(_row_key(row)),
            "record_sha256": row["record_sha256"],
            "matrix_sha256": row["matrix_sha256"],
        }
        for row in rows
    ]
    manifest = {
        "status": "tanzania_current_flow_candidate_grid_complete_before_outcomes",
        "n_candidate_rows": len(rows),
        "n_resolution_comparisons": len(comparisons),
        "factors": [4, 8],
        "regions": ["E", "W"],
        "n_resistance_combinations_per_region_factor": 512,
        "candidate_index_sha256": canonical_sha256(rows_projection),
        "resolution_comparison_sha256": canonical_sha256(comparisons),
        "resolution_summary": {
            "matrix_spearman": summarize(("matrix", "spearman")),
            "matrix_pearson_log1p": summarize(("matrix", "pearson_log1p")),
            "primary_isolation_spearman": summarize(("weighted_isolation_primary", "spearman")),
            "primary_isolation_pearson_log1p": summarize(("weighted_isolation_primary", "pearson_log1p")),
            "sensitivity_isolation_spearman": summarize(("weighted_isolation_sensitivity", "spearman")),
        },
        "primary_factor": 4,
        "sensitivity_factor": 8,
        "selection_basis": (
            "factor 4 is the finest predeclared standard-runner resolution; "
            "factor 8 preserves all 42 focal cells and is retained as computational-resolution sensitivity. "
            "Neither choice uses species occurrence performance."
        ),
        "native_cell_size_m_approx": 30,
        "primary_cell_size_m_approx": 120,
        "sensitivity_cell_size_m_approx": 240,
        "literal_30m_source_reproduction_completed": False,
        "species_outcomes_inspected": False,
        "resistance_selected": False,
        "occurrence_model_fitted": False,
        "performance_metric_computed": False,
        "eog_performance_inspected": False,
    }
    if expected_contract is not None:
        manifest = _verify_expected_manifest(manifest, expected_contract)
    (output_dir / "candidate_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-contract", type=Path)
    args = parser.parse_args()
    print(json.dumps(aggregate(**vars(args)), indent=2))


if __name__ == "__main__":
    main()
