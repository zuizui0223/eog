# EOG v31 — identity storage versus unlabeled abundance structure

## Status

**FROZEN BEFORE ANY v31 SCORE IS CALCULATED.**

v28 and v30 independently showed strong target-specific differences in the amount of
assembly history retained by present ecological variables. Those results do not by
themselves distinguish whether history is stored in:

1. the identity of taxa / functional groups occupying abundance ranks; or
2. the unlabeled shape of the abundance distribution itself.

v31 tests that distinction directly while holding the raw abundance values, dimensionality,
experimental units and history model fixed.

## Primary question

> **Does manipulated assembly history persist mainly in ecological identity, rather than
> in the unlabeled rank-abundance structure of the same present community?**

## Core transformation

For every community vector x, define two targets:

- **identity-resolving target**: the original labeled vector x;
- **identity-stripped rank target**: sort exactly the same entries within that experimental
  unit from largest to smallest and discard the taxon / functional-group labels.

The sorted target preserves:

- the same number of dimensions;
- the same abundance values;
- the same total abundance;
- the same dominance/evenness profile.

It removes only the mapping from an abundance value to a named taxon or functional group.

Thus any reduction in history retention cannot be attributed simply to lower target
dimensionality or to replacing a multivariate response with a scalar.

## System A — v28 plant microbiome

Reuse the frozen v28 common panel and representation:

- 233 plants;
- five bias-corrected fungal-taxon proportions;
- history = fungal arrival-order Treatment;
- context = Genotype;
- reduced model = Genotype;
- full model = Genotype × Treatment;
- Treatment permuted within Genotype;
- 9,999 permutations;
- seed 20261005.

Targets:

1. original labeled five-taxon composition;
2. the same five proportions sorted descending within each plant.

Distance: Bray–Curtis for both.

## System B — v30 grassland

Reuse the frozen v30 common panel and representation:

- 19 rhizoboxes;
- shoot biomass of Forbs, Grasses and Legumes;
- history = F-first / G-first / L-first;
- block = Replicate;
- reduced model = Replicate;
- full model = Replicate + History;
- History permuted within Replicate;
- 9,999 permutations;
- seed 20261005.

Targets:

1. original labeled three-functional-group shoot-biomass vector;
2. the same three biomass values sorted descending within each rhizobox.

Distance: Bray–Curtis for both.

## Primary estimand

For each system s and target t, retain the already established null-calibrated score:

E(s,t) = observed partial R² - median(null partial R²).

Define the prospective **identity-storage gap**:

G_s = E(s,labeled) - E(s,rank).

Primary hypothesis:

> **G_s > 0 in both independent systems.**

This directional hypothesis is frozen before either rank-abundance target is scored.

No minimum effect-size threshold is preregistered.

## Secondary label-invariant sensitivity

For each original composition vector, calculate Shannon entropy after closing positive
entries to proportions.

This scalar intentionally ignores taxon / functional-group identity.

Use the same reduced/full model and the same paired permutation stream as the primary
targets.

This is sensitivity-only because dimensionality differs from the original composition.

## Paired randomization rule

Within each system, the same permuted history assignment must be used for:

- labeled composition;
- rank-abundance composition;
- Shannon entropy.

This preserves a paired null comparison.

## Exposure boundary

Already known before v31:

- all v28 and v30 labeled-composition scores;
- source data and source-paper conclusions;
- v28 and v30 target-specific attenuation results.

Not calculated before v31 freeze:

- either system's rank-abundance partial R²;
- either rank-abundance null distribution;
- either identity-storage gap G;
- either Shannon-entropy history-retention score.

Therefore v31 is a prospective derived-target analysis, not a blinded reanalysis of the
original experiments.

## Claim boundary

v31 must not claim:

- first discovery of compositional contingency;
- first discovery of functional convergence;
- that identity storage is universal from two systems;
- that rank-abundance structure is ecologically unimportant;
- that weak label-invariant retention implies absence of priority effects.

If both G values are positive, the allowed ecological conclusion is:

> **In two independently manipulated assembly-history experiments, much of the persistent
> historical signal in final community composition is carried by which ecological
> identities occupy abundance ranks, rather than by the unlabeled shape of the abundance
> distribution itself.**

That is narrower than composition-versus-function decoupling and directly tests the
identity-storage interpretation of v28-v30.
