"""Exact post-exposure positive-evidence loss audit for published survreps.

This audits stochastic row-selection mechanics under one source-pinned
public hunviphab function version. It does not fit an occupancy model,
infer a realized historical random draw, or claim causal ecology.
"""
import argparse
import hashlib
import itertools
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks import wetland_duplicate_gate_v1 as source_gate
from benchmarks.wetland_duplicate_bounds_v1 import publication_cohort_ids

REPS = 20
PACKAGE_COMMIT = "25d4c64da289ffcc14679619bb3b18bd494de872"
SURVREPS_BLOB_SHA = "ae7de0753faa1660b9e1ce1bc81b8cdb39a9c670"


def loss_probability(n, k, reps=REPS):
    """Probability of dropping *every* recorded positive row.

    Uses the published survreps sp='X0' with X0=1 for every row.
    A result here is conditional on row sampling, NOT the probability
    that a species is biologically absent or not detected in the field.
    """
    if not all(isinstance(v, int) for v in (n, k, reps)):
        raise TypeError("integer n,k,reps required")
    if n <= 0 or not (1 <= k <= n) or reps <= 0:
        raise ValueError("positive target, nonempty site and reps required")
    if n <= reps:
        return ((n - k) / n) ** reps
    if n - k < reps:
        return 0.0
    p = 1.0
    for j in range(reps):
        p *= (n - k - j) / (n - j)
    return p


def validate_original_hunviphab_source(path):
    """Authenticate *public* upstream source, not unverified 2025 install."""
    raw = Path(path).read_bytes()
    blob = b"blob " + str(len(raw)).encode() + b"\0" + raw
    if hashlib.sha1(blob).hexdigest() != SURVREPS_BLOB_SHA:
        raise ValueError("hunviphab survreps source Git blob SHA drift")
    text = raw.decode("utf-8").replace("\r", "")
    for required in (
        "if(nrow(x.j)>reps)",
        "if(nrow(x.j)<=reps)",
        "sample.int(nrow(x.j),reps,replace=T)",
        "sample.int(nrow(x.j.pres),reps,replace=F)",
        "x.j.pres <- x.j[which(x.j[,sp]>=1),]",
    ):
        if required not in text:
            raise ValueError("upstream sampling semantics differ from audit")
    return hashlib.sha256(raw).hexdigest()


def _group_site(rows):
    sites = defaultdict(list)
    for row in rows:
        sites[row["site"]].append(row)
    return sites


def describe(rows, site_rows, species):
    by = _group_site(rows)
    declared_sites = {row["site"] for row in site_rows}
    if set(by) != declared_sites:
        raise ValueError("site source and survey source roster mismatch")
    counts = sorted([(site, len(grp)) for site, grp in by.items()])
    positive_pairs = []
    for site, group in sorted(by.items()):
        n = len(group)
        for sp in species:
            observations = [int(row[sp]) for row in group]
            if any(v < 0 for v in observations):
                raise ValueError("negative native species counts")
            k = sum(v > 0 for v in observations)
            if k:
                positive_pairs.append({
                    "site": site,
                    "species": sp,
                    "raw_row_count": n,
                    "positive_native_rows": k,
                    "conditional_drop_probability": loss_probability(n, k),
                })
    by_species = {}
    for sp in species:
        these = [p for p in positive_pairs if p["species"] == sp]
        by_species[sp] = {
            "positive_site_count": len(these),
            "expected_lost_positive_sites": math.fsum(
                p["conditional_drop_probability"] for p in these
            ),
        }
    return {
        "source_site_count": len(by),
        "source_survey_rows": len(rows),
        "20_row_normalized_total": REPS * len(by),
        "resample_with_replacement_sites": sum(n <= REPS for _, n in counts),
        "subsample_without_replacement_sites": sum(n > REPS for _, n in counts),
        "observed_positive_site_species_pairs": len(positive_pairs),
        "positive_pairs_at_nonzero_drop_risk": sum(
            p["conditional_drop_probability"] > 0 for p in positive_pairs
        ),
        "positive_pairs_at_least_25pct_drop_risk": sum(
            p["conditional_drop_probability"] >= .25 for p in positive_pairs
        ),
        "expected_lost_positive_site_species_pairs": math.fsum(
            p["conditional_drop_probability"] for p in positive_pairs
        ),
        "maximum_site_species_drop_probability": max(
            (p["conditional_drop_probability"] for p in positive_pairs), default=0
        ),
        "site_raw_row_counts": dict(counts),
        "by_species": by_species,
        "highest_drop_probability_pairs": sorted(
            positive_pairs,
            key=lambda p: (-p["conditional_drop_probability"], p["site"], p["species"])
        )[:15],
    }


