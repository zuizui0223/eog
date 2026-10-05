# EOG v33 result — role-mapping specificity audit

## Verdict

The preregistered v28 specificity prediction was **refuted**.

v33 was designed to audit a vulnerability in v32: the role-aligned response is itself
indexed by the observed history treatment.  To ask whether the *biologically correct*
first-arriver mapping was specifically informative, v33 enumerated every equally complex
one-to-one history-to-coordinate mapping.

Authoritative execution:

- workflow run: `37303768610`;
- artifact: `11342098187`;
- artifact digest:
  `sha256:a0f38b3a3a301e842febe1fe9e6905e4c9cd78c7e8f7234b05e51e946df5f7d3`;
- result fingerprint:
  `e41b9fafdc7902a0fd6649c96d6f61b7aafa53de9abca6180179e3cb5fa335fb`.

The v32 correct-mapping R² values were reproduced exactly before any placebo mapping was
accepted, and every mapping preserved the exact abundance multiset in every experimental
unit.

## v28 microbiome — the correct biological mapping is not specific

All **120** fungal history-to-coordinate bijections were enumerated.

Correct biological mapping:

- role-aligned R² = **0.945878**;
- median of the 119 incorrect mappings = **0.945209**;
- correct minus incorrect median = **+0.000669**;
- descending rank = **53 / 120**;
- exact mapping-specificity upper-tail probability = **0.4417**.

So the correct mapping is essentially central in the placebo ensemble, not exceptional.

The five highest-scoring mappings all retained:

- `Alternaria -> Alternaria`;

but permuted the other four fungal identities.  The maximum incorrect mapping reached:

- R² = **0.956289**,

which exceeds the biologically correct mapping.

This means the large v32 role-aligned score cannot be interpreted as evidence that the
full biological first-arriver mapping is the uniquely relevant storage representation.

## v30 grassland — the correct mapping is the weakest of all six

All **6** functional-group bijections were enumerated.

Correct biological mapping:

- role-aligned R² = **0.337247**;
- median of the five incorrect mappings = **0.876815**;
- correct minus incorrect median = **−0.539569**;
- descending rank = **6 / 6**;
- exact mapping-tail fraction = **1.0**.

The highest incorrect mapping reached:

- R² = **0.938223**.

Thus arbitrary treatment-dependent coordinate mappings can create much stronger apparent
separation than the biologically correct first-arriver mapping.

## Consequence for v32

The numerical v32 results remain reproducible:

- its role-aligned targets were calculated as declared;
- its first-arriver share summaries remain descriptive facts.

But the mechanistic interpretation is **not retained**.

v32 had proposed:

> storage mode tracks how interchangeable identities are in the first-arriver role.

v33 shows that the role-aligned statistic is not specific to the actual biological
history-to-identity correspondence.  Therefore it cannot support that explanation.

The correct post-v33 status is:

> **v31's system-specific storage-channel result remains supported, but the ecological
> mechanism that determines the storage channel is unresolved.**

## New clue, not yet a result

The mapping ensemble reveals a sharper candidate in v28.

Every top-five placebo mapping preserved `Alternaria -> Alternaria` while freely
reassigning the remaining histories.

That pattern suggests the architecture-level memory may be disproportionately driven by
one highly distinctive history state rather than by a general asymmetric first-arriver
role.

This is a post-result clue only.  It requires a separate frozen leverage / leave-one-
history-out test before it can be promoted.

## Claim boundary

Do not claim:

- that v32 identified first-arriver role symmetry as the mechanism;
- that the mapping-tail fraction is a causal randomization p-value;
- that Alternaria is already proven to be the sole driver;
- that v31 is invalidated.

Do claim:

> **Treatment-indexed role alignment is not biologically specific in either completed
> system.  The robust result remains target- and system-specific storage of assembly
> history; its mechanistic cause is still open.**
