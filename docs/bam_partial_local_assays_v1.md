# Original EOG × BAM: which *local* observation is enough? (Exploratory v1)

## Question and evidence level

The merged EOG × BAM geometry-response study, PR #677, showed that a current
distribution can have multiple compatible A/B/M mechanisms, yet some
counterfactual geometric response directions agree across those mechanisms.
Its additional-evidence exercise assumed an *entire axis mask* was known.

This add-on asks a narrower and more operational question:

> Within the original finite-world candidate set, if one can measure a single
> ideal A/B/M state at one site at a time, can a target-aware, truth-blind
> selection strategy resolve the sign of the EOG span response?

This is a **post-exposure exploratory reanalysis of the same 12 artificial
landscapes and 768 already-exposed candidate worlds**. It is not new independent
ecological evidence, not an intervention, and not a verified field survey.

## Frozen source and choices

Protocol fixed *before the new partial-assay scoring* at commit
\`95cd3ca57041983f2c8037768a3f75d8dfe8438c\`.
Source code and geometry are the same as PR #677:
\`benchmarks/bam_geometry_response_envelopes_v1.py\`,
\`eog.v2.known_truth_bam_generality\`, and the original
\`axis_release_outcome\` conventions.

The baseline evidence is ideal **complete current occupancy G**, not
presence-only detections. Within each of its 129 exact-G equivalence classes,
one candidate local measurement is one *noise-free Boolean A, B or M mask
state* at one declared grid cell. This is stronger than observing an organism
or sampling a single plant: the ideal measurement reveals the actual
constraint-mask state without measurement error.

Three target-aware query policies (any A/B/M, only B, only A) select sites
using candidate-world predictions of the **M-release span direction**,
never the hidden true world. An action can then split the candidate set
by its observed binary outcome. The policy runs separately for each
declared target, so different current-G fibres can call for different sites.

For comparison, 16 deterministic SHA-256-ranked generic site policies
(20261107–20261122) use no target response label in choosing a site.
All policies have equal costs and budgets of 0, 1, 2 or 3 assays. They
stop once the target direction is identified, or if no useful candidate
measurement remains.

Selection operates on **distinct (A,B,M) mask triples**, not the number
of arbitrary parameter labels producing each mask. Original world-label
counts are retained as bookkeeping, not independent biological samples
or prior probabilities.

## Local exploratory readout — requires canonical CI replay

Under the primary M-release span target, 8 of 129 current-G classes are
initially direction-ambiguous, including 5 with both positive and
negative possible span responses.

| Assay policy | Zero sites | One ideal site | Two ideal sites | Three ideal sites |
|---|---:|---:|---:|---:|
| Target-aware, choose A/B/M | 121/129 | 126/129 | **129/129** | 129/129 |
| Target-aware, B sites only | 121/129 | 126/129 | 126/129 | 126/129 |
| Target-aware, A sites only | 121/129 | 121/129 | 121/129 | 121/129 |
| Generic hashed sites: median of 16 seeds | 121/129 | 122/129 | 125/129 | 128/129 |

These are **number of G fibres for which every possible truth mask branch
ends with an identified direction**. One ideal site is not guaranteed
to resolve an arbitrary actual field population. Adaptive two-site
selection means the *second site can depend on the first observed bit*.
Two sites per class are sufficient under this chosen strategy and fixed
model universe; the study does not claim a general optimal lower bound.

Other response targets use identical rules: target-aware all-axis
policies reach 129/129 A-release span-direction classes within two
sites, and 129/129 B-release classes within **one** ideal site.
The M result's B-only ceiling of 126/129 matches the parent result
for an ideal entire B mask. The remaining 3 families require
information from another axis in this finite candidate set.

## Scope limits and safeguards

- This is **model-based measurement planning**: candidate response labels
  are available to the planner but the true world's label is hidden.
  Candidate-world assumptions can fail in real ecology.
- A one-site observation has no assigned detection error or cost
  heterogeneity, and an entire complete current distribution is
  assumed known. Real-world measurements are substantially weaker.
- Span is the original positive-distance 90th-percentile EOG readout,
  not hull area, true niche breadth, true dispersal or causal mechanism.
  All geometry uses *full census* occupied cells, not the prior
  matched-size comparison.
- No candidate-world probability, confidence interval, species
  prevalence, field effect or predictive superiority is inferred.
- Count 129 equivalence classes nested in **12 constructed landscapes**,
  not 129 independent ecological species or replicates.
- Hash-based generic policies are a defined alternative query strategy,
  not a neutral representation of all conceivable field sampling.
- The Charaxes real-data resource-geometry result cannot directly
  validate this ideal perfect-current-G and noiseless-BAM assay planner.

## Reproduction

\`\`\`bash
python -m pytest -q tests/test_bam_partial_local_assays_v1.py
python benchmarks/bam_partial_local_assays_v1.py \
  --output-dir /tmp/eog_bam_partial_local_assays
\`\`\`

The canonical CI uses the **original generator** and freezes
the source-code hash. Every candidate truth path is audited:
a measurement may shrink, never expand, its compatible model
set; model truth must remain; identification cannot be lost.

Outputs: \`summary.json\`, \`fibre_budget.csv\`, \`paths.csv\`,
\`summary_sha256.txt\`. A GitHub Actions receipt must be pinned
only after canonical verification. Result expectations were inspected
locally and are regression checks, not independent preregistration.
