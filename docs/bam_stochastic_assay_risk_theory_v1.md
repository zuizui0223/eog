# Exact robustness versus stochastic risk for BAM future-target assays

## 1. Two different inferential claims

Let (H_1,H_2) be joint ecological/observation hypotheses with different future target
values.

An **exact robust** assay design requires at least one selected action whose possible
outcome supports are disjoint.

A **risk-bounded** design permits overlapping support and instead controls a
distributional error criterion.

These claims must remain distinct.

## 2. Full-support error prevents finite-repeat exact robustness

Let one assay under hypothesis (H_i) have categorical distribution (P_i), with

[
P_i(y)>0
]

for every code (y).

For (n) iid repeats, every finite sequence has positive probability

[
P_i^{\otimes n}(y_1,\ldots,y_n)>0.
]

Therefore two full-support hypotheses retain overlapping support for every finite
(n).

If a target-discordant pair remains under the same assay-quality world, no finite
repeat count can provide support-disjoint exact separation.

Phase VIII verified this boundary in all **67** scored fibers.

## 3. Repetition can still reduce stochastic overlap

Define Bhattacharyya affinity

[
BC(P,Q)=\sum_y\sqrt{P(y)Q(y)}.
]

For iid repeats,

[
BC(P^{\otimes n},Q^{\otimes n})
=
BC(P,Q)^n.
]

For conditionally independent selected assay fields, the field affinities also
multiply.

Thus, whenever the relevant distributions differ and (BC<1), repeated independent
measurement can drive the affinity toward zero exponentially even though support
overlap never disappears.

The frozen Phase-VIII decision criterion uses

[
P_e^*\le BC/2\le0.05
]

for every target-discordant pair.

This is a pairwise sufficient upper bound, not an exact global error probability.

## 4. When quality calibration can help

Let (q) index assay-quality worlds.

Idealized quality calibration perfectly separates pairs with

[
q_1\neq q_2.
]

It has no effect on pairs with

[
q_1=q_2.
]

Therefore, under a worst-pair criterion, quality calibration can reduce the required
repeat depth only if every pair attaining the uncalibrated worst bound is cross-quality
or if removing cross-quality pairs reveals a strictly smaller same-quality maximum.

If a same-quality target-discordant pair is already the bottleneck, perfect quality
calibration cannot improve that bound.

Phase VIII observed exactly this latter regime in **67/67** fibers.

Consequently H4 was refuted: perfect quality calibration produced zero strict total
synthetic action-cost savings.

## 5. Observation-process routing now has three levels

The BAM successor now distinguishes:

1. **deterministic systematic miscoding** — repetition can be exactly redundant;
2. **random full-support error** — repetition reduces risk but cannot recover exact
   robustness;
3. **observation-world calibration** — useful only when nuisance observation-world
   ambiguity is actually part of the target-limiting pair.

This makes the correct routing question:

> **What observation process is generating the uncertainty, and what guarantee does
> the ecological decision require?**

Only after those are declared should one choose replication, multichannel
self-calibration, explicit calibration, or a different evidence class.

## Boundary

Bhattacharyya affinity and iid product identities are standard probability theory and
are not claimed as new mathematics.

The BAM-specific contribution is using this distinction downstream of an
occurrence-conditioned finite A/B/M survivor fiber with a frozen future ecological
target and a frozen target-specific assay set.
