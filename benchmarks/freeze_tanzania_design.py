"""Freeze Tanzania CV, graph scales, and source formulas before outcomes."""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Mapping

from eog.tanzania_design import build_tanzania_design_contract


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"missing CSV header: {path}")
        return [dict(row) for row in reader]


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _source_formula_evidence(source_dir: Path) -> dict[str, bool]:
    usambara = _compact((source_dir / "0_usambara.R").read_text(encoding="utf-8"))
    sites = _compact((source_dir / "1_sites.R").read_text(encoding="utf-8"))
    occurrence = _compact(
        (source_dir / "2_isolation_occurrence").read_text(encoding="utf-8")
    )
    return {
        "three_resistance_axes_each_1_to_128": all(
            token in usambara
            for token in (
                "euc<-c(1,2,4,8,16,32,64,128)",
                "tea<-c(1,2,4,8,16,32,64,128)",
                "oth<-c(1,2,4,8,16,32,64,128)",
            )
        ),
        "source_site_resistance_grid": (
            "relresist<-c(1,2,4,8,16,32,64,128)" in sites
        ),
        "east_landcover_mapping": all(
            token in usambara
            for token in (
                "cost[cost==1]<-oth[o]",
                "cost[cost==2]<-1",
                "cost[cost==3]<-tea[t]",
                "cost[cost==4]<-euc[e]",
            )
        ),
        "west_landcover_mapping": all(
            token in usambara
            for token in (
                "cost[cost==1]<-oth[o]",
                "cost[cost==2]<-euc[e]",
                "cost[cost==3]<-1",
                "cost[cost==4]<-tea[t]",
            )
        ),
        "circuitscape_pairwise_scenario": "scenario=pairwise" in usambara,
        "east_weighted_isolation_formula": (
            "RD.E$WeightedRD<-RD.E$value*(1/RD.E$logArea)" in sites
            and "pE$isol[p]<-sum(RD.E$WeightedRD)" in sites
        ),
        "west_weighted_isolation_formula": (
            "RD.W$WeightedRD<-RD.W$value*(1/RD.W$logArea)" in sites
            and "pW$isol[p]<-sum(RD.W$WeightedRD)" in sites
        ),
        "source_glm_area_isolation_interaction": (
            "glm(occur$occur~log10(occur$area_ha)*log10(occur[,c+15]),family=\"binomial\")"
            in occurrence
        ),
        "source_514_predictor_loop": "for(cin1:514)" in occurrence,
        "source_convergence_rule": all(
            token in occurrence
            for token in (
                "mod$converged==\"TRUE\"",
                "(mod$null.deviance-mod$deviance)/mod$null.deviance<1",
                "(mod$null.deviance-mod$deviance)/mod$null.deviance>=0",
            )
        ),
    }


def _assert_expected(
    contract: Mapping[str, Any],
    expected: Mapping[str, Any],
) -> None:
    if expected.get("status") != "tanzania_preoutcome_design_expected_values":
        raise ValueError("unexpected Tanzania expected-design contract status")
    if contract.get("design_fingerprint") != expected.get("design_fingerprint"):
        raise ValueError(
            "Tanzania design fingerprint drift: "
            f"got {contract.get('design_fingerprint')}, "
            f"expected {expected.get('design_fingerprint')}"
        )

    source = dict(contract.get("source") or {})
    expected_source = dict(expected.get("source") or {})
    for key in (
        "doi",
        "version_id",
        "n_sites",
        "n_species",
        "n_eligible_species",
        "eligible_species_sha256",
    ):
        if source.get(key) != expected_source.get(key):
            raise ValueError(
                f"Tanzania source design drift at {key}: "
                f"got {source.get(key)!r}, expected {expected_source.get(key)!r}"
            )

    cross_validation = dict(contract.get("cross_validation") or {})
    expected_cv = dict(expected.get("cross_validation") or {})
    if dict(cross_validation.get("primary") or {}).get("n_folds") != expected_cv.get(
        "primary_n_folds"
    ):
        raise ValueError("Tanzania primary fold count drift")
    if dict(cross_validation.get("spatial_sensitivity") or {}).get(
        "n_folds"
    ) != expected_cv.get("spatial_sensitivity_n_folds"):
        raise ValueError("Tanzania spatial-sensitivity fold count drift")
    if dict(cross_validation.get("spatial_sensitivity") or {}).get(
        "blocks"
    ) != expected_cv.get("spatial_blocks"):
        raise ValueError("Tanzania geometry-only spatial block membership drift")

    regions = dict(dict(contract.get("eog_graph") or {}).get("regions") or {})
    expected_regions = dict(expected.get("eog_graph") or {})
    if set(regions) != set(expected_regions):
        raise ValueError("Tanzania EOG region set drift")
    for region in sorted(expected_regions):
        actual = dict(regions[region])
        frozen = dict(expected_regions[region])
        for key in ("n_nodes", "mst_edge_sha256", "scenario_radii_km"):
            if actual.get(key) != frozen.get(key):
                raise ValueError(
                    f"Tanzania {region} graph drift at {key}: "
                    f"got {actual.get(key)!r}, expected {frozen.get(key)!r}"
                )

    models = dict(contract.get("heldout_probability_models") or {})
    expected_models = dict(expected.get("heldout_probability_models") or {})
    for key in (
        "l2_penalty",
        "strict_incremental_reference",
        "strict_incremental_candidate",
    ):
        if models.get(key) != expected_models.get(key):
            raise ValueError(f"Tanzania held-out model contract drift at {key}")

    for key in (
        "species_outcomes_inspected",
        "model_fitted",
        "current_flow_computed",
        "eog_score_computed",
    ):
        if contract.get(key) is not expected.get(key):
            raise ValueError(f"Tanzania scientific-boundary flag drift at {key}")


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

    contract = build_tanzania_design_contract(
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
