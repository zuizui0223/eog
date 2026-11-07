# EOG × BAM: does one missed occupied cell change a geometric-response decision?

## Scientific question

The existing EOG × BAM target-identification analysis showed that
**121 of 129** exact-current-G equivalence classes identify the direction
of the *ideal M-release change in 90th-percentile environmental pairwise
span*. A separate noiseless A/B/M site-assay planner could resolve the
remaining eight with up to two adaptively chosen assays.

This follow-up tests the dependency on the **perfect current G map**,
without adding field data or retuning the original result. It asks:

> When an otherwise complete current distribution map may have missed
> exactly zero or one truly occupied cell, which geometric-response
> decisions remain robust, and how many ideal local A/B/M measurements
> recover them?

This is a retrospective exploratory **known-truth stress test of the
same already-exposed 12 model landscapes and 768 candidate worlds**.
The model worlds, EOG reference and BAM axis-release definitions are unchanged.

## Fixed source, measurement and outcome

Pre-score protocol commit:
\`cc89f3ac67cf05bd9a42a3a0d17644f10bca4f42\` at
\`validation/bam_one_missed_G_v1/protocol_v1.json\`.

True current G = A∩B∩M. For every distinct G within each landscape,
enumerate all possible observed maps \`D = G\` and
\`D = G \ {i}\` for every occupied cell \`i\`.
An unseen occupied cell is the **only** permitted source of map error:
every otherwise unobserved grid cell is certified unoccupied except
the one possible miss, and no false positives occur.

A candidate world with true G' is compatible with D exactly when
\`D ⊆ G'\` and \`|G' \ D| <= 1\`. This is much stronger
than opportunistic presence-only occurrence records and does not
estimate a probabilistic detection rate.

Primary response target: the sign of the **original full-census EOG
90th-percentile strictly positive pairwise environmental span change**
after ideal M release (M removed; candidate response G'=A∩B).
A and B releases are fixed secondary targets. Every world has its own
true G, so when D admits several G values its response is calculated
relative to that world's actual complete G—not a fabricated geometric
span of the incomplete observation D.

All environmental coordinates use each parent landscape's **unchanged
shared median/MAD reference**. Sign tolerance is the original
scale-aware \`1e-10\` criterion. No newly selected features or response
thresholds.

## One-to-three-site model-based evidence

From the finite candidate set compatible with D, choose one ideal
noise-free **A, B or M constraint-state measurement at a single grid
cell**. A/B/M are direct mask bits in the generator, not field measures.
For target-aware greedy selection, maximize the number of pairs of
distinct compatible mask triples with different response directions
separated by the query. Ties break A/B/M then row-major cell order.
A queried site's **true bit is hidden until after selection**.

Controls: B-only target-aware, A-only target-aware, and 16
predeclared SHA-256-ranked target-blind site-choice strategies.
All use budgets 0, 1, 2 and 3 with equal nominal costs.
Original 64 parameter-world labels within a landscape are **not**
probabilities or independent observations. Repeated A/B/M signatures
are deduplicated before decisions.

## Numerical result and two distinct denominators

The 129 original true-G classes produce **2,627 distinct (landscape,
observed D) patterns**, of which 48 admit more than one possible true
G. Each observational fibre retains every compatible original parameter
world; these 2,627 patterns are not independent samples.

**Primary M-release:**

| Assumptions / target-aware all-axis budget | True-G classes robust against *every* omission | Distinct observed-D fibres with unanimous direction |
|---|---:|---:|
| Original perfect G baseline, no added assay | 121 / 129 | N/A |
| At most one missed occupied cell; zero assays | **86 / 129** | 2,483 / 2,627 |
| + one noiseless local assay | **117 / 129** | 2,570 / 2,627 |
| + two noiseless local assays | **121 / 129** | 2,623 / 2,627 |
| + three noiseless local assays | **129 / 129** | 2,627 / 2,627 |

The **robust true-G** criterion is deliberately stronger than a
single conveniently chosen observation: for each of the original 129
true G maps, *every* possible D it could generate must be decision-
identifiable for every surviving candidate truth path.

For this primary M target, B-only local assays plateau at 98/129
robust true-G classes; A-only at 88/129. The 16 generic target-blind
policies have median robust counts **86, 102.5, 113, 122** at budgets
0,1,2,3. The medians can be half-integers because they summarize
16 algorithmic seeds, not populations or biological replications.

Other original release targets (A,B) are retained in full:
target-aware A-release robust-G counts 64→115→124→129;
B-release 81→110→127→129 across budgets 0–3.
No negative, null or ambiguous classes have been discarded.

## Post-result exact optimality audit

After the initial exploratory scoring, an **independent exhaustive
binary decision-tree audit** considered *every* variable local A/B/M
query at each D, including both possible observed-bit branches.
This is post-result verification, not another preregistration.

For the M-release target, the **minimum worst-case adaptive query
depth** across 2,627 distinct D patterns was:

| Exact minimum | Number of observed-D patterns |
|---|---:|
| 0 | 2,483 |
| 1 | 87 |
| 2 | 54 |
| 3 | 3 |

The corresponding **optimal** true-G robustness is
86→117→**123**→129; the fixed greedy selection reaches
86→117→**121**→129. Thus, the greedy algorithm is not
globally optimal at two queries in this finite dataset.
Nevertheless **three** ideal queries are genuinely required for
three observed-D patterns; this is not solely a greedy algorithm
artifact.

Do not call this a field sampling-minimum theorem. It is exact only
for the predeclared finite candidate-world support and perfect
noise-free A/B/M binary queries.

## Why this advances the original EOG × BAM claim

A geometric decision that is fully determined from an exact current
distribution may become indeterminate from a *nearly* complete
distribution. The same framework can keep **all compatible G and
BAM decompositions** instead of treating a missed positive as a true
absence. Target-specific local measurement restores some decisions
without requiring full mechanism recovery.

This is a conditional structural robustness theorem for this finite
worldset, not an ecological law or proof of EOG predictive superiority.
No species, site, experiment, new independent natural response or
fourth EOG-WF endpoint is added.

## Verification and reproduction

\`\`\`bash
python -m pytest -q tests/test_bam_one_missed_G_v1.py
python benchmarks/bam_one_missed_G_v1.py --output-dir /tmp/eog_one_miss
python benchmarks/audit_bam_one_missed_exact_queries_v1.py \
  --output /tmp/eog_one_miss/exact_minimum.json
\`\`\`

CI checks the canonical source-generator blob, exact 12×64 roster,
129 original G classes, 2,627 unique observation patterns,
source-perfect parent results, all three release axes,
truth-blind site choice and the independent exact-query audit.
Only after a successful canonical run should the post-result artifact
fingerprints be pinned in a separate receipt.

## Limits and next scientific dependency

- Perfect current G was relaxed **only by one false-negative occupied
  cell**, not by a realistic detection model with repeated imperfect
  encounters, false positives or effort heterogeneity.
- The local A/B/M measurements are still **noiseless direct mask
  readings** with equal costs. In practice, interactions and migration
  barriers often have noisy indirect proxies.
- The study's 12 synthetic landscapes are not independent natural
  species and do not represent an ecological prevalence distribution.
- The world universe itself is assumed complete; omitted real-world
  mechanisms invalidate any claimed universal certainty.
- No inference about actual climate adaptation, species movement,
  host interaction causality or occupied-area forecasting follows from
  the static mask-release experiment.
