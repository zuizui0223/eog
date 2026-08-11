from __future__ import annotations

import csv
import hashlib
import json
import math
from io import StringIO
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "figures" / "figure_manifest.json"
PRIMARY_SUMMARY = ROOT / "benchmarks" / "aislands_authoritative_expected.json"
PRIMARY_SPECIES = ROOT / "benchmarks" / "aislands_structural_species_expected.csv"
SECONDARY_SUMMARY = ROOT / "benchmarks" / "aislands_reachability_modes_expected.json"
BOTTLENECK_SUMMARY = ROOT / "benchmarks" / "aislands_bottleneck_expected.json"
APPLICABILITY = ROOT / "benchmarks" / "aislands_structural_applicability_expected.csv"
PROVENANCE = ROOT / "benchmarks" / "aislands_structural_species_expected_provenance.json"

OUTPUTS = {
    "svg": ROOT / "figures" / "output" / "figure_2_aislands.svg",
    "metadata": ROOT / "figures" / "output" / "figure_2_metadata.json",
    "species": ROOT / "figures" / "output" / "aislands_species_concordance.csv",
    "modes": ROOT / "figures" / "output" / "aislands_mode_estimates.csv",
    "applicability": ROOT / "figures" / "output" / "aislands_applicability.csv",
    "folds": ROOT / "figures" / "output" / "aislands_fold_coverage.csv",
    "caption": ROOT / "manuscript" / "figure_2_caption.md",
    "accessibility": ROOT / "manuscript" / "figure_2_accessibility.md",
}

