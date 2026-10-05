# EOG v30 — grassland above/belowground target-specific history retention

## Status

**FROZEN BEFORE ANY EOG v30 RETENTION SCORE IS CALCULATED.**

v30 is a second independent empirical benchmark for the target-specific history-retention
idea developed in v26 and demonstrated in v28.

Source experiment:

Alonso-Crespo et al. (2021),
*Assembly history modulates vertical root distribution in a grassland experiment.*

Public source repository:

- `BenjaminDelory/PE_Rhizobox_2017_data`
- pinned commit: `438f028fb2e1713a9e253be9e07df0833b491f47`
- repository license: **GNU GPL v3**

The repository contains raw data and the authors' analysis code.

## Why this is independent of v28

v28 used a manipulated fungal arrival-order experiment in a plant microbiome and compared
fungal community composition with host rust lesion state.

v30 uses:

- a different research group;
- a terrestrial grassland plant community;
- a different history manipulation;
- a different pair of present-state targets;
- a different experimental-unit structure.

The target-specific question is therefore not tied to the Leopold–Busby microbiome system.

## Manipulated assembly history

The source experiment manipulated the order in which plant functional groups arrived.

The deposited `Treatment` factor has five levels:

- `Sync1` — all groups sown together at the first sowing event;
- `Sync2` — all groups sown together at the second sowing event;
- `F-first` — forbs sown 10 days before grasses and legumes;
- `G-first` — grasses sown 10 days before forbs and legumes;
- `L-first` — legumes sown 10 days before forbs and grasses.

The primary EOG history estimand uses **only the three directional arrival histories**:

- `F-first`;
- `G-first`;
- `L-first`.

The synchronous treatments are excluded from the primary history identity because they
encode sowing-time controls rather than the identity of the first-arriving functional group.

## Experimental unit and block

The experimental unit is one rhizobox, identified by `Rz`.

`Replicate` is the randomized/blocking factor and must remain a nuisance/block variable,
not an independent response or history variable.

The source shoot-biomass file has:

- 35 rhizoboxes;
- seven replicates per treatment.

The source root-biomass file has:

- 31 rhizoboxes;
- six root-depth layers for every retained rhizobox.

Exact common-unit matching by `Rz` yields 31 rhizoboxes.

Restricting to the three directional history treatments gives the frozen primary common
panel:

- **19 rhizoboxes**;
- F-first = **6**;
- G-first = **7**;
- L-first = **6**.

Block structure:

- Replicates 1, 2, 3, 6 and 7 retain all three histories;
- Replicate 4 retains G-first and L-first;
- Replicate 5 retains F-first and G-first.

Every retained replicate therefore contains at least two history labels and remains
permutable.

## Source identity

Pinned source blobs:

- shoot biomass:
  `Data/Data_shoot_biomass_RZ_PE_2017.txt`
  blob `4fb311a7bbe9bb14cdac77bbc889e2dcbb9cfedc`;
- root biomass:
  `Data/Data_root_biomass_RZ_PE_2017.txt`
  blob `d7822cefa35f41b144a87c0184f6029e9726bca9`;
- data dictionary:
  `Data/README.txt`
  blob `31d7398c8f5259ad48095324ab575575a6b39312`.

Raw files are read from the pinned public source and are not copied into EOG.

## Primary ecological question

> **How much manipulated functional-group arrival history remains visible in the
> final aboveground community composition, and how much remains visible in the
> belowground vertical root distribution of the same grassland communities?**

This is a target-specific retention question, not a fresh test of whether assembly history
affects grassland communities.

## Target A — aboveground functional-group composition

Use the three deposited functional-group shoot dry-mass columns:

- `Forbs`;
- `Grasses`;
- `Legumes`.

These aggregate columns are used instead of the nine species columns because the source
species-level table contains missing `Lotus corniculatus` values that the original analysis
removed post hoc. The three functional-group columns are complete and directly match the
functional-group history manipulation.

Use the raw non-negative biomass vector for each rhizobox.

Primary distance: **Bray–Curtis**.

No closure, pseudocount, rarefaction, or outcome-dependent taxon filtering is allowed.

## Target B — belowground vertical root distribution

For each retained rhizobox construct a six-element root dry-mass vector ordered by:

- 0–10 cm;
- 10–20 cm;
- 20–30 cm;
- 30–40 cm;
- 40–50 cm;
- 50–60 cm.

Use the deposited `RDW` values directly.

