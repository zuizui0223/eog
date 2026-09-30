# Joint-universe evidence burden for finite BAM future targets

## Setup

Let (W_E) be a finite ecological BAM world universe and (W_O) a finite
observation-process universe.

The joint hypotheses are

[
W_J = W_E \times W_O.
]

A declared future target

[
T:W_E\rightarrow\mathcal Y
]

depends only on the ecological world. Observation-world identity is nuisance
uncertainty.

Let (mathcal A) be a fixed finite action library. Each action maps each joint
hypothesis to an outcome support.

Define (b(W_E,W_O;T)) as the exact minimum number of actions whose joint outcomes
robustly separate every pair of joint hypotheses carrying different target values.

## T1 — Burden monotonicity under joint-universe expansion

If

[
W_E^0\subseteq W_E^1
quad\text{and}\quad
W_O^0\subseteq W_O^1,
]

then every target-discordant pair present in a smaller joint universe is also present in
the corresponding larger joint universe.

Therefore, for the same action library,

[
b(W_E^0,W_O^0;T)
\le
b(W_E^0,W_O^1;T)
\le
b(W_E^1,W_O^1;T)
]

and

[
b(W_E^0,W_O^0;T)
\le
b(W_E^1,W_O^0;T)
\le
b(W_E^1,W_O^1;T).
]

Insufficiency is treated as infinity.

This is elementary finite-set logic, not a novel theorem.

The Phase-IX audit found zero violations across 387 fiber-target rows.

## T2 — A joint burden interaction contrast

Define

[
I
=
b(W_E^1,W_O^1;T)
-
\max\{
b(W_E^1,W_O^0;T),
b(W_E^0,W_O^1;T)
\}.
]

A positive (I) means the combined expanded universe requires more evidence than
either single-axis expansion alone.

This does not assert a statistical interaction parameter. It is an exact contrast of
minimum target-separation burdens.

The frozen BAM audit observed (I>0) in 51/387 rows.

## T3 — Calibration relevance is joint-universe dependent

Let (mathcal A^{-c}) be the fixed action library without explicit
observation-process calibration.

Calibration is required for every minimum-size design in a joint universe when

[
b_{mathcal A}(W_E,W_O;T)
<
b_{mathcal A^{-c}}(W_E,W_O;T),
]

where an insufficient no-calibration library has infinite burden.

The Phase-IX audit found nine cases satisfying:

1. W0O1 had a finite no-calibration target design;
2. W1O1 had a strictly smaller full-library burden than any no-calibration design.

Thus ecological-world expansion can make an observation-process calibration action
newly target-relevant.

## Interpretation

Measurement quality should not be assessed in isolation from model uncertainty.

An assay ambiguity that maps only among same-target ecological alternatives is harmless
for that target.  Expanding the ecological world family can add a target-discordant
alternative with the same assay code, turning the same observation-process uncertainty
into a decision bottleneck.

Conversely, multiple assay channels can sometimes provide enough joint signature
structure to resolve the target without explicitly identifying the observation world.

## Boundary

All statements are conditional on the finite ecological, observation and action
universes.

No claim is made that the Phase-IX systematic assay process represents laboratory
measurement error or that action cardinality represents real field cost.
