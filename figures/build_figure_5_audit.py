#!/usr/bin/env python3
"""Build Figure 5: frozen source-to-result audit trail for the structural manuscript."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import textwrap
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "figures/figure_5_audit_contract.json"
DEFAULT_OUT = ROOT / "figures/output"
DEFAULT_CAPTION = ROOT / "manuscript/figure_5_caption.md"
DEFAULT_ALT = ROOT / "manuscript/figure_5_accessibility.md"


class AuditContractError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditContractError(message)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditContractError(f"cannot read valid JSON from {path}: {exc}") from exc
    require(isinstance(value, dict), f"expected JSON object in {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def short(value: str, n: int = 12) -> str:
    value = str(value)
    if value.startswith("sha256:"):
        return "sha256:" + value.split(":", 1)[1][:n]
    return value[:n]


def validate_contract(contract_path: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    contract = load_json(contract_path)
    require(contract.get("schema_version") == "eog_structural_figure5_audit_v1", "unexpected Figure 5 schema")
    rows = contract.get("rows")
    require(isinstance(rows, list) and len(rows) == 5, "Figure 5 requires five audit rows")
    require([row.get("id") for row in rows] == contract.get("required_row_ids"), "Figure 5 audit row order changed")
    constraints = contract.get("design_constraints", {})
    require(constraints == {"new_effect_sizes": False, "new_hypothesis_tests": False, "movement_arrows": False, "causal_arrows": False}, "Figure 5 design constraints changed")

    figure_manifest = load_json(ROOT / contract["figure_manifest"])
    result_manifest = load_json(ROOT / contract["results_table_manifest"])
    result_metadata = load_json(ROOT / contract["results_table_metadata"])
    require(figure_manifest.get("schema_version") == "eog_structural_figure_manifest_v1", "unexpected figure manifest schema")
    require(result_manifest.get("schema_version") == "eog_structural_results_tables_v2", "unexpected results-table manifest schema")
    require(result_metadata.get("schema_version") == "eog_structural_results_tables_v2", "unexpected results-table metadata schema")
    return contract, figure_manifest, result_manifest, result_metadata


def build_records(contract: dict[str, Any], figure_manifest: dict[str, Any], result_manifest: dict[str, Any], result_metadata: dict[str, Any]) -> list[dict[str, str]]:
    f1 = figure_manifest["figure_1_roles"]["expected"]
    f2 = figure_manifest["figure_2_aislands"]["expected"]
    f3 = figure_manifest["figure_3_tanzania"]["expected"]
    f4 = figure_manifest["figure_4_boundary"]["expected"]

    source_ids = {
        "F1": f"matrix {short(f1['competitor_matrix_git_blob_sha1'])}; contract {short(f1['contract_sha256'])}",
        "F2": f"primary {short(f2['primary_artifact_digest'])}; secondary {short(f2['secondary_artifact_digest'])}; bottleneck {short(f2['bottleneck_artifact_digest'])}",
        "F3": f"artifact {short(f3['artifact_digest'])}; result {short(f3['result_fingerprint'])}; library {short(f3['candidate_library_fingerprint'])}",
        "F4": f"A {short(f4['aislands_summary_sha256'])}; T {short(f4['tanzania_result_fingerprint'])}",
        "T3": f"A sidecar {short(result_manifest['inputs']['aislands_mode_estimates']['sha256'])}; A strong {short(result_manifest['inputs']['aislands_strong_reference']['result_fingerprint'])}; T {short(result_manifest['inputs']['tanzania_expected']['result_fingerprint'])}",
    }

    records: list[dict[str, str]] = []
    for row in contract["rows"]:
        result_path = ROOT / row["result_path"]
        require(result_path.is_file(), f"missing audited result: {result_path}")
        transform_root = ROOT / ("manuscript" if row["id"] == "T3" else "figures")
        transform_path = transform_root / row["transform"]
        require(transform_path.is_file(), f"missing audited transform: {transform_path}")
        result_hash = sha256(result_path)

        if row["id"] == "F1":
            require(result_hash == f1["svg_sha256"], "Figure 1 SVG fingerprint mismatch")
        elif row["id"] == "T3":
            expected = result_metadata["outputs"][result_path.name]
            require(result_hash == expected, "Table 3 fingerprint mismatch")
            require(result_metadata["tanzania_result_fingerprint"] == f3["result_fingerprint"], "Tanzania table/figure fingerprint mismatch")
            require(result_metadata["aislands_species_output_sha256"] == f2["primary_species_table_sha256"], "A-Islands table/figure fingerprint mismatch")
            require(result_metadata["aislands_strong_reference_result_fingerprint"] == result_manifest["inputs"]["aislands_strong_reference"]["result_fingerprint"], "A-Islands strong-reference table fingerprint mismatch")

        records.append({
            "id": row["id"],
            "label": row["label"],
            "source": source_ids[row["id"]],
            "transform": row["transform"],
            "result": row["result"],
            "result_sha256": result_hash,
        })
    return records


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def wrap(text: str, width: int) -> list[str]:
    return textwrap.wrap(str(text), width=width, break_long_words=False, break_on_hyphens=False) or [""]


def text_svg(x: float, y: float, lines: list[str], *, size: int = 14, weight: int = 400, fill: str = "#172033", gap: int = 18) -> str:
    spans = []
    for index, line in enumerate(lines):
        spans.append(f'<tspan x="{x}" dy="{0 if index == 0 else gap}">{esc(line)}</tspan>')
    return f'<text x="{x}" y="{y}" font-family="Arial,Helvetica,sans-serif" font-size="{size}" font-weight="{weight}" fill="{fill}">' + "".join(spans) + "</text>"


def render_svg(contract: dict[str, Any], records: list[dict[str, str]]) -> str:
    width, height = 1600, 930
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="1600" height="930" fill="#f8fafc"/>',
        text_svg(60, 62, ["Figure 5 | Frozen evidence-to-result audit trail"], size=29, weight=700),
        text_svg(60, 96, ["Fingerprints make provenance inspectable; they are not ecological effect sizes or causal evidence."], size=16, fill="#5c667a"),
    ]
    x = [60, 265, 725, 1080]
    headers = ["Output", "Frozen evidence / contract", "Committed transform", "Result fingerprint"]
    for hx, header in zip(x, headers):
        out.append(text_svg(hx, 145, [header], size=15, weight=700, fill="#334155"))
    out.append('<line x1="55" y1="160" x2="1545" y2="160" stroke="#94a3b8" stroke-width="2"/>')

    y0, row_h = 190, 126
    for idx, record in enumerate(records):
        y = y0 + idx * row_h
        fill = "#ffffff" if idx % 2 == 0 else "#f1f5f9"
        out.append(f'<rect x="55" y="{y-20}" width="1490" height="108" rx="10" fill="{fill}" stroke="#d7dee8"/>')
        out.append(text_svg(x[0], y + 12, [record["id"], record["label"]], size=14, weight=700, gap=19))
        out.append(text_svg(x[1], y + 7, wrap(record["source"], 55), size=13, fill="#334155", gap=17))
        out.append(text_svg(x[2], y + 7, wrap(record["transform"], 38), size=13, fill="#334155", gap=17))
        out.append(text_svg(x[3], y + 2, wrap(record["result"], 45), size=13, weight=700, fill="#334155", gap=17))
        out.append(text_svg(x[3], y + 43, ["sha256:" + record["result_sha256"][:20]], size=12, fill="#64748b"))

    out.append(text_svg(60, 850, wrap(contract["claim_boundary"], 150), size=14, weight=700, fill="#334155", gap=18))
    out.append(text_svg(60, 892, ["No new model fit, effect size, hypothesis test, movement route, or causal ordering is introduced in this figure."], size=13, fill="#5c667a"))
    out.append("</svg>")
    svg = "\n".join(out) + "\n"
    require("marker-end" not in svg and "marker-start" not in svg, "Figure 5 cannot contain arrow markers")
    return svg


def caption_text(contract: dict[str, Any], records: list[dict[str, str]]) -> str:
    return (
        "# Figure 5 caption\n\n"
        "**Figure 5 | Frozen evidence-to-result audit trail.** "
        "Each row links a manuscript output to its frozen evidence or semantic contract, the committed transform that builds the output, and the resulting SHA-256 fingerprint. "
        "Figure 1 is additionally pinned to the competitor-matrix Git blob; Figure 2 records the three frozen original A-Islands artifact digests; Figure 3 records the Tanzania artifact, result fingerprint, and candidate-library fingerprint; Figure 4 records the two benchmark projections; and Table 3/Table S1 records the original A-Islands sidecar, prospective A-Islands strong-reference fingerprint, and Tanzania benchmark fingerprint. "
        + contract["claim_boundary"]
        + " The audit trail establishes provenance and rebuildability only.\n"
    )


def accessibility_text(records: list[dict[str, str]]) -> str:
    lines = [
        "# Figure 5 accessibility description",
        "",
        "A five-row audit table shows how each main structural-manuscript output is linked to frozen evidence, a committed transform script, and a result fingerprint.",
    ]
    for record in records:
        lines.append(f"{record['id']} is {record['label']}; its transform is {record['transform']} and its displayed result fingerprint begins sha256:{record['result_sha256'][:20]}.")
    lines.append("The figure has no movement or causal arrows and introduces no new effect size or hypothesis test.")
    return "\n\n".join(lines) + "\n"


def build(contract_path: Path = DEFAULT_CONTRACT, out_dir: Path = DEFAULT_OUT, caption_path: Path = DEFAULT_CAPTION, alt_path: Path = DEFAULT_ALT) -> dict[str, Any]:
    contract, figure_manifest, result_manifest, result_metadata = validate_contract(contract_path)
    records = build_records(contract, figure_manifest, result_manifest, result_metadata)
    out_dir.mkdir(parents=True, exist_ok=True)
    svg_path = out_dir / "figure_5_audit.svg"
    svg_path.write_text(render_svg(contract, records), encoding="utf-8")
    caption_path.parent.mkdir(parents=True, exist_ok=True)
    caption_path.write_text(caption_text(contract, records), encoding="utf-8")
    alt_path.write_text(accessibility_text(records), encoding="utf-8")
    metadata = {
        "figure_id": "figure_5_audit",
        "schema_version": contract["schema_version"],
        "contract_sha256": sha256(contract_path),
        "figure_manifest_sha256": sha256(ROOT / contract["figure_manifest"]),
        "results_table_manifest_sha256": sha256(ROOT / contract["results_table_manifest"]),
        "rows": records,
        "svg_sha256": sha256(svg_path),
        "new_effect_sizes": False,
        "new_hypothesis_tests": False,
        "movement_arrows": False,
        "causal_arrows": False,
    }
    (out_dir / "figure_5_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--caption", type=Path, default=DEFAULT_CAPTION)
    parser.add_argument("--accessibility", type=Path, default=DEFAULT_ALT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(json.dumps(build(args.contract, args.out_dir, args.caption, args.accessibility), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