MIRRORS = {
    "species": ROOT / "manuscript" / "figure_data" / "aislands_species_concordance.csv",
    "modes": ROOT / "manuscript" / "figure_data" / "aislands_mode_estimates.csv",
    "applicability": ROOT / "manuscript" / "figure_data" / "aislands_applicability.csv",
    "folds": ROOT / "manuscript" / "figure_data" / "aislands_fold_coverage.csv",
}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _fmt(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def _csv_text(fieldnames: list[str], rows: list[dict]) -> str:
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def _load_species() -> list[dict]:
    with PRIMARY_SPECIES.open(encoding="utf-8", newline="") as handle:
        rows = []
        for row in csv.DictReader(handle):
            value = row["conditional_concordance"].strip()
            rows.append(
                {
                    "species": row["species"],
                    "estimable_folds": int(row["estimable_folds"]),
                    "conditional_concordance": None if value == "" else float(value),
                }
            )
    return rows


def _load_applicability() -> list[dict]:
    with APPLICABILITY.open(encoding="utf-8", newline="") as handle:
        return [
            {
                "analysis": row["analysis"],
                "fold": row["fold"],
                "status": row["status"],
                "count": int(row["count"]),
            }
            for row in csv.DictReader(handle)
        ]


def validate_inputs() -> dict:
    manifest = _read_json(MANIFEST_PATH)["figure_2_aislands"]
    expected = manifest["expected"]

    checks = {
        PRIMARY_SUMMARY: expected["primary_summary_sha256"],
        PRIMARY_SPECIES: expected["primary_species_table_sha256"],
        SECONDARY_SUMMARY: expected["secondary_summary_sha256"],
        BOTTLENECK_SUMMARY: expected["bottleneck_summary_sha256"],
        APPLICABILITY: expected["applicability_table_sha256"],
        PROVENANCE: expected["provenance_sha256"],
    }
    for path, wanted in checks.items():
        actual = _sha256_bytes(path.read_bytes())
        _require(actual == wanted, f"SHA mismatch for {path.name}: expected {wanted}, got {actual}")

    primary = _read_json(PRIMARY_SUMMARY)
    secondary = _read_json(SECONDARY_SUMMARY)
    bottleneck = _read_json(BOTTLENECK_SUMMARY)
    provenance = _read_json(PROVENANCE)
    species = _load_species()
    applicability = _load_applicability()

    _require(provenance["preregistered"] is False, "post-outcome projection must not be labelled preregistered")
    _require("not_preregistration" in provenance["status"], "post-outcome provenance status missing")

    for key, prefix in [("primary", "primary"), ("secondary", "secondary"), ("bottleneck", "bottleneck")]:
        record = provenance[key]
        _require(record["workflow_run_id"] == expected[f"{prefix}_workflow_run_id"], f"{key} workflow run mismatch")
        _require(record["artifact_id"] == expected[f"{prefix}_artifact_id"], f"{key} artifact id mismatch")
        _require(record["artifact_digest"] == expected[f"{prefix}_artifact_digest"], f"{key} artifact digest mismatch")

    _require(primary["n_islands"] == expected["islands"], "island count drift")
    _require(primary["n_declared_taxa"] == expected["declared_taxa"], "declared taxon count drift")
    _require(primary["n_species_estimable"] == expected["primary_estimable_taxa"], "primary estimable count drift")
    _require(bottleneck["n_species_estimable"] == expected["bottleneck_estimable_taxa"], "bottleneck estimable count drift")
    _require(primary["null"] == 0.5 == secondary["null"] == bottleneck["null"], "null drift")

    for summary in (primary, secondary, bottleneck):
        inputs = summary["input_sha256"]
        _require(inputs["cohort"] == expected["shared_cohort_sha256"], "cohort SHA drift")
        _require(inputs["folds"] == expected["shared_folds_sha256"], "fold SHA drift")
        _require(inputs["climate"] == expected["shared_climate_sha256"], "climate SHA drift")

    combined = secondary["modes"]["combined"]
    _require(abs(combined["mean_conditional_concordance"] - primary["overall_conditional_concordance"]) < 1e-15, "combined mode drifted from primary")
    _require(combined["bootstrap_95_ci"] == primary["bootstrap_95_ci"], "combined interval drifted from primary")

    finite = [r for r in species if r["conditional_concordance"] is not None]
    above = sum(r["conditional_concordance"] > 0.5 for r in finite)
    equal = sum(r["conditional_concordance"] == 0.5 for r in finite)
    below = sum(r["conditional_concordance"] < 0.5 for r in finite)
    _require(len(species) == expected["declared_taxa"], "species projection must retain every declared taxon")
    _require(len(finite) == expected["primary_estimable_taxa"], "species projection estimable count mismatch")
    _require(above == expected["species_above_null"], "species-above-null count drift")
    _require(equal == expected["species_equal_null"], "species-equal-null count drift")
    _require(below == expected["species_below_null"], "species-below-null count drift")
    _require(len(species) - len(finite) == expected["species_not_estimable"], "species-not-estimable count drift")

    overall = {(r["analysis"], r["status"]): r["count"] for r in applicability if r["fold"] == "ALL"}
    _require(overall[("primary_combined", "evaluable")] == expected["primary_evaluable_species_folds"], "primary evaluable fold count drift")
    _require(overall[("primary_combined", "no_comparable_pairs_within_frozen_strata")] == expected["primary_no_comparable_pair_species_folds"], "primary no-pair count drift")
    _require(overall[("primary_combined", "insufficient_training_classes")] == expected["primary_insufficient_training_species_folds"], "primary training-class count drift")
    _require(overall[("bottleneck_secondary", "evaluable")] == expected["bottleneck_evaluable_species_folds"], "bottleneck evaluable count drift")
    _require(overall[("bottleneck_secondary", "no_finite_comparable_pairs_within_frozen_strata")] == expected["bottleneck_no_comparable_pair_species_folds"], "bottleneck no-pair count drift")
    _require(overall[("bottleneck_secondary", "insufficient_training_classes")] == expected["bottleneck_insufficient_training_species_folds"], "bottleneck training-class count drift")

    return {
        "manifest": manifest,
        "expected": expected,
        "primary": primary,
        "secondary": secondary,
        "bottleneck": bottleneck,
        "provenance": provenance,
        "species": species,
        "applicability": applicability,
        "direction_counts": {"above": above, "equal": equal, "below": below, "not_estimable": len(species) - len(finite)},
    }


def _species_rows(data: dict) -> list[dict]:
    finite = [r for r in data["species"] if r["conditional_concordance"] is not None]
    finite.sort(key=lambda r: (r["conditional_concordance"], r["species"]))
    rows = []
    for rank, row in enumerate(finite, start=1):
        score = row["conditional_concordance"]
        direction = "above_0.5" if score > 0.5 else "below_0.5" if score < 0.5 else "equal_0.5"
        rows.append(
            {
                "rank": rank,
                "species": row["species"],
                "estimable_folds": row["estimable_folds"],
                "conditional_concordance": f"{score:.12f}",
                "direction_vs_null": direction,
            }
        )
    return rows


def _mode_rows(data: dict) -> list[dict]:
    secondary = data["secondary"]
    bottle = data["bottleneck"]
    labels = {
        "combined": "Combined connected frequency",
        "geography_only": "Geography-only connected frequency",
        "environmentally_constrained": "Environment-constrained connected frequency",
    }
    rows = []
    for mode in ("combined", "geography_only", "environmentally_constrained"):
        rec = secondary["modes"][mode]
        rows.append(
            {
                "quantity": mode,
                "label": labels[mode],
                "n_species": rec["n_species_estimable"],
                "effect": f"{rec['mean_conditional_concordance']:.12f}",
                "ci_low": f"{rec['bootstrap_95_ci'][0]:.12f}",
                "ci_high": f"{rec['bootstrap_95_ci'][1]:.12f}",
                "null_value": "0.500000000000",
                "direction_note": "higher conditional concordance is favourable",
            }
        )
    rows.append(
        {
            "quantity": "bottleneck_secondary",
            "label": "Normalized geographic bottleneck secondary",
            "n_species": bottle["n_species_estimable"],
            "effect": f"{bottle['mean_conditional_concordance']:.12f}",
            "ci_low": f"{bottle['bootstrap_95_ci'][0]:.12f}",
            "ci_high": f"{bottle['bootstrap_95_ci'][1]:.12f}",
            "null_value": "0.500000000000",
            "direction_note": "score is -median normalized bottleneck; higher concordance means smaller bottleneck is favourable",
        }
    )
    return rows


def _applicability_rows(data: dict) -> list[dict]:
    overall = [r for r in data["applicability"] if r["fold"] == "ALL"]
    order = {
        "evaluable": 0,
        "no_comparable_pairs_within_frozen_strata": 1,
        "no_finite_comparable_pairs_within_frozen_strata": 1,
        "insufficient_training_classes": 2,
        "other_failure": 3,
    }
    overall.sort(key=lambda r: (r["analysis"], order.get(r["status"], 9), r["status"]))
    return overall


def _fold_rows(data: dict) -> list[dict]:
    result = []
    for analysis in ("primary_combined", "bottleneck_secondary"):
        for fold in range(1, 6):
            rows = [r for r in data["applicability"] if r["analysis"] == analysis and r["fold"] == str(fold)]
            counts = {r["status"]: r["count"] for r in rows}
            no_pair = counts.get("no_comparable_pairs_within_frozen_strata", 0) + counts.get("no_finite_comparable_pairs_within_frozen_strata", 0)
            result.append(
                {
                    "analysis": analysis,
                    "fold": fold,
                    "evaluable": counts.get("evaluable", 0),
                    "no_comparable_pairs": no_pair,
                    "insufficient_training_classes": counts.get("insufficient_training_classes", 0),
                    "total": sum(counts.values()),
                }
            )
    return result


def _x_map(value: float, left: float, right: float, low: float, high: float) -> float:
    return left + (value - low) / (high - low) * (right - left)


def _svg(data: dict, species_rows: list[dict], mode_rows: list[dict], app_rows: list[dict], fold_rows: list[dict]) -> str:
    W, H = 1600, 1120
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
        '<title id="title">Figure 2. A-Islands confirmatory structural benchmark</title>',
        f'<desc id="desc">Frozen design, within-stratum comparison, all {data["expected"]["primary_estimable_taxa"]} estimable species conditional concordance values, four structural quantities with intervals, and explicit fold non-estimability.</desc>',
        '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#111}.panel{fill:#fff;stroke:#bbb;stroke-width:1.2}.head{font-size:24px;font-weight:700}.sub{font-size:17px;font-weight:700}.body{font-size:14px}.small{font-size:12px}.tiny{font-size:10px}.axis{stroke:#555;stroke-width:1}.ref{stroke:#666;stroke-width:1.4;stroke-dasharray:6 5}.ci{stroke:#111;stroke-width:2}.pt{fill:#111}.light{fill:#eee}.mid{fill:#bbb}.dark{fill:#555}.outline{fill:none;stroke:#777;stroke-width:1}.grid{stroke:#ddd;stroke-width:1}</style>',
        '<rect x="0" y="0" width="1600" height="1120" fill="white"/>',
        '<text class="head" x="55" y="48">A-Islands: structure retains incidence information after local support and source distance are frozen</text>',
    ]

    # Panel boxes.
    panels = {
        'A': (50, 75, 420, 260),
        'B': (490, 75, 500, 260),
        'C': (1010, 75, 540, 610),
        'D': (50, 355, 940, 330),
        'E': (50, 705, 1500, 355),
    }
    for label, (x,y,w,h) in panels.items():
        parts.append(f"""<rect class="panel" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>""")
        parts.append(f"""<text class="sub" x="{x+14}" y="{y+27}">{label}</text>""")

    exp = data['expected']
    # A: frozen design.
    ax, ay, aw, ah = panels['A']
    parts.append(f"""<text class="sub" x="{ax+52}" y="{ay+28}">Frozen confirmatory design</text>""")
    design = [
        (str(exp["islands"]), "islands"),
        (str(exp["declared_taxa"]), "declared taxa"),
        (str(exp["primary_estimable_taxa"]), "primary estimable taxa"),
        (str(exp["folds"]), "spatial folds"),
        (str(exp["chelsa_predictors"]), "CHELSA predictors"),
        (str(exp["graph_scenarios"]), "predeclared graph scenarios"),
    ]
    for i,(num,lab) in enumerate(design):
        col=i%2; row=i//2
        x=ax+28+col*195; y=ay+68+row*58
        parts.append(f"""<rect x="{x}" y="{y}" width="170" height="42" rx="6" class="light"/>""")
        parts.append(f"""<text x="{x+12}" y="{y+20}" class="body" font-weight="700">{num}</text>""")
        parts.append(f"""<text x="{x+45}" y="{y+20}" class="small">{escape(lab)}</text>""")
    parts.append(f"""<text class="tiny" x="{ax+28}" y="{ay+244}">All three structural summaries share the frozen cohort, folds and climate hashes.</text>""")

    # B: 5 x 5 strata concept.
    bx, by, bw, bh = panels['B']
    parts.append(f"""<text class="sub" x="{bx+52}" y="{by+28}">Conditional comparison</text>""")
    gx, gy, cell = bx+100, by+67, 27
    for r in range(exp["distance_strata"]):
        for c in range(exp["support_strata"]):
            shade = 245 - 10*(r+c)
            parts.append(f"""<rect x="{gx+c*cell}" y="{gy+r*cell}" width="{cell}" height="{cell}" fill="rgb({shade},{shade},{shade})" stroke="#fff"/>""")
    parts.append(f"""<text class="small" x="{gx}" y="{gy-9}">pointwise CHELSA support →</text>""")
    parts.append(f"""<text class="small" transform="translate({gx-48},{gy+130}) rotate(-90)">nearest training occurrence distance →</text>""")
    # same-stratum occupied/unoccupied icons.
    sx, sy = bx+300, by+100
    parts.append(f"""<rect x="{sx}" y="{sy}" width="145" height="80" rx="6" fill="#f7f7f7" stroke="#aaa"/>""")
    parts.append(f"""<text class="small" x="{sx+12}" y="{sy+20}">within one frozen stratum</text>""")
    parts.append(f"""<circle cx="{sx+35}" cy="{sy+48}" r="7" fill="#111"/><text class="tiny" x="{sx+48}" y="{sy+52}">occupied</text>""")
    parts.append(f"""<circle cx="{sx+35}" cy="{sy+68}" r="7" fill="white" stroke="#111"/><text class="tiny" x="{sx+48}" y="{sy+72}">unoccupied</text>""")
    parts.append(f"""<text class="small" x="{bx+45}" y="{by+226}">Compare structure only after local support and direct source distance are matched.</text>""")

    # C: all species points.
    cx, cy, cw, ch = panels['C']
    parts.append(f"""<text class="sub" x="{cx+52}" y="{cy+28}">All estimable species</text>""")
    plot_l, plot_r = cx+60, cx+510
    plot_t, plot_b = cy+78, cy+530
    low, high = 0.15, 1.0
    refx = _x_map(0.5, plot_l, plot_r, low, high)
    parts.append(f"""<line class="ref" x1="{refx:.1f}" y1="{plot_t}" x2="{refx:.1f}" y2="{plot_b}"/>""")
    for tick in [0.2,0.4,0.5,0.6,0.8,1.0]:
        x=_x_map(tick,plot_l,plot_r,low,high)
        parts.append(f"""<line class="grid" x1="{x:.1f}" y1="{plot_t}" x2="{x:.1f}" y2="{plot_b}"/>""")
        parts.append(f"""<text class="tiny" x="{x-10:.1f}" y="{plot_b+18}">{tick:.1f}</text>""")
    # deterministic vertical spread, sorted ranks.
    bands=31
    for i,row in enumerate(species_rows):
        score=float(row['conditional_concordance'])
        x=_x_map(score,plot_l,plot_r,low,high)
        band=(i*17)%bands
        y=plot_t+8+band*(plot_b-plot_t-16)/(bands-1)
        parts.append(f"""<circle class="pt" cx="{x:.2f}" cy="{y:.2f}" r="1.65"/>""")
    cnt=data['direction_counts']
    parts.append(f"""<text class="body" x="{cx+58}" y="{cy+565}">n = {len(species_rows)}: above 0.5 = {cnt["above"]}; equal = {cnt["equal"]}; below = {cnt["below"]}</text>""")
    not_estimable = cnt["not_estimable"]
    parts.append(f"""<text class="small" x="{cx+58}" y="{cy+590}">{not_estimable} declared taxa had no primary species statistic and remain in Panel E.</text>""")

    # D: forest plot.
    dx, dy, dw, dh = panels['D']
    parts.append(f"""<text class="sub" x="{dx+52}" y="{dy+28}">Frozen structural quantities</text>""")
    fl, fr = dx+390, dx+885
    ft, fb = dy+70, dy+275
    for tick in [0.5,0.55,0.60,0.65]:
        x=_x_map(tick,fl,fr,0.49,0.66)
        parts.append(f"""<line class="grid" x1="{x:.1f}" y1="{ft-18}" x2="{x:.1f}" y2="{fb+5}"/>""")
        parts.append(f"""<text class="tiny" x="{x-12:.1f}" y="{fb+25}">{tick:.2f}</text>""")
    ref=_x_map(0.5,fl,fr,0.49,0.66)
    parts.append(f"""<line class="ref" x1="{ref:.1f}" y1="{ft-18}" x2="{ref:.1f}" y2="{fb+5}"/>""")
    for i,row in enumerate(mode_rows):
        y=ft+i*51
        eff=float(row['effect']); lo=float(row['ci_low']); hi=float(row['ci_high'])
        x=_x_map(eff,fl,fr,0.49,0.66); xlo=_x_map(lo,fl,fr,0.49,0.66); xhi=_x_map(hi,fl,fr,0.49,0.66)
        parts.append(f"""<text class="small" x="{dx+35}" y="{y+5}">{escape(row["label"])}</text>""")
        parts.append(f"""<text class="tiny" x="{dx+305}" y="{y+5}">n={row["n_species"]}</text>""")
        parts.append(f"""<line class="ci" x1="{xlo:.1f}" y1="{y}" x2="{xhi:.1f}" y2="{y}"/>""")
        parts.append(f"""<circle cx="{x:.1f}" cy="{y}" r="5" fill="#111"/>""")
        parts.append(f"""<text class="tiny" x="{fr+8}" y="{y+4}">{eff:.3f} [{lo:.3f}, {hi:.3f}]</text>""")
    parts.append(f"""<text class="tiny" x="{dx+35}" y="{dy+320}">Bottleneck evaluation uses -median normalized geographic bottleneck: higher concordance means smaller bottleneck aligns with occupancy.</text>""")

    # E: applicability and failures.
    ex, ey, ew, eh = panels['E']
    parts.append(f"""<text class="sub" x="{ex+52}" y="{ey+28}">Applicability is part of the result</text>""")
    parts.append(f"""<text class="small" x="{ex+35}" y="{ey+57}">Declared: {exp['declared_taxa']} taxa × {exp['folds']} folds = {exp['declared_taxa'] * exp['folds']:,} species-fold evaluations. Non-estimable rows are not dropped.</text>""")
    overall = {}
    for row in app_rows:
        overall.setdefault(row['analysis'], {})[row['status']] = row['count']
    labels={
        'primary_combined':'Primary combined connected frequency',
        'bottleneck_secondary':'Bottleneck secondary',
    }
    for idx,analysis in enumerate(('primary_combined','bottleneck_secondary')):
        y=ey+105+idx*92
        counts=overall[analysis]
        evaluable=counts.get('evaluable',0)
        no_pairs=counts.get('no_comparable_pairs_within_frozen_strata',0)+counts.get('no_finite_comparable_pairs_within_frozen_strata',0)
        training=counts.get('insufficient_training_classes',0)
        parts.append(f"""<text class="small" x="{ex+35}" y="{y-14}">{labels[analysis]}</text>""")
        barx=ex+350; barw=930; barh=26
        total=evaluable+no_pairs+training
        widths=[barw*evaluable/total,barw*no_pairs/total,barw*training/total]
        cur=barx
        for cls,w in zip(('dark','mid','light'),widths):
            parts.append(f"""<rect class="{cls}" x="{cur:.1f}" y="{y-29}" width="{w:.1f}" height="{barh}"/>""")
            cur+=w
        parts.append(f"""<text class="tiny" x="{barx}" y="{y+12}">evaluable {evaluable}</text>""")
        parts.append(f"""<text class="tiny" x="{barx+230}" y="{y+12}">no comparable pairs {no_pairs}</text>""")
        parts.append(f"""<text class="tiny" x="{barx+500}" y="{y+12}">insufficient training classes {training}</text>""")
    # fold compact table.
    parts.append(f"""<text class="small" x="{ex+35}" y="{ey+285}">Fold-level evaluable counts (primary / bottleneck)</text>""")
    primary_f={r['fold']:r for r in fold_rows if r['analysis']=='primary_combined'}
    bottle_f={r['fold']:r for r in fold_rows if r['analysis']=='bottleneck_secondary'}
    for fold in range(1,6):
        x=ex+330+(fold-1)*190
        parts.append(f"""<text class="tiny" x="{x}" y="{ey+285}">Fold {fold}: {primary_f[fold]["evaluable"]} / {bottle_f[fold]["evaluable"]}</text>""")
    parts.append(f"""<text class="tiny" x="{ex+35}" y="{ey+326}">The primary {exp['primary_estimable_taxa']}-species distribution and {exp['bottleneck_estimable_taxa']}-species bottleneck summary therefore have different applicability; neither denominator is hidden.</text>""")

    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def _caption(data: dict) -> str:
    p=data['primary']; s=data['secondary']; b=data['bottleneck']; c=data['direction_counts']
    return (
        "**Figure 2. Frozen A-Islands confirmatory structural benchmark.** "
        f"(A) The analysis used {p['n_islands']} islands, {p['n_declared_taxa']} declared native taxa, {data['expected']['folds']} spatial folds, {data['expected']['chelsa_predictors']} CHELSA predictors and {data['expected']['graph_scenarios']} predeclared graph scenarios. "
        f"(B) Held-out occupied and unoccupied islands were compared only within the same frozen {data['expected']['support_strata']} × {data['expected']['distance_strata']} pointwise-support × nearest-training-occurrence-distance stratum, so the structural score asks whether configuration retains incidence information after those two simpler quantities are controlled. "
        f"(C) All {p['n_species_estimable']} taxa with a primary species statistic are shown: {c['above']} were above the 0.5 concordance null, {c['equal']} equalled it and {c['below']} were below it; {c['not_estimable']} declared taxa were not estimable. "
        f"(D) Mean species-level conditional concordance was {p['overall_conditional_concordance']:.3f} (95% bootstrap interval {p['bootstrap_95_ci'][0]:.3f}–{p['bootstrap_95_ci'][1]:.3f}) for combined connected frequency, {s['modes']['geography_only']['mean_conditional_concordance']:.3f} ({s['modes']['geography_only']['bootstrap_95_ci'][0]:.3f}–{s['modes']['geography_only']['bootstrap_95_ci'][1]:.3f}) for geography-only connected frequency, {s['modes']['environmentally_constrained']['mean_conditional_concordance']:.3f} ({s['modes']['environmentally_constrained']['bootstrap_95_ci'][0]:.3f}–{s['modes']['environmentally_constrained']['bootstrap_95_ci'][1]:.3f}) for environmentally constrained connected frequency, and {b['mean_conditional_concordance']:.3f} ({b['bootstrap_95_ci'][0]:.3f}–{b['bootstrap_95_ci'][1]:.3f}; n={b['n_species_estimable']}) for the predeclared normalized geographic bottleneck secondary. "
        "The bottleneck evaluation uses the negative median normalized bottleneck, so higher concordance means that smaller bottlenecks align with occupancy. These mode estimates are descriptive; no pairwise superiority test among the modes was predeclared. "
        "(E) Non-estimable species-folds remain visible: the primary analysis had 3,041 evaluable rows, 1,190 rows without comparable presence–absence pairs in the frozen strata and 199 rows with insufficient training classes; the bottleneck secondary had 2,591, 1,640 and 199, respectively. "
        "Connected frequency and bottleneck are structural graph summaries, not dispersal or colonisation probabilities or realised pathways.\n"
    )