def hypothetical_one_row_resolutions(rows, species):
    """Enumerate 4 one-retained-row scenarios, without selecting a 'truth'."""
    groups = defaultdict(list)
    for row in rows:
        groups[row["surv"]].append(row)
    duplicate_keys = sorted(k for k, grp in groups.items() if len(grp) > 1)
    if len(duplicate_keys) != 2:
        raise ValueError("expected two native two-row conflicts")
    for key in duplicate_keys:
        grp = groups[key]
        if len(grp) != 2:
            raise ValueError("cannot enumerate arbitrary multiplicity")
        flags = [any(int(x[sp]) > 0 for sp in species) for x in grp]
        if sorted(flags) != [False, True]:
            raise ValueError("source conflicts changed")
    for flags in itertools.product(range(2), repeat=2):
        selected = {key: groups[key][i] for key, i in zip(duplicate_keys, flags)}
        subset = [
            row for row in rows
            if row["surv"] not in selected or row is selected[row["surv"]]
        ]
        yield subset


def run(survey_path, site_path, upstream_path):
    old = source_gate.analyze(survey_path, site_path)
    if old["status"] != "BLOCKED_CONFLICTING_SURVEY_IDENTIFIERS":
        raise ValueError("source identity conflict contract drift")
    upstream_sha256 = validate_original_hunviphab_source(upstream_path)
    surveys, headers = source_gate.load(survey_path)
    sites, _ = source_gate.load(site_path)
    species = [k for k in headers if k not in source_gate.META]
    if len(species) != 9:
        raise ValueError("native species roster changed")
    if any(row["0"] != "1" for row in surveys):
        # Original published R overwrites X0 to 1 irrespective of this column.
        raise ValueError("observed archive unexpected 0 column contents")

    result = {
        "schema": "eog.wetland_survreps_positive_evidence_loss.v1",
        "status": "POST_EXPOSURE_CONDITIONAL_ALGORITHM_DIAGNOSTIC",
        "source_sha256": {"survey":source_gate.SURVEY_SHA,"site":source_gate.SITE_SHA},
        "upstream": {
            "repo": "edvardmizsei/hunviphab",
            "commit": PACKAGE_COMMIT,
            "function_path": "R/survreps.R",
            "git_blob_sha1": SURVREPS_BLOB_SHA,
            "sha256": upstream_sha256,
            "reps": REPS,
            "selection_species": "X0",
            "selection_species_value": 1,
            "historical_package_runtime_confirmed": False
        },
        "cohorts": {},
        "ambiguity": {},
        "interpretation_boundary": [
            "Sums of exact conditional probabilities are expectations, not realized lost records.",
            "The same resampling draws are shared across all species in one site and loss events are dependent.",
            "External hunviphab implementation is a pinned public source version, not a verified published runtime lock.",
            "Replicated rows are NOT new independent field occasions; no occupancy or causal A/B/M inferred.",
            "Original R script may have additional downstream transformations outside this algorithmic audit.",
            "The closed EOG-WF 3/31/3 empirical evidence is untouched.",
        ],
    }
    for name in ("archived_all", "published_q1", "published_q2"):
        ids = publication_cohort_ids(sites, name)
        scoped_sites = [row for row in sites if row["site"] in ids]
        scoped_rows = [row for row in surveys if row["site"] in ids]
        baseline = describe(scoped_rows, scoped_sites, species)
        alt_expected = []
        for candidate in hypothetical_one_row_resolutions(scoped_rows, species):
            alt_expected.append(
                describe(candidate, scoped_sites, species)[
                    "expected_lost_positive_site_species_pairs"
                ]
            )
        result["cohorts"][name] = baseline
        result["ambiguity"][name] = {
            "hypothetical_resolutions": 4,
            "expected_lost_min": min(alt_expected),
            "expected_lost_max": max(alt_expected),
            "expected_lost_each": alt_expected,
            "status": "NOT_NATIVE_ROW_ADJUDICATION",
        }
    result["fingerprint"] = hashlib.sha256(json.dumps(
        result, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()
    return result


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--surveys",type=Path,required=True)
    parser.add_argument("--sites",type=Path,required=True)
    parser.add_argument("--survreps-source",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=run(args.surveys,args.sites,args.survreps_source)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("WETLAND_SURVREPS_AUDIT="+json.dumps({
        "fingerprint":result["fingerprint"],
        "results":{name:{
            "native":r["source_survey_rows"],
            "normalized":r["20_row_normalized_total"],
            "site_species_positive_pairs":r["observed_positive_site_species_pairs"],
            "expected_lost":r["expected_lost_positive_site_species_pairs"],
            "high_risk_pairs":r["positive_pairs_at_least_25pct_drop_risk"],
        } for name,r in result["cohorts"].items()}
    },sort_keys=True))
