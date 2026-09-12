#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import html
import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = ROOT / "manuscript/STRUCTURAL_ISLAND_PAPER_BOUNDARY_V1.json"
OUT_SVG = ROOT / "figures/output/figure_1_reference_conditioned.svg"
OUT_META = ROOT / "figures/output/figure_1_reference_conditioned_metadata.json"
OUT_CAPTION = ROOT / "manuscript/figure_1_reference_conditioned_caption.md"
OUT_ALT = ROOT / "manuscript/figure_1_reference_conditioned_accessibility.md"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def wrap(text: str, width: int) -> list[str]:
    return textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False) or [""]


def text(x: float, y: float, lines: list[str], *, size: int = 16, weight: int = 400, anchor: str = "start", fill: str = "#172033", gap: int = 21) -> str:
    spans = []
    for i, line in enumerate(lines):
        spans.append(f'<tspan x="{x}" dy="{0 if i == 0 else gap}">{esc(line)}</tspan>')
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{fill}">' + "".join(spans) + "</text>"


def load_boundary() -> dict:
    boundary = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    assert boundary["schema"] == "eog.structural_island_paper_boundary.v1"
    assert boundary["status"] == "scientific_content_closed_presentation_release_active"
    assert boundary["non_overlap_with_eog_wf_paper"]["structural_paper_empirical_denominator_is_separate"] is True
    return boundary


