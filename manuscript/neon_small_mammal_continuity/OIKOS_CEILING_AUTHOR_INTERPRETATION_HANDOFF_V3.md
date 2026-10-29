# Oikos NEON manuscript: author's scientific-interpretation review gate (v3)

**Date:** 2026-10-29  
**Status:** **UNAPPROVED EDITORIAL PROPOSAL — NOT READY FOR SCHOLARONE.**  
**Scope:** Only the already closed NEON 16-site manuscript, no new ecological response or EOG-WF endpoint.

## Current operational boundary

The NEON paper's original 32 manuscript/figure/code assets were imported byte-for-byte in PR #663 and are still historically frozen. PR #664 added the Oikos submission policy gate: the original 9-page PDF has an obsolete Data Availability placement, its Introduction starts on page 1, and it lacks an **author-approved** AI use statement. The v2 builder may produce a *different* anonymous PDF after **private human AI-declaration approval**, but that alone does not imply the scientific interpretation has been reviewed following the October 28 audit.

PR #666's independent **post-response algebraic reviewer audit** established:

- At **16/16** fixed sites, a constituent species already attained full world survival **M_obs=1** under the declared one-step spatial criterion. This is a real observation under that endpoint, not a universal method identity.
- Consequently, the observed pooled-minus-best gain **C−M_obs=C−1 ≤ 0** at every original NEON site.
- Under the frozen assemblage-relocation null, the exact community-positive trap set is invariant. Since permuted best-species survival cannot exceed 1, **G_perm ≥ G_obs**, so the **upper-tail permutation p=1 and nonpositive null-adjusted gains follow mathematically** from the observed saturation; the sitewise and aggregate sign results are not independent corroboration that turnover is biologically absent.
- The method is *not* universally unable to detect positive turnover gain: a separately verified **synthetic** four-trap alternating A/B arrangement produces positive raw and positive null-adjusted gain. This is a **model check**, not an additional biological site.
- The original descriptive ecology remains: **13/16** sites have ≥2 individually sufficient species; **32** different species serve that role across sites; none is a provider at >3 sites; ORNL shows an occurrence-metric pooled reduction from **1.0 to 0.25**. None of this directly measures movement, survival, functional redundancy or demographic insurance.

The historical **MANUSCRIPT_V1.md** still describes the initial hypothesis as "rejected completely" and places p=1 alongside the primary effect without explaining its dependent algebraic status. Reusing that unqualified language as a journal-level inference risks overstating the closed result. **The author/coauthors must decide on the proposed interpretation.**

## Concrete author-review-only output (separate from v2 AI-approval gate)

The new reproducible \`build_oikos_ceiling_interpretation_review_v3.py\` checks the original 32 frozen Git blob SHA1s, original locked NEON response fingerprint and independently reviewed PR #666 audit before preparing **a side-by-side diff and a clearly UNAPPROVED candidate**. It makes only the following proposed **interpretive revisions**:

1. **Title and abstract:** report saturation as the empirical ceiling, rather than treating p=1 as a separately decisive negative effect. Preserve the one-time 16-site design, ORNL pooling penalty and the 13/16 / 32-provider observations.
2. **Results 3.1:** retain all numerical values; state the algebra \`G_obs=C−1≤0\` and \`G_perm≥G_obs\` explicitly so that readers see the dependency under the fixed-margin null.
3. **Discussion:** qualify turnover-hypothesis non-support within this fully saturated best-species cohort; separate genuine provider redundancy from unmeasured functional insurance; label the original-code synthetic A/B positive demonstration correctly.
4. **ScholarOne Significance Statement:** propose a *separate*, revised text for coauthor approval. The historical author-prepared statement and the previously verified v2 ScholarOne form field stay unchanged until the user explicitly approves a replacement.

**The original Introduction, all Methods, Results 3.2–3.5, Data Availability, captions and References are byte-for-byte identical inside the proposed candidate**, except for their positions following the modified sections. These and all historical source files in main remain untouched. This is *not* a new data analysis or a new manuscript accepted by human authors.

### Generate reproducible review materials

\`\`\`bash
python -m pytest -q tests/test_neon_small_mammal_oikos_ceiling_interpretation_v3.py
python manuscript/neon_small_mammal_continuity/build_oikos_ceiling_interpretation_review_v3.py \
  --output-dir build/OIKOS_CEILING_AUTHOR_REVIEW_ONLY_V3
\`\`\`

Outputs are **only**:

- \`OIKOS_CEILING_INTERPRETATION_AUTHOR_REVIEW_UNAPPROVED_V3.md\`
- \`OIKOS_CEILING_EDITORIAL_DIFF_UNAPPROVED_V3.patch\`
- \`OIKOS_SIGNIFICANCE_AUTHOR_REVIEW_UNAPPROVED_V3.txt\`
- \`OIKOS_CEILING_INTERPRETATION_REVIEW_PREFLIGHT_V3.json\`, with every author-approved and PDF/submission flag **false**, and complete source/output integrity hashes.

The dedicated CI artifact may contain those proposed texts for author review, **never** a presumed author-approved AI statement, title page or a final PDF.

## Author-only next decisions

**Science interpretation:** approve or revise the corrected ceiling/dependent-null language with coauthors, including a truthful significance field. This is a substantive editorial decision; an AI-generated candidate is not automatically authorized for submission.

**AI disclosure and administrative record:** independently complete the private \`OIKOS_AI_AUTHOR_APPROVAL_TEMPLATE_V2.json\` with actual AI tools/versions and role, human check and full coauthor approval; confirm title page/author order, ORCID, disclosures, journal fields, anonymous reviewer package and the ScholarOne proof. Never invent a declaration or approval.

**Critical compatibility warning:** the existing v2 AI-author-approved PDF builder still uses the *original historical* \`MANUSCRIPT_V1.md\` as its scientific source. Even after the v2 AI-declaration gate passes, do **not** treat that PDF as scientifically cleared for Oikos until the ceiling interpretation in this v3 packet has been explicitly adjudicated by the human authors and integrated in a separately, fully vetted submission build.

The journal submission and final PDF are **not completed** by this PR. EOG-WF retains **3 scored /31 scientific STOPs /3 administrative exclusions**. The PR #666 response audit's observed all-site ceiling is a dependency of the original null p-values, not an independent favorable ecological endpoint.
