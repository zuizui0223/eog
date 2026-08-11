#!/usr/bin/env python3
"""Build conceptual Figure 1 separating five spatial-analysis roles."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import textwrap
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "figures/figure_1_roles.json"
DEFAULT_OUT = ROOT / "figures/output"
DEFAULT_CAPTION = ROOT / "manuscript/figure_1_caption.md"
DEFAULT_ALT = ROOT / "manuscript/figure_1_accessibility.md"


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


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FigureContractError(message)


def validate_contract(contract_path: Path) -> tuple[dict[str, Any], Path]:
    contract = load_json(contract_path)
    require(
        contract.get("schema_version") == "eog_structural_figure1_roles_v1",
        "unexpected Figure 1 schema",
    )
    competitor_path = ROOT / str(contract.get("competitor_matrix_path", ""))
    require(competitor_path.is_file(), "competitor matrix is missing")
    require(
        git_blob_sha1(competitor_path) == contract.get("competitor_matrix_git_blob_sha1"),
        "competitor matrix fingerprint changed; Figure 1 semantics require review",
    )

    panels = contract.get("panels")
    require(isinstance(panels, list) and len(panels) == 5, "Figure 1 requires five panels")
    panel_ids = [panel.get("id") for panel in panels if isinstance(panel, dict)]
    require(panel_ids == contract.get("required_panel_ids"), "Figure 1 panel order changed")
    require(panel_ids == ["A", "B", "C", "D", "E"], "Figure 1 must retain A-E ordering")

    for panel in panels:
        require(isinstance(panel, dict), "panel entry must be an object")
        for key in ("title", "question", "role", "output"):
            require(isinstance(panel.get(key), str) and panel[key].strip(), f"panel {panel.get('id')} lacks {key}")

    constraints = contract.get("design_constraints", {})
    require(constraints.get("movement_arrows") is False, "movement arrows are prohibited")
    require(constraints.get("shared_effect_axis") is False, "Figure 1 cannot imply a shared effect scale")
    require(constraints.get("empirical_effect_sizes") is False, "Figure 1 must remain conceptual")
    require(constraints.get("causal_ordering") is False, "Figure 1 cannot imply causal ordering")

    combined = " ".join(
        str(panel[key])
        for panel in panels
        for key in ("title", "question", "role", "output")
    ).lower()
    for phrase in contract.get("prohibited_implications", []):
        require(str(phrase).lower() not in combined, f"prohibited implication appears in Figure 1 contract: {phrase}")
    return contract, competitor_path


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def wrap(text: str, width: int) -> list[str]:
    return textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False) or [""]


def text_svg(
    x: float,
    y: float,
    lines: list[str],
    *,
    size: int = 14,
    weight: int = 400,
    fill: str = "#172033",
    anchor: str = "start",
    gap: int = 18,
) -> str:
    spans = []
    for index, line in enumerate(lines):
        dy = 0 if index == 0 else gap
        spans.append(f'<tspan x="{x}" dy="{dy}">{esc(line)}</tspan>')
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
        f'text-anchor="{anchor}" fill="{fill}">' + "".join(spans) + "</text>"
    )


def line(x1: float, y1: float, x2: float, y2: float, *, stroke: str = "#6b7280", width: int = 3, dash: str = "") -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{width}"{dash_attr}/>'


def circle(cx: float, cy: float, r: float, *, fill: str, stroke: str = "#172033", width: int = 2) -> str:
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'


def panel_a(x: float, y: float) -> list[str]:
    out = []
    for px in (x + 76, x + 206):
        out.append(f'<rect x="{px}" y="{y+70}" width="86" height="74" rx="10" fill="#eef4ff" stroke="#2b6cb0" stroke-width="2"/>')
        out.append(f'<rect x="{px+14}" y="{y+98}" width="58" height="13" rx="6" fill="#2b6cb0"/>')
    out.append(text_svg(x + 184, y + 169, ["equal local support"], size=12, anchor="middle", fill="#5c667a"))
    out.append(line(x + 83, y + 182, x + 285, y + 182, stroke="#cbd5e1", width=2, dash="6 5"))
    return out


def panel_b(x: float, y: float) -> list[str]:
    out = []
    cell = 39
    x0, y0 = x + 83, y + 54
    for row in range(4):
        for col in range(5):
            held = col >= 3
            fill = "#fef3c7" if held else "#e8f5ee"
            stroke = "#b7791f" if held else "#2f855a"
            out.append(f'<rect x="{x0+col*cell}" y="{y0+row*cell}" width="{cell-3}" height="{cell-3}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
    out.append(text_svg(x0 + 37, y0 + 178, ["training blocks"], size=11, anchor="middle", fill="#2f855a"))
    out.append(text_svg(x0 + 156, y0 + 178, ["held-out blocks"], size=11, anchor="middle", fill="#b7791f"))
    return out


def panel_c(x: float, y: float) -> list[str]:
    out = []
    anchor_x, anchor_y = x + 86, y + 116
    out.append(circle(anchor_x, anchor_y, 13, fill="#2f855a"))
    out.append(text_svg(anchor_x, anchor_y + 31, ["training anchor"], size=10, anchor="middle", fill="#5c667a"))
    targets = [(x + 280, y + 82), (x + 280, y + 152)]
    for tx, ty in targets:
        out.append(f'<rect x="{tx-12}" y="{ty-12}" width="24" height="24" rx="4" fill="#eef4ff" stroke="#2b6cb0" stroke-width="2"/>')
        out.append(line(anchor_x + 15, anchor_y, tx - 15, ty, stroke="#8b95a7", width=2, dash="7 5"))
    for step_x, step_y in ((x + 150, y + 105), (x + 205, y + 92)):
        out.append(circle(step_x, step_y, 6, fill="#ffffff", stroke="#64748b", width=1))
    out.append(text_svg(x + 183, y + 188, ["same direct source distance;", "different intermediate configuration"], size=11, anchor="middle", fill="#5c667a", gap=15))
    return out


def panel_d(x: float, y: float) -> list[str]:
    out = []
    x0, y0, cell = x + 68, y + 45, 34
    resistance = [
        [0, 0, 1, 2, 2, 2, 1],
        [0, 1, 1, 2, 2, 1, 0],
        [0, 1, 2, 3, 2, 1, 0],
        [0, 0, 1, 2, 1, 0, 0],
    ]
    fills = ["#f1f5f9", "#dbeafe", "#bfdbfe", "#94a3b8"]
    for row, values in enumerate(resistance):
        for col, level in enumerate(values):
            out.append(f'<rect x="{x0+col*cell}" y="{y0+row*cell}" width="{cell-2}" height="{cell-2}" fill="{fills[level]}"/>')
    out.append(circle(x0 + 7, y0 + 65, 9, fill="#2f855a"))
    out.append(circle(x0 + 6*cell + 23, y0 + 65, 9, fill="#b7791f"))
    paths = [
        [(x0+13, y0+65), (x0+85, y0+35), (x0+155, y0+45), (x0+6*cell+15, y0+65)],
        [(x0+13, y0+65), (x0+85, y0+103), (x0+155, y0+100), (x0+6*cell+15, y0+65)],
    ]
    for points in paths:
        coords = " ".join(f"{px},{py}" for px, py in points)
        out.append(f'<polyline points="{coords}" fill="none" stroke="#7c3aed" stroke-width="3" opacity="0.8"/>')
    out.append(text_svg(x + 185, y + 191, ["declared resistance surface; multiple paths"], size=11, anchor="middle", fill="#5c667a"))
    return out


def panel_e(x: float, y: float) -> list[str]:
    out = []
    labels = ["scenario 1", "scenario 2", "scenario 3"]
    for index, label in enumerate(labels):
        sx = x + 44 + index * 108
        sy = y + 66
        out.append(text_svg(sx + 42, sy - 13, [label], size=9, anchor="middle", fill="#5c667a"))
        out.append(circle(sx + 6, sy + 44, 8, fill="#2f855a"))
        out.append(f'<rect x="{sx+70}" y="{sy+36}" width="16" height="16" rx="3" fill="#eef4ff" stroke="#2b6cb0" stroke-width="2"/>')
        if index != 1:
            out.append(line(sx + 16, sy + 44, sx + 68, sy + 44, stroke="#2b6cb0", width=3))
            out.append(circle(sx + 42, sy + 44, 5, fill="#ffffff", stroke="#64748b", width=1))
        else:
            out.append(line(sx + 16, sy + 44, sx + 38, sy + 44, stroke="#94a3b8", width=2, dash="5 4"))
            out.append(line(sx + 48, sy + 44, sx + 68, sy + 44, stroke="#94a3b8", width=2, dash="5 4"))
    out.append(text_svg(x + 185, y + 174, ["connected frequency = share of", "predeclared scenarios with connection"], size=11, anchor="middle", fill="#5c667a", gap=15))
    return out


def render_panel(panel: dict[str, Any], x: float, y: float, width: float, height: float) -> list[str]:
    panel_id = panel["id"]
    out = [
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="18" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>',
        circle(x + 27, y + 27, 16, fill="#172033", stroke="#172033"),
        text_svg(x + 27, y + 33, [panel_id], size=14, weight=700, fill="#ffffff", anchor="middle"),
        text_svg(x + 54, y + 32, [panel["title"]], size=18, weight=700),
        text_svg(x + 24, y + height - 100, wrap(panel["question"], 45), size=13, weight=700, fill="#334155", gap=16),
        text_svg(x + 24, y + height - 55, wrap("Output: " + panel["output"], 48), size=12, fill="#5c667a", gap=15),
    ]
    if panel_id == "A":
        out.extend(panel_a(x, y))
    elif panel_id == "B":
        out.extend(panel_b(x, y))
    elif panel_id == "C":
        out.extend(panel_c(x, y))
    elif panel_id == "D":
        out.extend(panel_d(x, y))
    elif panel_id == "E":
        out.extend(panel_e(x, y))
    return out


def render_svg(contract: dict[str, Any]) -> str:
    width, height = 1600, 1120
    panels = contract["panels"]
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="1600" height="1120" fill="#f8fafc"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif}</style>',
        text_svg(60, 58, ["Figure 1 | Distinct spatial roles in the structural EOG workflow"], size=29, weight=700),
        text_svg(60, 91, ["These quantities can coexist in one analysis, but they answer different questions and are not interchangeable."], size=16, fill="#5c667a"),
    ]
    positions = [
        (55, 130, 480, 405),
        (560, 130, 480, 405),
        (1065, 130, 480, 405),
        (305, 565, 480, 405),
        (815, 565, 480, 405),
    ]
    for panel, position in zip(panels, positions):
        out.extend(render_panel(panel, *position))

    out.append(text_svg(800, 1020, ["No panel is a movement, dispersal, or colonisation probability."], size=15, weight=700, anchor="middle", fill="#334155"))
    out.append(text_svg(800, 1047, ["Figure 1 defines semantics; Figures 2–4 provide the frozen empirical evidence."], size=14, anchor="middle", fill="#5c667a"))
    out.append("</svg>")
    svg = "\n".join(out) + "\n"
    require("marker-end" not in svg and "marker-start" not in svg, "Figure 1 cannot contain arrow markers")
    lower = svg.lower()
    for phrase in contract.get("prohibited_implications", []):
        require(str(phrase).lower() not in lower, f"prohibited implication rendered: {phrase}")
    return svg


def caption_text(contract: dict[str, Any]) -> str:
    panels = contract["panels"]
    sentences = [
        "# Figure 1 caption",
        "",
        "**Figure 1 | Distinct spatial roles in the structural EOG workflow.**",
        "The five panels are deliberately non-sequential: they separate quantities that can be used together but answer different questions.",
    ]
    for panel in panels:
        sentences.append(f"**{panel['id']}, {panel['title']}.** {panel['role']}")
    sentences.extend([
        "The figure is conceptual and contains no empirical effect size or causal ordering.",
        "In particular, occurrence-anchored connected frequency is a structural robustness diagnostic across predeclared graph scenarios, not a movement, dispersal, or colonisation probability.",
        "",
    ])
    return "\n\n".join(sentences)


def accessibility_text(contract: dict[str, Any]) -> str:
    lines = [
        "# Figure 1 accessibility description",
        "",
        "A five-panel conceptual figure separates environmental support, spatial evaluation, source proximity, matrix-aware connectivity, and occurrence-anchored EOG configuration.",
    ]
    for panel in contract["panels"]:
        lines.append(f"Panel {panel['id']} is titled '{panel['title']}' and asks: {panel['question']} Its declared output is {panel['output']}.")
    lines.append("The panels are arranged as distinct roles rather than as a causal or movement sequence, and no arrows are used to imply movement.")
    return "\n\n".join(lines) + "\n"


def build(contract_path: Path, out_dir: Path, caption_path: Path, alt_path: Path) -> dict[str, Any]:
    contract, competitor_path = validate_contract(contract_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    svg_path = out_dir / "figure_1_roles.svg"
    metadata_path = out_dir / "figure_1_metadata.json"
    svg_path.write_text(render_svg(contract), encoding="utf-8")
    caption_path.parent.mkdir(parents=True, exist_ok=True)
    caption_path.write_text(caption_text(contract), encoding="utf-8")
    alt_path.write_text(accessibility_text(contract), encoding="utf-8")
    metadata = {
        "figure_id": "figure_1_roles",
        "schema_version": contract["schema_version"],
        "conceptual_only": True,
        "panel_ids": contract["required_panel_ids"],
        "contract_sha256": sha256(contract_path),
        "competitor_matrix_git_blob_sha1": git_blob_sha1(competitor_path),
        "svg_sha256": sha256(svg_path),
        "movement_arrows": False,
        "empirical_effect_sizes": False,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
    metadata = build(args.contract, args.out_dir, args.caption, args.accessibility)
    print(json.dumps(metadata, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
