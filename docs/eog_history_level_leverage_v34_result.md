# EOG v34 result — history-level leverage on abundance-architecture memory

## Verdict

The prospectively frozen prediction was **supported**:

> **Removing the Alternaria arrival history produces the largest positive loss of
> identity-free rank-abundance history retention.**

Authoritative execution:

- workflow run: `37304759267`;
- artifact: `11343470202`;
- artifact digest:
  `sha256:f0f3b139af77cb6f8dc1bf696279cc51b0ff3a7057fddcbcbec3632579cf7b56`;
- result fingerprint:
  `6ddf1d089dd3885c6d12a1809629ef1dd1486fcab7a03c81bfb9b7ce81ca0325`.

The authoritative v31 full-panel rank-abundance result was reproduced exactly before any
deletion result was accepted.

## Full architecture-memory baseline

All five fungal histories:

- n = **233** plants;
- partial R² = **0.3672**;
- null median = **0.2186**;
- retained-history excess E = **+0.1486**;
- permutation p = **0.0001**.

## Leave-one-history-out leverage

Define:

[
D_h = E_{mathrm{full}} - E_{-!h}.
]

Positive D means that removing history h weakens identity-free abundance-architecture
memory.

### Alternaria

- removed n = **48**;
- remaining n = **185**;
- E_without = **+0.0875**;
- p = **0.0086**;
- leverage D = **+0.0611**.

This is the largest leverage among the five histories.

### Cladosporium

- E_without = **+0.1222**;
- p = **0.0018**;
- D = **+0.0264**.

### Aureobasidium

- E_without = **+0.1575**;
- p = **0.0001**;
- D = **−0.0088**.

### Fusarium

- E_without = **+0.1715**;
- p = **0.0001**;
- D = **−0.0229**.

### Dioszegia

- E_without = **+0.1822**;
- p = **0.0001**;
- D = **−0.0336**.

Frozen leverage ranking:

1. **Alternaria** +0.0611
2. **Cladosporium** +0.0264
3. Aureobasidium −0.0088
4. Fusarium −0.0229
5. Dioszegia −0.0336

Thus the v33 Alternaria clue was not merely a placebo-mapping coincidence.

## Alternaria versus all other histories

On the full 233-plant panel, collapsing history to Alternaria versus all other fungal
histories gave:

- partial R² = **0.1332**;
- null median = **0.0529**;
- E = **+0.0803**;
- p = **0.0004**.

A single binary contrast therefore captures a substantial fraction of the architecture-
level history signal.

## What this means — and what it does not

Alternaria has **disproportionate leverage** on architecture-level memory.

But it is **not the sole driver**.

After removing every Alternaria treatment plant, the four-history panel still retains:

- E = **+0.0875**;
- p = **0.0086**.

So the correct biological interpretation is:

> **The microbiome's identity-free abundance architecture contains distributed assembly
> memory, but that memory is strongly uneven across histories, with Alternaria providing
> the largest leverage.**

This is narrower and better supported than the v32 claim that a general asymmetric
first-arriver role explains the storage channel.

## Relation to v33

v33 showed that the full history-to-first-arriver coordinate mapping was not biologically
specific relative to placebo mappings.

However, every top-five v33 mapping retained `Alternaria -> Alternaria`.

v34 tested that post-result clue using a Treatment-independent rank-abundance response.
The prospective deletion prediction succeeded.

Therefore the new mechanism-facing clue is not:

> all fungal identities express the first-arriver role asymmetrically.

It is:

> **one arrival history is unusually influential in shaping identity-free community
> architecture, while weaker architecture memory remains distributed among other
> histories.**

This still does not identify the ecological interaction mechanism.

## Claim boundary

Do not claim:

- Alternaria is the sole source of microbiome historical memory;
- Alternaria causally modifies the community through a specific interaction mechanism;
- niche preemption or niche modification;
- that unequal history leverage is universal;
- that leave-one-history-out differences are directly comparable to a balanced factorial
  intervention after deletion.

Do claim:

> **Among the five randomized fungal arrival histories, Alternaria has the largest
> prospective deletion leverage on identity-free abundance-architecture memory, while
> significant residual memory persists without it.**
