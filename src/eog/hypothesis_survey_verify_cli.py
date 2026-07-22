"""CLI for verifying audited hypothesis-survey outputs."""
from __future__ import annotations

import argparse
from pathlib import Path

from .hypothesis_survey_verify import verify_hypothesis_survey_bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="eog-hypothesis-survey-verify")
    parser.add_argument("--scenarios", required=True, type=Path)
    parser.add_argument("--families", required=True, type=Path)
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--ranking", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = verify_hypothesis_survey_bundle(
        args.scenarios,
        args.families,
        args.candidates,
        args.ranking,
        args.manifest,
    )
    for name, passed in sorted(result.checks.items()):
        print(f"{name}={'ok' if passed else 'failed'}")
    print(f"verification={'valid' if result.valid else 'invalid'}")
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
