#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = (
    ROOT
    / "manuscript"
    / "bam_identifiability"
    / "MANUSCRIPT_DRAFT_V4_JBI.md"
)


def words(text: str):
    return re.findall(r"[A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9'’+\-/]*", text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "manuscript/bam_identifiability/JBI_READINESS_V1.json"
        ),
    )
    args = parser.parse_args()

    text = MANUSCRIPT.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = lines[0].removeprefix("# ")
    running = next(
        line.split(":", 1)[1].strip()
        for line in lines
        if line.startswith("**Running title:**")
    )
    abstract = text.split("## Abstract", 1)[1].split("## 1. Introduction", 1)[0]
    keyword_line = next(
        line for line in abstract.splitlines() if line.startswith("**Keywords:**")
    )
    keywords = [value.strip() for value in keyword_line.split(":", 1)[1].split(",")]

    checks = {
        "title_le_115_chars": len(title) <= 115,
        "running_title_lt_40_chars": len(running) < 40,
        "structured_abstract_le_300_words": (
            len(words(abstract)) <= 300
            and all(
                label in abstract
                for label in (
                    "**Aim:**",
                    "**Location:**",
                    "**Taxon:**",
                    "**Methods:**",
                    "**Results:**",
                    "**Main conclusions:**",
                )
            )
        ),
        "keywords_6_to_10_alphabetical": (
            6 <= len(keywords) <= 10
            and keywords == sorted(keywords, key=str.lower)
        ),
        "full_manuscript_le_6000_words": len(words(text)) <= 6000,
        "major_structure": all(
            marker in text
            for marker in (
                "## 1. Introduction",
                "## 2. Methods",
                "## 3. Results",
                "## 4. Discussion",
                "## References",
                "## Data Accessibility Statement",
                "## Figure legends",
            )
        ),
        "six_main_figure_legends": all(
            f"**Figure {number}." in text for number in range(1, 7)
        ),
        "double_anonymous_surface": all(
            token not in text.lower()
            for token in ("zhang ruiqi", "zuizui0223", "tohoku university")
        ),
        "eog_wf_separation": all(
            token not in text.lower()
            for token in (
                "azores yellow eel",
                "king rail",
                "tampa bay",
                "layer b",
                "macro log loss",
                "3/31/3",
            )
        ),
    }

    payload = {
        "schema": "eog.bam_inverse_identifiability.jbi_readiness.v1",
        "manuscript": str(MANUSCRIPT.relative_to(ROOT)),
        "status": "PASS" if all(checks.values()) else "FAIL",
        "metrics": {
            "title_chars": len(title),
            "running_title_chars": len(running),
            "abstract_words": len(words(abstract)),
            "keyword_count": len(keywords),
            "full_manuscript_words_approx": len(words(text)),
        },
        "checks": checks,
    }
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    payload["fingerprint"] = hashlib.sha256(encoded).hexdigest()

    output = args.output
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
