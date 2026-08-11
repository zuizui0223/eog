#!/usr/bin/env python3
"""Build Figure 3 from frozen Tanzania held-out projections and artifact-backed species rows."""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIGURE_ID = "figure_3_tanzania"
DEFAULT_MANIFEST = ROOT / "figures/figure_manifest.json"
DEFAULT_EXPECTED = ROOT / "benchmarks/tanzania_heldout_expected.json"
DEFAULT_SPECIES = ROOT / "benchmarks/tanzania_heldout_species_expected.csv"
DEFAULT_PROVENANCE = ROOT / "benchmarks/tanzania_heldout_species_expected_provenance.json"
DEFAULT_OUTPUT = ROOT / "figures/output"
DEFAULT_DATA = ROOT / "manuscript/figure_data"
DEFAULT_CAPTION = ROOT / "manuscript/figure_3_caption.md"
DEFAULT_ALT = ROOT / "manuscript/figure_3_accessibility.md"



class FigureContractError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FigureContractError(f"cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FigureContractError(f"expected a JSON object in {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise FigureContractError(f"{label}: expected {expected!r}, got {actual!r}")


def read_species(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {
        "isolation_mode", "analysis_partition", "species_id",
        "mean_log_loss_difference", "mean_brier_difference",
        "n_declared_predictions", "n_matched_predictions", "n_invalid_predictions",
    }
    if not rows or not required.issubset(rows[0]):
        raise FigureContractError("species source table has an invalid schema")
    parsed = []
    for row in rows:
        parsed.append({
            **row,
            "mean_log_loss_difference": float(row["mean_log_loss_difference"]),
            "mean_brier_difference": float(row["mean_brier_difference"]),
            "n_declared_predictions": int(row["n_declared_predictions"]),
            "n_matched_predictions": int(row["n_matched_predictions"]),
            "n_invalid_predictions": int(row["n_invalid_predictions"]),
        })
    return parsed


def validate_sources(manifest_path: Path, expected_path: Path, species_path: Path, provenance_path: Path):
    manifest = load_json(manifest_path)
    contract = manifest.get(FIGURE_ID)
    if not isinstance(contract, dict):
        raise FigureContractError("Figure 3 contract is missing")
    exp = contract["expected"]
    frozen = load_json(expected_path)
    provenance = load_json(provenance_path)
    rows = read_species(species_path)

    require(sha256(species_path), exp["species_table_sha256"], "species table SHA")
    require(sha256(species_path), provenance["derivation"]["output_sha256"], "provenance output SHA")
    require(provenance.get("not_preregistration"), True, "post-outcome provenance flag")
    source = provenance["source"]
    require(source["artifact_digest"], exp["artifact_digest"], "artifact digest")
    require(source["workflow_run_id"], exp["workflow_run_id"], "workflow run")
    require(source["artifact_id"], exp["artifact_id"], "artifact ID")
    require(source["members"]["heldout_predictions.jsonl"]["sha256"], exp["raw_prediction_rows_sha256"], "raw prediction SHA")
    require(source["members"]["heldout_groups.jsonl"]["sha256"], exp["raw_group_rows_sha256"], "raw group SHA")
    require(source["members"]["heldout_species_results.jsonl"]["sha256"], exp["raw_species_rows_sha256"], "raw species SHA")

    require(frozen.get("results_frozen"), True, "frozen result flag")
    projection = frozen["expected_projection"]
    require(projection["result_fingerprint"], exp["result_fingerprint"], "result fingerprint")
    require(frozen["required_inputs"]["candidate_library_fingerprint"], exp["candidate_library_fingerprint"], "candidate-library fingerprint")
    require(projection["prediction_rows_cross_run_sha256"], exp["prediction_rows_cross_run_sha256"], "prediction cross-run SHA")
    require(projection["group_rows_cross_run_sha256"], exp["group_rows_cross_run_sha256"], "group cross-run SHA")
    require(projection["species_rows_cross_run_sha256"], exp["species_rows_cross_run_sha256"], "species cross-run SHA")
    require(projection["n_species"], exp["species"], "species count")
    require(projection["n_prediction_rows"], exp["prediction_rows"], "prediction count")
    require(projection["n_group_rows"], exp["group_rows"], "group count")
    require(len(rows), exp["derived_species_rows"], "derived species rows")

    combos = {(r["isolation_mode"], r["analysis_partition"]) for r in rows}
    expected_combos = {
        ("primary", "primary_loso"),
        ("inverse_area_sensitivity", "primary_loso"),
        ("primary", "spatial_mst_block"),
        ("inverse_area_sensitivity", "spatial_mst_block"),
    }
    require(combos, expected_combos, "species-table analysis combinations")
    seen = set()
    for row in rows:
        key = (row["isolation_mode"], row["analysis_partition"], row["species_id"])
        if key in seen:
            raise FigureContractError(f"duplicate species row: {key}")
        seen.add(key)
    for mode, partition in expected_combos:
        subset = [r for r in rows if r["isolation_mode"] == mode and r["analysis_partition"] == partition]
        require(len(subset), exp["species"], f"species count for {mode}::{partition}")
        contrast = projection["contrasts"][f"{mode}::{partition}"]
        mean_effect = sum(r["mean_log_loss_difference"] for r in subset) / len(subset)
        mean_brier = sum(r["mean_brier_difference"] for r in subset) / len(subset)
        if round(mean_effect, projection["result_decimals"]) != contrast["macro_mean_species_log_loss_difference"]:
            raise FigureContractError(f"macro log-loss drift for {mode}::{partition}")
        if round(mean_brier, projection["result_decimals"]) != contrast["macro_mean_species_brier_difference"]:
            raise FigureContractError(f"macro Brier drift for {mode}::{partition}")
        require(sum(r["n_matched_predictions"] for r in subset), contrast["n_matched"], f"matched rows for {mode}::{partition}")
        require(sum(r["n_invalid_predictions"] for r in subset), contrast["n_invalid_rows"], f"invalid rows for {mode}::{partition}")
        require(sum(r["n_declared_predictions"] for r in subset), exp["species"] * 14, f"declared rows for {mode}::{partition}")
    return manifest, frozen, provenance, rows


def make_tables(frozen: dict[str, Any], rows: list[dict[str, Any]]):
    projection = frozen["expected_projection"]
    primary_species = [r for r in rows if r["isolation_mode"] == "primary" and r["analysis_partition"] == "primary_loso"]
    primary_species.sort(key=lambda r: (r["mean_log_loss_difference"], r["species_id"]))
    species_table = []
    for rank, row in enumerate(primary_species, start=1):
        effect = row["mean_log_loss_difference"]
        species_table.append({
            "rank": rank,
            "species_id": row["species_id"],
            "mean_log_loss_difference": effect,
            "mean_brier_difference": row["mean_brier_difference"],
            "n_declared_predictions": row["n_declared_predictions"],
            "n_matched_predictions": row["n_matched_predictions"],
            "n_invalid_predictions": row["n_invalid_predictions"],
            "direction": "adverse" if effect > 0 else ("favourable" if effect < 0 else "equal"),
        })

    order = [
        ("primary::primary_loso", "Primary weighting | LOSO"),
        ("inverse_area_sensitivity::primary_loso", "Inverse-area weighting | LOSO"),
        ("primary::spatial_mst_block", "Primary weighting | spatial MST blocks"),
        ("inverse_area_sensitivity::spatial_mst_block", "Inverse-area weighting | spatial MST blocks"),
    ]
    contrast_table = []
    for key, label in order:
        item = projection["contrasts"][key]
        lo, hi = item["log_loss_bootstrap_ci95"]
        contrast_table.append({
            "contrast_key": key,
            "label": label,
            "effect": item["macro_mean_species_log_loss_difference"],
            "ci_low": lo,
            "ci_high": hi,
            "n_species": item["n_species"],
            "n_matched": item["n_matched"],
            "n_invalid_rows": item["n_invalid_rows"],
            "sign_flip_p": item["log_loss_sign_flip_p_value"],
            "interval_class": "adverse" if lo > 0 else ("favourable" if hi < 0 else "uncertain"),
        })

    applicability = []
    for partition, label in (("primary_loso", "Leave-one-fragment-out"), ("spatial_mst_block", "Spatial MST blocks")):
        item = projection["contrasts"][f"primary::{partition}"]
        reasons = item["invalid_reason_counts"]
        applicability.append({
            "analysis_partition": partition,
            "label": label,
            "declared_rows_per_weighting": projection["n_species"] * 14,
            "matched_rows_per_weighting": item["n_matched"],
            "invalid_rows_per_weighting": item["n_invalid_rows"],
            "single_class_failures": reasons.get("valid_model_training_rows_single_class", 0),
            "current_flow_selection_failures": reasons.get("current_flow_selection_failed: training response must contain both classes", 0),
        })
    return species_table, contrast_table, applicability


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise FigureContractError(f"refusing to write empty table: {path}")
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for original in rows:
            row = dict(original)
            for key, value in row.items():
                if isinstance(value, float):
                    row[key] = format(value, ".17g")
            writer.writerow(row)


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def text(x: float, y: float, value: str, *, size=15, weight=400, anchor="start", fill="#172033", cls="") -> str:
    class_attr = f' class="{cls}"' if cls else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{fill}"{class_attr}>{esc(value)}</text>'


def line(x1, y1, x2, y2, *, stroke="#8a94a8", width=1.5, dash=""):
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"{dash_attr}/>'


def nice_limits(values: list[float]) -> tuple[float, float, float]:
    lo, hi = min(values + [0.0]), max(values + [0.0])
    span = max(hi - lo, 1e-9)
    raw = span / 6
    power = 10 ** math.floor(math.log10(raw))
    fraction = raw / power
    step = (1 if fraction <= 1 else 2 if fraction <= 2 else 5 if fraction <= 5 else 10) * power
    xmin = math.floor((lo - 0.08 * span) / step) * step
    xmax = math.ceil((hi + 0.08 * span) / step) * step
    if xmin == xmax:
        xmax = xmin + step
    return xmin, xmax, step


def scale(value: float, vmin: float, vmax: float, x0: float, x1: float) -> float:
    return x0 + (value - vmin) / (vmax - vmin) * (x1 - x0)


def render_svg(species: list[dict[str, Any]], contrasts: list[dict[str, Any]], applicability: list[dict[str, Any]], frozen: dict[str, Any]) -> str:
    width, height = 1800, 1240
    all_values = [r["mean_log_loss_difference"] for r in species]
    for row in contrasts:
        all_values.extend([row["ci_low"], row["ci_high"]])
    xmin, xmax, step = nice_limits(all_values)
    colours = {"adverse": "#a84a2a", "favourable": "#2d6f73", "uncertain": "#6b7280", "equal": "#6b7280"}
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="1800" height="1240" fill="#ffffff"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif}</style>',
        text(55, 48, "Figure 3 | Tanzania strong-competitor external benchmark", size=27, weight=700),
        text(55, 78, "Candidate-minus-reference log loss: negative favours EOG; positive is worse.", size=15, fill="#596579"),
    ]

    # Panel A
    out += [text(55, 125, "A", size=22, weight=700), text(90, 125, "Leakage-safe outer-fold workflow", size=19, weight=700)]
    steps = [
        "Outer-training labels only",
        "Select frozen current-flow candidate",
        "Build nearest-anchor and EOG features",
        "Fit shared reference and candidate tiers",
        "Score untouched held-out label",
    ]
    box_x, box_y, box_w, gap = 90, 150, 300, 28
    for i, label in enumerate(steps):
        x = box_x + i * (box_w + gap)
        out.append(f'<rect x="{x}" y="{box_y}" width="{box_w}" height="74" rx="12" fill="#eef2f7" stroke="#718096" stroke-width="1.5"/>')
        out.append(text(x + box_w / 2, box_y + 31, str(i + 1), size=14, weight=700, anchor="middle", fill="#596579"))
        words = label.split()
        split = max(1, len(words) // 2)
        out.append(text(x + box_w / 2, box_y + 51, " ".join(words[:split]), size=13, weight=700, anchor="middle"))
        if split < len(words):
            out.append(text(x + box_w / 2, box_y + 67, " ".join(words[split:]), size=13, weight=700, anchor="middle"))
        if i < len(steps) - 1:
            out.append(line(x + box_w, box_y + 37, x + box_w + gap, box_y + 37, stroke="#718096", width=2))

    # Panel B
    out += [text(55, 280, "B", size=22, weight=700), text(90, 280, "Strict paired comparison", size=19, weight=700)]
    out.append(f'<rect x="90" y="305" width="760" height="92" rx="14" fill="#f7fafc" stroke="#4a5568" stroke-width="1.5"/>')
    out.append(text(120, 337, "Reference", size=15, weight=700))
    out.append(text(120, 366, "area + selected current flow + area × current flow + nearest occurrence", size=15))
    out.append(f'<rect x="900" y="305" width="760" height="92" rx="14" fill="#fff7ed" stroke="#a84a2a" stroke-width="1.5"/>')
    out.append(text(930, 337, "Candidate", size=15, weight=700, fill="#a84a2a"))
    out.append(text(930, 366, "reference + EOG connected frequency", size=15))

    # Panel C species distribution
    cx0, cx1, cy0, cy1 = 90, 1120, 470, 1110
    out += [text(55, 440, "C", size=22, weight=700), text(90, 440, "Species-level primary LOSO effects", size=19, weight=700)]
    xzero = scale(0, xmin, xmax, cx0, cx1)
    out.append(line(xzero, cy0, xzero, cy1, stroke="#253047", width=2, dash="6 5"))
    tick = math.ceil(xmin / step) * step
    while tick <= xmax + step * 0.1:
        x = scale(tick, xmin, xmax, cx0, cx1)
        out.append(line(x, cy1, x, cy1 + 8, stroke="#596579", width=1.2))
        out.append(text(x, cy1 + 29, f"{tick:+.2f}" if abs(tick) > 1e-12 else "0", size=12, anchor="middle", fill="#596579"))
        tick += step
    n = len(species)
    row_gap = (cy1 - cy0) / max(n - 1, 1)
    adverse = sum(r["direction"] == "adverse" for r in species)
    favourable = sum(r["direction"] == "favourable" for r in species)
    equal = n - adverse - favourable
    out.append(text(cx0, cy0 - 17, f"{favourable} species below zero", size=13, weight=700, fill=colours["favourable"]))
    out.append(text(cx1, cy0 - 17, f"{adverse} species above zero" + (f"; {equal} equal" if equal else ""), size=13, weight=700, anchor="end", fill=colours["adverse"]))
    for i, row in enumerate(species):
        y = cy1 - i * row_gap
        x = scale(row["mean_log_loss_difference"], xmin, xmax, cx0, cx1)
        out.append(line(xzero, y, x, y, stroke="#d5dae3", width=1.0))
        radius = 3.6 + 2.0 * row["n_matched_predictions"] / max(r["n_matched_predictions"] for r in species)
        out.append(f'<circle class="species-point" cx="{x:.1f}" cy="{y:.1f}" r="{radius:.2f}" fill="{colours[row["direction"]]}" fill-opacity="0.86" data-matched="{row["n_matched_predictions"]}"/>')
    out.append(text((cx0 + cx1) / 2, cy1 + 58, "Mean candidate-minus-reference log-loss difference", size=14, weight=700, anchor="middle"))
    out.append(text(cx0, cy1 + 82, "Improved relative to reference", size=12, fill=colours["favourable"]))
    out.append(text(cx1, cy1 + 82, "Worsened relative to reference", size=12, anchor="end", fill=colours["adverse"]))

    # Panel D aggregate contrasts on same scale
    dx0, dx1, dy0 = 1220, 1715, 500
    out += [text(1180, 440, "D", size=22, weight=700), text(1220, 440, "Species-macro aggregate contrasts", size=19, weight=700)]
    out.append(line(scale(0, xmin, xmax, dx0, dx1), dy0 - 20, scale(0, xmin, xmax, dx0, dx1), dy0 + 300, stroke="#253047", width=2, dash="6 5"))
    for i, row in enumerate(contrasts):
        y = dy0 + i * 70
        colour = colours[row["interval_class"]]
        xlo, xhi = scale(row["ci_low"], xmin, xmax, dx0, dx1), scale(row["ci_high"], xmin, xmax, dx0, dx1)
        xe = scale(row["effect"], xmin, xmax, dx0, dx1)
        out.append(text(dx0, y - 18, row["label"], size=13, weight=700))
        out.append(line(xlo, y + 8, xhi, y + 8, stroke=colour, width=6))
        out.append(f'<circle class="aggregate-point" cx="{xe:.1f}" cy="{y + 8:.1f}" r="7" fill="{colour}" stroke="#ffffff" stroke-width="2"/>')
        out.append(text(dx1, y - 18, f'{row["effect"]:+.3f} [{row["ci_low"]:+.3f}, {row["ci_high"]:+.3f}]', size=12, anchor="end", fill=colour))
    out.append(text((dx0 + dx1) / 2, dy0 + 312, "Same log-loss-difference scale as panel C", size=12, weight=700, anchor="middle", fill="#596579"))

    # Panel E applicability and failures
    out += [text(1180, 850, "E", size=22, weight=700), text(1220, 850, "Applicability and explicit failures", size=19, weight=700)]
    total_rows = frozen["expected_projection"]["n_prediction_rows"]
    out.append(text(1220, 882, f"{total_rows:,} declared held-out rows across four weighting × partition combinations", size=13, fill="#596579"))
    for i, row in enumerate(applicability):
        y = 910 + i * 132
        out.append(f'<rect x="1220" y="{y}" width="495" height="112" rx="12" fill="#f8fafc" stroke="#a0a8b8" stroke-width="1.2"/>')
        out.append(text(1245, y + 28, row["label"], size=15, weight=700))
        out.append(text(1245, y + 53, f'{row["matched_rows_per_weighting"]} matched / {row["declared_rows_per_weighting"]} declared per weighting', size=13))
        out.append(text(1245, y + 76, f'{row["invalid_rows_per_weighting"]} non-estimable', size=13, weight=700, fill="#a84a2a" if row["invalid_rows_per_weighting"] else "#596579"))
        reasons = []
        if row["single_class_failures"]:
            reasons.append(f'{row["single_class_failures"]} single-class')
        if row["current_flow_selection_failures"]:
            reasons.append(f'{row["current_flow_selection_failures"]} current-flow selection')
        out.append(text(1245, y + 98, "Failure reasons: " + (", ".join(reasons) if reasons else "none"), size=12, fill="#596579"))

    out += [
        text(55, 1210, "All 60 species are shown; species identifiers remain in the plotted-data sidecar rather than being selectively labelled.", size=12, fill="#596579"),
        "</svg>",
    ]
    return "\n".join(out) + "\n"


def caption(species, contrasts, applicability, frozen) -> str:
    primary = contrasts[0]
    spatial = contrasts[2]
    favourable = sum(r["direction"] == "favourable" for r in species)
    adverse = sum(r["direction"] == "adverse" for r in species)
    return (
        "# Figure 3 caption\n\n"
        "**Leakage-safe Tanzania current-flow versus EOG benchmark.** "
        "For each species and outer fold, current-flow resistance was selected using outer-training responses only; nearest-occurrence and EOG features were constructed from training occurrences, the selected current-flow quantity was reused in both probability tiers, and the untouched held-out label was scored. "
        "The strict reference contained patch area, selected matrix-aware current flow, their interaction, and nearest-training-occurrence distance; the candidate added EOG connected frequency. "
        "Differences are candidate minus reference, so negative values favour EOG and positive values are worse. "
        f"Panel C displays all {len(species)} species under primary leave-one-fragment-out validation: {favourable} species had negative and {adverse} had positive mean differences. "
        f"The species-macro primary LOSO difference was {primary['effect']:+.3f} (95% interval {primary['ci_low']:+.3f} to {primary['ci_high']:+.3f}; {primary['n_matched']} matched rows), showing an adverse incremental result. "
        f"The primary spatial-block sensitivity was smaller and uncertain ({spatial['effect']:+.3f}, 95% interval {spatial['ci_low']:+.3f} to {spatial['ci_high']:+.3f}; {spatial['n_matched']} matched rows). "
        "Non-estimable rows and their single-class or current-flow-selection reasons are retained explicitly.\n"
    )


def accessibility(species, contrasts, applicability, frozen) -> str:
    primary = contrasts[0]
    spatial = contrasts[2]
    favourable = sum(r["direction"] == "favourable" for r in species)
    adverse = sum(r["direction"] == "adverse" for r in species)
    return (
        "# Figure 3 accessibility description\n\n"
        "The figure has five panels. Panel A shows a five-step outer-fold workflow from training-only resistance selection to untouched held-out scoring. Panel B contrasts the current-flow-plus-distance reference with the same model plus EOG connected frequency. "
        f"Panel C shows one point for each of 60 species on a candidate-minus-reference log-loss axis; {favourable} points are below zero and {adverse} are above zero. Point size indicates the number of valid held-out predictions, which ranges from {min(r['n_matched_predictions'] for r in species)} to {max(r['n_matched_predictions'] for r in species)}. "
        f"Panel D shows four aggregate intervals. Both LOSO intervals are entirely above zero, including the primary estimate {primary['effect']:+.3f}; both spatial-block intervals cross zero, including the primary estimate {spatial['effect']:+.3f}. "
        f"Panel E reports {frozen['expected_projection']['n_prediction_rows']:,} declared prediction rows, {applicability[0]['matched_rows_per_weighting']} matched LOSO rows per weighting, and {applicability[1]['matched_rows_per_weighting']} matched spatial-block rows per weighting, with all failure categories visible.\n"
    )


def build(*, manifest_path=DEFAULT_MANIFEST, expected_path=DEFAULT_EXPECTED,
          species_source_path=DEFAULT_SPECIES, provenance_path=DEFAULT_PROVENANCE,
          output_dir=DEFAULT_OUTPUT, data_dir=DEFAULT_DATA,
          caption_path=DEFAULT_CAPTION, accessibility_path=DEFAULT_ALT,
          build_timestamp: str | None = None):
    paths = [Path(p) for p in (manifest_path, expected_path, species_source_path, provenance_path)]
    manifest, frozen, provenance, rows = validate_sources(*paths)
    species, contrasts, applicability = make_tables(frozen, rows)
    out_dir, data_dir = Path(output_dir), Path(data_dir)
    out_dir.mkdir(parents=True, exist_ok=True); data_dir.mkdir(parents=True, exist_ok=True)
    data_paths = {
        "species": data_dir / "tanzania_species_loso_effects.csv",
        "contrasts": data_dir / "tanzania_aggregate_contrasts.csv",
        "applicability": data_dir / "tanzania_applicability.csv",
    }
    output_data_paths = {key: out_dir / (path.stem + ".csv") for key, path in data_paths.items()}
    for key, table in (("species", species), ("contrasts", contrasts), ("applicability", applicability)):
        write_csv(data_paths[key], table); write_csv(output_data_paths[key], table)
    svg_path = out_dir / "figure_3_tanzania.svg"
    svg_path.write_text(render_svg(species, contrasts, applicability, frozen), encoding="utf-8")
    caption_path, accessibility_path = Path(caption_path), Path(accessibility_path)
    caption_path.parent.mkdir(parents=True, exist_ok=True)
    caption_path.write_text(caption(species, contrasts, applicability, frozen), encoding="utf-8")
    accessibility_path.write_text(accessibility(species, contrasts, applicability, frozen), encoding="utf-8")
    stamp = build_timestamp or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    metadata = {
        "schema_version": "eog_structural_figure_3_metadata_v1",
        "figure_id": FIGURE_ID,
        "built_at_utc": stamp,
        "software": {"python": platform.python_version(), "implementation": platform.python_implementation()},
        "source": {
            "manifest_sha256": sha256(paths[0]),
            "frozen_result_sha256": sha256(paths[1]),
            "species_table_sha256": sha256(paths[2]),
            "provenance_sha256": sha256(paths[3]),
            "artifact_digest": provenance["source"]["artifact_digest"],
            "workflow_run_id": provenance["source"]["workflow_run_id"],
            "result_fingerprint": frozen["expected_projection"]["result_fingerprint"],
        },
        "derived": {
            "species_displayed": len(species),
            "species_favourable": sum(r["direction"] == "favourable" for r in species),
            "species_adverse": sum(r["direction"] == "adverse" for r in species),
            "species_equal": sum(r["direction"] == "equal" for r in species),
            "aggregate_contrasts": len(contrasts),
        },
        "outputs": {
            "svg_sha256": sha256(svg_path),
            "caption_sha256": sha256(caption_path),
            "accessibility_sha256": sha256(accessibility_path),
            **{f"{key}_data_sha256": sha256(path) for key, path in data_paths.items()},
        },
    }
    metadata_path = out_dir / "figure_3_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"svg": svg_path, "metadata": metadata_path, "caption": caption_path, "accessibility": accessibility_path, **data_paths, **{f"output_{k}":v for k,v in output_data_paths.items()}}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-timestamp")
    args = parser.parse_args()
    outputs = build(build_timestamp=args.build_timestamp)
    print(json.dumps({key: str(value) for key, value in outputs.items()}, indent=2))


if __name__ == "__main__":
    main()
