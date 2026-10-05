# EOG v29 frozen design — wood-decomposer target-specific history retention

## Status

**FROZEN BEFORE ANY V29 TARGET SCORING.**

The raw Dryad CSV byte streams remain blocked to automated access by Dryad transport
controls, but the official Dryad metadata API and official preview endpoints exposed
sufficient source schema to freeze the analysis contract without calculating any target
score.

No EOG v29 partial R², null distribution, or cross-target contrast has been calculated
before this protocol.

## Source

Leopold et al. (2017), *Ecology Letters* 20:1054–1063.

Article DOI: `10.1111/ele.12803`

Dryad DOI: `10.5061/dryad.7p2cv`

Dryad version/resource ID: **13946**

Frozen public file identities:

- `sample.data.csv` — file 52325, MD5
  `d35287fd5f8522d8180451d42dc8969b`, 35,448 bytes;
- `species.prevalence.csv` — file 52326, MD5
  `1f879a53fafcaaa5d148dbe112d3b389`, 12,148 bytes;
- `collembola.csv` — file 52327, MD5
  `b7264f326709ab41d1fe8cac8ddc4a48`, 2,621 bytes.

Dryad distributes the dataset under CC0.

## Official schema recovered before scoring

### sample.data.csv

Columns:

- `Sample_ID`
- `Experiment`
- `Harvest`
- `Fungivores`
- `Nitrogen_added`
- `Initial_species`
- `Disc_dry_mass_g_initial`
- `Disc_dry_mass_g_final`
- `Disc_nitrogen_pct_final`
- `Disc_carbon_pct_final`

The official preview confirms:

- `Experiment = PriorityEffects`;
- `Harvest` contains `6 month` and `12 month`;
- `Fungivores` is Boolean;
- `Nitrogen_added` is Boolean.

The preview is truncated and therefore is **not** used to infer the complete
`Initial_species` level set.

### species.prevalence.csv

Columns:

- `Sample_ID`
- `Trametes`
- `Daldinia`
- `Bisporella`
- `Ascocoryne`
- `Calocera`
- `Pleurotus`
- `Sistotrema`
- `Artomyces`
- `Helicogloea`
- `Armillaria`

The deposited description states that each value is the number of wood-disc subsamples,
out of nine, in which the fungal species was detected.

### collembola.csv

Columns:

- `Sample_ID`
- `Harvest_1`
- `Harvest_2`

The deposited description defines the ordinal abundance scale 0–3.

This file is provenance/context information only for the primary v29 analysis because the
manipulated `Fungivores` factor is already present in `sample.data.csv`.

## Biological question

v28 showed that manipulated arrival history was strongly retained above its randomized
baseline in fungal community composition but almost completely attenuated in aggregate
rust disease state.

v29 asks prospectively:

> **Does the same community-to-function attenuation occur in a second manipulated
> assembly-history experiment, or can ecological context preserve or reverse the amount
> of historical information reaching ecosystem function?**

The two frozen targets are:

1. fungal community composition;
2. wood decomposition.

## Experimental unit

One `Sample_ID` is one experimental microcosm.

The only allowed join between `sample.data.csv` and
`species.prevalence.csv` is exact `Sample_ID`.

No row-order matching or approximate identifiers are allowed.

## Primary time point

The primary endpoint is **12 month**.

Reason fixed before scoring:

- the source paper's headline inference concerns effects one year after introduction;
- v29 asks how much historical information survives into a later present state;
- using the later harvest avoids selecting the harvest with the more favorable EOG
  retention contrast.

The **6 month** harvest is the only temporal sensitivity.

## Primary history levels

The primary manipulated history factor is the identity of the initial fungal colonist.

Expected exact source labels:

- `Ascocoryne`
- `Bisporella`
- `Daldinia`
- `Trametes`

These correspond to the four published manipulated initial species.

Any additional `Initial_species` label, including a no-fungus control, is excluded from
the primary history profile and reported separately.

The control is not treated as a fifth history identity because absence of an initial
colonist is not the same estimand as identity of the initial colonist.

## Context

Freeze one four-level ecological context:

[
C = mathrm{Nitrogen_added} 	imes mathrm{Fungivores}.
]

No outcome-dependent merging of context levels is allowed.

## Primary common panel

At 12 months retain only microcosms satisfying all of:

1. `Experiment == "PriorityEffects"`;
2. `Harvest == "12 month"`;
3. `Initial_species` is one of the four frozen history labels;
4. nonmissing `Fungivores`;
5. nonmissing `Nitrogen_added`;
6. positive finite initial dry mass;
7. finite final dry mass;
8. exact matching `Sample_ID` in `species.prevalence.csv`;
9. all ten community prevalence values are finite and lie in [0, 9].

The published balanced design implies an expected primary panel of:

[
2 	imes 2 	imes 4 	imes 5 = 80
]

microcosms.

