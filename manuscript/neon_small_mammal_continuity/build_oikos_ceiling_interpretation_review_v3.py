#!/usr/bin/env python3
"""Source-locked scientific clarification DRAFT for Oikos author/coauthor review.

This builder never edits the original 32 manuscript science assets, never opens
NEON response data, never approves an AI declaration, and never emits a PDF or
any supposedly submission-ready material. It applies small, anchored editorial
replacement sections to an independent UNAPPROVED Markdown candidate.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
LANE = ROOT / "manuscript/neon_small_mammal_continuity"
SOURCE = LANE / "MANUSCRIPT_V1.md"
SIGNIFICANCE = LANE / "OIKOS_SIGNIFICANCE_STATEMENT_V1.md"
REVIEW = ROOT / "validation/neon_mammal_ceiling_review_v1/result_frozen_v1.json"
OUTPUT_SCHEMA = "eog.neon_small_mammal_continuity.ceiling_editorial_author_review.v3"
ORIGINAL_BLOB = "ada5a84d3b862e122b1d6895c47ed3511de05854"
SIGNIFICANCE_BLOB = "f1b223d9a159de37d5ab5ebe2da69266fb3da099"
ORIGINAL_RESPONSE_FINGERPRINT = (
    "c845289d6ad8caf8e932adb90340237b01b120acce52ca2ccb4e6f1d9c10b860"
)
REVIEW_ARTIFACT_SHA256 = "71dc92196f2438f66d6919c73a62527d7f02d33143e9422d8b7c1c52f2acc412"
REVISED_TITLE = (
    "Species-level saturation constrains pooled spatial-continuity gains "
    "across 16 NEON small-mammal sites"
)

REVISED_ABSTRACT = (
    "Pooling species can in principle create spatial continuity that no one "
    "constituent species supports, but the possibility depends on how "
    "continuous the best species already is. We tested this prediction in "
    "16 prospectively fixed NSF NEON small-mammal sites using response-blind "
    "trap geometries, multiscale one-step neighbourhood graphs and an "
    "assemblage-relocation null. All 16 sites were scorable. At every site, "
    "at least one constituent species already satisfied the complete "
    "declared spatial-continuity criterion across all graph scales "
    "(best-species world survival = 1.0). Consequently, a positive "
    "pooled-minus-best-species survival gain was impossible in this observed "
    "cohort: fifteen pooled guilds were also fully continuous, whereas at "
    "ORNL pooling reduced survival from 1.0 to 0.25. Because the original "
    "permutation null preserves the guild-positive trap set, its sitewise "
    "upper-tail p-values of 1 and nonpositive null-adjusted gains follow "
    "algebraically from the observed best-species ceiling, rather than "
    "providing independent evidence against turnover in general. "
    "Thirteen of 16 sites had at least two individually fully continuous "
    "species; 32 distinct species contributed this pattern across the "
    "study, none at more than three sites. These results describe recurrent "
    "species-level sufficiency and locally redundant occupancy continuity "
    "under this fixed occurrence-based criterion. They do not measure "
    "dispersal, demographic insurance or the absence of spatial "
    "complementarity in settings without a fully continuous constituent."
)

REVISED_RESULTS_3_1 = (
    "### 3.1 Observed best-species saturation constrained the primary contrast\n\n"
    "All 16 prospectively selected NEON sites were scorable. The maximum "
    "single-species world-survival fraction was 1.0 at every site. Since "
    "pooled guild survival cannot exceed 1.0, the prespecified "
    "community-minus-best-species gain could not be positive in this "
    "observed cohort. Fifteen sites had a raw gain of zero, and the "
    "remaining site, ORNL, had a raw gain of -0.75.\n\n"
    "The frozen assemblage-relocation null preserves the exact guild-positive "
    "trap set and therefore the pooled guild's world-survival fraction. "
    "A permuted best-species score cannot exceed 1.0, so every permuted "
    "guild-minus-best-species contrast is at least as large as the "
    "observed contrast. Consequently the 16 sitewise one-sided "
    "upper-tail permutation p-values equal 1.0 and no positive "
    "null-adjusted gain can occur. The one-sided across-site sign-test "
    "p = 1.0 follows from these same nonpositive contrasts; it is not "
    "independent negative evidence. Thus the preregistered positive-gain "
    "prediction was not supported under the stated one-step criterion, "
    "without establishing a general absence of turnover mechanisms."
)

REVISED_DISCUSSION = (
    "## 4. Discussion\n\n"
    "The preregistered prediction that pooling different small-mammal "
    "species would create multiscale spatial continuity beyond that of "
    "the strongest constituent was not supported across the 16 fixed "
    "NEON sites. The primary, empirically observed pattern was that "
    "at least one species at every site already satisfied the entire "
    "declared one-step continuity criterion. Because this constituent "
    "score had reached the maximum of 1.0, no pooled community could "
    "obtain a positive increment in world-survival fraction at these sites. "
    "This is an important boundary on interpreting the null result: "
    "the permutation p-values and lack of positive null-adjusted gains "
    "are mathematically dependent on the same observed saturation, "
    "not independent experiments confirming the absence of turnover.\n\n"
    "The original assay is not mathematically incapable of detecting "
    "emergence in every conceivable assemblage. A separate, explicitly "
    "invented four-trap example with two species occupying alternating "
    "sites yields a positive pooled-minus-best-species gain and a "
    "positive null-adjusted gain under the original relocation rule. "
    "This synthetic counterexample demonstrates estimator feasibility; "
    "it is not another NEON site, biological replication or "
    "confirmatory response test. Our result is therefore limited to "
    "the original selected sites, eligible species, trap geometry "
    "and prescribed one-step neighbourhood worlds.\n\n"
    "The observations also reveal a descriptive pattern beyond the "
    "absence of pooled increment. Thirteen sites contained two or more "
    "constituent species that each met every declared continuity scale, "
    "and 32 different species served as fully continuous providers "
    "across the sixteen sites, with none appearing in that role at more "
    "than three sites. We call this occupancy-continuity redundancy: "
    "multiple species independently meet the same geometric criterion. "
    "It should not be confused with measured demographic insurance, "
    "replacement after local extinction, or functional equivalence, "
    "none of which was observed in this study.\n\n"
    "Pooling also illustrates how the chosen spatial statistic depends "
    "on the set of positive trap locations. At ORNL, the most continuous "
    "species survived every graph, while the pooled guild survived only "
    "one quarter of the graphs. Adding guild-positive traps can introduce "
    "new locations that lack admitted occupied neighbours under the "
    "all-positive support rule. This is an observed pooling penalty "
    "under the metric, not a claim that more biodiversity generally "
    "reduces actual animal movement or connectivity.\n\n"
    "Heterospecific-only local neighbourhood rescue occurred, but was "
    "rare, and the absence of any strict guild-only surviving graph "
    "is likewise consistent with the observed best-species ceiling. "
    "Exploratory associations involving richness and the count of "
    "individually fully continuous species were computed after the "
    "confirmatory result was closed. Richer sites contain more eligible "
    "species that may qualify as providers by construction; these "
    "post hoc correlations do not establish that richness caused a "
    "spatial-insurance mechanism.\n\n"
    "Most importantly, this analysis concerns trap-level occurrence "
    "and a frozen adjacency criterion. It does not measure animal "
    "dispersal, realized demographic exchange, local persistence, "
    "causal filtering, or stability following a perturbation. "
    "The original positive turnover-emergence hypothesis was not "
    "supported in these sites, but the saturated constituent baseline "
    "leaves the study unable to estimate what turnover could contribute "
    "in other metacommunities where the best species is not already "
    "fully continuous. This separation between an empirical "
    "species-level ceiling and its statistically dependent consequences "
    "is necessary for a defensible ecological interpretation."
)

REVISED_SIGNIFICANCE = (
    "Species turnover can sometimes connect spatial locations that no "
    "single species spans. We prospectively evaluated this possibility "
    "using a fixed one-step spatial-continuity criterion at 16 NEON "
    "small-mammal sites. At every site a constituent species already "
    "met that criterion across every declared spatial graph, which "
    "left no positive gain available for the pooled guild under "
    "the observed species-level ceiling. The associated permutation "
    "and sign-test p-values are conditional mathematical consequences "
    "of that ceiling, not separate independent negative findings. "
    "Thirteen sites nevertheless had multiple individually sufficient "
    "species; 32 distinct species provided this occurrence-based "
    "continuity across sites. These observations reveal species-level "
    "sufficiency and locally redundant spatial occurrence under "
    "a specific geometric measure. They do not measure movement, "
    "demographic insurance or a universal absence of turnover benefits. "
    "The result illustrates why community-level aggregation must be "
    "interpreted together with the strongest constituent's baseline "
    "and the particular spatial outcome being tested."
)


def validate_review_source(reviewed: dict) -> None:
    if (
        reviewed.get("schema") !=
        "eog.neon_small_mammal_continuity.ceiling_conditioned_null_review.reviewed_v1"
        or reviewed.get("authority", {}).get("full_audit_canonical_sha256")
        != REVIEW_ARTIFACT_SHA256
        or reviewed["authority"]["independent_frozen_source_response_fingerprint"]
        != ORIGINAL_RESPONSE_FINGERPRINT
    ):
        raise ValueError("Fixed original empirical reviewer audit identity changed")
    expected = {
        "fixed_scored_sites": 16,
        "observed_best_species_survival_equals_one": 16,
        "sites_whose_permutation_null_upper_tail_p_one_is_forced_by_ceiling": 16,
        "sites_whose_null_adjusted_positive_is_forced_impossible": 16,
        "sites_whose_strict_guild_only_world_is_forced_impossible": 16,
        "observed_positive_raw_gain_sites": 0,
        "observed_positive_null_adjusted_gain_sites": 0,
        "observed_aggregate_one_sided_p": 1,
        "sites_with_at_least_two_independently_fully_continuous_species": 13,
        "unique_continuity_provider_species_across_sites": 32,
        "largest_number_of_sites_any_provider_species_recurred": 3,
    }
    if any(reviewed["counts"].get(key) != value for key, value in expected.items()):
        raise ValueError("Source reviewer ceiling or NEON site counts drifted")
    if not all(reviewed["interpretation"].get(key) is True for key in (
        "negative_gain_and_p_one_follow_once_saturation_observed",
        "site_null_p_one_and_aggregate_sign_p_one_not_independent_confirmation",
        "no_proof_of_universal_ecological_absence_of_turnover",
        "original_locked_manuscript_paper_science_text_untouched",
        "Oikos_AI_approval_and_title_page_still_pending",
    )):
        raise ValueError("Fixed scientific inference boundaries changed")


def anchored_replace(text: str, start: str, next_heading: str,
                     replacement: str) -> str:
    if text.count(start) != 1 or text.count(next_heading) != 1:
        raise ValueError("Original scientific section anchors are not unique")
    left = text.index(start)
    right = text.index(next_heading)
    if left >= right:
        raise ValueError("Unexpected historical source section order")
    return text[:left] + replacement.strip() + "\n\n" + text[right:]


def build_proposal() -> dict:
    from manuscript.neon_small_mammal_continuity import (
        build_oikos_initial_submission_policy_v2 as policy
    )
    source_check = policy.integrity_guard()
    if (
        source_check["original_imported_blobs_SHA1_verified"] != 32
        or source_check["original_response_lock_fingerprint_verified"]
        != ORIGINAL_RESPONSE_FINGERPRINT
        or policy.git_blob_sha1(SOURCE) != ORIGINAL_BLOB
        or policy.git_blob_sha1(SIGNIFICANCE) != SIGNIFICANCE_BLOB
    ):
        raise ValueError("Historical manuscript, significance or response source changed")

    validate_review_source(json.loads(REVIEW.read_text(encoding="utf-8")))
    original = SOURCE.read_text(encoding="utf-8")
    if not original.startswith(
        "# Community spatial continuity is redundant across species "
        "rather than generated by turnover in small-mammal metacommunities\n"
    ):
        raise ValueError("Historical title changed or scientific candidate already updated")
    proposed = original.replace(
        original.split("\n", 1)[0], "# " + REVISED_TITLE, 1
    )
    proposed = anchored_replace(
        proposed, "## Abstract\n", "**Keywords:**",
        "## Abstract\n\n" + REVISED_ABSTRACT
    )
    proposed = anchored_replace(
        proposed, "### 3.1 Species turnover did not create emergent community continuity\n",
        "### 3.2 At least one individual species was fully continuous at every site",
        REVISED_RESULTS_3_1
    )
    proposed = anchored_replace(
        proposed, "## 4. Discussion\n", "## Data availability\n",
        REVISED_DISCUSSION
    )

    # Sections below are strictly retained at their source bytes. The
    # original Oikos v2 author-approved AI text / PDF gate stays separate.
    for heading in (
        "## 1. Introduction", "## 2. Methods",
        "### 3.2 At least one individual species was fully continuous at every site",
        "### 3.3 Pooling reduced continuity at ORNL",
        "### 3.4 Heterospecific rescue was local and rare",
        "### 3.5 Richness was associated with continuity redundancy, not stronger turnover rescue",
        "## Data availability", "## Figure captions", "## References",
    ):
        if proposed.count(heading) != 1:
            raise ValueError("An original scientific section was lost")
    for marker, until in (
        ("## 1. Introduction\n", "### 3.1 Species turnover did not create emergent community continuity\n"),
        ("### 3.2 At least one individual species was fully continuous at every site",
         "## 4. Discussion\n"),
        ("## Data availability\n", None),
    ):
        if marker == "## 1. Introduction\n":
            original_part = original[original.index(marker):original.index(until)]
            revised_part = proposed[proposed.index(marker):proposed.index(
                "### 3.1 Observed best-species saturation constrained the primary contrast")]
        elif until is None:
            original_part = original[original.index(marker):]
            revised_part = proposed[proposed.index(marker):]
        else:
            original_part = original[original.index(marker):original.index(until)]
            revised_part = proposed[proposed.index(marker):proposed.index(until)]
        if original_part != revised_part:
            raise ValueError("Historical methods, secondary results, data, figures or references changed")
    if any(x in proposed for x in (
        "The preregistered primary hypothesis was rejected completely.",
        "The preregistered turnover hypothesis was rejected:",
        "a second independent confirmation",
    )):
        raise ValueError("Ceiling-driven statistics still overclaimed")
    if not all(s.lower() in proposed.lower() for s in (
        "all 16", "Thirteen of 16", "32", "ORNL",
        "not independent negative evidence", "not supported",
    )):
        raise ValueError("Required conservative results and inference boundaries absent")

    original_form = policy.significance_for_form(
        SIGNIFICANCE.read_text(encoding="utf-8")
    )
    revised_form = REVISED_SIGNIFICANCE
    if "32 species" not in original_form or "32 distinct species" not in revised_form:
        raise ValueError("Original significance source evidence was lost")

    review_document = (
        "<!-- UNAPPROVED SCIENTIFIC REVISION FOR HUMAN AUTHOR/COAUTHOR REVIEW ONLY. "
        "NOT A SUBMISSION MANUSCRIPT. NO APPROVED AI STATEMENT. -->\n\n"
        + proposed
    )
    change_diff = "".join(difflib.unified_diff(
        original.splitlines(keepends=True),
        proposed.splitlines(keepends=True),
        fromfile="ORIGINAL_LOCKED_MANUSCRIPT_V1.md",
        tofile="UNAPPROVED_CEILING_INTERPRETATION_DRAFT_V3.md",
    ))
    if not change_diff.startswith("--- ORIGINAL_LOCKED_MANUSCRIPT_V1.md"):
        raise ValueError("Expected non-empty original-to-candidate review diff")
    return {
        "candidate": review_document,
        "diff": change_diff,
        "significance": (
            "UNAPPROVED AUTHOR/COAUTHOR REVIEW PROPOSAL; DO NOT PASTE TO SCHOLARONE.\n\n"
            + revised_form + "\n"
        ),
        "receipt": {
            "schema": OUTPUT_SCHEMA,
            "status": "CEILING_QUALIFIED_EDITORIAL_CANDIDATE__AUTHOR_APPROVAL_PENDING__NO_PDF",
            "source": {
                "original_scientific_manuscript_git_blob_sha1": ORIGINAL_BLOB,
                "original_significance_git_blob_sha1": SIGNIFICANCE_BLOB,
                "original_32_manuscript_blobs_verified": 32,
                "original_response_fingerprint": ORIGINAL_RESPONSE_FINGERPRINT,
                "post_response_reviewer_audit_canonical_sha256": REVIEW_ARTIFACT_SHA256,
                "all_original_sources_unchanged": True,
            },
            "changes": {
                "title_qualified": True,
                "abstract_qualified": True,
                "original_results_3_1_ceiling_and_dependent_null_qualified": True,
                "discussion_qualified": True,
                "significance_form_separate_proposal": True,
                "original_introduction_methods_results_3_2_to_3_5_captions_references_unchanged": True,
                "prior_source_data_availability_section_unchanged": True,
            },
            "author_approved_science_interpretation": False,
            "author_approved_AI_statement": False,
            "blinded_submission_pdf_created": False,
            "title_page_or_ScholarOne_data_submitted": False,
            "new_NEON_biological_response_or_scientific_score": False,
            "new_EOG_WF_endpoint_or_denominator_change": False,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    if args.output_dir.exists() or args.output_dir.is_symlink():
        raise FileExistsError("Refuse to overwrite any prior author review material")
    result = build_proposal()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    outputs = {
        "OIKOS_CEILING_INTERPRETATION_AUTHOR_REVIEW_UNAPPROVED_V3.md": result["candidate"],
        "OIKOS_CEILING_EDITORIAL_DIFF_UNAPPROVED_V3.patch": result["diff"],
        "OIKOS_SIGNIFICANCE_AUTHOR_REVIEW_UNAPPROVED_V3.txt": result["significance"],
    }
    for filename, content in outputs.items():
        (args.output_dir / filename).write_text(content, encoding="utf-8")
    receipt = result["receipt"]
    receipt["review_only_output_sha256"] = {
        name: hashlib.sha256(body.encode("utf-8")).hexdigest()
        for name, body in outputs.items()
    }
    (args.output_dir / "OIKOS_CEILING_INTERPRETATION_REVIEW_PREFLIGHT_V3.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": receipt["status"],
        "original_32_sources_untouched": True,
        "has_author_approved_AI_or_science": False,
        "submission_pdf_created": False,
    }))


if __name__ == "__main__":
    main()
