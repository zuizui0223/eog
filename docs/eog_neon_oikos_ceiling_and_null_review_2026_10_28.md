# Oikos NEON continuity paper: ceiling-conditioned null and reviewer-risk audit

**Status:** post-response mathematical interpretation audit, 2026-10-28. This is **not a new ecological response analysis**, new confirmatory significance test, independent replication, or change to the original once-only 16-site results. The underlying response and all **32 historical manuscript source blobs remain immutable**.

## Editorial decision relevant to initial submission

The published-in-the-repository, closed study's strongest empirical observation is **16/16 sites have at least one individual species surviving every declared neighbourhood graph**. Under the original all-positive/one-step spatial support rule, the best-species world-survival fraction is therefore \(M_{\mathrm{obs}}=1\) at every site.

Given that observation, **three other apparently different negative endpoints are mathematically constrained**, rather than three separate, statistically independent confirmations:

1. The raw pooled-community minus best-species gain cannot be positive.
2. Under the specified assemblage-row-relocation null that preserves the community-positive trap set, the observed raw gain is the **minimum possible gain** relative to any null relocation. Thus the reported one-sided site permutation upper-tail \(p=1\), and the inability to obtain **positive null-adjusted gain**, follow algebraically.
3. Because an individual species survives every declared graph, no graph can be a *strict guild-only survivor*: a pooled-success graph where every constituent species fails is excluded.

This audit does **not** imply the method was engineered to be incapable of finding emergence. The original suite includes a four-node chain with A and B occupying alternating nodes. Neither A nor B individually has positive one-step support, but the pooled guild does, producing \(M_{\mathrm{obs}}=0\), \(C_{\mathrm{obs}}=1\) and raw gain \(+1\). With the declared row-shuffle null and invented input, the same estimator can yield **positive null-adjusted gain**. The data-conditional saturation ceiling at the 16 NEON sites is therefore distinct from a global mathematical impossibility in the estimator.

## Formal proof — no reaccess to the biological response needed

For site \(s\), define:

- \(C_s\): observed fraction of the fixed spatial graph family where the pooled target guild survives, \(0\le C_s\le1\).
- \(M_s\): maximum over eligible species of their observed fraction of surviving graphs, \(0\le M_s\le1\).
- \(G_s=C_s-M_s\): original raw positive-emergence statistic.
- \(\pi\): a relocation of entire trap assemblages **among the original guild-positive trap locations**, preserving the exact guild-positive node set and the declared graph family. This is the original fixed-margin spatial null.

The source tables record \(M_s=1\) for **all 16 sites**, hence:

\[
G_s^{\mathrm{obs}}=C_s-1\le0.
\]

For every allowable \(\pi\), the guild-positive trap set is unchanged, so \(C_s^\pi=C_s\). No permuted species can have graph-survival fraction exceeding one: \(M_s^\pi\le1\). Therefore:

\[
G_s^\pi=C_s-M_s^\pi\ge C_s-1=G_s^{\mathrm{obs}}.
\]

Every null replicate lies at or above the observed score. **Consequences conditional on the observed site saturation and the frozen null**:

