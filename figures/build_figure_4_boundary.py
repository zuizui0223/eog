#!/usr/bin/env python3
"""Build the cross-system evidence-boundary figure from frozen projections."""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import platform
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIGURE_ID = "figure_4_boundary"
DEFAULT_MANIFEST = ROOT / "figures/figure_manifest.json"
DEFAULT_A = ROOT / "benchmarks/aislands_authoritative_expected.json"
DEFAULT_A_PROV = ROOT / "benchmarks/aislands_authoritative_expected_provenance.json"
DEFAULT_T = ROOT / "benchmarks/tanzania_heldout_expected.json"
DEFAULT_DATA = ROOT / "manuscript/figure_data/structural_cross_system_evidence.csv"
DEFAULT_OUT = ROOT / "figures/output"
DEFAULT_CAPTION = ROOT / "manuscript/figure_4_caption.md"
DEFAULT_ALT = ROOT / "manuscript/figure_4_accessibility.md"
PROHIBITED_TERMS = (
    "movement probability", "colonisation probability", "dispersal probability",
    "dispersal route", "connectivity truth",
)


class FigureContractError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FigureContractError(f"cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FigureContractError(f"expected JSON object in {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise FigureContractError(f"{label}: expected {expected!r}, got {actual!r}")


def source_rows(manifest_path: Path, a_path: Path, prov_path: Path, t_path: Path):
    manifest = load_json(manifest_path)
    contract = manifest.get(FIGURE_ID)
    if not isinstance(contract, dict) or contract.get("metrics_share_axis") is not False:
        raise FigureContractError("Figure 4 must declare separate metric axes")
    expected = contract["expected"]
    a, prov, t = load_json(a_path), load_json(prov_path), load_json(t_path)
    source = prov.get("source", {})

    require(sha256(a_path), source.get("member_sha256"), "A-Islands archive member SHA")
    require(sha256(a_path), expected["aislands_summary_sha256"], "A-Islands figure source SHA")
    require(source.get("artifact_digest"), expected["aislands_artifact_digest"], "A-Islands artifact digest")
    require(source.get("workflow_run_id"), expected["aislands_workflow_run_id"], "A-Islands workflow run")
    require(prov.get("not_preregistration"), True, "A-Islands post-outcome provenance flag")
    require(a.get("status"), "first_authoritative_aislands_species_outcome_execution", "A-Islands status")
    require(a.get("n_declared_taxa"), expected["aislands_declared_taxa"], "A-Islands declared taxa")
    require(a.get("n_species_estimable"), expected["aislands_estimable_taxa"], "A-Islands estimable taxa")
    require(a.get("n_islands"), expected["aislands_spatial_units"], "A-Islands islands")
    require(a.get("species_output_sha256"), expected["aislands_species_output_sha256"], "A-Islands species output")

    require(t.get("results_frozen"), True, "Tanzania frozen result flag")
    proj = t.get("expected_projection", {})
    require(proj.get("result_fingerprint"), expected["tanzania_result_fingerprint"], "Tanzania result fingerprint")
    require(t.get("required_inputs", {}).get("candidate_library_fingerprint"), expected["tanzania_candidate_library_fingerprint"], "Tanzania candidate library")
    require(proj.get("n_species"), expected["tanzania_species"], "Tanzania species")
    require(proj.get("n_prediction_rows"), expected["tanzania_prediction_rows"], "Tanzania prediction rows")
    primary = proj.get("contrasts", {}).get("primary::primary_loso")
    if not isinstance(primary, dict):
        raise FigureContractError("Tanzania primary LOSO contrast is missing")
    require(primary.get("n_matched"), expected["tanzania_primary_matched"], "Tanzania primary matched rows")

    ae = float(a["overall_conditional_concordance"])
    alo, ahi = map(float, a["bootstrap_95_ci"])
    anull = float(a["null"])
    te = float(primary["macro_mean_species_log_loss_difference"])
    tlo, thi = map(float, primary["log_loss_bootstrap_ci95"])
    if not alo <= ae <= ahi or not tlo <= te <= thi:
        raise FigureContractError("an effect lies outside its frozen interval")
    if alo <= anull:
        raise FigureContractError("A-Islands interval no longer clears the 0.5 null")
    if tlo <= 0:
        raise FigureContractError("Tanzania adverse LOSO interval no longer clears zero")

    rows = [
        {
            "benchmark_id": "A_ISLANDS", "benchmark_label": "A-Islands plants",
            "declared_taxa": a["n_declared_taxa"], "estimable_taxa": a["n_species_estimable"],
            "spatial_units": a["n_islands"], "local_reference_term": "CHELSA pointwise support",
            "nearest_source_distance_in_reference": "yes", "matrix_connectivity_in_reference": "no",
            "eog_structural_addition": "12-scenario connected frequency",
            "holdout_design": "shared five-fold spatial partition",
            "endpoint": "conditional occupied-vs-unoccupied concordance within support-distance strata",
            "metric_label": "conditional concordance", "effect": ae, "ci_low": alo, "ci_high": ahi,
            "null_value": anull, "favourable_direction": "higher indicates added information",
            "result_class": "added_information",
            "result_statement": "Added information after pointwise support and nearest-source distance were controlled",
            "permitted_conclusion": "Structure retained incidence information beyond pointwise support and nearest-source distance",
            "source_fingerprint": a["species_output_sha256"],
        },
        {
            "benchmark_id": "TANZANIA", "benchmark_label": "Tanzania forest birds",
            "declared_taxa": proj["n_species"], "estimable_taxa": primary["n_species"],
            "spatial_units": 14, "local_reference_term": "patch area",
            "nearest_source_distance_in_reference": "yes",
            "matrix_connectivity_in_reference": "training-selected matrix-aware current flow",
            "eog_structural_addition": "four-scenario geography-only connected frequency",
            "holdout_design": "leave-one-fragment-out",
            "endpoint": "candidate-minus-reference paired held-out Bernoulli log loss",
            "metric_label": "delta log loss: EOG minus reference", "effect": te, "ci_low": tlo,
            "ci_high": thi, "null_value": 0.0,
            "favourable_direction": "negative favours EOG; positive is worse",
            "result_class": "adverse_increment",
            "result_statement": "No incremental benefit beyond current flow and nearest-source distance; LOSO prediction worsened",
            "permitted_conclusion": "The tested EOG feature had no incremental benefit beyond current flow and nearest-source distance",
            "source_fingerprint": proj["result_fingerprint"],
        },
    ]
    require([r["benchmark_id"] for r in rows], contract["required_benchmark_ids"], "benchmark order")
    return rows, {"manifest": manifest, "a": a, "a_prov": prov, "t": t}


FIELDS = [
    "benchmark_id", "benchmark_label", "declared_taxa", "estimable_taxa", "spatial_units",
    "local_reference_term", "nearest_source_distance_in_reference", "matrix_connectivity_in_reference",
    "eog_structural_addition", "holdout_design", "endpoint", "metric_label", "effect", "ci_low",
    "ci_high", "null_value", "favourable_direction", "result_class", "result_statement",
    "permitted_conclusion", "source_fingerprint",
]


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            clean = dict(row)
            for key in ("effect", "ci_low", "ci_high", "null_value"):
                clean[key] = f"{float(clean[key]):.9f}"
            writer.writerow(clean)


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def wrapped(text: str, width: int) -> list[str]:
    return textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False) or [""]


def svg_text(x: int, y: int, lines: list[str], *, size=14, weight=400, anchor="start", fill="#172033", gap=19):
    spans = [f'<tspan x="{x}" dy="{0 if i == 0 else gap}">{esc(line)}</tspan>' for i, line in enumerate(lines)]
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{fill}">' + "".join(spans) + "</text>"


def scale(value: float, lo: float, hi: float, x0: float, x1: float) -> float:
    return x0 + (value - lo) / (hi - lo) * (x1 - x0)


def render_svg(rows: list[dict[str, Any]]) -> str:
    width, height = 1600, 930
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="1600" height="930" fill="#ffffff"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif}.muted{fill:#5c667a}</style>',
        svg_text(60, 55, ["Figure 4 | Cross-system evidence boundary"], size=28, weight=700),
        svg_text(60, 88, ["Incompatible endpoints are shown on separate row-specific scales."], size=16, fill="#5c667a"),
    ]
    for idx, row in enumerate(rows):
        y = 125 + idx * 350
        colour = "#2b6cb0" if idx == 0 else "#b7791f"
        pale = "#ebf4ff" if idx == 0 else "#fffaf0"
        out += [
            f'<rect x="50" y="{y}" width="1500" height="315" rx="18" fill="{pale}" stroke="{colour}" stroke-width="2"/>',
            svg_text(80, y + 40, [row["benchmark_label"]], size=23, weight=700, fill=colour),
            svg_text(80, y + 69, [f'{row["estimable_taxa"]} estimable of {row["declared_taxa"]} taxa | {row["spatial_units"]} spatial units'], size=14, fill="#5c667a"),
            svg_text(80, y + 110, ["Reference already contained"], size=14, weight=700),
        ]
        terms = [
            ("Local term", row["local_reference_term"], True),
            ("Nearest-source distance", "included", row["nearest_source_distance_in_reference"] == "yes"),
            ("Matrix-aware connectivity", row["matrix_connectivity_in_reference"], row["matrix_connectivity_in_reference"] != "no"),
        ]
        tx = 80
        for label, detail, present in terms:
            mark = "●" if present else "○"
            out.append(svg_text(tx, y + 143, [f"{mark} {label}"], size=14, weight=700 if present else 400, fill=colour if present else "#5c667a"))
            out.append(svg_text(tx, y + 165, wrapped(detail, 28), size=12, fill="#5c667a", gap=15))
            tx += 260
        out.append(svg_text(80, y + 218, ["EOG addition"], size=13, weight=700))
        out.append(svg_text(80, y + 241, wrapped(row["eog_structural_addition"], 42), size=13, fill="#39445a", gap=16))
        out.append(svg_text(435, y + 218, ["Holdout / endpoint"], size=13, weight=700))
        out.append(svg_text(435, y + 241, wrapped(row["holdout_design"] + "; " + row["endpoint"], 55), size=13, fill="#39445a", gap=16))

        x0, x1 = 1040, 1485
        effect, low, high, null = [float(row[k]) for k in ("effect", "ci_low", "ci_high", "null_value")]
        if row["benchmark_id"] == "A_ISLANDS":
            axis_lo, axis_hi = 0.48, 0.66
            value = f'{effect:.3f} [{low:.3f}–{high:.3f}]'
        else:
            axis_lo, axis_hi = -0.02, 0.06
            value = f'{effect:+.3f} [{low:+.3f} to {high:+.3f}]'
        yn = y + 160
        out += [
            svg_text(x0, y + 105, wrapped(row["metric_label"], 43), size=13, weight=700),
            f'<line x1="{x0}" y1="{yn}" x2="{x1}" y2="{yn}" stroke="#a0a8b8" stroke-width="3"/>',
            f'<line x1="{scale(null,axis_lo,axis_hi,x0,x1):.1f}" y1="{yn-18}" x2="{scale(null,axis_lo,axis_hi,x0,x1):.1f}" y2="{yn+18}" stroke="#39445a" stroke-width="2" stroke-dasharray="5 5"/>',
            f'<line x1="{scale(low,axis_lo,axis_hi,x0,x1):.1f}" y1="{yn}" x2="{scale(high,axis_lo,axis_hi,x0,x1):.1f}" y2="{yn}" stroke="{colour}" stroke-width="8" stroke-linecap="round"/>',
            f'<circle cx="{scale(effect,axis_lo,axis_hi,x0,x1):.1f}" cy="{yn}" r="9" fill="{colour}" stroke="#ffffff" stroke-width="3"/>',
            svg_text((x0+x1)//2, y + 198, [value], size=17, weight=700, anchor="middle", fill=colour),
            svg_text(x0, y + 221, [row["favourable_direction"]], size=12, fill="#5c667a"),
            svg_text(x0, y + 254, wrapped(row["result_statement"], 54), size=14, weight=700, fill=colour, gap=18),
        ]
    out += [
        svg_text(60, 850, ["Interpretation boundary"], size=17, weight=700),
        svg_text(60, 878, wrapped("Occurrence-anchored configuration added information beyond pointwise support and direct source distance in A-Islands, but the same generic feature was not beneficial after a strong matrix-aware current-flow reference in Tanzania.", 150), size=14, fill="#39445a"),
        svg_text(60, 912, ["The two endpoints are intentionally shown on separate scales; no cross-metric magnitude comparison is implied."], size=13, weight=700, fill="#5c667a"),
        "</svg>",
    ]
    svg = "\n".join(out) + "\n"
    low_svg = svg.lower()
    for term in PROHIBITED_TERMS:
        if term in low_svg:
            raise FigureContractError(f"prohibited claim language in SVG: {term}")
    return svg


def caption(rows: list[dict[str, Any]]) -> str:
    a, t = rows
    return (
        "# Figure 4 caption\n\n"
        "**Cross-system evidence boundary for occurrence-anchored structural reachability.** "
        "Filled and open circles indicate whether each reference already contained the named quantity. "
        f"In A-Islands, connected frequency was evaluated for {a['estimable_taxa']} of {a['declared_taxa']} declared plant taxa across {a['spatial_units']} islands after conditioning on pointwise climatic support and nearest-training-occurrence distance. "
        f"The conditional concordance was {a['effect']:.3f} (species-bootstrap 95% interval {a['ci_low']:.3f}–{a['ci_high']:.3f}; null {a['null_value']:.1f}), supporting added held-out incidence information under the frozen graph scenarios. "
        "In Tanzania, the reference already contained patch area, training-selected matrix-aware current flow, their interaction, and nearest-training-occurrence distance. "
        f"Adding the frozen EOG feature increased leave-one-fragment-out log loss by {t['effect']:+.3f} (95% interval {t['ci_low']:+.3f} to {t['ci_high']:+.3f}; null {t['null_value']:.1f}) across {t['declared_taxa']} bird species, indicating no incremental benefit and an adverse LOSO result. "
        "Row-specific axes are used because conditional concordance and candidate-minus-reference log loss are incompatible metrics and must not be compared as a common effect size.\n"
    )


def accessibility(rows: list[dict[str, Any]]) -> str:
    a, t = rows
    return (
        "# Figure 4 accessibility description\n\n"
        "A two-row matrix contrasts the frozen A-Islands and Tanzania benchmarks. "
        "The A-Islands reference contained pointwise CHELSA support and nearest-source distance but no matrix-connectivity term. "
        f"Its separate interval plot lies above the 0.5 null at {a['effect']:.3f}, with interval {a['ci_low']:.3f} to {a['ci_high']:.3f}. "
        "The Tanzania reference contained patch area, nearest-source distance, and training-selected matrix-aware current flow. "
        f"Its separate interval plot lies above the zero log-loss null at {t['effect']:+.3f}, with interval {t['ci_low']:+.3f} to {t['ci_high']:+.3f}; positive values mean worse prediction. "
        "The figure therefore states that structural configuration added information in A-Islands but did not improve the strong Tanzania reference. "
        "The axes are deliberately separate and no cross-metric magnitude comparison is implied.\n"
    )


def build(*, manifest_path=DEFAULT_MANIFEST, aislands_path=DEFAULT_A,
          aislands_provenance_path=DEFAULT_A_PROV, tanzania_path=DEFAULT_T,
          panel_data_path=DEFAULT_DATA, output_dir=DEFAULT_OUT,
          caption_path=DEFAULT_CAPTION, accessibility_path=DEFAULT_ALT,
          build_timestamp: str | None = None):
    paths = [Path(p) for p in (manifest_path, aislands_path, aislands_provenance_path, tanzania_path)]
    rows, raw = source_rows(*paths)
    panel_data_path, output_dir = Path(panel_data_path), Path(output_dir)
    caption_path, accessibility_path = Path(caption_path), Path(accessibility_path)
    write_rows(panel_data_path, rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_panel_path = output_dir / "figure_4_panel_data.csv"
    write_rows(output_panel_path, rows)
    svg_path = output_dir / "figure_4_boundary.svg"
    meta_path = output_dir / "figure_4_metadata.json"
    svg_path.write_text(render_svg(rows), encoding="utf-8")
    caption_path.parent.mkdir(parents=True, exist_ok=True)
    caption_path.write_text(caption(rows), encoding="utf-8")
    accessibility_path.write_text(accessibility(rows), encoding="utf-8")
    stamp = build_timestamp or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    provenance_source = raw["a_prov"]["source"]
    tproj = raw["t"]["expected_projection"]
    metadata = {
        "schema_version": "eog_structural_figure_4_metadata_v1",
        "figure_id": FIGURE_ID,
        "built_at_utc": stamp,
        "metrics_share_axis": False,
        "software": {"python": platform.python_version(), "implementation": platform.python_implementation()},
        "sources": {
            "manifest": {"path": str(paths[0].relative_to(ROOT)), "sha256": sha256(paths[0])},
            "aislands": {
                "path": str(paths[1].relative_to(ROOT)), "sha256": sha256(paths[1]),
                "workflow_run_id": provenance_source["workflow_run_id"],
                "artifact_digest": provenance_source["artifact_digest"],
                "species_output_sha256": raw["a"]["species_output_sha256"],
            },
            "tanzania": {
                "path": str(paths[3].relative_to(ROOT)), "sha256": sha256(paths[3]),
                "result_fingerprint": tproj["result_fingerprint"],
                "prediction_rows_sha256": tproj["prediction_rows_cross_run_sha256"],
                "group_rows_sha256": tproj["group_rows_cross_run_sha256"],
                "species_rows_sha256": tproj["species_rows_cross_run_sha256"],
            },
        },
        "outputs": {
            "panel_data_sha256": sha256(panel_data_path),
            "output_panel_data_sha256": sha256(output_panel_path),
            "svg_sha256": sha256(svg_path),
            "caption_sha256": sha256(caption_path),
            "accessibility_sha256": sha256(accessibility_path),
        },
    }
    meta_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "svg": svg_path, "metadata": meta_path, "panel_data": panel_data_path,
        "output_panel_data": output_panel_path, "caption": caption_path,
        "accessibility": accessibility_path,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-timestamp")
    args = parser.parse_args()
    outputs = build(build_timestamp=args.build_timestamp)
    print(json.dumps({key: str(value) for key, value in outputs.items()}, indent=2))


if __name__ == "__main__":
    main()
