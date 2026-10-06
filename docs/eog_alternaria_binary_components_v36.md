# EOG v36 — direct Alternaria-versus-rest component test

## Status

**FROZEN BEFORE ANY v36 COMPONENT SCORE IS CALCULATED.**

v34 showed that Alternaria has the largest prospective leave-one-history-out leverage on
identity-free rank-abundance memory. v35 then localized more of that leverage to rank-1
dominance than to the normalized lower-rank tail.

Those results are deletion based. v36 asks the corresponding direct contrast on the full
233-plant panel.

## Primary question

> **Does the direct Alternaria-versus-rest history contrast remain more strongly encoded
> in identity-free rank-1 dominance than in the normalized structure of lower abundance
> ranks?**

## Frozen source and panel

Reuse the exact v28/v31 microbiome panel:

- 233 plants;
- five bias-corrected focal fungal proportions;
- context = Genotype;
- original history = Treatment;
- 48 Alternaria-history plants;
- 185 plants assigned to the other four histories.

No plant, genotype, taxon or source transformation may be added or removed.

## Binary history

Define one frozen binary history variable:

- `Alternaria`
- `Other`

where `Other` pools Aureobasidium, Cladosporium, Dioszegia and Fusarium.

This is the same binary contrast used as a secondary diagnostic in v34.

## Identity-free response decomposition

For every plant, sort the five corrected proportions descending:

r1 >= r2 >= r3 >= r4 >= r5.

### Target A — dominance

[
D_i = r_{1i}.
]

Scalar nested partial R².

### Target B — lower-rank shape

Remove rank 1 and renormalize ranks 2–5:

[
T_i = rac{(r_{2i},r_{3i},r_{4i},r_{5i})}
           {r_{2i}+r_{3i}+r_{4i}+r_{5i}}.
]

Primary distance: Bray–Curtis.

If any lower-rank sum is zero, STOP.

### Gate target — full rank abundance

The five sorted values are also retained as a gate only.

The v36 scorer must reproduce the authoritative v34 Alternaria-versus-rest full
rank-abundance result before either component is accepted:

- E_rank_binary = **0.08031760324496914**
- p = **0.0004**.

## Model and randomization

Reduced model:

[
M_0: 1 + mathrm{Genotype}.
]

Full model:

[
M_1: 1 + mathrm{Genotype}
+ mathrm{BinaryHistory}
+ mathrm{Genotype}:mathrm{BinaryHistory}.
]

Permute BinaryHistory within Genotype.

- permutations: **9,999**
- seed: **20261005**
- use the same permuted binary labels for dominance, lower-rank tail and full rank
  abundance in each iteration.

## Primary estimand

For each component:

[
E_c =
R^2_{c,mathrm{observed}}
-
operatorname{median}(R^2_{c,mathrm{null}}).
]

Define:

[
Delta E_{D-T} =
E_{mathrm{dominance}}
-
E_{mathrm{tail}}.
]

## Prospective prediction

Frozen before scoring:

> **The direct Alternaria-versus-rest contrast is dominance-centered.**

Operational criteria:

1. (E_{mathrm{dominance}} > 0);
2. (Delta E_{D-T} > 0).

No minimum magnitude or p-value threshold is required for support of the directional
prediction.

Permutation p-values remain diagnostics and are reported for both targets.

## Secondary descriptive summaries

Report:

- median and mean rank-1 share for Alternaria;
- median and mean rank-1 share for Other;
- raw observed partial R² for both components;
- null medians and 95% null intervals.

Do not introduce alternative dominance statistics after scoring.

## Gates

Before biological interpretation:

1. reproduce the v34 Alternaria-versus-rest full rank-abundance E exactly;
2. reproduce the 48 versus 185 binary history counts;
3. preserve each plant's exact abundance multiset after sorting;
4. verify positive lower-tail sum for all plants;
5. verify generic and fast observed statistics agree for full-rank, dominance and tail
   targets.

## Exposure boundary

Known before v36:

- all v28-v35 source data and results;
- v34 Alternaria-versus-rest full rank-abundance score;
- v35 dominance and tail deletion leverages;
- descriptive v35 median rank-1 shares by original history.

Not calculated before freeze:

- binary-history dominance E;
- binary-history tail E;
- (Delta E_{D-T});
- either binary component permutation p-value.

## Interpretation boundary

If supported, v36 may state:

> **On the full panel, the direct Alternaria-versus-rest historical contrast is encoded
> more strongly in identity-free dominance intensity than in the relative structure of
> the lower abundance ranks.**

This would strengthen v35 by replacing a deletion comparison with a direct randomized
history contrast.

If refuted, the v35 leverage result must remain interpreted as a deletion property rather
than evidence that Alternaria-versus-rest itself is dominance-centered.

## Claim boundary

Do not claim:

- that the dominant taxon is Alternaria;
- that Alternaria is the sole driver of architecture memory;
- niche preemption or niche modification;
- causal mediation;
- a universal dominance mechanism;
- cross-system generality.
