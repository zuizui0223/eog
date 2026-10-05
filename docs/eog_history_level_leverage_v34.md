# EOG v34 — history-level leverage on abundance-architecture memory

## Status

**FROZEN BEFORE ANY v34 LEAVE-ONE-HISTORY-OUT SCORE IS CALCULATED.**

v31 established that the v28 microbiome retains assembly history even after fungal
identity labels are removed from the response. v33 then found that the five highest
placebo role mappings all preserve `Alternaria -> Alternaria` while freely permuting the
other four identities.

That pattern is only a post-result clue.

v34 tests it without using any treatment-dependent response transformation.

## Primary question

> **Is the microbiome's identity-free abundance-architecture memory disproportionately
> dependent on one exceptional arrival history, specifically Alternaria?**

## Frozen response

Reuse the exact v31 microbiome rank-abundance target:

1. start from the five bias-corrected focal-fungal proportions used in v28;
2. sort the five values descending within every plant;
3. discard fungal identity labels;
4. calculate Bray–Curtis distance.

The response therefore does not use Treatment to choose or reorder a coordinate.

## Baseline gate

Before any leave-one-history-out result is accepted, reproduce the authoritative v31
full-panel rank-abundance result:

- n = 233 plants;
- rank-abundance retained-history excess E_full =
  **0.14860894599445995**;
- permutation p = **0.0001**.

History model:

- reduced: Genotype;
- full: Genotype × Treatment;
- Treatment permuted within Genotype;
- 9,999 permutations;
- seed 20261005.

## Leave-one-history-out panel

Histories:

- Alternaria;
- Aureobasidium;
- Cladosporium;
- Dioszegia;
- Fusarium.

For each history h:

1. remove all plants assigned to h;
2. keep the same rank-abundance response definition on the remaining plants;
3. fit the same genotype-aware nested history model using the four remaining treatments;
4. permute the remaining Treatment labels within Genotype;
5. calculate null-calibrated retained-history excess E_minus_h.

No reweighting, balancing, genotype deletion or outcome-based filtering is allowed.

If the remaining history increment is not identifiable, that exclusion triggers STOP
rather than an alternate model.

## Primary leverage statistic

For each history:

D_h = E_full - E_minus_h.

Interpretation:

- D_h > 0: removing that history weakens identity-free architecture memory;
- D_h < 0: removing that history strengthens it.

## Prospective prediction

The v33 clue makes one directional prediction:

> **D_Alternaria is positive and is the largest of the five D_h values.**

No minimum magnitude is preregistered.

This is a rank prediction across all five complete leave-one-history-out analyses, not a
post hoc choice of the largest deletion effect.

## Secondary binary diagnostic

Also freeze one secondary diagnostic:

- recode history as Alternaria versus all four other histories;
- retain all 233 plants;
- use the same rank-abundance distance;
- reduced model: Genotype;
- full model: Genotype × binary history;
- permute the binary history label within Genotype;
- 9,999 permutations, seed 20261005.

Report its observed partial R², null-calibrated excess and permutation p-value.

This diagnostic asks whether a simple Alternaria-versus-rest contrast itself carries
architecture-level history. It is secondary and cannot replace the primary leverage
ranking.

## Gates

Before interpretation:

1. reproduce the v31 full-panel rank-abundance E exactly;
2. preserve the exact v28 source blobs and common panel;
3. verify each deletion removes exactly one declared Treatment level;
4. verify the remaining history term is identifiable;
5. verify generic and fast observed partial-R² implementations agree for every panel.

## Exposure boundary

Known before v34:

- v28 source data;
- v31 full rank-abundance result;
- v32 first-arriver share summaries;
- v33 complete mapping-specificity result;
- the observation that every top-five v33 mapping preserved Alternaria->Alternaria.

Not calculated before freeze:

- any E_minus_h;
- any D_h;
- the ordering of D_h;
- Alternaria-versus-rest binary retained-history score.

## Interpretation boundary

If the prediction is supported, the allowed conclusion is:

> **The v28 architecture-level memory is disproportionately sensitive to removal of the
> Alternaria arrival history.**

This does not establish that Alternaria is the sole source of history memory or identify
the ecological interaction mechanism.

If the prediction is refuted, the Alternaria clue from v33 must be treated as a mapping-
ensemble coincidence rather than promoted.

## Claim boundary

Do not claim:

- Alternaria is the sole driver unless the remaining histories have no retained signal;
- niche preemption or modification from this deletion test;
- causal mediation;
- cross-system generality from one microbiome.

The purpose is to locate leverage among randomized history levels using a response that is
independent of the history labels.