Primary distance: **Bray–Curtis**.

Every primary rhizobox must have exactly six unique layers.

## Nuisance/block model

The primary model spaces are shared across both targets.

Reduced model:

[
M_0: 1 + mathrm{Replicate}
]

Full model:

[
M_1: 1 + mathrm{Replicate} + mathrm{History}.
]

History is the three-level `Treatment` factor restricted to F-first, G-first and L-first.

The incremental history subspace is therefore the variation attributable to manipulated
arrival history after accounting for the replicate block.

## Retention statistic

For both distance targets use the same Gower-centered nested partial R²:

[
R_k =
rac{SS_{mathrm{reduced}}-SS_{mathrm{full}}}
     {SS_{mathrm{reduced}}}.
]

As in v29, raw R² is not interpreted without null calibration.

## Randomization and null calibration

Permute the history label **within Replicate**.

- permutations: **9,999**;
- seed: **20261005**;
- the same permuted history assignment is used for both targets at each iteration.

For each target (k), report:

- observed partial R²;
- null mean;
- null median;
- null SD;
- null 2.5% and 97.5% quantiles;
- permutation p-value;
- null-calibrated retained-history excess:

[
E_k =
R_k - mathrm{median}(R_{k,mathrm{null}}).
]

## Primary cross-target contrast

Freeze:

[
Delta E =
E_{mathrm{shoot composition}}
-
E_{mathrm{root vertical distribution}}.
]

Interpretation:

- (Delta E > 0): history is more visible aboveground;
- (Delta E approx 0): similar target-specific retention;
- (Delta E < 0): history is more visible in belowground spatial organization.

No directional outcome is preregistered.

## Frozen scalar sensitivities

Exactly two scalar sensitivities are declared:

1. **total shoot biomass** from deposited `Total`;
2. **root mean depth**, calculated from the six root-biomass layers as the
   biomass-weighted midpoint depth using midpoints 5, 15, 25, 35, 45 and 55 cm.

For each scalar sensitivity use the same reduced/full model spaces and within-replicate
permutation contract.

These are sensitivities, not replacement primary endpoints.

## Source-analysis outlier boundary

The original R code excludes rhizobox 137 from a root-biomass analysis because one layer
was considered potentially affected by a data-encoding mistake.

v30 does **not** exclude rhizobox 137 in the primary analysis because:

- the deposited raw root data contain the rhizobox;
- adopting that exclusion would require an outcome-specific repair rule;
- the EOG primary contract is defined from deposited data structure rather than choosing
  a favorable source-paper cleanup.

A frozen sensitivity will report the primary target scores after removing Rz 137, but no
claim may depend solely on that sensitivity.

## STOP rules

Stop before biological interpretation if:

1. any pinned source blob changes;
2. the shoot or root table cannot be joined exactly by `Rz`;
3. any joined `Treatment` or `Replicate` value disagrees across files;
4. the primary common panel is not exactly 19 rhizoboxes;
5. the history counts are not F-first=6, G-first=7, L-first=6;
6. any retained replicate has fewer than two history labels;
7. any primary root rhizobox does not contain exactly six unique depth layers;
8. any target biomass is negative or nonfinite;
9. the reduced design is not nested in the full design;
10. the history increment is not identifiable;
11. scoring requires an undeclared outcome-dependent filter.

STOP is not biological evidence.

## Exposure boundary

Before freeze, the following source material was viewed:

- the source paper's qualitative conclusion;
- the full data dictionary;
- source analysis code;
- source file schemas;
- row-level shoot-biomass values during structural inspection;
- early root-biomass rows;
- common-unit counts and block structure.

Therefore v30 is explicitly an **external benchmark**, not a blinded confirmatory test.

Before freeze, the following were **not** calculated:

- EOG shoot-composition partial R²;
- EOG root-distribution partial R²;
- either permutation null;
- either null-calibrated retained-history excess;
- (Delta E).

## Claim boundary

Do not claim:

- discovery that assembly history affects grassland structure;
- causal mediation from aboveground composition to root distribution;
- that a larger retained-history excess means a target is more important;
- that agreement with v28 constitutes a universal law;
- that disagreement with v28 invalidates v28.

The allowed EOG question is narrower:

> **In an independently published grassland experiment, does the same manipulated
> arrival history remain equally visible in aboveground community composition and
> belowground spatial organization, once both are evaluated under one blocked,
> null-calibrated retention contract?**
