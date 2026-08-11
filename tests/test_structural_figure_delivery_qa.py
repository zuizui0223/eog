from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manuscript/submission/submission_manifest.json"
SVG_NS = "http://www.w3.org/2000/svg"


def numeric(value: str) -> float:
    match = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)(?:px)?\s*", value)
    assert match is not None, value
    return float(match.group(1))


def test_submission_figure_paths_are_valid_self_contained_svgs() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    figures = manifest["figure_files"]
    assert len(figures) == 5
    assert len(set(figures)) == 5
    for relative in figures:
        path = ROOT / relative
        assert path.suffix.lower() == ".svg"
        assert path.is_file(), relative
        root = ET.fromstring(path.read_text(encoding="utf-8"))
        assert root.tag == f"{{{SVG_NS}}}svg"
        assert numeric(root.attrib["width"]) > 0
        assert numeric(root.attrib["height"]) > 0
        viewbox = [float(item) for item in root.attrib["viewBox"].split()]
        assert len(viewbox) == 4
        assert viewbox[2] > 0 and viewbox[3] > 0

        # No external raster/image assets or network dependencies are allowed in
        # the manuscript SVGs; every scientific element must be self-contained.
        assert not root.findall(f".//{{{SVG_NS}}}image")
        for element in root.iter():
            for key, value in element.attrib.items():
                lowered = value.lower()
                assert not lowered.startswith("http://"), (relative, key, value)
                assert not lowered.startswith("https://"), (relative, key, value)


def test_figure_text_does_not_drop_below_internal_minimum() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for relative in manifest["figure_files"]:
        root = ET.fromstring((ROOT / relative).read_text(encoding="utf-8"))
        font_sizes = []
        for element in root.findall(f".//{{{SVG_NS}}}text"):
            if "font-size" in element.attrib:
                font_sizes.append(numeric(element.attrib["font-size"]))
        assert font_sizes, relative
        assert min(font_sizes) >= 9.0, (relative, min(font_sizes))


def test_every_figure_has_caption_and_accessibility_prose() -> None:
    for number in range(1, 6):
        caption = ROOT / f"manuscript/figure_{number}_caption.md"
        accessibility = ROOT / f"manuscript/figure_{number}_accessibility.md"
        assert caption.is_file(), caption
        assert accessibility.is_file(), accessibility
        caption_text = caption.read_text(encoding="utf-8")
        accessibility_text = accessibility.read_text(encoding="utf-8")
        assert len(re.findall(r"\b[\w’'-]+\b", caption_text)) >= 25
        assert len(re.findall(r"\b[\w’'-]+\b", accessibility_text)) >= 25
        lowered = (caption_text + "\n" + accessibility_text).lower()
        assert "colonisation probability" not in lowered
        assert "dispersal probability" not in lowered


def test_manual_visual_checks_remain_explicitly_open() -> None:
    qa = (ROOT / "manuscript/submission/figure_qa.md").read_text(encoding="utf-8")
    assert "Automated QA covered by CI" in qa
    assert "Manual QA that must remain open until journal upload" in qa
    assert "- [ ] inspect grayscale print output;" in qa
    assert "- [ ] inspect every figure at the journal's final single-/double-column display width;" in qa
