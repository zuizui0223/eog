# EOG v35 result — dominance versus lower-rank architecture

## Verdict

The prospectively frozen prediction was **supported**:

> **Alternaria's disproportionate leverage on identity-free abundance architecture is
> stronger in rank-1 dominance than in the normalized lower-rank structure.**

Authoritative execution:

- workflow run: `37309569097`;
- artifact: `11344724499`;
- artifact digest:
  `sha256:f775e63378a500ed096c0d817fff89e1dd7c9085aaaf1d1c0195b63e59c0f133`;
- result fingerprint:
  `185147dabd36f3890f8de9c86fb2cb46c8cb63a96c0e1fae102299bd3a9ac533`.

The authoritative v31 full-panel rank-abundance result and the authoritative v34
Alternaria-deletion rank-abundance result were both reproduced exactly before the new
component scores were accepted.

An independent local NumPy reconstruction from the pinned source matrix reproduced all
reported scores as a second audit.

## Full five-history panel

n = **233** plants.

### Rank-1 dominance

The identity-free scalar target was the largest of the five sorted fungal proportions.

- partial R² = **0.3914**;
- null median = **0.2155**;
- retained-history excess E = **+0.1759**;
- permutation p = **0.0002**.

### Lower-rank shape

Ranks 2–5 were renormalized to sum to one before Bray–Curtis distance was calculated.

- partial R² = **0.3499**;
- null median = **0.2241**;
- E = **+0.1258**;
- p = **0.0005**.

Thus identity-free assembly history is visible in both components of abundance
architecture, not only in the dominant rank.

## Alternaria deletion

After removing all **48** Alternaria-history plants, n = **185**.

### Rank-1 dominance

- partial R² = **0.2953**;
- null median = **0.2059**;
- E = **+0.0895**;
- p = **0.0241**.

### Lower-rank shape

- partial R² = **0.2988**;
- null median = **0.2126**;
- E = **+0.0862**;
- p = **0.0252**.

Both components therefore retain detectable architecture memory without Alternaria.

## Component-specific Alternaria leverage

For component c:

[
L_c =
E_{c,mathrm{full}}
-
E_{c,mathrm{without Alternaria}}.
]

Results:

- **dominance leverage** = **+0.08647**;
- **lower-rank-tail leverage** = **+0.03957**;
- dominance minus tail leverage = **+0.04690**.

Both preregistered criteria were met:

1. dominance leverage > 0;
2. dominance leverage > lower-rank-tail leverage.

## Descriptive dominance pattern

Median rank-1 abundance share by randomized history:

- Alternaria: **0.793**;
- Fusarium: **0.738**;
- Dioszegia: **0.713**;
- Cladosporium: **0.707**;
- Aureobasidium: **0.695**.

Alternaria-history communities therefore have the strongest typical top-rank dominance in
the frozen focal community representation.

This descriptive ordering is consistent with the prospective component-leverage result,
but it does not identify which named taxon occupies rank 1 in each plant.

## Biological interpretation

v34 showed that Alternaria has the largest history-level leverage on identity-free
rank-abundance memory.

v35 now localizes much of that leverage:

> **Alternaria disproportionately changes the intensity of community dominance, while a
> smaller but still substantial part of its historical leverage extends into the relative
> organization of the non-dominant ranks.**

The result is therefore not simply:

> Alternaria creates all architecture memory.

Nor is it:

> history only affects the dominant rank.

Instead, the microbiome contains two layers of identity-free historical storage:

1. a strong dominance component, on which Alternaria has especially high leverage;
2. a lower-rank architecture component that also retains significant history and remains
   significant after Alternaria is removed.

## Relation to the v28–v35 chain

- v28: history is strong in fungal composition but weak in aggregate rust state.
- v31: fungal history survives removal of taxon identity.
- v33: a general first-arriver-role mapping does not specifically explain that memory.
- v34: Alternaria has the largest prospective history-level leverage.
- v35: that excess leverage is **dominance-centered**, but not dominance-exclusive.

This is a substantially narrower and more defensible biological result than the
superseded v32 role-symmetry explanation.

## Claim boundary

Do not claim:

- that the dominant taxon is necessarily Alternaria from this identity-free analysis;
- that Alternaria is the sole source of architecture memory;
- that lower-rank structure is unimportant;
- niche preemption versus niche modification;
- a universal dominance-storage law;
- cross-system generality.

Do claim:

> **In the v28 microbiome, the largest randomized-history leverage on identity-free
> community architecture is concentrated more strongly in rank-1 dominance than in the
> normalized structure of lower abundance ranks, while both components retain historical
> information.**
