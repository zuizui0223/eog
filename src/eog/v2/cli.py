"""Stable console-script facade for prospective EOG v2.

The historical implementation modules remain importable for compatibility and frozen
reproduction. Public console entry points route through this facade so the v2 package
has one discoverable command boundary.
"""
from __future__ import annotations


def genetic_validate_main() -> int | None:
    """Run the existing frozen/prospective genetic validation CLI."""
    from ..genetic_validation_cli import main

    return main()


def occurrence_freeze_main() -> int | None:
    """Run the response-free empirical occurrence freeze CLI."""
    from ..v2_empirical_occurrence_freeze_cli import main

    return main()


def occurrence_validate_main() -> int | None:
    """Run the held-out empirical occurrence validation CLI."""
    from ..v2_empirical_occurrence_validate_cli import main

    return main()


def pre_response_freeze_main() -> int:
    """Compile a declarative safe-source manifest into a pre-response certificate."""
    import argparse
    import json
    from pathlib import Path

    from .pre_response_manifest import compile_pre_response_manifest_file

    parser = argparse.ArgumentParser(
        prog="eog-v2-pre-response-freeze",
        description=(
            "Compile response-independent registry/effort/world inputs and frozen "
            "policies into one content-addressed EOG-WF v2 pre-response certificate."
        ),
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace an existing output file",
    )
    args = parser.parse_args()

    output = args.output.resolve()
    if output.exists() and not args.force:
        parser.error(f"output already exists: {output}; pass --force to replace it")

    result = compile_pre_response_manifest_file(args.manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": result["statuses"],
                "result_fingerprint": result["result_fingerprint"],
                "output": str(output),
            },
            sort_keys=True,
        )
    )
    return 0


def source_qualify_main() -> int:
    """Compile frozen pre-lock evidence into one candidate-lock certificate."""
    import argparse
    import json
    from pathlib import Path

    from .source_qualification_manifest import (
        compile_source_qualification_manifest_file,
    )

    parser = argparse.ArgumentParser(
        prog="eog-v2-source-qualify",
        description=(
            "Join metadata-only discovery, exact source identity, response-blind "
            "transport and candidate preflight into one candidate-lock decision."
        ),
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    output = args.output.resolve()
    if output.exists() and not args.force:
        parser.error(f"output already exists: {output}; pass --force to replace it")

    result = compile_source_qualification_manifest_file(args.manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "candidate_lock_allowed": result["candidate_lock_allowed"],
                "blocking_layer": result["blocking_layer"],
                "certificate_fingerprint": result["certificate"]["fingerprint"],
                "output": str(output),
            },
            sort_keys=True,
        )
    )
    return 0


__all__ = [
    "genetic_validate_main",
    "occurrence_freeze_main",
    "occurrence_validate_main",
    "pre_response_freeze_main",
    "source_qualify_main",
]