def _accessibility(data: dict) -> str:
    p=data['primary']; b=data['bottleneck']; c=data['direction_counts']
    return (
        f"**Figure 2 accessibility description.** The figure has five panels. Panel A lists the frozen A-Islands design: {p['n_islands']} islands, {p['n_declared_taxa']} declared taxa, {p['n_species_estimable']} taxa with a primary species statistic, {data['expected']['folds']} spatial folds, {data['expected']['chelsa_predictors']} CHELSA predictors and {data['expected']['graph_scenarios']} graph scenarios. Panel B shows a {data['expected']['support_strata']} by {data['expected']['distance_strata']} grid representing pointwise-support and nearest-training-occurrence-distance strata; occupied and unoccupied held-out islands are compared only within a shared stratum. Panel C displays all {p['n_species_estimable']} estimable species as small points on a conditional-concordance axis with a dashed {p['null']:.1f} null; {c['above']} points are above the null, {c['equal']} equal it and {c['below']} are below. Panel D shows four interval estimates on the same concordance scale: combined {p['overall_conditional_concordance']:.3f}, geography-only {data['secondary']['modes']['geography_only']['mean_conditional_concordance']:.3f}, environmentally constrained {data['secondary']['modes']['environmentally_constrained']['mean_conditional_concordance']:.3f} and bottleneck secondary {b['mean_conditional_concordance']:.3f}; all displayed intervals are above the null, but the figure does not claim pairwise superiority among modes. Panel E uses stacked bars to show that non-estimability is substantial and differs by analysis: {data['expected']['primary_evaluable_species_folds']:,} of {data['expected']['declared_taxa'] * data['expected']['folds']:,} primary species-fold rows are evaluable versus {data['expected']['bottleneck_evaluable_species_folds']:,} bottleneck rows, with the remainder attributed to unavailable comparable pairs or insufficient training classes. The figure explicitly states that structural graph summaries are not dispersal probabilities or realised routes.\n"
    )


