#!/usr/bin/env python3
"""Build an immutable-input AUTHOR REVIEW bundle; never a submission approval."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "manuscript" / "inferential_openness"
FLOW = ROOT / "manuscript" / "paper_ready" / "candidate_flow_table.csv"
LEDGER = PAPER / "CROSS_PROJECT_EVIDENCE_LEDGER_V2.json"

PAPER_FILES = (
    "MANUSCRIPT_DRAFT_V2.md",
    "FIGURE_LEGENDS_V1.md",
    "FIGURE_PLAN_V2.md",
    "TITLE_PAGE_TEMPLATE_V1.md",
    "HIGHLIGHTS_ECOINF_V1.md",
    "COVER_LETTER_ECOINF_V1.md",
    "SUBMISSION_READINESS_V1.md",
    "CLAIM_BOUNDARY_V2.md",
    "AI_ASSISTANCE_DECLARATION_AUTHOR_REVIEW.template.md",
)
EXPECTED_MAIN_FIGURES = (
    "figure1_inferential_openness_ladder.svg",
    "figure2_eog_candidate_funnel.svg",
    "figure3_response_access.svg",
    "figure4_level_c_calibration_funnel.svg",
)
GRAPHICAL = "graphical_abstract_inferential_openness.svg"
SUPPLEMENTARY_FIGURE = "supplementary_figure_S1_terminal_taxonomy.svg"
SUPPLEMENTARY_TABLE = "supplementary_table_S1_terminal_stops.csv"

REVIEW_STATUS = """# EOG inferential-openness AUTHOR REVIEW bundle

This ZIP is a scientific/production review package, NOT an approved journal submission.
No biological response was reopened or reanalysed in producing this bundle.

Frozen results: 34 scientific attempts; 31 scientific/protocol STOPs;
3 scored endpoints; 3 excluded administrative records;
12 relation systems screened, 2 architecture-qualified, 0 calibrated negatives.

Unresolved human/administrative gates:
- Author order, affiliations and corresponding-author details
- CRediT contributions, funding, acknowledgements and conflict declarations
- All-author manuscript/figure/reference review and approval
- Human-approved generative-AI assistance disclosure
- Final publisher formatting and archival DOI for the exact approved release