\[
p_{\mathrm{site,upper}}=
\frac{1+\#\{G^\pi\ge G^{\mathrm{obs}}\}}{999+1}
=1,
\]

\[
G_s^{\mathrm{obs}}-\operatorname{median}_{\pi}G_s^\pi\le0.
\]

When all 16 sites satisfy \(M_s=1\), the number of sites with positive null-adjusted gain is necessarily zero, so the original **one-sided sign-test \(p=1\)** follows under its predeclared nonpositive/tie convention. This is a *mathematical implication of the observed ceiling*, **not a second independent test corroborating absence of species-turnover effects**.

Similarly, since \(M_s=1\), some eligible species survives *every* graph; a strict graph where guild survives but **no** species survives is impossible.

### What is empirical rather than algebraically forced?

That **all 16 response-blind selected sites had at least one species with survival 1** is itself an observation under the original site set, target taxon criteria and spatial neighbourhood definitions. The number of such independently sufficient species differs among sites. In original archived site CSVs:

- **13/16** sites contain at least **two** independently fully continuous species.
- **32** distinct species appear as full-continuity providers across the sites; none serves that role in more than **three** sites.
- At ORNL, pooling reduced community survival from **1.0** for the best species to **0.25**, with raw gain **−0.75**; this is a legitimate observed example of the all-positive support rule's sensitivity to additional unsupported sites, *not evidence that more biodiversity generally harms connectivity*.
- The richness/number-of-continuous-species correlation remains **post hoc and exploratory**, subject to the mechanical effect of having more species eligible to count.

These are occupancy-continuity patterns in **trap-level occurrence**, not independently measured movement, survival, population flux, insurance, or ecological functional redundancy.

## Why a reviewer might object to the unqualified original language

The archived manuscript says that turnover-generated emergent continuity was *rejected completely* and reports the negative guild-minus-best-species score, zero null-adjusted gains, zero strict emergent worlds and one-sided \(p=1\). Those are **faithful numerical reports**, but the apparent multiplicity of independent null-supporting indicators is **illusory** once the 16/16 empirical saturation pattern is known.

One-sided \(p=1\) means no evidence in favor of the preregistered **positive-gain** alternative. It is **not a test of an exactly zero ecological mechanism**, cannot establish absence of local complementarity at sites where best-species continuity is not already saturated, and cannot justify a universal claim about species turnover or spatial insurance.

The original test's decision rule can legitimately **not support its predicted positive effect** in this closed, fixed study. The stronger interpretation supported is:

> *In these 16 response-blind selected NEON sites, one or more constituent species already met the entire declared multiscale continuity criterion, leaving no additional positive world-survival fraction that species turnover could contribute. The observed redundancy of individually sufficient species is an ecological occurrence pattern; the additional nonpositive permutation statistics are conditional consequences of the same empirical ceiling.*

### Recommended controlled manuscript wording — requires author sign-off

Suggested *replacement interpretation* for the existing abstract/discussion after author/coauthor approval, not an unauthorized automatic edit of the original manuscript:

> We found no support for the preregistered prediction of turnover-generated emergence under the declared one-step continuity criterion. At all 16 sites, at least one constituent species already had maximal world survival, so positive pooled-minus-best-species gain was precluded given those observations. Because the assemblage-relocation null preserves guild-positive locations, the associated one-sided permutation and site-level sign results are conditional consequences of the observed species-level ceiling rather than independent evidence that turnover is generally absent. Thirteen sites contained multiple individually sufficient species, consistent with occupancy-continuity redundancy under this particular spatial assay.

The original response hypothesis, all numerical results, the null definition, the species roster and the original 32 manuscript blobs **must remain frozen**. This document is a **reviewer-preparation note and proposed qualified interpretation**, not permission to alter the archived paper or bypass author-controlled submission and AI statements.

## Provenance and reproduction

The audit code \`scripts/audit_neon_continuity_ceiling_v1.py\` performs all of the following *without accessing original NEON response records*:

1. Verify all **32 original Oikos manuscript source Git blob SHA1s**, plus the unchanged continuity algorithm and original response fingerprint \`c845289d6ad8caf8e932adb90340237b01b120acce52ca2ccb4e6f1d9c10b860\`.
2. Independently reconcile every one of the **16** original \`site_summary_v1.csv\` and \`site_metrics_v1.csv\` rows and all common numeric fields to 1e−12.
3. Apply the exact data-conditional algebraic ceiling to each site's originally observed \((C_s,M_s)\). Do **not** replay 639 NEON response files, 999 site permutations from original field data, or fabricate an alternative ecological endpoint.
4. Verify the existing **four-node synthetic counterexample** to establish metric non-tautology and positive null-adjusted feasibility (invented data only).
5. Emit a complete 16-site evidence receipt and the independently derivable theorem flags, with source-control, no-new-response, no-author-approval and no-EOG-WF-fourth-endpoint flags.

Reproduce using:

\`\`\`bash
python -m pytest -q tests/test_neon_continuity_ceiling_review_v1.py
python scripts/audit_neon_continuity_ceiling_v1.py \
  --output build/neon-oikos-ceiling-review-v1.json
\`\`\`

The dedicated CI must produce a reviewed complete-result SHA256 lock after the original source-derived JSON is inspected and all package/author-gate regressions pass.

**Submission state remains author-gated:** Current [Oikos policy/handoff](../manuscript/neon_small_mammal_continuity/OIKOS_POLICY_2026_10_27_AUTHOR_HANDOFF_V2.md) requires explicit author-approved AI statement and author metadata before a policy-compliant anonymous PDF can be generated. No AI approval, title page, private correspondence, DOI minting or ScholarOne submission is implied here. EOG-WF **3 scored endpoints /31 scientific STOPs /3 administrative exclusions** remains unchanged.
