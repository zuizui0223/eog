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
