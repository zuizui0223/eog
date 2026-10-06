# EOG v37 — genotype generality of the Alternaria dominance contrast

## Status

**FROZEN BEFORE ANY GENOTYPE-SPECIFIC DOMINANCE RESPONSE IS INSPECTED.**

v35 established that Alternaria has disproportionate leverage on identity-free rank-1
dominance. v36 prospectively tests the direct Alternaria-versus-rest dominance contrast on
the full panel.

v37 asks a different question:

> **Is that dominance contrast broadly shared across host genotypes, or concentrated in
> genotype-specific interactions?**

The design is frozen from treatment allocation alone. No genotype-specific dominance
response has been inspected before this protocol.

## Panel and treatment support

Reuse the frozen v28 common panel of **233 plants**.

Binary history:

- Alternaria: **48**
- Other: **185**

All **12/12 host genotypes** contain both binary history levels, so no genotype is
excluded and no extrapolation across empty cells is required.

Frozen treatment counts:

- West-7: Alternaria 3, Other 13
- West-6: Alternaria 4, Other 14
- West-3: Alternaria 2, Other 19
- West-4: Alternaria 5, Other 17
- East-3: Alternaria 4, Other 13
- West-2: Alternaria 5, Other 16
- West-1: Alternaria 5, Other 15
- East-4: Alternaria 5, Other 19
- East-5: Alternaria 5, Other 17
- East-1: Alternaria 4, Other 16
- East-2: Alternaria 3, Other 13
- West-5: Alternaria 3, Other 13

## Response

Identity-free rank-1 dominance:

1. bias-correct the five focal fungal abundances exactly as in v28;
2. close to proportions;
3. sort descending;
4. retain only the largest proportion (r_1).

No taxon identity is used in the response.

## Model decomposition

Let B be BinaryHistory and G be Genotype.

Reduced model:

[
M_0: 1 + G.
]

Common-shift model:

[
M_1: 1 + G + B.
]

Full context-dependent model:

[
M_2: 1 + G + B + G:B.
]

Using ordinary least-squares residual sums of squares:

[
SS_{common}=SSE_0-SSE_1
]

[
SS_{context}=SSE_1-SSE_2
]

[
SS_{total}=SSE_0-SSE_2
=SS_{common}+SS_{context}.
]

Define:

[
F_{common}=
SS_{common}/SS_{total}.
]

This fraction asks how much of the observed binary-history fit is captured by one
genotype-shared dominance shift rather than genotype-specific deviations.

## Per-genotype contrasts

For every genotype g, report:

[
delta_g =
overline{r_1}_{Alternaria,g}
-
overline{r_1}_{Other,g}.
]

Also report:

- number of genotypes with (delta_g>0);
- equal-genotype-weighted mean (ar{delta});
- median (delta_g);
- minimum and maximum (delta_g).

No genotype may be dropped because its direction is inconvenient.

## Randomization

Permute BinaryHistory within Genotype, preserving the exact frozen counts above.

- permutations: **9,999**
- seed: **20261005**

For each permutation recompute:

- common-shift R² from M0 -> M1;
- total-history R² from M0 -> M2;
- context-interaction R² contribution from M1 -> M2;
- equal-genotype-weighted mean (ar{delta}).

Report null medians, 95% intervals and permutation p-values.

## Prospective prediction

Frozen before genotype-specific response inspection:

> **The Alternaria dominance contrast is broadly genotype-shared rather than primarily
> concentrated in genotype-specific interactions.**

Operational criteria:

1. (F_{common} > 0.5);
2. at least **7 of 12** genotype contrasts have (delta_g>0);
3. the equal-genotype-weighted mean (ar{delta}>0).

All three criteria must hold for the prospective prediction to be supported.

The 7/12 criterion is a simple majority rule fixed prospectively, not an optimized
threshold.

## Secondary context diagnostic

Report East and West region summaries of the genotype-specific (delta_g) values.

These are descriptive only; no regional hypothesis is preregistered.

## Gates

Before interpretation:

1. reproduce the frozen v28 common panel and the 48/185 binary counts;
2. verify all 12 genotypes contain both history levels;
3. reproduce the v35 full-panel rank-1 dominance response construction;
4. verify M0 is nested in M1 and M1 in M2;
5. verify (SS_{common}+SS_{context}=SS_{total}) to numerical tolerance;
6. do not inspect or filter genotype-specific (delta_g) before the frozen scorer runs.

## Exposure boundary

Known before v37:

- v28-v35 source data and aggregate results;
- treatment counts by genotype;
- pooled descriptive dominance ordering by original history from v35.

Not inspected before freeze:

- any genotype-specific Alternaria-versus-rest dominance mean;
- any (delta_g);
- common-shift versus interaction sums of squares;
- (F_{common});
- the number of positive genotype contrasts.

## Interpretation boundary

If supported:

> **Alternaria's dominance-associated historical fingerprint is expressed broadly across
> host genotypes rather than arising mainly from a small subset of genotype-specific
> responses.**

If refuted:

> **The pooled dominance signal is context dependent and cannot be described as a common
> host-genotype response.**

Either outcome sharpens the biological interpretation without invoking an unmeasured
interaction mechanism.

## Claim boundary

Do not claim:

- causal physiological mechanism;
- genotype independence from a positive common component;
- universal host generality beyond these 12 genotypes;
- niche preemption or modification;
- cross-system generality.
