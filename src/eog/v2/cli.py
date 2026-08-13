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


__all__ = [
    "genetic_validate_main",
    "occurrence_freeze_main",
    "occurrence_validate_main",
]