def build_assets() -> dict[str, str]:
    data=validate_inputs()
    species_rows=_species_rows(data)
    mode_rows=_mode_rows(data)
    app_rows=_applicability_rows(data)
    fold_rows=_fold_rows(data)

    species_text=_csv_text(["rank","species","estimable_folds","conditional_concordance","direction_vs_null"],species_rows)
    modes_text=_csv_text(["quantity","label","n_species","effect","ci_low","ci_high","null_value","direction_note"],mode_rows)
    app_text=_csv_text(["analysis","fold","status","count"],app_rows)
    folds_text=_csv_text(["analysis","fold","evaluable","no_comparable_pairs","insufficient_training_classes","total"],fold_rows)
    svg=_svg(data,species_rows,mode_rows,app_rows,fold_rows)
    caption=_caption(data)
    accessibility=_accessibility(data)

    output_hashes={
        "figure_2_aislands.svg": _sha256_bytes(svg.encode()),
        "aislands_species_concordance.csv": _sha256_bytes(species_text.encode()),
        "aislands_mode_estimates.csv": _sha256_bytes(modes_text.encode()),
        "aislands_applicability.csv": _sha256_bytes(app_text.encode()),
        "aislands_fold_coverage.csv": _sha256_bytes(folds_text.encode()),
        "figure_2_caption.md": _sha256_bytes(caption.encode()),
        "figure_2_accessibility.md": _sha256_bytes(accessibility.encode()),
    }
    metadata={
        "schema_version":"eog_figure_2_metadata_v1",
        "source_status":"post_outcome_archive_projection_not_preregistration",
        "input_sha256":{
            "primary_summary":data['expected']['primary_summary_sha256'],
            "primary_species":data['expected']['primary_species_table_sha256'],
            "secondary_summary":data['expected']['secondary_summary_sha256'],
            "bottleneck_summary":data['expected']['bottleneck_summary_sha256'],
            "applicability_projection":data['expected']['applicability_table_sha256'],
            "provenance":data['expected']['provenance_sha256'],
        },
        "artifact_digests":{
            "primary":data['expected']['primary_artifact_digest'],
            "secondary":data['expected']['secondary_artifact_digest'],
            "bottleneck":data['expected']['bottleneck_artifact_digest'],
        },
        "counts":{
            "islands":data['primary']['n_islands'],
            "declared_taxa":data['primary']['n_declared_taxa'],
            "primary_estimable_taxa":data['primary']['n_species_estimable'],
            "bottleneck_estimable_taxa":data['bottleneck']['n_species_estimable'],
            **data['direction_counts'],
        },
        "claim_boundary":"Added held-out structural information conditional on frozen pointwise support and nearest-training-occurrence distance; not SDM superiority, dispersal probability, colonisation probability, or realised pathway.",
        "output_sha256":output_hashes,
    }
    metadata_text=json.dumps(metadata,indent=2,sort_keys=True)+"\n"

    return {
        str(OUTPUTS['svg'].relative_to(ROOT)):svg,
        str(OUTPUTS['metadata'].relative_to(ROOT)):metadata_text,
        str(OUTPUTS['species'].relative_to(ROOT)):species_text,
        str(OUTPUTS['modes'].relative_to(ROOT)):modes_text,
        str(OUTPUTS['applicability'].relative_to(ROOT)):app_text,
        str(OUTPUTS['folds'].relative_to(ROOT)):folds_text,
        str(OUTPUTS['caption'].relative_to(ROOT)):caption,
        str(OUTPUTS['accessibility'].relative_to(ROOT)):accessibility,
        str(MIRRORS['species'].relative_to(ROOT)):species_text,
        str(MIRRORS['modes'].relative_to(ROOT)):modes_text,
        str(MIRRORS['applicability'].relative_to(ROOT)):app_text,
        str(MIRRORS['folds'].relative_to(ROOT)):folds_text,
    }


def main() -> None:
    assets=build_assets()
    for relative,text in assets.items():
        path=ROOT/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(text,encoding='utf-8')
    print(f"wrote {len(assets)} Figure 2 assets")


if __name__ == "__main__":
    main()
