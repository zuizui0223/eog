#!/usr/bin/env python3
"""Algebraic reviewer audit of already-locked NEON metacommunity results.

All 16-site empirical responses and the manuscript's original 32 source blobs
are frozen. This derives a CONDITIONAL mathematical ceiling and a synthetic
positive counterexample, without opening, refitting or reselecting NEON data.
It does NOT establish a new biological null or confirm an absent mechanism.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "manuscript/neon_small_mammal_continuity"
PROTOCOL = ROOT / "validation/neon_mammal_ceiling_review_v1/protocol_v1.json"
LOCK = ROOT / "validation/neon_metacommunity_connectivity_v1/response_lock_v1.json"
MODULE = ROOT / "src/eog/v2/metacommunity_connectivity.py"
SCHEMA = "eog.neon_small_mammal_continuity.ceiling_conditioned_null_review.result.v1"
TOL = 1e-12
FIXED_FINGERPRINT = "c845289d6ad8caf8e932adb90340237b01b120acce52ca2ccb4e6f1d9c10b860"
MODULE_SHA = "a09ecd84d965ab4d2d0161f0567a8367ec7fec21"
METRICS_SHA = "c3a89797785aaf68e128b91272e6e58a544cde3f"
SUMMARY_SHA = "a5d23fb36123d3977f30f4125e8a4d6d073fbb8e"
PAPER_SHA = "ada5a84d3b862e122b1d6895c47ed3511de05854"
EXPECTED_16 = (
    "JORN","KONA","LAJA","LENO","MLBS","MOAB","NIWO","NOGP","OAES","ONAQ",
    "ORNL","OSBS","RMNP","SERC","SJER","SOAP"
)
MAP_FIELDS = (
    ("site_code","site"),
    ("guild_positive_node_count","guild_positive_nodes"),
    ("observed_target_species_count","target_species_richness"),
    ("species_with_two_positive_nodes","species_ge2"),
    ("community_survival_fraction","community_continuity_fraction"),
    ("max_species_survival_fraction","best_species_continuity_fraction"),
    ("best_species_count","individually_saturated_species_count"),
    ("emergent_connectivity_gain","emergent_gain"),
    ("strict_emergent_world_fraction","strict_emergent_world_fraction"),
    ("cross_species_rescue_fraction","cross_species_rescue_fraction"),
    ("dominance_coverage","dominance_coverage"),
    ("null_adjusted_gain","null_adjusted_gain"),
    ("site_upper_tail_p","site_upper_tail_p"),
)


def git_blob_sha1(path: Path) -> str:
    """Independent Git object hash check without invoking git or fetching records."""
    content = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError("Original manuscript site summary has no header")
        return list(reader)


def _numeric(value: str, field: str) -> float:
    z = float(value)
    if not math.isfinite(z):
        raise ValueError("Nonfinite site-level " + field)
    return z


def verify_original_source() -> dict:
    p=json.loads(PROTOCOL.read_text(encoding="utf-8"))
    scope=p["interpretation"]
    if not (
        p["schema"] == "eog.neon_small_mammal_continuity.ceiling_conditioned_null_review.protocol.v1"
        and p["status"] == "EXPLICITLY_POST_RESPONSE_EXPLORATORY_REVIEW__NO_ENDPOINT_REDEFINITION"
        and p["baseline"]["main_before_review"] == "b3a94279f626cacc4a781b8f3bc7854d54db5724"
        and p["baseline"]["response_fingerprint"] == FIXED_FINGERPRINT
        and p["baseline"]["imported_source_files_blob_count"] == 32
        and p["baseline"]["original_module_blob_sha1"] == MODULE_SHA
        and p["baseline"]["original_metrics_blob_sha1"] == METRICS_SHA
        and p["baseline"]["original_summary_blob_sha1"] == SUMMARY_SHA
        and p["baseline"]["original_manuscript_blob_sha1"] == PAPER_SHA
        and all(scope.values())
    ):
        raise ValueError("Original source lock or postresponse claim limits altered")
    lock=json.loads(LOCK.read_text(encoding="utf-8"))
    boundary=json.loads((BASE/"SUBMISSION_BOUNDARY_V1.json").read_text(encoding="utf-8"))
    port=json.loads((BASE/"MAINLINE_PORT_REPRODUCIBILITY_RECEIPT_V1.json").read_text(encoding="utf-8"))
    if not (
        lock["result_fingerprint"] == FIXED_FINGERPRINT
        and lock["denominator"] == {"fixed_sites":16,"scored_sites":16,"response_consumed_stops":0}
        and lock["rerun_allowed"] is False
        and lock["post_response_rule_change_allowed"] is False
        and lock["primary"]["site_count"] == 16
        and lock["primary"]["positive_null_adjusted_site_count"] == 0
        and lock["primary"]["one_sided_sign_test_p"] == 1
        and boundary["source_result_fingerprint"] == FIXED_FINGERPRINT
        and boundary["authoritative_analysis_module_blob_sha1"] == MODULE_SHA
        and boundary["empirical_denominator"] == {"fixed_sites":16,"scored_sites":16,"stops":0}
        and len(port["original_32_imported_files"]) == 32
    ):
        raise ValueError("Original NEON response/source closure record changed")
    if git_blob_sha1(MODULE) != MODULE_SHA:
        raise ValueError("Original NEON continuity algorithm has changed")
    entries=port["original_32_imported_files"]
    unique=set()
    for file in entries:
        path=file["path"]
        allowed_other_roots = {
            ".github/workflows/neon-small-mammal-continuity-paper-assets.yml",
            "tests/test_neon_small_mammal_continuity_oikos_submission.py",
            "tests/test_neon_small_mammal_continuity_paper_assets.py",
        }
        if path in unique or not (
            path.startswith("manuscript/neon_small_mammal_continuity/")
            or path in allowed_other_roots
        ):
            raise ValueError("Duplicate or misplaced frozen original file")
        unique.add(path)
        current=ROOT/path
        if not current.is_file() or git_blob_sha1(current) != file["blob_sha1"]:
            raise ValueError("Original immutable source Git blob drift: " + path)
    for file, digest in (
        ("MANUSCRIPT_V1.md",PAPER_SHA),
        ("site_metrics_v1.csv",METRICS_SHA),
        ("site_summary_v1.csv",SUMMARY_SHA)
    ):
        if git_blob_sha1(BASE/file) != digest:
            raise ValueError("Original frozen site/manuscript source drift: " + file)
    return {
        "original_frozen_NEON_response_fingerprint":FIXED_FINGERPRINT,
        "original_16_sites_scored":16,
        "imported_original_paper_source_blobs_verified":len(entries),
        "original_continuity_algorithm_blob_verified":True,
        "original_response_records_reopened":False,
        "original_Oikos_science_text_edited":False,
    }


def proof_for_ceiling(C: float, M_obs: float, *,
                      null_preserves_guild_positive_sites: bool=True) -> dict:
    """Check data-CONDITIONAL proposition, no rerun of permutations.

    With M_obs=1, G_obs=C-1. Each null rearrangement preserves guild C,
    and any M_null<=1, hence G_null>=G_obs. The site-level upper-tail p
    and lack of positive null-adjusted gain follow algebraically.
    """
    if not (0 <= C <= 1 and 0 <= M_obs <= 1):
        raise ValueError("World survival fractions must lie in [0,1]")
    if not null_preserves_guild_positive_sites:
        raise ValueError("The theorem needs the original fixed-guild positive set")
    saturated=abs(M_obs-1.0)<=TOL
    return {
        "guild_survival":C,
        "observed_max_species_survival":M_obs,
        "observed_gain":C-M_obs,
        "data_conditional_saturation":saturated,
        "raw_positive_gain_excluded_by_ceiling":saturated,
        "strict_guild_only_world_excluded_by_species_survives_all_graphs":saturated,
        "null_all_permutation_gains_ge_observed":saturated,
        "null_positive_adjusted_site_gain_excluded_by_ceiling":saturated,
        "null_one_sided_site_upper_tail_p_forced_to_one":saturated,
    }


def audit() -> dict:
    src=verify_original_source()
    metrics=_read_csv(BASE/"site_metrics_v1.csv")
    summary=_read_csv(BASE/"site_summary_v1.csv")
    ms={}
    ss={}
    for row in metrics:
        key=row["site_code"]
        if key in ms:
            raise ValueError("Repeated original per-site metric")
        ms[key]=row
    for row in summary:
        key=row["site"]
        if key in ss:
            raise ValueError("Repeated original per-site summary")
        ss[key]=row
    if tuple(sorted(ms)) != EXPECTED_16 or set(ms)!=set(ss):
        raise ValueError("Original fixed 16-site roster changed")
    over16=[]
    provider_counts=Counter()
    for site in EXPECTED_16:
        row,other=ms[site],ss[site]
        for m,s in MAP_FIELDS:
            if m in ("site_code",):
                if row[m]!=other[s]:
                    raise ValueError("Site key mismatch")
            elif abs(_numeric(row[m],m)-_numeric(other[s],s))>TOL:
                raise ValueError("Original two independent site tabulations disagree: "+site+"/"+m)
        C=_numeric(row["community_survival_fraction"],"community fraction")
        M=_numeric(row["max_species_survival_fraction"],"species fraction")
        gain=_numeric(row["emergent_connectivity_gain"],"gain")
        adjusted=_numeric(row["null_adjusted_gain"],"null adjusted gain")
        tail=_numeric(row["site_upper_tail_p"],"site permutation p")
        strict=_numeric(row["strict_emergent_world_fraction"],"guild-only world fraction")
        witness=proof_for_ceiling(C,M)
        if not (
            abs(gain-witness["observed_gain"])<=TOL
            and witness["data_conditional_saturation"]
            and gain <= TOL
            and adjusted <= TOL
            and tail == 1.0
            and strict <= TOL
        ):
            raise ValueError("Some original NEON observations violate the conditional ceiling")
        names=[item.strip() for item in row["best_species_names"].split(";") if item.strip()]
        number=int(row["best_species_count"])
        if number!=len(names) or len(set(names))!=number or number<=0:
            raise ValueError("Best continuous species count/name mismatch: "+site)
        provider_counts.update(set(names))
        over16.append({
            "site":site,"guild_survival_fraction":C,
            "observed_best_species_fraction":M,
            "raw_gain":gain,"null_adjusted_gain":adjusted,
            "site_upper_tail_p":tail,
            "strict_guild_only_fraction":strict,
            "individually_fully_continuous_species_count":number,
            "raw_gain_positive_eligible_given_observed_best_1":False,
            "site_null_upper_tail_one_is_algebraically_forced":True,
            "site_positive_null_adjusted_gain_algebraically_excluded":True,
            "positive_strict_emergent_world_algebraically_excluded":True,
        })
    site_count=len(over16)
    saturated=sum(row["observed_best_species_fraction"]==1 for row in over16)
    multiple=sum(row["individually_fully_continuous_species_count"]>=2 for row in over16)
    ORNL=next(x for x in over16 if x["site"]=="ORNL")
    if not (
        site_count == 16 and saturated == 16 and multiple == 13
        and len(provider_counts) == 32 and max(provider_counts.values()) == 3
        and abs(ORNL["guild_survival_fraction"]-0.25)<=TOL
        and abs(ORNL["raw_gain"]+0.75)<=TOL
        and sum(row["raw_gain"]>0 for row in over16)==0
        and sum(row["null_adjusted_gain"]>0 for row in over16)==0
    ):
        raise ValueError("Frozen 16-site ecological count or original ORNL counterexample changed")
    sign_p=(.5**site_count) * sum(math.comb(site_count,k)
        for k in range(0,site_count+1))
    if sign_p!=1:
        raise ValueError("Frozen all-zero one-sided sign test does not reconcile")

    # The original Python estimator has an independently executed synthetic
    # positive example in the existing source-locked test suite; the audit
    # proves its feasibility again without any new biological response.
    import numpy as np
    from eog.v2.metacommunity_connectivity import (
        calculate_metacommunity_connectivity,
        assemblage_row_permutation_null
    )
    graph=np.zeros((4,4),dtype=bool)
    for a,b in ((0,1),(1,2),(2,3)):
        graph[a,b]=graph[b,a]=True
    toy=np.array([[1,0],[0,1],[1,0],[0,1]],dtype=bool)
    counterexample=calculate_metacommunity_connectivity({"chain":graph},toy,
        species_ids=("invented_A","invented_B"))
    synthetic_null=assemblage_row_permutation_null(
        {"chain":graph},toy,species_ids=("invented_A","invented_B"),
        replicates=999,seed=424242
    )
    if not (
        counterexample.emergent_connectivity_gain == 1
        and counterexample.strict_emergent_world_fraction == 1
        and synthetic_null.null_adjusted_gain > 0
        and synthetic_null.row_sum_preserved and synthetic_null.column_sum_preserved
        and synthetic_null.guild_positive_set_preserved
    ):
        raise ValueError("Original metric cannot identify synthetic positive complementarity")
    return {
        "schema":SCHEMA,
        "status":"POST_RESPONSE_ALGEBRAIC_CEILING_AUDIT__NO_NEW_BIOLOGICAL_ENDPOINT",
        "source_identity":src,
        "counts":{
            "fixed_scored_sites":site_count,
            "observed_best_species_survival_equals_one":saturated,
            "sites_with_any_raw_positive_emergence_possible_after_observed_saturation":0,
            "sites_whose_permutation_null_upper_tail_p_one_is_forced_by_ceiling":saturated,
            "sites_whose_null_adjusted_positive_is_forced_impossible":saturated,
            "sites_whose_strict_guild_only_world_is_forced_impossible":saturated,
            "observed_positive_raw_gain_sites":0,
            "observed_positive_null_adjusted_gain_sites":0,
            "observed_aggregate_one_sided_p":sign_p,
            "sites_with_at_least_two_independently_fully_continuous_species":multiple,
            "unique_continuity_provider_species_across_sites":len(provider_counts),
            "largest_number_of_sites_any_provider_species_recurred":max(provider_counts.values()),
        },
        "all_fixed_16_site_arithmetic_witnesses":over16,
        "synthetic_counterexample":{
            "source":"existing original NEON estimator on invented four-node alternating-species chain",
            "single_world_guild_survival":counterexample.community_survival_fraction,
            "single_world_best_species_survival":counterexample.max_species_survival_fraction,
            "positive_emergent_gain":counterexample.emergent_connectivity_gain,
            "strict_guild_only_world_fraction":counterexample.strict_emergent_world_fraction,
            "positive_null_adjusted_gain_possible":synthetic_null.null_adjusted_gain>0,
            "null_999_replicates_fixed_assemblage_margins_verified":True,
            "toy_has_no_real_NEON_observations":True,
        },
        "algebraic_inference":"For C∈[0,1], observed M=1 and each permutation preserving C with M_perm≤1, G_obs=C-1≤0 and G_perm=C-M_perm≥G_obs. Every original permutation upper-tail p=1; G_obs−median(G_perm)≤0 and the all-site one-sided sign p=1 are data-conditional consequences, not independent repeated ecological evidence. As one species survives all graphs, a strict guild-only survivor graph cannot occur.",
        "original_16_site_empirical_null_distribution_rerun":False,
        "original_confirmatory_result_changed":False,
        "original_32_paper_source_blobs_modified":False,
        "Oikos_author_submission_or_AI_declaration_approved":False,
        "EOG_WF_fourth_empirical_endpoint_added":False,
    }


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    result=audit()
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("Refuse to overwrite reviewer audit result")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(
        json.dumps(result,ensure_ascii=False,allow_nan=False,sort_keys=True,indent=2)+"\n",
        encoding="utf-8"
    )
    print(json.dumps({k:result["counts"][k] for k in (
        "fixed_scored_sites",
        "observed_best_species_survival_equals_one",
        "sites_whose_permutation_null_upper_tail_p_one_is_forced_by_ceiling",
        "sites_with_at_least_two_independently_fully_continuous_species",
    )},sort_keys=True))


if __name__=="__main__":
    main()
