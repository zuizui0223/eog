#!/usr/bin/env python3
"""Build Figure 4 from three frozen reference-conditioned evidence states."""
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
DEFAULT_A = ROOT / "benchmarks/aislands_authoritative_expected.json"
DEFAULT_A_PROV = ROOT / "benchmarks/aislands_authoritative_expected_provenance.json"
DEFAULT_A_STRONG = ROOT / "validation/aislands_isolation_adequacy_20260812/authoritative_outcome.json"
DEFAULT_T = ROOT / "benchmarks/tanzania_heldout_expected.json"
DEFAULT_DATA = ROOT / "manuscript/figure_data/structural_cross_system_evidence.csv"
DEFAULT_OUT = ROOT / "figures/output"
DEFAULT_CAPTION = ROOT / "manuscript/figure_4_caption.md"
DEFAULT_ALT = ROOT / "manuscript/figure_4_accessibility.md"
AIS_STRONG_FP = "5c9b1594b29d362e5983484614a49d530797d06e826c0b96a3e8442a6b6b493a"
TANZANIA_FP = "6b555c28d61d3f39b9e672f5a97250de6870301871cf3e60378e97863cd109e4"
PROHIBITED_TERMS = (
    "movement probability", "colonisation probability", "dispersal probability",
    "dispersal route", "connectivity truth", "historical colonisation route",
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


def source_rows(a_path: Path, prov_path: Path, strong_path: Path, t_path: Path):
    a, prov, strong, t = map(load_json, (a_path, prov_path, strong_path, t_path))
    source = prov.get("source", {})
    require(sha256(a_path), source.get("member_sha256"), "original A-Islands archive member SHA")
    require(prov.get("not_preregistration"), True, "original A-Islands provenance flag")
    require(a.get("status"), "first_authoritative_aislands_species_outcome_execution", "original A-Islands status")
    require(strong.get("schema_version"), "eog_aislands_isolation_adequacy_outcome_v1", "strong A-Islands schema")
    require(strong.get("status"), "first_and_only_authoritative_island_isolation_adequacy_execution", "strong A-Islands status")
    require(strong.get("result_fingerprint"), AIS_STRONG_FP, "strong A-Islands result fingerprint")
    require(t.get("results_frozen"), True, "Tanzania frozen result flag")
    proj = t.get("expected_projection", {})
    require(proj.get("result_fingerprint"), TANZANIA_FP, "Tanzania result fingerprint")
    primary_t = proj.get("contrasts", {}).get("primary::primary_loso")
    if not isinstance(primary_t, dict):
        raise FigureContractError("Tanzania primary LOSO contrast is missing")

    ae = float(a["overall_conditional_concordance"])
    alo, ahi = map(float, a["bootstrap_95_ci"])
    anull = float(a["null"])
    sp = strong["primary"]
    se = float(sp["species_macro_mean"])
    slo, shi = map(float, sp["bootstrap_95_ci"])
    te = float(primary_t["macro_mean_species_log_loss_difference"])
    tlo, thi = map(float, primary_t["log_loss_bootstrap_ci95"])
    if not alo <= ae <= ahi or not slo <= se <= shi or not tlo <= te <= thi:
        raise FigureContractError("an effect lies outside its frozen interval")
    if alo <= anull:
        raise FigureContractError("original A-Islands interval no longer clears the 0.5 null")
    if slo <= 0:
        raise FigureContractError("strong A-Islands adverse interval no longer clears zero")
    if tlo <= 0:
        raise FigureContractError("Tanzania adverse interval no longer clears zero")

    rows = [
        {
            "benchmark_id": "A_ISLANDS_ORIGINAL", "benchmark_label": "A-Islands | limited reference",
            "declared_taxa": a["n_declared_taxa"], "estimable_taxa": a["n_species_estimable"],
            "spatial_units": a["n_islands"], "local_reference_term": "CHELSA support + nearest outer-training source distance",
            "nearest_source_distance_in_reference": "yes", "matrix_connectivity_in_reference": "no",
            "eog_structural_addition": "12-scenario connected frequency",
            "holdout_design": "five-fold spatial partition; 5×5 support-distance matching",
            "endpoint": "conditional occupied-vs-unoccupied concordance",
            "metric_label": "conditional concordance", "effect": ae, "ci_low": alo, "ci_high": ahi,
            "null_value": anull, "favourable_direction": "higher than 0.5 favours added ordering information",
            "result_class": "residual_information",
            "result_statement": "Structural ordering remained after limited conditioning",
            "permitted_conclusion": "Configuration retained incidence ordering beyond climate support and nearest-source distance",
            "source_fingerprint": a["species_output_sha256"],
        },
        {
            "benchmark_id": "A_ISLANDS_STRONG", "benchmark_label": "A-Islands | prospective strong R3",
            "declared_taxa": strong["taxa_declared"], "estimable_taxa": strong["taxa_estimable"],
            "spatial_units": 842, "local_reference_term": "R3: climate, area, mainland/source pressure, landmass, generic stepping-stone/network terms",
            "nearest_source_distance_in_reference": "yes", "matrix_connectivity_in_reference": "generic multidimensional island structure",
            "eog_structural_addition": "geography-only species-conditioned connected frequency",
            "holdout_design": "same frozen five-fold partition; matched R3 versus C predictions",
            "endpoint": "candidate-minus-R3 held-out Bernoulli log loss",
            "metric_label": "delta log loss: C minus R3", "effect": se, "ci_low": slo, "ci_high": shi,
            "null_value": 0.0, "favourable_direction": "negative favours EOG; positive is worse",
            "result_class": "adverse_increment",
            "result_statement": "No predictive increment beyond R3; held-out loss increased",
            "permitted_conclusion": "The species-conditioned EOG term did not improve the prospectively frozen strong island reference",
            "source_fingerprint": strong["result_fingerprint"],
        },
        {
            "benchmark_id": "TANZANIA", "benchmark_label": "Tanzania forest birds | strong current-flow reference",
            "declared_taxa": proj["n_species"], "estimable_taxa": primary_t["n_species"],
            "spatial_units": 14, "local_reference_term": "patch area + nearest source + selected current flow + interaction",
            "nearest_source_distance_in_reference": "yes",
            "matrix_connectivity_in_reference": "training-selected matrix-aware current flow",
            "eog_structural_addition": "four-scenario geography-only connected frequency",
            "holdout_design": "leave-one-fragment-out",
            "endpoint": "candidate-minus-reference held-out Bernoulli log loss",
            "metric_label": "delta log loss: EOG minus reference", "effect": te, "ci_low": tlo,
            "ci_high": thi, "null_value": 0.0,
            "favourable_direction": "negative favours EOG; positive is worse",
            "result_class": "adverse_increment",
            "result_statement": "No incremental benefit beyond current flow; primary LOSO loss increased",
            "permitted_conclusion": "The tested EOG term had no primary LOSO benefit beyond the strong Tanzania reference",
            "source_fingerprint": proj["result_fingerprint"],
        },
    ]
    return rows, {"a": a, "a_prov": prov, "strong": strong, "t": t}


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


def svg_text(x: int, y: int, lines: list[str], *, size=14, weight=400, anchor="start", fill="#172033", gap=18):
    spans = [f'<tspan x="{x}" dy="{0 if i == 0 else gap}">{esc(line)}</tspan>' for i, line in enumerate(lines)]
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{fill}">' + "".join(spans) + "</text>"


def scale(value: float, lo: float, hi: float, x0: float, x1: float) -> float:
    return x0 + (value - lo) / (hi - lo) * (x1 - x0)


def row_axis(row: dict[str, Any]) -> tuple[float, float, str]:
    if row["benchmark_id"] == "A_ISLANDS_ORIGINAL":
        return 0.48, 0.66, f'{row["effect"]:.3f} [{row["ci_low"]:.3f}–{row["ci_high"]:.3f}]'
    if row["benchmark_id"] == "A_ISLANDS_STRONG":
        return -0.002, 0.007, f'{row["effect"]:+.4f} [{row["ci_low"]:+.4f} to {row["ci_high"]:+.4f}]'
    return -0.02, 0.06, f'{row["effect"]:+.3f} [{row["ci_low"]:+.3f} to {row["ci_high"]:+.3f}]'


def render_svg(rows: list[dict[str, Any]]) -> str:
    width, height = 1600, 1260
    colours = ["#2b6cb0", "#805ad5", "#b7791f"]
    pales = ["#ebf4ff", "#faf5ff", "#fffaf0"]
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="1600" height="1260" fill="#ffffff"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif}</style>',
        svg_text(60, 55, ["Figure 4 | Reference-conditioned evidence boundary"], size=28, weight=700),
        svg_text(60, 88, ["Three frozen tests answer different questions; every row uses its own metric scale."], size=16, fill="#5c667a"),
    ]
    for idx, row in enumerate(rows):
        y = 120 + idx * 340
        colour, pale = colours[idx], pales[idx]
        out += [
            f'<rect x="50" y="{y}" width="1500" height="305" rx="18" fill="{pale}" stroke="{colour}" stroke-width="2"/>',
            svg_text(80, y + 38, [row["benchmark_label"]], size=22, weight=700, fill=colour),
            svg_text(80, y + 66, [f'{row["estimable_taxa"]} estimable of {row["declared_taxa"]} taxa | {row["spatial_units"]} spatial units'], size=13, fill="#5c667a"),
            svg_text(80, y + 102, ["Declared reference"], size=13, weight=700),
            svg_text(80, y + 125, wrapped(row["local_reference_term"], 70), size=12, fill="#39445a", gap=15),
            svg_text(80, y + 181, ["Structural probe"], size=13, weight=700),
            svg_text(80, y + 204, wrapped(row["eog_structural_addition"], 55), size=12, fill="#39445a", gap=15),
            svg_text(470, y + 181, ["Held-out endpoint"], size=13, weight=700),
            svg_text(470, y + 204, wrapped(row["holdout_design"] + "; " + row["endpoint"], 65), size=12, fill="#39445a", gap=15),
        ]
        x0, x1, yn = 1060, 1480, y + 145
        axis_lo, axis_hi, value = row_axis(row)
        effect, low, high, null = [float(row[k]) for k in ("effect", "ci_low", "ci_high", "null_value")]
        out += [
            svg_text(x0, y + 96, wrapped(row["metric_label"], 42), size=12, weight=700),
            f'<line x1="{x0}" y1="{yn}" x2="{x1}" y2="{yn}" stroke="#a0a8b8" stroke-width="3"/>',
            f'<line x1="{scale(null,axis_lo,axis_hi,x0,x1):.1f}" y1="{yn-18}" x2="{scale(null,axis_lo,axis_hi,x0,x1):.1f}" y2="{yn+18}" stroke="#39445a" stroke-width="2" stroke-dasharray="5 5"/>',
            f'<line x1="{scale(low,axis_lo,axis_hi,x0,x1):.1f}" y1="{yn}" x2="{scale(high,axis_lo,axis_hi,x0,x1):.1f}" y2="{yn}" stroke="{colour}" stroke-width="8" stroke-linecap="round"/>',
            f'<circle cx="{scale(effect,axis_lo,axis_hi,x0,x1):.1f}" cy="{yn}" r="9" fill="{colour}" stroke="#ffffff" stroke-width="3"/>',
            svg_text((x0+x1)//2, y + 185, [value], size=16, weight=700, anchor="middle", fill=colour),
            svg_text(x0, y + 211, wrapped(row["favourable_direction"], 48), size=11, fill="#5c667a"),
            svg_text(x0, y + 247, wrapped(row["result_statement"], 50), size=13, weight=700, fill=colour, gap=17),
        ]
    out += [
        svg_text(60, 1164, ["Synthesis"], size=17, weight=700),
        svg_text(60, 1192, wrapped("The original island ordering signal survives a limited reference, but species-conditioned EOG does not improve either prospectively frozen strong reference. Reference content and endpoint are therefore part of the structural claim.", 155), size=14, fill="#39445a"),
        svg_text(60, 1230, ["Separate scales are intentional; no cross-row effect-size magnitude comparison is implied."], size=13, weight=700, fill="#5c667a"),
        "</svg>",
    ]
    svg = "\n".join(out) + "\n"
    for term in PROHIBITED_TERMS:
        if term in svg.lower():
            raise FigureContractError(f"prohibited claim language in SVG: {term}")
    return svg


def caption(rows: list[dict[str, Any]]) -> str:
    original, strong, t = rows
    return (
        "# Figure 4 caption\n\n"
        "**Reference-conditioned evidence boundary across the three frozen structural tests.** "
        f"The original A-Islands benchmark retained conditional ordering information after matching climatic support and nearest-source distance ({original['effect']:.3f}, species-bootstrap 95% interval {original['ci_low']:.3f}–{original['ci_high']:.3f}; null 0.5; {original['estimable_taxa']} estimable taxa). "
        f"A prospectively frozen second A-Islands test then asked whether the species-conditioned EOG term improved a substantially stronger R3 reference containing climate, recipient area, continental-mainland distance, direct and area-weighted source pressure, surrounding landmass, generic stepping-stone accessibility and generic network position. Its candidate-minus-R3 log-loss difference was {strong['effect']:+.4f} (95% interval {strong['ci_low']:+.4f} to {strong['ci_high']:+.4f}; 341 species favourable, 545 adverse), so the added EOG term was adverse rather than beneficial. "
        f"In Tanzania, adding EOG after patch area, training-selected matrix-aware current flow and nearest-source distance likewise increased primary leave-one-fragment-out log loss by {t['effect']:+.3f} (95% interval {t['ci_low']:+.3f} to {t['ci_high']:+.3f}); the separately frozen spatial-block sensitivity was smaller and uncertain. "
        "Each row uses its own endpoint and plotting scale. The figure therefore compares claim boundaries, not effect-size magnitudes across metrics.\n"
    )


def accessibility(rows: list[dict[str, Any]]) -> str:
    original, strong, t = rows
    return (
        "# Figure 4 accessibility description\n\n"
        "Three stacked rows show how the EOG conclusion changes with the declared reference and endpoint. "
        f"The first row is the original A-Islands conditional-concordance test, whose estimate {original['effect']:.3f} and interval {original['ci_low']:.3f} to {original['ci_high']:.3f} lie above the 0.5 null. "
        f"The second row is the prospective A-Islands strong-reference predictive test. Its C-minus-R3 log-loss estimate is {strong['effect']:+.4f}, interval {strong['ci_low']:+.4f} to {strong['ci_high']:+.4f}; positive values mean worse prediction and the result is adverse. "
        f"The third row is the Tanzania primary LOSO strong-reference test, with log-loss difference {t['effect']:+.3f}, interval {t['ci_low']:+.3f} to {t['ci_high']:+.3f}; its spatial-block sensitivity is described as uncertain rather than confirming a universal adverse effect. "
        "All rows use separate scales because conditional concordance and predictive-loss differences are incompatible metrics.\n"
    )


def build(*, aislands_path=DEFAULT_A, aislands_provenance_path=DEFAULT_A_PROV,
          aislands_strong_path=DEFAULT_A_STRONG, tanzania_path=DEFAULT_T,
          panel_data_path=DEFAULT_DATA, output_dir=DEFAULT_OUT,
          caption_path=DEFAULT_CAPTION, accessibility_path=DEFAULT_ALT,
          build_timestamp: str | None = None):
    paths = [Path(p) for p in (aislands_path, aislands_provenance_path, aislands_strong_path, tanzania_path)]
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
        "schema_version": "eog_structural_figure_4_metadata_v2",
        "figure_id": FIGURE_ID,
        "built_at_utc": stamp,
        "metrics_share_axis": False,
        "row_count": 3,
        "software": {"python": platform.python_version(), "implementation": platform.python_implementation()},
        "sources": {
            "aislands_original": {
                "path": str(paths[0].relative_to(ROOT)), "sha256": sha256(paths[0]),
                "workflow_run_id": provenance_source["workflow_run_id"],
                "artifact_digest": provenance_source["artifact_digest"],
                "species_output_sha256": raw["a"]["species_output_sha256"],
            },
            "aislands_strong_reference": {
                "path": str(paths[2].relative_to(ROOT)), "sha256": sha256(paths[2]),
                "result_fingerprint": raw["strong"]["result_fingerprint"],
            },
            "tanzania": {
                "path": str(paths[3].relative_to(ROOT)), "sha256": sha256(paths[3]),
                "result_fingerprint": tproj["result_fingerprint"],
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
