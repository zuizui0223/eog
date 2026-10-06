# EOG v37 result — host-genotype generality of Alternaria dominance

## Verdict

The prospectively frozen prediction was **supported**:

> **The Alternaria-associated increase in identity-free rank-1 dominance is broadly shared
> across host genotypes rather than arising mainly from genotype-specific interactions.**

Authoritative execution:

- workflow run: `37425656169`;
- artifact: `11395371699`;
- artifact digest:
  `sha256:e4de2d1ff1e9afa1e74200ccb3b9ef86f2c01de13466bc4c0900c1bebeebf1c7`;
- result fingerprint:
  `bfc500301fbea9672d7e167f8f33e9c491220cc951a72678f1a8327d40fcbdf6`.

All 12 frozen host genotypes retained both Alternaria and Other history levels.

## Common versus genotype-specific history fit

Nested model decomposition:

- M0: Genotype;
- M1: Genotype + BinaryHistory;
- M2: Genotype × BinaryHistory.

Observed components:

- common history R² = **0.13530**;
- genotype-specific interaction R² = **0.03417**;
- total history R² = **0.16947**.

The common component accounts for:

- **79.83%** of the total observed binary-history sum of squares.

Permutation diagnostics:

### Common component

- null median R² = **0.00204**;
- null 95% interval = **0.000004–0.02287**;
- p = **0.0001**.

### Genotype-specific interaction component

- null median R² = **0.04699**;
- null 95% interval = **0.01705–0.09645**;
- p = **0.7548**.

### Total binary history

- null median R² = **0.05135**;
- p = **0.0002**.

Thus the strong dominance signal is primarily a genotype-shared shift; the extra
genotype-specific interaction contribution is smaller than expected under the frozen
within-genotype randomization baseline.

## Within-genotype dominance contrasts

Define:

[
delta_g =
overline{r_1}_{Alternaria,g}
-
overline{r_1}_{Other,g}.
]

Results:

- positive in **11/12** genotypes;
- equal-genotype-weighted mean = **+0.06099**;
- median = **+0.07142**;
- minimum = **−0.04471**;
- maximum = **+0.09090**.

The equal-weighted mean contrast had:

- null median ≈ **0.00011**;
- null 95% interval = **−0.02377 to +0.02304**;
- p = **0.0001**.

Only West-7 was negative.

## Regional descriptive summary

These were not preregistered as regional hypotheses.

East:

- 5 genotypes;
- **5/5 positive**;
- mean delta = **+0.07697**.

West:

- 7 genotypes;
- **6/7 positive**;
- mean delta = **+0.04957**.

## Biological interpretation

v34-v36 established that Alternaria has disproportionate leverage on identity-free
community dominance.

v37 shows that this is not principally a one- or two-host-genotype phenomenon:

> **Across nearly the entire tested host-genotype panel, Alternaria arrival history shifts
> the final fungal community toward stronger identity-free dominance.**

The genotype-shared component explains about four fifths of the observed binary-history
fit, while the genotype-specific interaction component is not unusually large relative to
the permutation null.

This makes the dominance-centered history signature substantially more general within the
experiment than a model based only on genotype-specific idiosyncrasy.

## Claim boundary

Do not claim:

- complete genotype independence;
- universality beyond these 12 host genotypes;
- physiological or molecular mechanism;
- that the dominant fungal identity is necessarily Alternaria;
- niche preemption versus niche modification;
- cross-system generality.
