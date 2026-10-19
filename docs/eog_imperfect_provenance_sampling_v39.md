# EOG v39 — noisy provenance and incomplete source sampling

**Before result:** The fixed protocol at \`validation/eog_original_idea_imperfect_provenance_v39/protocol_v39.json\` was committed at \`582833e08d3f35075783ff51a845deee26dc8468\` BEFORE imperfect-tag simulations were scored.

## Ecological question

Earlier EOG v23 used an idealized, error-free label of the **source of earliest arrival** at a node. The full occupancy snapshot library alone uniquely identified 579/768 activation histories; perfect occupancy plus a potentially complete provenance assay library identified 687/768. v23 does **not** establish that field-collected genetic ancestry, a later observed migrant's origin or noisy assignments have the same information.

Saatoglu et al. (2021), Molecular Ecology doi:10.1111/mec.16083, demonstrates why the distinction matters: genetic assignment error and the fraction of source populations genotyped are relevant observation processes. The original Dryad individual records could not be accessed through the tested official URL in EOG #652 (HTTP 403); no 2021 error rates or measured ancestry were used in v39.

This follow-on **known-truth** experiment asks:

> When source tags are noisy or only a fraction can be measured, is topology-based sampling at potential confluence sites more informative about history than equally budgeted history-blind node sampling? Where does the incremental value over complete occupancy disappear?

## Fixed simulation

Reuse exactly the v23 384 landscapes crossed by clustered vs dispersed source geometry (768 design rows), the same three activation histories, and the four complete post-activation non-source occupancy snapshots at t=4, 5, 6 and 8. A truth is drawn uniformly from those three histories. There is no use of real genetic samples or field outcomes.

Each ideal source tag reports the precise **set of sources tied for earliest arrival** in the synthetic graph. This is a first-arrival order readout, not actual genome-wide ancestry. A measurement channel has:

- **Coverage q = 0, 0.25, 0.60, 1.00:** the assay is missing at probability 1−q, independently of the hidden history.
- **Miscall e = 0, 0.10, 0.25:** if measured, its exact categorical tag is correct with probability 1−e; otherwise its report is uniformly distributed among all other declared tag categories at that node, including one synthetic "unseen label" category.
- The likelihood is *known exactly* for this controlled simulation; there is no inference of actual genotyping quality.

The **same budget of at most three sites** is compared for three observation policies:

1. \`confluence_targeted\`: choose sites potentially reachable from at least two sources (static source geometry), prioritizing those with more possible sources and deterministic node-ID ties. Do not use the outcome-dependent earliest-source values.
2. \`random_response_blind\`: choose a deterministic pseudo-random set of up to three non-source nodes, based on a fixed SHA256 ranking of scenario metadata/node ID; no peeking at tags or correct history.
3. \`unique_origin_negative_control\`: choose sites reached by exactly one graph source, where a correct earliest-origin tag cannot vary with activation history.

### Avoiding an unfair comparison

Confluence sites may be absent or fewer than three. Every policy's actual selected-node count is reported, not assumed. A stricter **equal-budget, occupancy-aliased** stratum includes only designs with ≥3 potential confluence sites and ≥3 non-source sites; that is the primary comparison for confluence-vs-random at q=0.60, e=0.10. Overall and complete-occupancy-alias strata are reported separately.

### Target and estimand

The inferential target is **which of the three synthetic activation histories generated observations**, not the identity of the actual genetic donor of a sampled bird and not an observed colonization route. Original v23 full occupancy snapshots are treated as deterministic, whereas noisy provenance reports are processed using their specified error likelihood.

The benchmark calculates exactly, by finite enumeration of all missing/observed categorical reports, the expected:

- additional conditional mutual information \`I(H; P_reports | O_t4,t5,t6,t8)\` in **bits**;
- incremental Bayes-optimal correct-history classification accuracy over occupancy only.

When e>0, all candidate tag categories may have positive probability in multiple histories, so full elimination of histories from a mislabeled report would be unjustified. **Do not use ideal-tag exact identification counts as if they were accuracy under imperfect sampling.**

### Predeclared falsifiable hypotheses

- **P1:** with q=1 and e=0, confluence sampling yields positive information among equal-budget occupancy-aliased designs.
- **P2:** unique-origin sites add precisely no history information for any q/e, including noisy measurement (structural negative control).
- **P3:** confluence-targeted sampling beats response-blind random sampling on average under **q=0.60, e=0.10**, equal-budget occupancy-aliased comparison. May be refuted.
- **P4:** average added information decreases with increasing miscall rate and increases with assay coverage. Failures remain refutations or channel implementation defects, not a reason to change the noise channel.
- **P5:** confluence sampling at q=0.60/e=0.10 still strictly improves expected correct-history classification on equal-budget occupancy-aliased designs.

Additional safeguards: zero coverage yields zero benefit, all parent v23 occupancy and perfect-library identifiable row counts must reconcile exactly (768/579/687), and correctly modeled noisy observations cannot lower **expected** Bayes-optimal accuracy.

## What a positive result could and could not mean

It could motivate testing *sampling at source-basin overlaps* rather than spreading genetic assays uniformly when the goal is to discriminate alternative source histories. It would not demonstrate that real genetic assignments are actual first-arrival source tags, that missingness is independent, that errors are uniform, that this assay has the assumed coverage/cost, or that any actual founder/colonization history is identified.

No EOG-WF fourth endpoint is created. The previously frozen EOG-WF validation stays at 3 scored, 31 scientific STOPs and 3 administrative exclusions.

## Reproducibility

\`\`\`bash
python -m pytest -q tests/test_eog_imperfect_provenance_sampling_v39.py
python benchmarks/run_eog_imperfect_provenance_sampling_v39.py \
  --output build/eog-v39-imperfect-source-provenance.json
\`\`\`

The dedicated CI builds the result from the source simulator and compares the complete reviewed JSON after it has been independently inspected and frozen. The simulator never opens a Dryad data file or a private bird record.


## First fully preregistered result — 2026-10-19

The dedicated [GitHub Actions run 39237967536](https://github.com/zuizui0223/eog/actions/runs/39237967536) passed the original v23 parent checks and all unit tests, then executed all 768 known-truth design worlds. The complete simulation result was independently downloaded as artifact **12180415330** (\`EOG-V39-NOISY-PROVENANCE-KNOWN-TRUTH-AGGREGATES\`), ZIP SHA256 \`ad41b561b4ed1255252dc094749c318320976d289bb06664239b088b4828dd75\`. Full canonical result JSON SHA256: \`eefbd3c2ef69e532d6efc5fef66fd7ec97def75e6dd6b74d533d042e78aaa865\`. The complete JSON is stored in the Actions artifact; its **entire canonical SHA256** and key science results are frozen at \`validation/eog_original_idea_imperfect_provenance_v39/result_frozen_v39.json\`, and every subsequent CI run must match that hash.

All parent truths reconciled exactly:
- v23 design rows: **768**;
- four-snapshot occupancy uniquely identifies exact history in **579**;
- complete ideal occupancy plus all provenance tags uniquely identifies **687**;
- occupancy alias residual: **189**;
- **88/189** occupancy-aliased designs have at least three potential confluence sites and are fair equal-three-site comparisons.

### Primary equal-budget comparison (88 occupancy-ambiguous worlds, exactly 3 sites)

Assumed synthetic assay coverage \`q=0.60\` and categorical misassignment \`e=0.10\`:

| Assay placement | Mean additional I(H; P_reports \| occupancy), bits | Mean improvement in Bayes correct-history probability |
| --- | ---: | ---: |
| Potential source confluence sites | **0.655816** | **0.333056** |
| Response-blind SHA256-random sites | 0.648676 | 0.330346 |
| Static single-origin sites (negative control; site count often zero) | 0.000000 | 0.000000 |

The mean mutual-information advantage of confluence targeting over random site placement was just **0.007140 bit**, and the improvement in correct-history probability was **0.002710 (0.271 percentage points)**. P3's preregistered *directional* claim is supported, but this effect is **too small** to warrant saying that confluence-targeted genetic field sampling is generally optimal or materially superior without independent replication, sampling costs and site-selection uncertainty. The random design has one fixed source-blind SHA256 rank seed; broader placement-randomization robustness has not been preregistered/tested.

The perfect, complete q=1/e=0 confluence design gave mean **0.836489 bit** and **0.393939** extra correct-history probability. Even q=0.25/e=0.10 retained **0.360665 bit** (mean accuracy gain **0.196645**). Reduced coverage and greater synthetic miscall rates reduce, but do not instantaneously abolish, conditional history information in this world universe.

### What happens across all original world designs?

At q=0.60/e=0.10, averaged over all **768** (including **579** worlds where occupancy already uniquely identifies history), confluence-targeted tags add only **0.099464 bit** and **0.050228** expected correct-history probability; response-blind random adds **0.098645 bit** and **0.049917**. Across all **189 occupancy-aliased worlds**, information is **0.404169 bit** versus **0.400845 bit**. These are different denominators and should not be reported as equal-budget field sampling comparisons (average selected confluence sites **1.66**, random **1.92** among aliases).

Source geometry was a major modifier in this controlled universe. At q=.60/e=.10 within occupancy-aliased worlds:

- **Clustered source geometry** (153 aliased designs): confluence **0.496531 bit**, random **0.492425 bit**.
- **Dispersed source geometry** (36 aliased designs): both **0.011631 bit**.

The vast difference is about how informative provenance *could be after the occupancy evidence* in these specific synthetic source configurations. It is **not** a measured field difference between farms/non-farms, a natural population estimate, or causal inference about island source geometry. Some dispersed-world occupancy signatures already resolve history, and the two alias subsets are not a matched comparison of ecological treatment groups.

### Preregistration verdicts / caveat

All five preregistered directional hypotheses **P1–P5 SUPPORTED** under the fixed simulation settings, with zero negative-control violations. P2 (unique-source-site invariance) and P4 (properly specified noise/coverage monotonicity) are mainly **model-integrity/structural properties**, not independently novel biological observations.

The main result is more specific than "genetics helps":

> **Imperfect observations of source-of-first-arrival can retain conditional information about a history even after detailed occupancy snapshots, but information yield is strongly context dependent, and merely choosing topological confluence sites yields only a small mean gain over a fixed response-blind random sample at three sites.**

The original v23 source tags record **earliest source arrivals of a diffusion simulation**. Actual SNP ancestry, parentage, genomic assignment and natal origin in Helgeland are **not** equivalent measurements by definition. The 2021 Saatoglu Dryad data remained inaccessible through the verified official URL (HTTP403 in PR #652); no empirical genotyping values, actual assignment-error rates, survey-effort records or movement outcomes entered v39.

The original EOG-WF 3 scored / 31 scientific STOP / 3 administrative exclusion boundary is untouched.
