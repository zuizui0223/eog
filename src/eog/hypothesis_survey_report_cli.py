"""CLI for rendering a verified hypothesis-survey report."""
from __future__ import annotations

import argparse
from pathlib import Path

from .hypothesis_survey_report import render_hypothesis_survey_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eog-hypothesis-survey-report",
        description="Verify a hypothesis-survey bundle and render a Markdown decision report.",
    )
    parser.add_argument("--scenarios", required=True, type=Path)
    parser.add_argument("--families", required=True, type=Path)
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--ranking", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--top-n", type=int, default=10)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = render_hypothesis_survey_report(
        args.scenarios,
        args.families,
        args.candidates,
        args.ranking,
        args.manifest,
        args.output,
        top_n=args.top_n,
    )
    print(f"report_markdown={report.output_path}")
    print(f"pipeline_fingerprint={report.pipeline_fingerprint}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
