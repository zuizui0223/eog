# Known-truth BAM v2.1 — orthogonal activation result

## Design gate

All preregistered activation gates passed before H1–H6 scoring:

- partner occupied fraction: **15/21 = 0.714**
- antagonist occupied fraction: **9/21 = 0.429**
- A-only witness pairs: **16**
- partner-B-only witness pairs: **11**
- antagonist-B-only witness pairs: **6**
- M-distance-only witness pairs: **7**
- M-barrier-only witness pairs: **12**
- same-final-G / different-arrival pairs: **812**
- positive-superset / diagnostic-negative pairs: **1,097**

This removes the v2 degeneracy. A, biotic interactions and movement limitation all generate independent contrasts in v2.1.

## Primary results

There were **64 candidate BAM worlds and 64 eligible truth worlds**.

All six frozen logical hypotheses were supported:

- H1 truth retention — SUPPORTED
- H2 axis-specific witness attribution — SUPPORTED
- H3 same-G non-identification — SUPPORTED
- H4 positive-superset ceiling — SUPPORTED
- H5 perfect-negative rescue — SUPPORTED
- H6 temporal-M rescue — SUPPORTED

No truth-retention, axis-attribution, equivalence, superset, negative-rescue or temporal-rescue violations occurred.

Result fingerprint:

`dbfd0c09b492c1e53914ddfdfe392c765df6da98a43e105245767c24c75ad9b3`

## A/B/M witnesses were genuinely present

Across ordered truth–candidate contrasts:

- A only: **179**
- B only: **307**
- M only: **207**
- A+B: **193**
- A+M: **53**
- B+M: **309**
- A+B+M: **87**

Thus the result is no longer driven only by B and M.

## The main negative result: BAM mechanism recovery remains weak

Truth uniquely identified from complete positive occurrences:

**0/64 = 0%**

After additionally observing every non-occupied node as a perfect surveyed negative:

**2/64 = 3.125%**

After additionally supplying exact known-truth first-arrival times for occupied nodes:

**6/64 = 9.375%**

So even an idealized data stream containing the complete final presence/absence map plus exact colonisation timing leaves **58/64 truth BAM worlds non-identifiable**.

This is not sampling error. It is structural non-identifiability of the decomposition

[
G=A\cap B\cap M.
]

Different A/B/M mechanisms can produce the same realised G, and different A/B decompositions can remain compatible even after M timing is known.

## What the extra evidence does accomplish

Perfect negatives eliminated **1,097/1,097** positive-superset false worlds that positive occurrences could not eliminate.

Temporal evidence eliminated **812/812** equal-G alternatives whose M first-arrival patterns differed from truth.

Therefore:

- positives constrain worlds through positive witnesses;
- negatives resolve permissive false worlds with extra predicted occupancy;
- time resolves some movement histories;
- none of these alone guarantees recovery of the full BAM decomposition.

## Scientific conclusion

The strongest supported claim is not that EOG recovers the true BAM mechanism.

It is:

> **EOG exposes which A, B and M explanations are contradicted by the available evidence and which remain observationally equivalent. Even complete occurrence and movement evidence need not identify a unique BAM decomposition.**

This makes the next target evidence design rather than forced model selection: identify which direct measurements of abiotic tolerance or biotic interaction state are needed to break the residual A/B equivalence classes.
