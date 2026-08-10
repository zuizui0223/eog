"""Freeze the non-degenerate Tanzania survey-component design before outcomes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from freeze_tanzania_design import _assert_expected, _rows, _source_formula_evidence
from eog.tanzania_survey_ladder import build_tanzania_survey_ladder_contract


def _assert_ladder_expected(
    contract: Mapping[str, Any],
    expected: Mapping[str, Any],
) -> None:
    graph = dict(contract.get("eog_graph") or {})
    if graph.get("radius_selection_audit") != expected.get("radius_selection_audit"):
        raise ValueError("Tanzania survey-component radius-selection audit drift")
    regions = dict(graph.get("regions") or {})
    expected_regions = dict(expected.get("eog_graph") or {})
    for region in sorted(expected_regions):
        actual = dict(regions.get(region) or {})
        frozen = dict(expected_regions[region])
        for key in ("survey_component_counts", "survey_component_partitions"):
            if actual.get(key) != frozen.get(key):
                raise ValueError(
                    f"Tanzania {region} survey-component design drift at {key}"
                )
        counts = list(dict(actual["survey_component_counts"]).values())
        if counts != [4, 3, 2, 1]:
            raise ValueError(
                f"Tanzania {region} ladder is structurally degenerate: {counts}"
            )


def freeze(
    *,
    source_dir: Path,
    semantics_audit: Path,
    expected_design: Path,
    output: Path,
) -> dict[str, Any]:
    semantics = json.loads(semantics_audit.read_text(encoding="utf-8"))
    if semantics.get("status") != "verified_semantics_alignment_and_eligibility_only":
        raise ValueError("verified Tanzania semantics audit is required")
    if semantics.get("species_outcomes_inspected") is not False:
        raise ValueError("semantics input indicates species outcomes were inspected")
    if semantics.get("eog_graph_constructed") is not False:
        raise ValueError("semantics input indicates an EOG graph was already constructed")
    occurrence = semantics.get("occurrence")
    if not isinstance(occurrence, dict):
        raise ValueError("semantics audit has no occurrence section")
    eligible = occurrence.get("eligible_species")
    if not isinstance(eligible, list):
        raise ValueError("semantics audit has no eligible species list")

    contract = build_tanzania_survey_ladder_contract(
        sites=_rows(source_dir / "Sites.csv"),
        east_nodes=_rows(source_dir / "Nodes_E.csv"),
        west_nodes=_rows(source_dir / "Nodes_W.csv"),
        eligible_species=[str(value) for value in eligible],
        source_formula_evidence=_source_formula_evidence(source_dir),
    )
    expected = json.loads(expected_design.read_text(encoding="utf-8"))
    if not isinstance(expected, dict):
        raise ValueError("Tanzania expected-design contract must be a JSON object")
    _assert_expected(contract, expected)
    _assert_ladder_expected(contract, expected)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    return contract


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--semantics-audit", type=Path, required=True)
    parser.add_argument("--expected-design", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            freeze(
                source_dir=args.source_dir,
                semantics_audit=args.semantics_audit,
                expected_design=args.expected_design,
                output=args.output,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
