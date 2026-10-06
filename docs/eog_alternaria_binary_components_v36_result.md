# EOG v36 result — direct Alternaria-versus-rest component test

## Verdict

The prospectively frozen prediction was **supported**:

> **The direct Alternaria-versus-rest assembly-history contrast is more strongly encoded
> in identity-free rank-1 dominance than in the normalized lower-rank abundance shape.**

Authoritative execution:

- workflow run: `37425205017`;
- platform: `ubuntu-24.04-arm`;
- artifact: `11395236358`;
- artifact digest:
  `sha256:bf4d4dc7e7fd04142d2a7d2de3e772cd16d771b00bcbd0c04615de432c16469e`;
- result fingerprint:
  `dfbe027e089089096c4a8a571396081a5531b5d57e4d00ea8a8ccab64d3ac421`.

The v34 Alternaria-versus-rest full-rank result was reproduced exactly before the new
component scores were accepted.

## Frozen binary contrast

Full panel:

- n = **233** plants;
- Alternaria history = **48**;
- Other histories = **185**.

No plant was removed.

## Full rank-abundance gate

The complete five-rank identity-free response reproduced v34:

- partial R² = **0.13318**;
- null median = **0.05286**;
- E = **+0.08032**;
- p = **0.0004**.

## Rank-1 dominance

Largest fungal abundance share:

- partial R² = **0.16947**;
- null median = **0.05135**;
- retained-history excess E = **+0.11812**;
- null 95% interval = **0.01965–0.10337**;
- permutation p = **0.0002**.

Descriptively:

- Alternaria-history mean rank-1 share = **0.7783**;
- median = **0.7929**;
- Other-history mean = **0.7112**;
- median = **0.7131**.

## Lower-rank architecture

Ranks 2–5 were renormalized to sum to one:

- partial R² = **0.10044**;
- null median = **0.05321**;
- E = **+0.04723**;
- null 95% interval = **0.02551–0.10304**;
- permutation p = **0.0316**.

The lower-rank community therefore also retains a detectable Alternaria-versus-rest
history signal.

## Frozen component contrast

[
Delta E_{D-T}
=
E_{mathrm{dominance}}
-
E_{mathrm{tail}}
=
mathbf{+0.07090}.
]

Both preregistered criteria were met:

1. dominance E > 0;
2. dominance E > lower-tail E.

## Biological interpretation

v35 showed that deleting Alternaria removes more history from dominance than from the
lower-rank tail.

v36 strengthens that result by using a direct randomized-history contrast on the full
panel:

> **Alternaria history is associated with a stronger present-day signature in the
> intensity of community dominance than in the relative organization of non-dominant
> ranks.**

This is not a claim that lower-rank structure is unaffected. Its retained-history excess
remains positive and its frozen permutation diagnostic is 0.0316.

The combined v34-v36 picture is therefore:

- architecture memory is distributed across multiple histories;
- Alternaria has the largest history-level leverage;
- that leverage is disproportionately expressed through dominance;
- the direct Alternaria-versus-rest contrast independently shows the same dominance-
  centered structure.

## Claim boundary

Do not claim:

- that the dominant taxon is necessarily Alternaria;
- that Alternaria is the sole source of history memory;
- that lower-rank structure is unimportant;
- niche preemption versus niche modification;
- a universal dominance mechanism;
- cross-system generality.
