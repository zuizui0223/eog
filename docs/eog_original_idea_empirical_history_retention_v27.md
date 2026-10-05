# Original EOG empirical history-retention benchmark — v27

## Purpose

v26 established in known truth that a present landscape does not simply remember or
forget colonization history. Different declared present-state targets can retain
different amounts of the same hidden colonization-age information.

v27 asks whether that diagnostic can be made ecologically legible in a real manipulated
assembly-history experiment.

This is an **external empirical benchmark**, not a fresh confirmatory test of whether
history affects ecosystem state. The published paper and its headline results were read
before this protocol was frozen.

## External benchmark

Primary benchmark:

Catano, Groves & Brudvig (2023), *Ecology* 104:e3910,
“Community assembly history alters relationships between biodiversity and ecosystem
functions during restoration.”

Public data DOI: 10.5281/zenodo.7120895.

The experiment initiated otherwise matched tallgrass-prairie restorations in three
establishment years (2014, 2015, 2016), followed species and trait trajectories over six
years, and measured ANPP, decomposition and floral-resource production in 2019–2020.

The publication already reports that establishment history affected species/trait
trajectories and that effects differed among ecosystem functions. Therefore v27 may not
claim discovery or independent confirmation of those directions.

## EOG question

The EOG-specific question is:

> **How much manipulated assembly history is retained in each declared present-state
> target when all targets are evaluated under the same experimental-unit and
> resampling contract?**

The object of interest is a **history-retention profile**, not a single “history matters”
test.

## Frozen target family

Restrict the empirical benchmark to 2019–2020, the two years in which the three ecosystem
functions were measured.

Declare seven target families before raw-data access:

1. species composition;
2. trait composition;
3. species diversity;
4. functional dispersion;
5. ANPP;
6. decomposition rate;
7. floral-resource production.

No target may be added because its result is favorable after scoring.

## History variable

The manipulated history label is establishment-year treatment: 2014, 2015 or 2016.

This label intentionally captures the realized assembly history created by the staggered
restoration treatment. It is **not** interpreted as a pure causal effect of calendar
year, succession or plot age separately.

Observation year (2019 versus 2020) is retained as a nuisance/time term.

## Experimental unit

The establishment-year treatment was assigned at the restoration-plot level.

Therefore:

- plot is the treatment/randomization unit;
- subplots are not treated as independent history replicates;
- permutations of establishment-year labels occur only among whole plots;
- resampling is plot-blocked;
- repeated subplot/year observations remain grouped with their plot.

Any analysis that treats the 144 subplots as 144 independent treatment replicates is
invalid for the primary benchmark.

## Primary estimand

For each target k, estimate

    R_k = partial variance attributable to establishment-year history

after accounting for observation year under a target-appropriate model.

The aim is not to force identical likelihoods across incompatible response types, but to
return a common dimensionless history-retention scale wherever defensible.

### Scalar targets

For species diversity, functional dispersion, ANPP, decomposition and floral resources,
compare a full model containing establishment year + observation year against the same
model without establishment year.

Primary effect size:

- partial R² attributable to establishment year.

Use the original transformations where needed for diagnostics, but report effect size on
the frozen transformed scale and retain raw-scale descriptive summaries separately.

### Multivariate targets

For species and trait composition:

- species composition distance: Bray–Curtis on declared abundance/cover representation;
- trait composition distance: Euclidean distance on the declared community-weighted
  trait representation;
- estimate partial PERMANOVA R² attributable to establishment year after observation
  year;
- restrict permutations to the plot-level treatment unit.

If the published dataset does not materialize the required target representation without
post hoc reconstruction ambiguity, mark that target STOP rather than silently change the
estimand.

## Secondary retention diagnostics

For each target report:

- point estimate R_k;
- plot-blocked bootstrap interval;
- exact/permutation diagnostic where valid;
- 2019-only and 2020-only sensitivity estimates;
- target rank by R_k;
- pairwise rank stability under declared sensitivities.

Do not threshold R_k into “history remembered / forgotten” as the primary result.

## EOG interpretation rule

A target with larger R_k is interpreted only as retaining more of the manipulated
history signal under this benchmark and representation.

Do not infer:

- the historical mechanism;
- a unique assembly trajectory;
- causal mediation by unmeasured states;
- that a low-R_k target has no ecological memory in general;
- that a high-R_k target is intrinsically more important.

## Benchmark success criterion

v27 succeeds methodologically if it can produce an auditable, target-specific retention
profile while respecting plot-level replication and while reproducing the broad published
fact that history effects differ across state variables.

It does **not** require a new biological finding.

The benchmark is especially informative if the seven targets are not ordered by a simple
“finer state always retains more history” hierarchy, but that outcome is descriptive
because related published results were already visible before freezing.

## Freshness / exposure boundary

Already viewed before raw-data scoring:

- establishment-year treatment design;
- existence of species and trait trajectories;
- existence of ANPP, decomposition and floral-resource endpoints;
- published direction that ANPP and floral resources differ among establishment years;
- published direction that decomposition did not clearly differ;
- published conclusion that history alters biodiversity–ecosystem-function relationships.

Therefore none of these may be presented as preregistered discoveries.

Not yet accessed for v27:

- raw Zenodo files;
- exact row-level values;
- EOG retention estimates;
- plot-blocked bootstrap distributions;
- target-retention ranking under the frozen v27 estimand.

## STOP rules

Stop rather than repair post hoc if:

1. plot identity cannot be reconstructed unambiguously;
2. establishment-year assignment cannot be mapped to plot without guessing;
3. 2019–2020 targets cannot be joined without ambiguous many-to-many linkage;
4. response variables require outcome-informed filtering not declared here;
5. species/trait representations cannot be reconstructed from public materials;
6. fewer than two establishment-year treatment levels survive a required-data filter;
7. a published processing step cannot be reproduced sufficiently to define the target.

STOP is not adverse biological evidence.

## Novelty boundary

v27 does not claim that:

- assembly history or priority effects are new;
- time since establishment affects ecosystem function for the first time;
- history effects across ecological organization have not been compared before;
- partial R² or PERMANOVA is new.

The role of v27 is narrower:

> **to demonstrate that EOG's target-specific history-retention concept can be audited on
> a real manipulated ecological history using a common target declaration, experimental
> unit and provenance contract.**

## Next action after freeze

Only after this document and its machine-readable protocol are committed may the public
raw data be downloaded and scored.