No immutable submission tag, DOI or author approval is asserted.
Refer to manuscript/SUBMISSION_READINESS_V1.md for the full checklist.
"""


def git_blob_sha(raw: bytes) -> str:
    prefix = b"blob " + str(len(raw)).encode("ascii") + b"\0"
    return hashlib.sha1(prefix + raw).hexdigest()


def canonical_json(payload: dict) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def inspect_frozen_inputs() -> tuple[dict, list[dict[str, str]]]:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    eog = ledger["sources"]["eog"]
    if not ledger.get("frozen_2026_10_07"):
        raise ValueError("Source evidence ledger was not declared frozen")
    pinned = (
        ("candidate_flow_table", FLOW),
        ("candidate_flow_ledger", ROOT / "validation/paper_ready_replication/candidate_flow_ledger.json"),
        ("funnel_summary", ROOT / "manuscript/paper_ready/candidate_funnel_summary.csv"),
    )
    for name, path in pinned:
        expected = eog[name]["blob_sha"]
        observed = git_blob_sha(path.read_bytes())
        if observed != expected:
            raise ValueError(f"Source blob mismatch for {name}: {observed} != {expected}")
    with FLOW.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    stop_rows = [r for r in rows if r["classification"] == "scientific_protocol_stop"]
    actual = (
        sum(r["classification"] != "administrative_exclusion" for r in rows),
        len(stop_rows),
        sum(r["classification"] == "predictive_result" for r in rows),
        sum(r["classification"] == "administrative_exclusion" for r in rows),
    )
    if actual != (34, 31, 3, 3):
        raise ValueError(f"Frozen scientific denominator changed: {actual}")
    if len({r["terminal_stage"] for r in stop_rows}) != 21:
        raise ValueError("The original fine-grained STOP taxonomy no longer has 21 labels")
    level = ledger["level_c_284b"]
    if (
        level["architecture_screened_candidates"],
        level["architecture_qualified_candidates"],
        level["candidate_specific_calibration_passed"],
        level["focal_value_opening_authorized"],
    ) != (12, 2, 0, 0):
        raise ValueError("Frozen 284b audit counts changed")
    manuscript = (PAPER / "MANUSCRIPT_DRAFT_V2.md").read_text(encoding="utf-8")
    title_page = (PAPER / "TITLE_PAGE_TEMPLATE_V1.md").read_text(encoding="utf-8")
    mk = re.search(r"^\*\*Keywords:\*\*\s*(.*)$", manuscript, flags=re.MULTILINE)
    tk = re.search(r"^\*\*Keywords\*\*\s*\n([^\n]+)", title_page, flags=re.MULTILINE)
    if not (mk and tk and mk.group(1).strip() == tk.group(1).strip()):
        raise ValueError("Manuscript/title-page keywords do not match")
    for claim in (
        "34 scientific candidate attempts",
        "31 scientific/protocol STOPs",
        "30/31 STOPs",
        "Neither outcome is a biological negative",
        "## Data and code availability",
    ):
        if claim not in manuscript:
            raise ValueError(f"Manuscript claim missing: {claim}")
    if "no DOI is assigned here" not in manuscript:
        raise ValueError("Unminted archive DOI gate is not explicit")
    return ledger, stop_rows


def build_review_bundle(output_dir: Path, source_commit: str = "local-review") -> tuple[Path, Path]:
    if not re.fullmatch(r"[0-9a-f]{40}|local-review", source_commit):
        raise ValueError("source_commit must be a full Git SHA or 'local-review'")
    ledger, stop_rows = inspect_frozen_inputs()
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="eog-inferential-figures-") as temp:
        figures_dir = Path(temp)
        subprocess.run(
            [
                sys.executable,
                str(PAPER / "build_figures_v1.py"),
                "--candidate-flow", str(FLOW),
                "--ledger", str(LEDGER),
                "--output-dir", str(figures_dir),
            ],
            cwd=ROOT, check=True, capture_output=True, text=True,
        )
        figure_manifest = json.loads((figures_dir / "figure_manifest.json").read_text(encoding="utf-8"))
        if tuple(figure_manifest["figures"]) != EXPECTED_MAIN_FIGURES:
            raise ValueError("Main figure set changed")
        if (
            figure_manifest["graphical_abstract"] != GRAPHICAL
            or figure_manifest["supplementary_figure"] != SUPPLEMENTARY_FIGURE
            or figure_manifest["supplementary_table"] != SUPPLEMENTARY_TABLE
            or figure_manifest["fine_terminal_label_count"] != 21
        ):
            raise ValueError("Supplementary figure / abstract contract changed")
        if (
            figure_manifest["scientific_attempts"],
            figure_manifest["scientific_stops"],
            figure_manifest["scored_endpoints"],
            figure_manifest["administrative_exclusions"],
        ) != (34, 31, 3, 3):
            raise ValueError("Figures do not reproduce frozen denominator")

        entries: dict[str, bytes] = {}
        for filename in PAPER_FILES:
            entries[f"manuscript/{filename}"] = (PAPER / filename).read_bytes()
        entries["provenance/CROSS_PROJECT_EVIDENCE_LEDGER_V2.json"] = LEDGER.read_bytes()
        entries["provenance/candidate_flow_table.csv"] = FLOW.read_bytes()
        entries["provenance/candidate_flow_ledger.json"] = (
            ROOT / "validation/paper_ready_replication/candidate_flow_ledger.json"
        ).read_bytes()
        entries["provenance/candidate_funnel_summary.csv"] = (
            ROOT / "manuscript/paper_ready/candidate_funnel_summary.csv"
        ).read_bytes()
        for name in (*EXPECTED_MAIN_FIGURES, GRAPHICAL):
            raw = (figures_dir / name).read_bytes()
            root = ET.fromstring(raw)
            if root.tag != "{http://www.w3.org/2000/svg}svg":
                raise ValueError(f"Not an SVG: {name}")
            entries[f"figures/{name}"] = raw
        raw = (figures_dir / SUPPLEMENTARY_FIGURE).read_bytes()
        ET.fromstring(raw)
        entries[f"supplementary/{SUPPLEMENTARY_FIGURE}"] = raw
        csv_data = (figures_dir / SUPPLEMENTARY_TABLE).read_bytes()
        supplement = list(csv.DictReader(io.StringIO(csv_data.decode("utf-8"))))
        if len(supplement) != 31 or len({r["terminal_stage"] for r in supplement}) != 21:
            raise ValueError("Supplementary original STOP records changed")
        entries[f"supplementary/{SUPPLEMENTARY_TABLE}"] = csv_data
        entries["provenance/figure_manifest.json"] = (figures_dir / "figure_manifest.json").read_bytes()
        entries["README_AUTHOR_REVIEW_NOT_SUBMISSION_READY.md"] = REVIEW_STATUS.encode("utf-8")

        manifest = {
            "schema": "eog.inferential_openness.author_review_bundle.v1",
            "source_commit": source_commit,
            "purpose": "author_review_only",
            "submission_ready": False,
            "all_author_approved": False,
            "archival_doi": None,
            "ecological_results_reestimated": False,
            "denominator": {"scientific_attempts": 34, "stops": 31,
                            "scored_endpoints": 3, "administrative_exclusions": 3},
            "stop_label_count": 21,
            "source_sha_verification": "three pinned EOG source blobs checked locally; 284b identities recorded in the ledger",
            "files_sha256": {
                name: hashlib.sha256(content).hexdigest() for name, content in sorted(entries.items())
            },
        }
        encoded_manifest = canonical_json(manifest)
        entries["BUNDLE_MANIFEST.json"] = encoded_manifest
        zip_path = output_dir / "eog_inferential_openness_AUTHOR_REVIEW_v1.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, data in sorted(entries.items()):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    receipt = output_dir / "author_review_bundle_manifest.json"
    receipt.write_bytes(encoded_manifest)
    return zip_path, receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-commit", default="local-review")
    opts = parser.parse_args()
    package, receipt = build_review_bundle(opts.output_dir, opts.source_commit)
    print(json.dumps({"package": str(package), "manifest": str(receipt),
                      "sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
                      "submission_ready": False}, sort_keys=True))


if __name__ == "__main__":
    main()
