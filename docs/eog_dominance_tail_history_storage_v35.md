# EOG v35 — dominance versus lower-rank architecture

## Status

**FROZEN BEFORE ANY v35 COMPONENT SCORE IS CALCULATED.**

v31 showed that the v28 microbiome retains assembly history even after fungal identity
labels are removed. v34 then showed that this identity-free rank-abundance memory is
distributed but uneven across arrival histories, with Alternaria producing the largest
prospective deletion leverage.

v35 asks what component of identity-free abundance architecture carries that leverage.

## Primary question

> **Is Alternaria's disproportionate leverage on architecture memory expressed mainly
> through the strength of the dominant abundance rank, or through the relative structure
> of the lower four ranks?**

## Frozen source and panel

Reuse exactly the v28/v31 frozen microbiome panel:

- 233 plants;
- five bias-corrected focal fungal proportions;
- history = Treatment;
- context = Genotype;
- reduced model = Genotype;
- full model = Genotype × Treatment;
- Treatment permuted within Genotype;
- 9,999 permutations;
- seed 20261005.

No source row, taxon, genotype or history level may be added or removed except the
predeclared Alternaria deletion sensitivity below.

## Identity-free decomposition

For each plant, sort the five bias-corrected fungal proportions descending:

r1 >= r2 >= r3 >= r4 >= r5.

Define two non-overlapping descriptive targets.

### Target A — dominance

[
D_i = r_{1i}.
]

This scalar is the proportion of the focal fungal community occupied by the single most
abundant taxon, without retaining its identity.

### Target B — lower-rank shape

Remove rank 1 and renormalize the remaining four ranks:

[
T_i =
rac{(r_{2i},r_{3i},r_{4i},r_{5i})}
     {r_{2i}+r_{3i}+r_{4i}+r_{5i}}.
]

Primary distance: Bray–Curtis on the four-dimensional normalized tail.

If the tail sum is zero for any primary plant, v35 triggers STOP rather than inventing a
pseudocount.

The normalization intentionally removes variation in the magnitude of rank 1 so that the
tail target asks whether history changes the *relative organization of the non-dominant
ranks*.

## Primary retained-history scores

For each component calculate the same null-calibrated retained-history excess:

[
E = R^2_{mathrm{observed}} - operatorname{median}(R^2_{mathrm{null}}).
]

- dominance: scalar nested partial R²;
- lower-rank shape: distance-based nested partial R².

Use paired within-Genotype permutations across both targets.

## Alternaria leverage decomposition

Repeat both targets after removing all Alternaria-history plants.

For component c define:

[
L_c =
E_{c,mathrm{full}}
-
E_{c,mathrm{without Alternaria}}.
]

This asks which component loses more history when the highest-leverage history from v34
is removed.

## Prospective prediction

Frozen before scoring:

> **Alternaria leverage is dominance-centered.**

Operational criteria:

1. (L_{mathrm{dominance}} > 0);
2. (L_{mathrm{dominance}} > L_{mathrm{tail}}).

No minimum magnitude is preregistered.

This prediction follows from the pre-v35 evidence that Alternaria-first communities had a
very high final first-arriver share and that Alternaria had the largest v34 deletion
leverage.

## Secondary diagnostics

Report:

- E_dominance on all five histories;
- E_tail on all five histories;
- E_dominance without Alternaria;
- E_tail without Alternaria;
- L_dominance and L_tail;
- paired permutation p-values for each target;
- median rank-1 share by history as descriptive context only.

No alternate dominance metric such as Berger-Parker, r1-r2 gap or Gini coefficient may
replace the frozen primary target after scoring.

## Gates

Before interpretation:

1. reproduce the authoritative v31 full-panel rank-abundance E;
2. reproduce the authoritative v34 Alternaria deletion panel membership;
3. verify each sorted row preserves the exact five abundance values;
4. verify every lower-rank tail has positive sum;
5. verify generic and fast observed partial-R² implementations agree for dominance and
   tail on both panels.

## Exposure boundary

Known before v35:

- v28-v34 source data and results;
- v32 descriptive first-arriver shares;
- v34 Alternaria deletion leverage.

Not calculated before freeze:

- any dominance retained-history score;
- any lower-rank-tail retained-history score;
- either Alternaria component leverage;
- the ordering of L_dominance versus L_tail.

## Interpretation boundary

If the prediction is supported, the allowed conclusion is:

> **The largest history-level leverage on identity-free microbiome architecture is
> expressed more strongly through dominance intensity than through the relative shape of
> the lower abundance ranks.**

This would still not identify the interaction mechanism that produces dominance.

If the prediction is refuted, Alternaria leverage must be interpreted as involving broader
rank-architecture restructuring rather than a simple dominance effect.

## Claim boundary

Do not claim:

- the identity of the dominant taxon from this analysis;
- niche preemption or niche modification;
- that dominance is the universal storage channel of priority effects;
- that lower-rank structure is irrelevant if its retained-history score is smaller;
- cross-system generality.
