# Original EOG external target-specific history retention — v28 Leopold benchmark

## Purpose

v26 showed in known truth that present ecological states retain a target-specific
projection of hidden distributional history. v27 attempted to move this idea into a real
assembly-history experiment but stopped before scoring because independent reuse was not
authorized and multivariate experimental-unit identities were not preserved.

v28 uses a different published experiment that passes those two pre-screen requirements:
Leopold & Busby (2020), *Current Biology*, “Joint effects of host genotype and species
arrival order determine plant microbiome composition and function.”

This remains an **external benchmark**, not a fresh discovery test. The original paper,
repository README, analysis code and qualitative headline have already been viewed before
v28 scoring.

## Source freeze

Canonical source repository:

- `dleopold/Populus_priorityEffects`
- pinned repository commit: `d8082daabfccccf3bcbdd631b4438f44c04014c1`
- GitHub license: MIT (`LICENSE.md`)
- corresponding Dryad dataset: DOI `10.5061/dryad.7p2cv` (Dryad CC0)

Source blobs used by the benchmark:

- sample metadata: `data/Sample_data.csv`
  blob `dcdc54ff26013714ab29ddce77211ac3b0043938`
- processed OTU matrix: `output/compiled/OTU.table.csv`
  blob `8784a02f7617a7cc207e3da8c7798753d082a4b6`
- taxon-bias estimates: `output/tabs/bias.csv`
  blob `45167a953653e7706e8a515516309bc6afec4cf5`
- rust measurements: `data/rust_measurements.csv`
  blob `a98138a2355f72b6946ba34138696d971c2cab37`

Raw source files are read from the pinned public source and are not copied into EOG.

## Biological question

The manipulated history variable is the identity of the fungal species introduced first
(`Treatment`).

The target-specific question is:

> **How much of this manipulated colonization history is retained in the later fungal
> community state, and how much is retained in the host disease state, after accounting
> for host genotype and allowing history effects to differ among genotypes?**

This does not ask whether priority effects exist. That is already a published result.

## Experimental unit and common-unit contract

The plant is the experimental unit.

For community state use the original paper's Timepoint 1 community sample. The source
code explicitly uses Timepoint 1 because the later sequencing sample was collected during
rust sampling and was overwhelmed by rust reads.

For rust state aggregate leaf measurements to the plant-level `SampID`, reproducing the
published aggregation:

[
\mathrm{lesion\ fraction}
=
\frac{\sum \mathrm{Lesion\_cm2}}
     {\sum \mathrm{Leaf\_cm2}}.
]

Community sample IDs have the form `<plant>.TP1`; rust IDs use `<plant>`.
The only allowed join is exact removal of the terminal `.TP1`.

Primary inference uses the **same plants for both targets**. A plant enters the common
panel only when all of the following are true:

1. metadata `Samp_type == "Experiment"`;
2. `Timepoint == 1`;
3. treatment is one of the five observed arrival-order treatments:
   Alternaria, Aureobasidium, Cladosporium, Dioszegia, Fusarium;
4. genotype is nonmissing;
5. the TP1 sample ID exists in the processed OTU table;
6. the base plant ID has rust measurements.

No missing unit is replaced and no sample may be recovered by approximate string matching.

## Primary targets

Exactly two primary targets are frozen.

### Target 1 — fungal community composition

Use only the five fungal taxa that define the arrival-order treatment family:

- Alternaria
- Aureobasidium
- Cladosporium
- Dioszegia
- Fusarium

For each common-panel plant:

1. take processed read counts for these five taxa;
2. divide each count by its frozen taxon-specific `Bhat` from `bias.csv`;
3. retain structural zeros as zero; do not apply post hoc zero replacement;
4. normalize the corrected five-taxon vector to sum to one;
5. if the corrected five-taxon sum is zero, mark that plant target-missing rather than
   adding a pseudocount;
6. calculate Bray–Curtis distance among plants.

This representation is intentionally simpler than the original paper's full
zero-replacement pipeline. It is frozen before scoring and is audited by raw-count
sensitivity below.

### Target 2 — host rust lesion fraction

Aggregate `rust_measurements.csv` to plant ID using:

[
y_i =
\frac{\sum \mathrm{Lesion\_cm2}}
     {\sum \mathrm{Leaf\_cm2}}.
]

Use the raw plant-level fraction as the primary scalar target. No outcome-dependent
transformation is selected after scoring.

## Context and estimand

Host genotype is a known context variable and the published paper reports
genotype-dependent arrival-order effects. Therefore a treatment main-effect-only model is
not an adequate history estimand.

For each target define:

### Reduced model

[
M_0: \quad 1 + \mathrm{Genotype}.
]

### Full model

[
M_1: \quad 1 + \mathrm{Genotype}
+ \mathrm{Treatment}
+ \mathrm{Genotype}\times\mathrm{Treatment}.
]

The **history-retention effect** is the incremental target variation explained by all
terms involving manipulated arrival history:

[
R_H =
\frac{SS_{res}(M_0)-SS_{res}(M_1)}
     {SS_{res}(M_0)}.
]

For rust this is ordinary nested-model partial (R^2).

For community composition use the corresponding Gower-centered distance-based nested
partial (R^2).

(R_H) is a dimensionless target-specific retention profile. The two targets are not
assumed to have identical sampling distributions, so v28 does not perform a naive
parametric test of equality between their (R_H) values.

## Randomization diagnostic

Treatment is permuted **within host genotype**, never globally.

Each permutation preserves:

- the exact common-panel plant set;
- genotype;
- treatment counts within each genotype;
- both response targets.

The full-vs-reduced (R_H) statistic is recomputed after permutation.

Primary permutation count: 9,999.
Seed: 20261005.

The permutation value is a diagnostic, not a binary acceptance criterion.

## Secondary sanity target

One secondary target is frozen before scoring:

### First-colonist proportional abundance

For each plant, select the abundance of the taxon named by that plant's `Treatment`
from the corrected five-taxon composition.

This directly measures the ecological state most closely tied to preemptive colonization.
It is a positive-control / mechanism-facing target, not a third primary endpoint.

## Frozen sensitivities

Only the following sensitivities are allowed:

1. **raw-count composition** — normalize the same five taxa without `Bhat` correction;
2. **published outlier exclusion** — remove `G4.T2.R5.TP1`, which the original source
   code excluded for model-fitting instability;
3. **matched-panel stability** — report composition-only score on all structurally
   eligible TP1 plants and compare it descriptively with the common-panel score;
4. **region summary** — aggregate target scores descriptively within East and West
   regions; no new inferential claim.

No new target or transformation may be added after scoring.

## Pre-score structural facts already viewed

Before the freeze, source schema inspection established:

- 252 non-negative experimental Timepoint-1 metadata rows;
- 12 host genotypes;
- 5 arrival-order treatments;
- unique TP1 → base plant-ID mapping;
- 237 of the 252 TP1 base IDs have rust measurements;
- OTU table contains named focal-taxon columns;
- the source repository contains an explicit MIT license.

These are design facts, not v28 outcomes.

## Exposure boundary

Already viewed before v28 scoring:

- published qualitative conclusion that arrival order affects fungal community composition
  and function;
- original source code using `Genotype * Treatment`;
- original source code using Timepoint 1 for community analysis;
- original published rust aggregation;
- source schema and first rows;
- the names of the focal taxa and bias factors.

Not yet viewed through the v28 estimand:

- common-panel (R_H) for fungal composition;
- common-panel (R_H) for rust lesion state;
- first-colonist proportional-abundance (R_H);
- genotype-stratified permutation distributions;
- target-retention ordering under the frozen sensitivities.

## Claim boundary

v28 must not claim:

- discovery of priority effects;
- discovery of genotype × arrival-order interaction;
- reconstruction of the true colonization trajectory;
- that a larger (R_H) means the target is biologically more important;
- that the two target (R_H) values are directly comparable as likelihood-based
  effect sizes;
- that failure to retain history in one target means ecological history is absent.

The intended contribution is narrower:

> **Using one randomized assembly-history experiment and one common set of experimental
> units, EOG can quantify how strongly the same manipulated history remains visible in
> different present ecological targets.**

## STOP rules

Stop rather than repair if:

1. the pinned source blobs cannot be recovered;
2. OTU sample IDs do not join exactly to the frozen metadata;
3. TP1 → base plant IDs are not unique;
4. rust leaves do not aggregate unambiguously to base plant ID;
5. any common-panel plant carries conflicting genotype or treatment labels;
6. fewer than three treatment levels remain after the common-panel filter;
7. the five focal taxa are absent from the pinned OTU table;
8. genotype × treatment full design is rank-deficient beyond ordinary missing-cell
   structure such that the incremental history subspace cannot be identified;
9. scoring would require an outcome-informed extra filter or transformation.

## Next step after freeze

After this document and the machine-readable protocol are committed:

1. implement generic nested-design partial-R² functions and tests without source outcomes;
2. run the source adapter against the pinned blobs;
3. freeze the exact common-panel manifest;
4. only then calculate the three frozen target scores.
