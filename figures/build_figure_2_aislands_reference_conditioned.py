#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "benchmarks/aislands_authoritative_expected.json"
ORIGINAL_SPECIES = ROOT / "benchmarks/aislands_structural_species_expected.csv"
STRONG = ROOT / "validation/aislands_isolation_adequacy_20260812/authoritative_outcome.json"
CONTRACT = ROOT / "validation/aislands_isolation_adequacy_20260812/preoutcome_contract.json"
FIGURE_MANIFEST = ROOT / "figures/figure_manifest.json"
BOUNDARY = ROOT / "manuscript/STRUCTURAL_ISLAND_PAPER_BOUNDARY_V1.json"

OUT_SVG = ROOT / "figures/output/figure_2_aislands_reference_conditioned.svg"
OUT_META = ROOT / "figures/output/figure_2_aislands_reference_conditioned_metadata.json"
OUT_DATA = ROOT / "figures/output/figure_2_aislands_reference_conditioned_data.csv"
OUT_CAPTION = ROOT / "manuscript/figure_2_reference_conditioned_caption.md"
OUT_ALT = ROOT / "manuscript/figure_2_reference_conditioned_accessibility.md"

EXPECTED_STRONG_FINGERPRINT = "5c9b1594b29d362e5983484614a49d530797d06e826c0b96a3e8442a6b6b493a"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def xmap(value: float, left: float, right: float, low: float, high: float) -> float:
    return left + (value - low) / (high - low) * (right - left)


def text(x: float, y: float, value: str, *, size: int = 14, weight: int = 400, anchor: str = "start", fill: str = "#172033") -> str:
    return f'<text x="{x}" y="{y}" font-family="Arial,Helvetica,sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{fill}">{esc(value)}</text>'


def original_direction_counts() -> dict[str, int]:
    above = equal = below = missing = 0
    with ORIGINAL_SPECIES.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            raw = row["conditional_concordance"].strip()
            if not raw:
                missing += 1
                continue
            value = float(raw)
            if value > 0.5:
                above += 1
            elif value < 0.5:
                below += 1
            else:
                equal += 1
    return {"above": above, "equal": equal, "below": below, "not_estimable": missing}


def validate() -> dict:
    original = load_json(ORIGINAL)
    strong = load_json(STRONG)
    contract = load_json(CONTRACT)
    manifest = load_json(FIGURE_MANIFEST)["figure_2_aislands"]["expected"]
    boundary = load_json(BOUNDARY)

    assert sha256_file(ORIGINAL) == manifest["primary_summary_sha256"]
    assert sha256_file(ORIGINAL_SPECIES) == manifest["primary_species_table_sha256"]
    assert original["n_declared_taxa"] == 886
    assert original["n_species_estimable"] == 845
    assert strong["result_fingerprint"] == EXPECTED_STRONG_FINGERPRINT
    assert strong["taxa_estimable"] == 886
    assert strong["primary"]["favourable_direction"] == "negative"
    assert strong["primary"]["contrast"] == "C_minus_R3_matched_heldout_log_loss"
    assert contract["schema_version"] == "eog_aislands_isolation_adequacy_v1_3"
    assert list(contract["reference_tiers"]) == ["R0", "R1", "R2", "R3", "C"]
    assert boundary["schema"] == "eog.structural_island_paper_boundary.v1"
    counts = original_direction_counts()
    assert counts == {"above": 672, "equal": 42, "below": 131, "not_estimable": 41}
    return {"original": original, "strong": strong, "contract": contract, "boundary": boundary, "counts": counts}


