from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "validation/paper_ready_replication/candidate_flow_ledger.json"
SYNTHESIS = ROOT / "validation/paper_ready_replication/observed_endpoint3_synthesis.json"
TAMPA_CERT = ROOT / "validation/tampa_seagrass_endpoint3/terminal_predictive_result_certificate.json"
DEFAULT_OUTPUT = ROOT / "build/paper_ready_eogwf"

FAVORABLE = "favorable_complementary_added_value"
ADVERSE = "adverse_complementary_added_value"
NULL = "no_confirmed_complementary_added_value"
BOUNDARY = "structural_diagnostic_plus_context_dependent_predictive_complement"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _fmt(value: float, digits: int = 7) -> str:
    return f"{value:.{digits}f}"


def _status_short(status: str) -> str:
    if status == FAVORABLE:
        return "favorable"
    if status == ADVERSE:
        return "adverse"
    if status == NULL:
        return "null"
    return status


def _validate_inputs(
    ledger: dict[str, object], synthesis: dict[str, object], tampa: dict[str, object]
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    fresh = list(ledger["fresh_predictive_results"])
    stops = list(ledger["fresh_candidate_stops"])
    admin = list(ledger["administrative_exclusions"])
    summary = dict(ledger["current_denominator_summary"])

    if len(fresh) != 3 or len(stops) != 31 or len(admin) != 3:
        raise RuntimeError(
            f"paper denominator drift: predictive={len(fresh)}, stops={len(stops)}, admin={len(admin)}"
        )
    if summary.get("fresh_predictive_endpoints_with_scores") != 3:
        raise RuntimeError("ledger no longer declares exactly three scored endpoints")
    if summary.get("fresh_candidate_stops_listed") != 31:
        raise RuntimeError("ledger no longer declares 31 protocol STOPs")
    if summary.get("administrative_exclusions") != 3:
        raise RuntimeError("ledger no longer declares three administrative exclusions")
    if summary.get("candidate_hunting_hard_stop") is not True:
        raise RuntimeError("candidate-hunting hard stop is not active")
    if summary.get("product_boundary") != BOUNDARY:
        raise RuntimeError("ledger product boundary drift")

    statuses = [str(row["terminal_status"]) for row in fresh]
    if statuses != [FAVORABLE, FAVORABLE, ADVERSE]:
        raise RuntimeError(f"fresh endpoint status order drift: {statuses!r}")

    if synthesis.get("observed_endpoint3_status") != ADVERSE:
        raise RuntimeError("observed endpoint-3 status drift")
    if synthesis.get("predeclared_product_boundary_applied") != BOUNDARY:
        raise RuntimeError("observed synthesis boundary drift")
    if synthesis.get("candidate_hunting_hard_stop") is not True:
        raise RuntimeError("observed synthesis no longer hard-stops candidate hunting")
    if synthesis.get("fourth_fresh_endpoint_allowed") is not False:
        raise RuntimeError("observed synthesis unexpectedly allows a fourth fresh endpoint")
    if synthesis.get("primary_submission_route") != "Methods in Ecology and Evolution":
        raise RuntimeError("primary submission route drift")

    if tampa.get("terminal_status") != ADVERSE:
        raise RuntimeError("Tampa terminal certificate drift")
    placebo = dict(tampa["secondary_placebo"])
    if placebo.get("replicates") != 20 or placebo.get("feature_count") != 10:
        raise RuntimeError("Tampa secondary placebo contract drift")
    if placebo.get("changes_primary_status") is not False:
        raise RuntimeError("secondary placebo must not redefine primary status")

    return fresh, stops, admin


def _endpoint_rows(fresh: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in fresh:
        baseline = float(item["baseline_macro_log_loss"])
        augmented = float(item["augmented_macro_log_loss"])
        delta = float(item["augmented_minus_baseline"])
        relative = item.get("relative_log_loss_change")
        if relative is None:
            relative = delta / baseline
        rows.append(
            {
                "issue": int(item["issue"]),
                "system": str(item["system"]),
                "endpoint": str(item["endpoint"]),
                "observation_process": str(item["observation_process"]),
                "terminal_status": str(item["terminal_status"]),
                "baseline_macro_log_loss": baseline,
                "augmented_macro_log_loss": augmented,
                "augmented_minus_baseline": delta,
                "relative_log_loss_change": float(relative),
                "augmented_heldout_wins": int(item["augmented_heldout_wins"]),
                "heldout_units": int(item["heldout_units"]),
                "once_only_run_id": int(item["once_only_run_id"]),
            }
        )
    return rows


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _full_candidate_rows(
    fresh: list[dict[str, object]], stops: list[dict[str, object]], admin: list[dict[str, object]]
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in fresh:
        rows.append(
            {
                "issue": item["issue"],
                "system": item.get("system", ""),
                "classification": "predictive_result",
                "terminal_stage": "paired_predictive_test",
                "terminal_status_or_reason": item["terminal_status"],
                "biological_response_access": "once_only_predictive_response",
                "counts_as_predictive_evidence": True,
            }
        )
    for item in stops:
        rows.append(
            {
                "issue": item["issue"],
                "system": item.get("system", ""),
                "classification": "scientific_protocol_stop",
                "terminal_stage": item.get("terminal_stage", "unspecified"),
                "terminal_status_or_reason": item.get("reason", ""),
                "biological_response_access": item.get("biological_response_access", "unspecified"),
                "counts_as_predictive_evidence": False,
            }
        )
    for item in admin:
        rows.append(
            {
                "issue": item["issue"],
                "system": item.get("system", ""),
                "classification": "administrative_exclusion",
                "terminal_stage": item.get("classification", "administrative"),
                "terminal_status_or_reason": item.get("reason", ""),
                "biological_response_access": item.get("biological_response_access", "not_applicable"),
                "counts_as_predictive_evidence": False,
            }
        )
    return sorted(rows, key=lambda row: int(row["issue"]))


def _svg_text(x: float, y: float, text: str, *, size: int = 16, anchor: str = "start", weight: str = "normal") -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" text-anchor="{anchor}" font-weight="{weight}">{html.escape(text)}</text>'
    )


def _architecture_svg(boundary: str) -> str:
    width, height = 1180, 510
    boxes = [
        (40, 145, 205, 120, "Occurrence evidence", "positive realized records"),
        (310, 125, 240, 160, "Layer A", "exact compatible-world set\ncontraction + falsification"),
        (615, 125, 240, 160, "Layer B", "10 symmetric support features\nworld-label invariant"),
        (920, 145, 220, 120, "Paired prediction", "same strong learner\nwith vs without Layer B"),
    ]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    parts.append('<rect width="100%" height="100%" fill="white"/>')
    parts.append(_svg_text(width / 2, 42, "EOG two-layer architecture", size=26, anchor="middle", weight="bold"))
    parts.append(_svg_text(width / 2, 75, "Exact structural inference is kept separate from label-invariant predictive compression", size=15, anchor="middle"))
    for x, y, w, h, title, subtitle in boxes:
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="none" stroke="black" stroke-width="2"/>')
        parts.append(_svg_text(x + w / 2, y + 35, title, size=19, anchor="middle", weight="bold"))
        for idx, line in enumerate(subtitle.split("\n")):
            parts.append(_svg_text(x + w / 2, y + 67 + idx * 24, line, size=14, anchor="middle"))
    for x1, x2 in [(245, 310), (550, 615), (855, 920)]:
        parts.append(f'<line x1="{x1}" y1="205" x2="{x2 - 10}" y2="205" stroke="black" stroke-width="2"/>')
        parts.append(f'<polygon points="{x2 - 10},199 {x2},205 {x2 - 10},211" fill="black"/>')
    parts.append(_svg_text(430, 330, "Layer A claim", size=16, anchor="middle", weight="bold"))
    parts.append(_svg_text(430, 356, "which declared worlds survive or are falsified", size=14, anchor="middle"))
    parts.append(_svg_text(735, 330, "Layer B claim", size=16, anchor="middle", weight="bold"))
    parts.append(_svg_text(735, 356, "whether the frozen summary adds heldout information", size=14, anchor="middle"))
    parts.append(f'<rect x="180" y="405" width="820" height="62" rx="8" fill="none" stroke="black" stroke-width="1.5" stroke-dasharray="6,5"/>')
    parts.append(_svg_text(width / 2, 431, "Observed cross-ecosystem boundary", size=16, anchor="middle", weight="bold"))
    parts.append(_svg_text(width / 2, 454, boundary, size=15, anchor="middle"))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _funnel_svg(predictive: int, stops: int, admin: int) -> str:
    total = predictive + stops + admin
    scientific = predictive + stops
    width, height = 1050, 520
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    parts.append('<rect width="100%" height="100%" fill="white"/>')
    parts.append(_svg_text(width / 2, 42, "Prospective validation funnel", size=26, anchor="middle", weight="bold"))
    rows = [
        (75, 100, 900, 70, f"{total} handled records", "all candidate attempts plus administrative exclusions"),
        (145, 200, 760, 70, f"{scientific} scientific denominator units", f"{predictive} scored endpoints + {stops} protocol STOPs"),
        (230, 300, 300, 75, f"{predictive} scored endpoints", "2 favorable, 1 adverse"),
        (600, 300, 300, 75, f"{stops} protocol STOPs", "methods-integrity evidence, not negative results"),
        (375, 420, 300, 58, f"{admin} administrative exclusions", "outside the scientific denominator"),
    ]
    for x, y, w, h, title, subtitle in rows:
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="none" stroke="black" stroke-width="2"/>')
        parts.append(_svg_text(x + w / 2, y + 29, title, size=19, anchor="middle", weight="bold"))
        parts.append(_svg_text(x + w / 2, y + 52, subtitle, size=13, anchor="middle"))
    parts.append('<line x1="525" y1="170" x2="525" y2="196" stroke="black" stroke-width="2"/><polygon points="519,190 525,200 531,190" fill="black"/>')
    parts.append('<line x1="525" y1="270" x2="385" y2="296" stroke="black" stroke-width="2"/><polygon points="391,289 385,300 397,297" fill="black"/>')
    parts.append('<line x1="525" y1="270" x2="750" y2="296" stroke="black" stroke-width="2"/><polygon points="739,296 750,300 742,291" fill="black"/>')
    parts.append('<line x1="525" y1="270" x2="525" y2="416" stroke="black" stroke-width="1.5" stroke-dasharray="5,4"/>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _performance_svg(rows: list[dict[str, object]]) -> str:
    width, height = 1180, 540
    zero_x = 610
    max_abs = max(abs(float(row["augmented_minus_baseline"])) for row in rows)
    usable = 430.0
    scale = usable / max_abs
    y_positions = [155, 275, 395]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    parts.append('<rect width="100%" height="100%" fill="white"/>')
    parts.append(_svg_text(width / 2, 42, "Fresh paired predictive performance", size=26, anchor="middle", weight="bold"))
    parts.append(_svg_text(width / 2, 72, "Delta = augmented macro log loss − baseline macro log loss; lower is better", size=15, anchor="middle"))
    parts.append(f'<line x1="{zero_x}" y1="105" x2="{zero_x}" y2="455" stroke="black" stroke-width="2"/>')
    parts.append(_svg_text(zero_x - 210, 105, "Layer B improves", size=14, anchor="middle"))
    parts.append(_svg_text(zero_x + 210, 105, "Layer B worsens", size=14, anchor="middle"))
    for y, row in zip(y_positions, rows, strict=True):
        delta = float(row["augmented_minus_baseline"])
        length = abs(delta) * scale
        x = zero_x - length if delta < 0 else zero_x
        status = _status_short(str(row["terminal_status"]))
        rel = 100.0 * float(row["relative_log_loss_change"])
        system = str(row["system"])
        parts.append(_svg_text(35, y + 6, system, size=15, weight="bold"))
        parts.append(f'<rect x="{x:.2f}" y="{y - 18}" width="{max(2.0, length):.2f}" height="36" fill="#444"/>')
        annotation = (
            f"Δ={delta:+.6f}; {rel:+.1f}%; "
            f"augmented wins {row['augmented_heldout_wins']}/{row['heldout_units']} ({status})"
        )
        parts.append(_svg_text(35, y + 34, annotation, size=13))
    parts.append(_svg_text(zero_x, 493, "0", size=13, anchor="middle"))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _decoupling_svg(louisiana: dict[str, object]) -> str:
    width, height = 1120, 440
    baseline = float(louisiana["baseline_macro_log_loss"])
    augmented = float(louisiana["augmented_macro_log_loss"])
    delta = float(louisiana["augmented_minus_baseline"])
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    parts.append('<rect width="100%" height="100%" fill="white"/>')
    parts.append(_svg_text(width / 2, 42, "Layer A and Layer B answer different questions", size=26, anchor="middle", weight="bold"))
    parts.append('<rect x="55" y="110" width="430" height="215" rx="12" fill="none" stroke="black" stroke-width="2"/>')
    parts.append(_svg_text(270, 145, "Louisiana — Layer A", size=20, anchor="middle", weight="bold"))
    parts.append(_svg_text(270, 185, "6 frozen local worlds", size=17, anchor="middle"))
    parts.append(_svg_text(270, 220, "↓ later evidence", size=16, anchor="middle"))
    parts.append(_svg_text(270, 255, "0 local worlds survive", size=18, anchor="middle", weight="bold"))
    parts.append(_svg_text(270, 286, "external_open survives", size=15, anchor="middle"))
    parts.append('<rect x="635" y="110" width="430" height="215" rx="12" fill="none" stroke="black" stroke-width="2"/>')
    parts.append(_svg_text(850, 145, "Louisiana — Layer B", size=20, anchor="middle", weight="bold"))
    parts.append(_svg_text(850, 188, f"baseline log loss = {_fmt(baseline)}", size=16, anchor="middle"))
    parts.append(_svg_text(850, 220, f"augmented log loss = {_fmt(augmented)}", size=16, anchor="middle"))
    parts.append(_svg_text(850, 254, f"Δ = {delta:+.7f}; augmented wins 7/8", size=17, anchor="middle", weight="bold"))
    parts.append(_svg_text(850, 286, "small favorable predictive complement", size=15, anchor="middle"))
    parts.append('<line x1="485" y1="217" x2="625" y2="217" stroke="black" stroke-width="2" stroke-dasharray="7,5"/>')
    parts.append(_svg_text(width / 2, 375, "Structural falsification does not imply that one local mechanism was confirmed; predictive complementarity is a separate heldout question.", size=15, anchor="middle"))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _methods_results(
    rows: list[dict[str, object]], stops: list[dict[str, object]], admin: list[dict[str, object]], tampa: dict[str, object]
) -> str:
    azores, louisiana, tampa_row = rows
    placebo = dict(tampa["secondary_placebo"])
    stage_counts = Counter(str(item.get("terminal_stage", "unspecified")) for item in stops)
    common_stages = ", ".join(
        f"{stage.replace('_', ' ')} ({count})"
        for stage, count in sorted(stage_counts.items(), key=lambda pair: (-pair[1], pair[0]))[:6]
    )
    return f"""# EOG-WF paper-ready Methods and Results core

This file is generated from frozen repository evidence. It is a manuscript core, not a new analysis. The primary submission route fixed by the prospective decision ladder is **Methods in Ecology and Evolution**.

## Methods

### Two-layer estimand

Environmental Occupancy Geometry (EOG) separates exact structural inference from predictive compression. **Layer A** retains the auditable set of declared worlds compatible with the accumulated positive evidence, including world contraction and finite-universe falsification. **Layer B** maps the surviving world ensemble to the unchanged ten-feature `symmetric_world_support_summary_v1`, which is invariant to world labels and member order. Exact world identities are therefore retained for structural interpretation but are not exposed as supervised feature labels.

The predictive question was deliberately narrower than a claim of general superiority: for a fresh ecological endpoint, does the frozen Layer-B summary contain heldout information beyond the same strong conventional learner? Each paired comparison used the same learner and conventional baseline features in both arms; the augmented arm differed only by the ten frozen Layer-B columns. Primary performance was binary log loss, evaluated on prospectively frozen heldout units. Favorable, null and adverse terminal outcomes were accepted under rules fixed before the relevant response was opened.

### Prospective endpoint funnel and outcome firewall

Fresh endpoints were advanced through response-blind source, registry, geometry, effort/negative-semantics and estimability gates before biological response access. Terminal pre-response and pre-model STOPs were retained as methods-integrity evidence and were never reclassified as adverse Layer-B results. The final ledger contains **3 scored predictive endpoints, 31 scientific/protocol STOPs and 3 administrative exclusions**. The most frequent STOP classes included {common_stages}. Candidate hunting was prospectively hard-stopped after the first valid third predictive endpoint; a fourth endpoint is not permitted to improve the apparent result.

### Cross-ecosystem synthesis

The ecosystem/endpoint, not the individual row, was the unit of fresh replication. The preregistered synthesis reports each endpoint separately using baseline and augmented macro log loss, their paired difference, the relative log-loss change and heldout-unit wins. No row-level pooling, common-effect estimate or pooled significance test is used. The preregistered adverse mapping narrows the supported product boundary to `{BOUNDARY}`.

### Feature-count placebo

For the third endpoint only, a secondary response-independent ten-feature placebo control tested whether adding any ten columns could explain an apparent gain. The placebo was explicitly secondary and could not alter the primary favorable/null/adverse classification. Tampa used {int(placebo['replicates'])} placebo replicates with {int(placebo['feature_count'])} features each.

## Results

### Fresh paired predictive endpoints

**Azores yellow eel telemetry.** The augmented arm reduced macro log loss from {_fmt(float(azores['baseline_macro_log_loss']))} to {_fmt(float(azores['augmented_macro_log_loss']))}, a difference of {float(azores['augmented_minus_baseline']):+.7f} ({100.0 * float(azores['relative_log_loss_change']):+.1f}%). It won all {azores['heldout_units']} heldout blocks, giving a favorable terminal result.

**Southwest Louisiana King Rail passive acoustics.** Macro log loss changed from {_fmt(float(louisiana['baseline_macro_log_loss']))} to {_fmt(float(louisiana['augmented_macro_log_loss']))}, a difference of {float(louisiana['augmented_minus_baseline']):+.7f} ({100.0 * float(louisiana['relative_log_loss_change']):+.2f}%). The augmented arm won {louisiana['augmented_heldout_wins']}/{louisiana['heldout_units']} heldout occasions. Independently, all six frozen local Layer-A worlds were eventually falsified and only `external_open` survived. Thus a small favorable Layer-B gain can coexist with strong Layer-A structural falsification; the predictive result does not identify a local movement mechanism.

**Tampa Bay seagrass monitoring.** The valid third endpoint was adverse. Baseline macro log loss was {_fmt(float(tampa_row['baseline_macro_log_loss']))}, whereas the augmented arm reached {_fmt(float(tampa_row['augmented_macro_log_loss']))}; the difference was {float(tampa_row['augmented_minus_baseline']):+.7f} ({100.0 * float(tampa_row['relative_log_loss_change']):+.1f}%). The augmented arm won only {tampa_row['augmented_heldout_wins']}/{tampa_row['heldout_units']} folds. The secondary placebo median log loss was {_fmt(float(placebo['median_macro_log_loss']))}; the real augmented arm beat {100.0 * float(placebo['fraction_placebo_replicates_beaten_by_real_augmented']):.0f}% of placebo replicates. The placebo therefore does not rescue the real Layer-B augmentation and does not change the adverse primary classification.

### Cross-ecosystem interpretation

The three fresh endpoints are heterogeneous rather than uniformly favorable: two systems show non-redundant heldout information in the frozen Layer-B representation, whereas one shows substantial degradation. The evidence therefore supports **Layer A as an auditable structural compatibility/falsification framework and Layer B as a context-dependent predictive complement**. It does not support universal predictive superiority, a standalone Layer-B predictor, causal identification, a recovered dispersal history, or the truth of an exact Layer-A world.

### Candidate funnel

The 31 scientific/protocol STOPs document where a prospective endpoint could not satisfy its frozen data contract without post-outcome repair. Three additional records were administrative exclusions and remain outside the scientific denominator. These STOPs support the integrity of the validation design but provide no evidence for or against Layer-B predictive value.
"""


def build(output_dir: Path) -> dict[str, object]:
    ledger = _load(LEDGER)
    synthesis = _load(SYNTHESIS)
    tampa = _load(TAMPA_CERT)
    fresh, stops, admin = _validate_inputs(ledger, synthesis, tampa)
    rows = _endpoint_rows(fresh)

    output_dir.mkdir(parents=True, exist_ok=True)

    _write_csv(
        output_dir / "fresh_endpoint_results.csv",
        [
            "issue",
            "system",
            "endpoint",
            "observation_process",
            "terminal_status",
            "baseline_macro_log_loss",
            "augmented_macro_log_loss",
            "augmented_minus_baseline",
            "relative_log_loss_change",
            "augmented_heldout_wins",
            "heldout_units",
            "once_only_run_id",
        ],
        rows,
    )

    candidate_rows = _full_candidate_rows(fresh, stops, admin)
    _write_csv(
        output_dir / "candidate_flow_table.csv",
        [
            "issue",
            "system",
            "classification",
            "terminal_stage",
            "terminal_status_or_reason",
            "biological_response_access",
            "counts_as_predictive_evidence",
        ],
        candidate_rows,
    )

    stage_counts = Counter(str(item.get("terminal_stage", "unspecified")) for item in stops)
    stage_rows = [
        {"terminal_stage": stage, "scientific_stop_count": count}
        for stage, count in sorted(stage_counts.items(), key=lambda pair: (-pair[1], pair[0]))
    ]
    _write_csv(
        output_dir / "candidate_funnel_summary.csv",
        ["terminal_stage", "scientific_stop_count"],
        stage_rows,
    )

    (output_dir / "figure_1_two_layer_architecture.svg").write_text(
        _architecture_svg(BOUNDARY), encoding="utf-8"
    )
    (output_dir / "figure_2_candidate_funnel.svg").write_text(
        _funnel_svg(len(rows), len(stops), len(admin)), encoding="utf-8"
    )
    (output_dir / "figure_3_endpoint_performance.svg").write_text(
        _performance_svg(rows), encoding="utf-8"
    )
    (output_dir / "figure_4_louisiana_decoupling.svg").write_text(
        _decoupling_svg(rows[1]), encoding="utf-8"
    )
    (output_dir / "methods_results_core.md").write_text(
        _methods_results(rows, stops, admin, tampa), encoding="utf-8"
    )

    boundary = {
        "schema": "eog.paper_ready_eogwf_submission_boundary.v1",
        "fresh_predictive_endpoints_with_scores": len(rows),
        "favorable_endpoints": sum(row["terminal_status"] == FAVORABLE for row in rows),
        "adverse_endpoints": sum(row["terminal_status"] == ADVERSE for row in rows),
        "scientific_protocol_stops": len(stops),
        "administrative_exclusions": len(admin),
        "candidate_hunting_hard_stop": True,
        "fourth_fresh_endpoint_allowed": False,
        "product_boundary": BOUNDARY,
        "allowed_claim": synthesis["allowed_claim"],
        "primary_submission_route": synthesis["primary_submission_route"],
        "nature_ecology_evolution_trigger_open": synthesis["nature_ecology_evolution_trigger_open"],
        "primary_aggregation": "endpoint-wise; no row-level pooling or common-effect claim",
    }
    (output_dir / "submission_boundary.json").write_text(
        json.dumps(boundary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    readme = f"""# Paper-ready EOG-WF manuscript assets

These files are generated from the frozen fresh-endpoint synthesis, candidate-flow ledger and Tampa terminal certificate. They do not rerun biological response processing or model fitting.

## Frozen scientific boundary

- fresh scored endpoints: **3**;
- scientific/protocol STOPs: **31**;
- administrative exclusions: **3**;
- observed endpoint pattern: **favorable / favorable / adverse**;
- product boundary: `{BOUNDARY}`;
- candidate hunting: **hard-stopped**;
- primary submission route: **Methods in Ecology and Evolution**.

## Generated files

- `fresh_endpoint_results.csv` — manuscript endpoint table;
- `candidate_flow_table.csv` — full prospective candidate ledger projection;
- `candidate_funnel_summary.csv` — STOP counts by terminal stage;
- `figure_1_two_layer_architecture.svg` — Layer A / Layer B architecture;
- `figure_2_candidate_funnel.svg` — prospective validation denominator;
- `figure_3_endpoint_performance.svg` — endpoint-wise paired log-loss differences;
- `figure_4_louisiana_decoupling.svg` — structural falsification vs predictive complementarity;
- `methods_results_core.md` — evidence-backed Methods/Results core;
- `submission_boundary.json` — final claim and journal boundary;
- `generation_manifest.json` — input/output SHA-256 audit.

Rebuild with:

```bash
python manuscript/build_paper_ready_eogwf.py --output-dir build/paper_ready_eogwf
```
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")

    output_files = sorted(path for path in output_dir.iterdir() if path.is_file())
    manifest = {
        "schema": "eog.paper_ready_eogwf_generation_manifest.v1",
        "inputs": {
            str(LEDGER.relative_to(ROOT)): _sha256_file(LEDGER),
            str(SYNTHESIS.relative_to(ROOT)): _sha256_file(SYNTHESIS),
            str(TAMPA_CERT.relative_to(ROOT)): _sha256_file(TAMPA_CERT),
        },
        "outputs": {
            path.name: _sha256_file(path)
            for path in output_files
        },
    }
    (output_dir / "generation_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return boundary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    boundary = build(args.output_dir)
    print(json.dumps(boundary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