def render(boundary: dict) -> str:
    W, H = 1600, 900
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
        '<title id="title">Reference-conditioned structural adequacy framework</title>',
        '<desc id="desc">A declared reference is frozen first. A held-out structural probe is then added without held-out labels entering feature construction. The increment is interpreted as earned, redundant or adverse, or indeterminate. The framework does not treat the structural probe as movement probability.</desc>',
        '<style>text{font-family:Arial,Helvetica,sans-serif}.box{fill:#fff;stroke:#cbd5e1;stroke-width:2}.stage{font-size:23px;font-weight:700}.body{font-size:16px}.small{font-size:13px}.arrow{stroke:#64748b;stroke-width:4;fill:none}.divider{stroke:#cbd5e1;stroke-width:2}</style>',
        '<rect width="1600" height="900" fill="#f8fafc"/>',
        text(65, 60, ["Figure 1 | Structural information is conditional on the declared reference"], size=30, weight=700),
        text(65, 96, ["The same structural feature can earn an increment under one reference and fail under a richer one."], size=17, fill="#526070"),
    ]

    boxes = [(70, 165, 420, 390), (590, 165, 420, 390), (1110, 165, 420, 390)]
    for x, y, w, h in boxes:
        parts.append(f'<rect class="box" x="{x}" y="{y}" width="{w}" height="{h}" rx="20"/>')

    # Stage 1
    x, y, w, h = boxes[0]
    parts.append(text(x+30, y+50, ["1  Declare the reference R"], size=23, weight=700))
    parts.append(text(x+30, y+94, wrap("Represent information that already belongs in the comparator before asking what structure adds.", 44), size=16, gap=22))
    rows = [
        ("Local support", "climate / habitat / recipient state"),
        ("Direct source context", "nearest source / multi-source pressure"),
        ("Generic landscape context", "area / mainland isolation / stepping stones / network position"),
        ("Landscape-specific reference", "e.g. matrix-aware current flow when available"),
    ]
    yy = y + 190
    for title_, detail in rows:
        parts.append(f'<rect x="{x+30}" y="{yy-24}" width="{w-60}" height="54" rx="10" fill="#f1f5f9"/>')
        parts.append(text(x+45, yy-2, [title_], size=14, weight=700))
        parts.append(text(x+45, yy+17, [detail], size=12, fill="#526070"))
        yy += 66

    # Stage 2
    x, y, w, h = boxes[1]
    parts.append(text(x+30, y+50, ["2  Add the held-out structural probe C"], size=23, weight=700))
    parts.append(text(x+30, y+94, wrap("Construct the occurrence-conditioned structural feature only from outer-training information under predeclared graph assumptions.", 44), size=16, gap=22))
    parts.append(f'<rect x="{x+70}" y="{y+185}" width="{w-140}" height="120" rx="18" fill="#eef6ff" stroke="#4f79a7" stroke-width="2"/>')
    parts.append(text(x+w/2, y+222, ["EOG connected frequency"], size=19, weight=700, anchor="middle"))
    parts.append(text(x+w/2, y+254, ["share of frozen graph scenarios"], size=14, anchor="middle", fill="#526070"))
    parts.append(text(x+w/2, y+278, ["linking target to training-presence anchors"], size=14, anchor="middle", fill="#526070"))
    parts.append(text(x+42, y+345, wrap("Held-out labels do not define anchors, scales, graph choices or predictor construction.", 47), size=14, weight=700, fill="#334155", gap=19))

    # Stage 3
    x, y, w, h = boxes[2]
    parts.append(text(x+30, y+50, ["3  Score C relative to R"], size=23, weight=700))
    parts.append(text(x+30, y+92, ["Use the same held-out units and the predeclared endpoint."], size=16))
    outcomes = [
        ("EARNED", "C improves the declared held-out endpoint", "#e8f5ee", "#2f855a"),
        ("REDUNDANT / NULL", "C adds no supported increment beyond R", "#f8fafc", "#64748b"),
        ("ADVERSE", "C worsens the declared held-out endpoint", "#fff1f2", "#b94a48"),
        ("INDETERMINATE", "reference or estimability gate fails", "#fff8e8", "#b7791f"),
    ]
    yy = y + 155
    for title_, detail, fill, stroke in outcomes:
        parts.append(f'<rect x="{x+30}" y="{yy}" width="{w-60}" height="67" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        parts.append(text(x+48, yy+26, [title_], size=14, weight=700, fill=stroke))
        parts.append(text(x+48, yy+49, [detail], size=12, fill="#334155"))
        yy += 78

    # arrows
    parts.append('<path class="arrow" d="M 500 360 L 570 360"/>')
    parts.append('<polygon points="570,360 552,349 552,371" fill="#64748b"/>')
    parts.append('<path class="arrow" d="M 1020 360 L 1090 360"/>')
    parts.append('<polygon points="1090,360 1072,349 1072,371" fill="#64748b"/>')

    # Bottom boundary
    parts.append('<line class="divider" x1="70" y1="625" x2="1530" y2="625"/>')
    parts.append(text(800, 670, ["Interpretation boundary"], size=20, weight=700, anchor="middle"))
    parts.append(text(800, 708, ["A positive structural signal under a restricted reference does not imply predictive gain beyond a richer reference."], size=17, weight=700, anchor="middle"))
    parts.append(text(800, 744, ["Connected frequency is a structural robustness summary — not a dispersal, movement or colonisation probability."], size=16, anchor="middle", fill="#526070"))
    parts.append(text(800, 808, ["This paper asks when structure earns an increment. The separate EOG-WF paper asks a different finite-world falsification / prediction-interface question."], size=14, anchor="middle", fill="#526070"))
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def build_assets() -> dict[str, str]:
    boundary = load_boundary()
    svg = render(boundary)
    caption = (
        "**Figure 1. Reference-conditioned structural adequacy.** A structural feature is not evaluated in isolation. "
        "First, a declared reference R represents the local, source and generic landscape information already available to the comparator. "
        "Second, the occurrence-conditioned structural probe C is constructed from outer-training information under frozen graph assumptions, without held-out labels entering feature construction. "
        "Third, C is scored on the same held-out units relative to R and can be classified as earned, redundant/null, adverse, or indeterminate under the predeclared endpoint and gates. "
        "The framework therefore treats the value of landscape configuration as reference-conditioned. Connected frequency is a structural robustness summary over declared graph scenarios, not a probability of movement, dispersal or colonisation.\n"
    )
    alt = (
        "**Figure 1 accessibility description.** Three large boxes run from left to right. The first box is the declared reference R and lists local environmental support, direct source context, generic landscape context and, where available, landscape-specific connectivity. The second box is the held-out structural probe C, represented by EOG connected frequency constructed only from outer-training occurrence anchors and frozen graph assumptions. The third box lists four possible outcomes when C is scored relative to R on the same held-out units: earned, redundant or null, adverse, and indeterminate. A bottom statement explains that a positive structural signal under a restricted reference does not guarantee predictive gain beyond a richer reference and that connected frequency is not a movement or colonisation probability.\n"
    )
    meta = {
        "schema": "eog.structural_figure1_reference_conditioned.v1",
        "boundary_schema": boundary["schema"],
        "conceptual_only": True,
        "movement_probability": False,
        "causal_sequence_claim": False,
        "separate_from_eog_wf_empirical_denominator": True,
        "svg_sha256": sha256_bytes(svg.encode()),
        "caption_sha256": sha256_bytes(caption.encode()),
        "accessibility_sha256": sha256_bytes(alt.encode()),
    }
    return {
        str(OUT_SVG.relative_to(ROOT)): svg,
        str(OUT_META.relative_to(ROOT)): json.dumps(meta, indent=2, sort_keys=True) + "\n",
        str(OUT_CAPTION.relative_to(ROOT)): caption,
        str(OUT_ALT.relative_to(ROOT)): alt,
    }


def main() -> None:
    for relative, content in build_assets().items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print("wrote reference-conditioned Figure 1 assets")


if __name__ == "__main__":
    main()