def render(data: dict) -> str:
    original = data["original"]
    strong = data["strong"]
    counts = data["counts"]
    W, H = 1600, 1080
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
        '<title id="title">A-Islands results at two declared reference depths</title>',
        '<desc id="desc">The figure separates the original conditional-concordance endpoint under a restricted reference from the prospectively frozen log-loss increment beyond the richer R3 reference. A reference ladder shows R0 through C. The two effect axes are intentionally different and are not pooled.</desc>',
        '<style>text{font-family:Arial,Helvetica,sans-serif}.panel{fill:#fff;stroke:#cbd5e1;stroke-width:2}.axis{stroke:#475569;stroke-width:1.5}.grid{stroke:#e2e8f0;stroke-width:1}.zero{stroke:#64748b;stroke-width:2;stroke-dasharray:6 5}.ci{stroke:#172033;stroke-width:4}.small{font-size:13px}.body{font-size:15px}.head{font-size:28px;font-weight:700}.sub{font-size:19px;font-weight:700}</style>',
        '<rect width="1600" height="1080" fill="#f8fafc"/>',
        text(60, 52, "Figure 2 | A-Islands: the structural conclusion changes with reference depth", size=29, weight=700),
        text(60, 84, "Restricted-reference ordering and rich-reference predictive increment are distinct estimands and remain on separate axes.", size=16, fill="#526070"),
    ]

    panels = {
        "A": (55, 120, 450, 825),
        "B": (535, 120, 1010, 245),
        "C": (535, 390, 1010, 245),
        "D": (535, 660, 490, 285),
        "E": (1055, 660, 490, 285),
    }
    for label, (x, y, w, h) in panels.items():
        parts.append(f'<rect class="panel" x="{x}" y="{y}" width="{w}" height="{h}" rx="16"/>')
        parts.append(text(x+18, y+28, label, size=17, weight=700))

    ax, ay, aw, ah = panels["A"]
    parts.append(text(ax+52, ay+30, "Prospectively declared reference ladder", size=19, weight=700))
    ladder = [
        ("R0", "climate", "5 CHELSA predictors"),
        ("R1", "+ recipient geometry", "area + mainland distance + nearest source"),
        ("R2", "+ species-source pressure", "unweighted + source-area weighted"),
        ("R3", "+ generic landscape context", "surrounding landmass + generic stepping stones / network position"),
        ("C", "+ species-conditioned EOG", "geography-only connected frequency"),
    ]
    yy = ay + 85
    for i, (tier, title_, detail) in enumerate(ladder):
        fill = "#eef6ff" if tier == "C" else "#f8fafc"
        stroke = "#4f79a7" if tier == "C" else "#94a3b8"
        parts.append(f'<rect x="{ax+45}" y="{yy}" width="{aw-90}" height="103" rx="14" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        parts.append(text(ax+65, yy+28, tier, size=18, weight=700, fill=stroke))
        parts.append(text(ax+115, yy+28, title_, size=15, weight=700))
        parts.append(text(ax+65, yy+57, detail, size=12, fill="#526070"))
        if i < len(ladder)-1:
            parts.append(f'<line x1="{ax+aw/2}" y1="{yy+103}" x2="{ax+aw/2}" y2="{yy+127}" stroke="#94a3b8" stroke-width="3"/>')
            parts.append(f'<polygon points="{ax+aw/2},{yy+129} {ax+aw/2-8},{yy+117} {ax+aw/2+8},{yy+117}" fill="#94a3b8"/>')
        yy += 137
    parts.append(text(ax+aw/2, ay+785, "Primary extension contrast: C − R3 only", size=15, weight=700, anchor="middle", fill="#b94a48"))

    bx, by, bw, bh = panels["B"]
    parts.append(text(bx+52, by+30, "Restricted reference: conditional ordering", size=19, weight=700))
    parts.append(text(bx+52, by+58, "Reference: climatic support + nearest outer-training source distance", size=14, fill="#526070"))
    left, right = bx+95, bx+bw-95
    yaxis = by+145
    lo_axis, hi_axis = 0.48, 0.66
    for tick in [0.50, 0.54, 0.58, 0.62, 0.66]:
        xx = xmap(tick, left, right, lo_axis, hi_axis)
        parts.append(f'<line class="grid" x1="{xx}" y1="{by+105}" x2="{xx}" y2="{by+188}"/>')
        parts.append(text(xx, by+210, f"{tick:.2f}", size=11, anchor="middle", fill="#526070"))
    nullx = xmap(0.5, left, right, lo_axis, hi_axis)
    parts.append(f'<line class="zero" x1="{nullx}" y1="{by+105}" x2="{nullx}" y2="{by+188}"/>')
    eff = original["overall_conditional_concordance"]
    lo, hi = original["bootstrap_95_ci"]
    parts.append(f'<line class="ci" x1="{xmap(lo,left,right,lo_axis,hi_axis)}" y1="{yaxis}" x2="{xmap(hi,left,right,lo_axis,hi_axis)}" y2="{yaxis}"/>')
    parts.append(f'<circle cx="{xmap(eff,left,right,lo_axis,hi_axis)}" cy="{yaxis}" r="8" fill="#2f855a"/>')
    parts.append(text(right-5, by+128, f"mean concordance = {eff:.3f}  [{lo:.3f}, {hi:.3f}]", size=14, anchor="end", weight=700))
    parts.append(text(right-5, by+158, "845 estimable taxa; null = 0.5", size=13, anchor="end", fill="#526070"))
    parts.append(text(right-5, by+184, "Interpretation: structure retains conditional ordering information", size=13, anchor="end", fill="#2f855a", weight=700))

    cx, cy, cw, ch = panels["C"]
    parts.append(text(cx+52, cy+30, "Rich R3 reference: incremental predictive value", size=19, weight=700))
    parts.append(text(cx+52, cy+58, "Primary endpoint: matched held-out log loss, C − R3; negative favours EOG", size=14, fill="#526070"))
    left, right = cx+95, cx+cw-95
    yaxis = cy+145
    lo_axis, hi_axis = -0.004, 0.008
    for tick in [-0.004, -0.002, 0.0, 0.002, 0.004, 0.006, 0.008]:
        xx = xmap(tick, left, right, lo_axis, hi_axis)
        parts.append(f'<line class="grid" x1="{xx}" y1="{cy+105}" x2="{xx}" y2="{cy+188}"/>')
        parts.append(text(xx, cy+210, f"{tick:+.3f}", size=11, anchor="middle", fill="#526070"))
    zerox = xmap(0.0, left, right, lo_axis, hi_axis)
    parts.append(f'<line class="zero" x1="{zerox}" y1="{cy+105}" x2="{zerox}" y2="{cy+188}"/>')
    eff = strong["primary"]["species_macro_mean"]
    lo, hi = strong["primary"]["bootstrap_95_ci"]
    parts.append(f'<line class="ci" x1="{xmap(lo,left,right,lo_axis,hi_axis)}" y1="{yaxis}" x2="{xmap(hi,left,right,lo_axis,hi_axis)}" y2="{yaxis}"/>')
    parts.append(f'<circle cx="{xmap(eff,left,right,lo_axis,hi_axis)}" cy="{yaxis}" r="8" fill="#b94a48"/>')
    parts.append(text(right-5, cy+128, f"C − R3 = {eff:+.5f}  [{lo:+.5f}, {hi:+.5f}]", size=14, anchor="end", weight=700))
    parts.append(text(right-5, cy+158, "886 estimable taxa; 4,231 / 4,430 folds evaluable", size=13, anchor="end", fill="#526070"))
    parts.append(text(right-5, cy+184, "Interpretation: adverse incremental predictive effect beyond R3", size=13, anchor="end", fill="#b94a48", weight=700))

    dx, dy, dw, dh = panels["D"]
    parts.append(text(dx+52, dy+30, "Species-level direction", size=19, weight=700))
    maxw = dw-110
    total_o = counts["above"] + counts["equal"] + counts["below"] + counts["not_estimable"]
    parts.append(text(dx+45, dy+72, "Original conditional-concordance endpoint", size=13, weight=700))
    xx = dx+45; yy = dy+90
    for count, fill in [(counts["above"],"#2f855a"),(counts["equal"],"#94a3b8"),(counts["below"],"#b94a48"),(counts["not_estimable"],"#e2e8f0")]:
        ww = maxw*count/total_o
        parts.append(f'<rect x="{xx}" y="{yy}" width="{ww}" height="28" fill="{fill}"/>'); xx += ww
    parts.append(text(dx+45, dy+136, f"above 0.5: {counts['above']} | equal: {counts['equal']} | below: {counts['below']} | N/E: {counts['not_estimable']}", size=11, fill="#526070"))
    fav = strong["primary"]["species_favourable_negative"]; adv = strong["primary"]["species_adverse_positive"]; total_s=fav+adv
    parts.append(text(dx+45, dy+185, "Strong-reference C − R3 endpoint", size=13, weight=700))
    xx=dx+45; yy=dy+203
    for count, fill in [(fav,"#2f855a"),(adv,"#b94a48")]:
        ww=maxw*count/total_s
        parts.append(f'<rect x="{xx}" y="{yy}" width="{ww}" height="28" fill="{fill}"/>'); xx += ww
    parts.append(text(dx+45, dy+249, f"favourable: {fav} | adverse: {adv}", size=11, fill="#526070"))

    ex, ey, ew, eh = panels["E"]
    parts.append(text(ex+52, ey+30, "What the pair of results establishes", size=19, weight=700))
    lines = [
        ("1", "The restricted-reference result earns a narrow structural-ordering claim."),
        ("2", "That signal does not survive as an incremental predictive gain beyond R3."),
        ("3", "The endpoints differ; they are not pooled or compared as one effect size."),
        ("4", "Reference depth is part of the estimand, not a nuisance detail."),
    ]
    yy=ey+76
    for num, line_ in lines:
        parts.append(f'<circle cx="{ex+55}" cy="{yy-5}" r="14" fill="#334155"/>')
        parts.append(text(ex+55, yy, num, size=12, weight=700, anchor="middle", fill="#fff"))
        parts.append(text(ex+82, yy, line_, size=12, fill="#334155"))
        yy += 49
    parts.append(text(ex+ew/2, ey+263, "No movement / dispersal / colonisation probability is inferred.", size=12, anchor="middle", weight=700, fill="#526070"))

    parts.append(text(800, 1018, "Positive under a restricted reference ≠ generally useful beyond a richer reference", size=18, weight=700, anchor="middle"))
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def build_assets() -> dict[str, str]:
    data = validate()
    original = data["original"]
    strong = data["strong"]
    counts = data["counts"]
    svg = render(data)
    rows = [
        ["endpoint", "estimand", "estimate", "ci_low", "ci_high", "favourable_direction", "interpretation"],
        ["original_restricted_reference", "conditional_concordance", f"{original['overall_conditional_concordance']:.12f}", f"{original['bootstrap_95_ci'][0]:.12f}", f"{original['bootstrap_95_ci'][1]:.12f}", "above_0.5", "positive_structural_ordering"],
        ["strong_R3", "C_minus_R3_log_loss", f"{strong['primary']['species_macro_mean']:.12f}", f"{strong['primary']['bootstrap_95_ci'][0]:.12f}", f"{strong['primary']['bootstrap_95_ci'][1]:.12f}", "negative", "adverse_incremental_predictive_effect"],
    ]
    data_csv = "\n".join(",".join(row) for row in rows) + "\n"
    caption = (
        "**Figure 2. A-Islands results at two declared reference depths.** "
        "(A) The prospective island extension fixed a nested reference ladder from R0 climate through R3 generic island and source context, with C adding only species-conditioned geography-only EOG connected frequency; C − R3 was the sole primary extension contrast. "
        f"(B) In the earlier restricted-reference endpoint, connected frequency retained conditional incidence ordering after matching on climatic support and nearest outer-training source distance (mean conditional concordance {original['overall_conditional_concordance']:.3f}, 95% bootstrap interval {original['bootstrap_95_ci'][0]:.3f}–{original['bootstrap_95_ci'][1]:.3f}; {original['n_species_estimable']} estimable taxa). "
        f"(C) In the separately frozen richer-reference test, adding C to R3 increased held-out log loss by {strong['primary']['species_macro_mean']:+.5f} (95% bootstrap interval {strong['primary']['bootstrap_95_ci'][0]:+.5f} to {strong['primary']['bootstrap_95_ci'][1]:+.5f}; negative had been predeclared as favourable), so the primary increment was adverse. "
        f"(D) Species directions also differ by endpoint: the original analysis had {counts['above']} above, {counts['equal']} equal and {counts['below']} below the 0.5 null with {counts['not_estimable']} not estimable, whereas the strong-reference contrast had {strong['primary']['species_favourable_negative']} favourable and {strong['primary']['species_adverse_positive']} adverse taxa. "
        "(E) These endpoints are intentionally shown on different axes because conditional concordance and incremental log loss are different estimands. Together they support a reference-conditioned structural-adequacy conclusion, not a common effect-size estimate and not a movement or colonisation probability.\n"
    )
    alt = (
        "**Figure 2 accessibility description.** Panel A shows five nested reference tiers: R0 climate; R1 adds island area, mainland distance and nearest species source; R2 adds multi-source and source-area pressure; R3 adds generic surrounding-landmass, stepping-stone and network context; C adds species-conditioned EOG connected frequency. Panel B shows the original restricted-reference conditional-concordance estimate near 0.618 with an interval around 0.609 to 0.627 on an axis whose null is 0.5. Panel C uses a separate log-loss-difference axis and shows the strong-reference C minus R3 estimate near plus 0.00349 with a positive interval, where negative would favour EOG, so this result is adverse. Panel D shows species direction counts for the two endpoints. Panel E states the inference boundary: the original result supports a narrow conditional structural-ordering claim, but it does not imply incremental predictive gain beyond the richer R3 reference; the two endpoints are not pooled.\n"
    )
    meta = {
        "schema": "eog.structural_figure2_aislands_reference_conditioned.v1",
        "original_summary_sha256": sha256_file(ORIGINAL),
        "original_species_sha256": sha256_file(ORIGINAL_SPECIES),
        "strong_result_fingerprint": strong["result_fingerprint"],
        "strong_contract_schema": data["contract"]["schema_version"],
        "metrics_share_axis": False,
        "common_effect_claim": False,
        "movement_probability": False,
        "original_direction_counts": counts,
        "svg_sha256": sha256_bytes(svg.encode()),
        "data_sha256": sha256_bytes(data_csv.encode()),
        "caption_sha256": sha256_bytes(caption.encode()),
        "accessibility_sha256": sha256_bytes(alt.encode()),
    }
    return {
        str(OUT_SVG.relative_to(ROOT)): svg,
        str(OUT_META.relative_to(ROOT)): json.dumps(meta, indent=2, sort_keys=True) + "\n",
        str(OUT_DATA.relative_to(ROOT)): data_csv,
        str(OUT_CAPTION.relative_to(ROOT)): caption,
        str(OUT_ALT.relative_to(ROOT)): alt,
    }


def main() -> None:
    for relative, content in build_assets().items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print("wrote reference-conditioned A-Islands Figure 2 assets")


if __name__ == "__main__":
    main()
