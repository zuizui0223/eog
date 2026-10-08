from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
PAPER=ROOT/'manuscript'/'inferential_openness'/'MANUSCRIPT_DRAFT_V2.md'
HIGHLIGHTS=ROOT/'manuscript'/'inferential_openness'/'HIGHLIGHTS_ECOINF_V1.md'
BUILDER=ROOT/'manuscript'/'inferential_openness'/'build_figures_v1.py'

def test_keywords_and_highlights_match_elsevier_submission_limits():
    paper=PAPER.read_text(encoding='utf-8')
    m=re.search(r'\*\*Keywords:\*\*\s*(.+)',paper)
    assert m
    assert len([x for x in m.group(1).split(';') if x.strip()]) <= 6
    bullets=[line[2:] for line in HIGHLIGHTS.read_text(encoding='utf-8').splitlines() if line.startswith('- ')]
    assert len(bullets)==5
    assert all(len(x)<=85 for x in bullets)

def test_graphical_abstract_meets_frozen_elsevier_geometry():
    text=BUILDER.read_text(encoding='utf-8')
    assert 'svg_start(1500,600' in text
    assert 'translate(150 20)' in text

def test_submission_figures_render_with_frozen_denominator(tmp_path):
    """Execute the actual stdlib-only builder, not just search its source text."""
    import csv
    import json
    import subprocess
    import sys
    import xml.etree.ElementTree as ET

    out = tmp_path / "figures"
    subprocess.run(
        [
            sys.executable,
            str(BUILDER),
            "--candidate-flow", str(ROOT / "manuscript" / "paper_ready" / "candidate_flow_table.csv"),
            "--ledger", str(ROOT / "manuscript" / "inferential_openness" / "CROSS_PROJECT_EVIDENCE_LEDGER_V2.json"),
            "--output-dir", str(out),
        ],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    manifest = json.loads((out / "figure_manifest.json").read_text(encoding="utf-8"))
    assert (
        manifest["scientific_attempts"],
        manifest["scientific_stops"],
        manifest["scored_endpoints"],
        manifest["administrative_exclusions"],
    ) == (34, 31, 3, 3)
    assert manifest["grouped_barriers"] == {
        "Transport / source identity": 11,
        "Registry / geometry / time": 10,
        "Separation / linkage / schema": 8,
        "Semantic / covariate validity": 2,
    }
    assert manifest["response_access_among_stops"] == {
        "none": 29, "header_only": 1, "full_response_once": 1,
    }
    assert len(manifest["figures"]) == 4
    assert manifest["graphical_abstract"] == "graphical_abstract_inferential_openness.svg"
    for name in [*manifest["figures"], manifest["graphical_abstract"]]:
        assert (out / name).exists()
        assert ET.parse(out / name).getroot().tag == "{http://www.w3.org/2000/svg}svg"
    with (out / manifest["supplementary_table"]).open(encoding="utf-8", newline="") as fh:
        assert len(list(csv.DictReader(fh))) == 31
