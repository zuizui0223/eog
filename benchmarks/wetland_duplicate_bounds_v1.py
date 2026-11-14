"""Exploratory partial-identification audit of conflicting wetland survey rows.

Only observed detection indicators are compared. No occurrence absence,
detection probability, occupancy, ecological effect or A/B/M is inferred.
"""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from itertools import product

from benchmarks import wetland_duplicate_gate_v1 as source_gate


def _positive_keys(rows, species, grain):
    positives = set()
    for row in rows:
        if grain == "site_species":
            prefix = row["site"]
        elif grain == "site_method_species":
            prefix = row["site"] + "|" + row["method"]
        elif grain == "survey_species":
            prefix = row["surv"]
        else:
            raise ValueError("unknown grain")
        for sp in species:
            if int(row[sp]) > 0:
                positives.add(prefix + "|" + sp)
    return positives


def build_bounds(surveys, sites, species):
    """Enumerate one retained native row per conflicting two-row identifier.

    This is a sensitivity envelope, NOT a proposed cleaning instruction.
    Each retained row is a hypothetical interpretation of source identity.
    """
    groups = defaultdict(list)
    for row in surveys:
        groups[row["surv"]].append(row)
    duplicated = sorted(k for k, rows in groups.items() if len(rows) > 1)
    if len(duplicated) != 2:
        raise ValueError("Expected exactly two known conflicting survey IDs")
    for sid in duplicated:
        rows = groups[sid]
        if len(rows) != 2:
            raise ValueError("Only two-row conflicts are covered")
        # The observed source has one all-zero and one positive species vector.
        signals = [any(int(r[sp]) > 0 for sp in species) for r in rows]
        if sorted(signals) != [False, True]:
            raise ValueError("Conflicting rows are not zero-versus-positive")
        if any(any(int(r[sp]) < 0 for sp in species) for r in rows):
            raise ValueError("Negative species counts are invalid")

    scenario_positive = {grain: [] for grain in (
        "site_species", "site_method_species", "survey_species"
    )}
    for selection in product((0, 1), repeat=len(duplicated)):
        chosen = {sid: groups[sid][choice] for sid, choice in zip(duplicated, selection)}
        retained = [
            row for row in surveys
            if row["surv"] not in chosen or row is chosen[row["surv"]]
        ]
        if len(retained) != len(groups):
            raise AssertionError("not one hypothetical row per survey ID")
        for grain in scenario_positive:
            scenario_positive[grain].append(_positive_keys(retained, species, grain))

    n_site = len({row["site"] for row in sites})
    n_site_method = len({(row["site"], row["method"]) for row in surveys})
    totals = {
        "site_species": n_site * len(species),
        "site_method_species": n_site_method * len(species),
        "survey_species": len(groups) * len(species),
    }
    output = {}
    for grain, arr in scenario_positive.items():
        common = set.intersection(*arr)
        possible = set.union(*arr)
        uncertain = sorted(possible - common)
        output[grain] = {
            "total_observed_unit_species_slots": totals[grain],
            "positive_in_all_resolutions": len(common),
            "positive_in_some_resolution_only": len(uncertain),
            "ambiguous_observed_detection_keys": uncertain,
        }
    return {
        "scenarios": len(scenario_positive["site_species"]),
        "conflicting_survey_ids": duplicated,
        "source_rows": len(surveys),
        "unique_survey_ids": len(groups),
        "grains": output,
    }


def run(surveys_path, sites_path):
    native = source_gate.analyze(surveys_path, sites_path)  # source SHA, row conflicts
    if native["status"] != "BLOCKED_CONFLICTING_SURVEY_IDENTIFIERS":
        raise ValueError("expected native duplicate source blocker")
    surveys, cols = source_gate.load(surveys_path)
    sites, _ = source_gate.load(sites_path)
    species = [c for c in cols if c not in source_gate.META]
    if len(species) != 9 or len(sites) != 29:
        raise ValueError("source species/site roster drift")
    result = {
        "schema": "eog.wetland_duplicate_sensitivity_v1",
        "status": "DESCRIPTIVE_DETECTION_BOUNDS_ONLY_OCCUPANCY_BLOCKED",
        "analysis_type": "POST_EXPOSURE_EXPLORATORY",
        "source_sha256": {
            "survey": source_gate.SURVEY_SHA,
            "site": source_gate.SITE_SHA,
        },
        "source_doi": "10.5281/zenodo.15044115",
        "bounds": build_bounds(surveys, sites, species),
        "readiness": {
            "site_species_detection_summary": "INVARIANT_TO_TWO_RECORDED_CONFLICTS",
            "rowwise_detection_likelihood": "BLOCKED",
            "occupancy_model": "BLOCKED",
            "independent_abiotic_biotic_movement_identification": "NOT_ESTIMABLE",
        },
        "limitations": [
            "A row-resolution scenario is not a verified sampling unit.",
            "Site-level positive detection is not latent occupancy or a true absence.",
            "Original published 27 sites versus archived 29 site rows remains unexplained.",
            "Native field effort, closure and the meaning of the duplicate IDs remain unresolved.",
            "No fourth EOG-WF empirical endpoint or causal BAM claim.",
        ],
    }
    result["fingerprint"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--surveys", type=Path, required=True)
    parser.add_argument("--sites", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.surveys, args.sites)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("WETLAND_BOUNDS=" + json.dumps({
        "status": result["status"],
        "counts": {key: val["positive_in_some_resolution_only"]
                   for key, val in result["bounds"]["grains"].items()},
        "fingerprint": result["fingerprint"],
    }, sort_keys=True))