If the raw data do not yield exactly 80 primary microcosms with five replicates in every
context × history cell, v29 triggers a structural STOP before target scoring.

## Target A — fungal community composition

Use the ten deposited fungal prevalence counts exactly as recorded.

Primary dissimilarity: **Bray–Curtis**.

No pseudocount, relative-abundance closure, rarefaction, taxon filtering, or
outcome-dependent transformation is allowed.

The counts share a common 0–9 prevalence scale, so the primary representation preserves
the deposited community information directly.

Frozen sensitivity:

- binary incidence (prevalence > 0) with Jaccard distance.

## Target B — wood decomposition

Define fractional dry-mass loss:

[
D_i =
rac{
mathrm{Disc_dry_mass_g_initial}_i -
mathrm{Disc_dry_mass_g_final}_i
}{
mathrm{Disc_dry_mass_g_initial}_i
}.
]

This is the primary scalar function target.

Frozen sensitivity:

- absolute mass loss =
  `Disc_dry_mass_g_initial - Disc_dry_mass_g_final`.

No target transformation may be selected after scoring.

## History-retention estimand

For both targets use the same nested model spaces.

Reduced:

[
M_0: 1 + C
]

Full:

[
M_1: 1 + C + H + C:H
]

where:

- (C) = nitrogen × fungivore context;
- (H) = initial fungal history.

Thus the incremental history subspace includes:

- the average history effect;
- context-dependent history expression.

For the four-level context and four-level history, the expected identifiable incremental
history rank is **12** in a complete balanced primary panel.

For the scalar decomposition target use nested partial R².

For the community target use Gower-centered distance-based nested partial R².

## Null calibration

v28 showed that raw partial R² from a multi-dimensional history expansion can be
misleading without calibration.

Therefore v29 prospectively makes null calibration part of the primary estimand.

Permute `Initial_species` **within the four-level context**.

- permutations: **9,999**;
- seed: **20261005**;
- same permuted history assignment is used for both targets in each iteration.

For each target (k), report:

[
R_k = R^2_{mathrm{observed}}
]

and

[
E_k =
R_k -
operatorname{median}(R^2_{k,mathrm{null}}).
]

(E_k) is the **null-calibrated retained-history excess**.

Also report:

- null mean;
- null median;
- null SD;
- 2.5% and 97.5% null quantiles;
- permutation p-value.

## Primary cross-target contrast

The primary v29 comparison is **not** the raw R² difference.

Freeze:

[
Delta E =
E_{mathrm{community}}
-
E_{mathrm{decomposition}}.
]

Interpretation:

- (Delta E > 0): more manipulated history remains visible in community composition;
- (Delta E approx 0): similar null-calibrated retention;
- (Delta E < 0): more manipulated history remains visible in decomposition.

No directional hypothesis is confirmatory.

The purpose is to determine whether v28-like attenuation is reproduced, absent, or
reversed.

## Frozen sensitivities

Exactly four sensitivity families are allowed:

1. **6-month temporal sensitivity** — identical estimands and common-panel rules;
2. **community incidence sensitivity** — Jaccard on prevalence > 0;
3. **decomposition scale sensitivity** — absolute dry-mass loss;
4. **context decomposition** — descriptive E values separately within each of the four
   nitrogen × fungivore contexts where estimable.

No new target, time point, taxon subset, transformation, or context grouping may be added
because the primary result is inconvenient.

## STOP rules

STOP before biological interpretation if:

1. any frozen Dryad MD5 fails;
2. the exact `Sample_ID` join is not one-to-one;
3. a required column is absent;
4. the four expected primary history labels are not all present;
5. the primary common panel is not exactly 80 microcosms;
6. any context × history primary cell does not contain exactly five microcosms;
7. a community prevalence value is outside [0, 9];
8. any primary initial mass is nonpositive or nonfinite;
9. the full model adds no identifiable history subspace;
10. scoring requires an undeclared filter or transformation.

STOP is not evidence for absence of historical effects.

## Exposure boundary

Viewed before protocol freeze:

- published headline results;
- published factorial design;
- public Dryad file IDs, sizes, MD5 digests, MIME types and descriptions;
- official Dryad preview headers;
- preview-confirmed harvest and treatment column structure;
- truncated preview rows solely for schema recovery.

Not viewed before protocol freeze:

- full raw CSV byte streams;
- complete primary common panel;
- any EOG v29 target score;
- any v29 permutation distribution;
- (Delta E).

## Claim boundary

v29 must not claim:

- discovery that history affects fungal composition;
- discovery that history affects decomposition;
- that v28 and v29 establish a universal law if their direction agrees;
- causal mediation from composition to decomposition;
- that lower retained-history excess means the function is biologically unimportant.

If completed, v29 can test only:

> **whether the same manipulated history leaves different null-calibrated amounts of
> information in community composition and ecosystem function under a second,
> independently manipulated ecological context.**
