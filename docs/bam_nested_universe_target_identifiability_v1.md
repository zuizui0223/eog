# Nested-world target identifiability for finite BAM inference

## Setup

Let (W_0\subseteq W_1\subseteq\cdots) be nested declared BAM world universes and let
(e) be fixed evidence.

Define the exact survivor fiber

[
S_i=S(e;W_i).
]

Because (W_i\subseteq W_{i+1}) and evidence compatibility is evaluated world by
world,

[
S_i\subseteq S_{i+1}.
]

Let a declared ecological target be

[
T:W\rightarrow\mathcal Y.
]

Examples are an exact counterfactual distribution or a binary intervention decision.

## T1 — Target-image monotonicity

Under universe expansion,

[
T(S_i)\subseteq T(S_{i+1}).
]

Therefore the number of distinct target values is monotone non-decreasing.

## T2 — Identification can only be lost under universe expansion

Target identification at level (i) means

[
|T(S_i)|=1.
]

If the target is already unresolved at level (i), adding worlds cannot make the
existing conflicting target values disappear.

Thus the identification indicator is monotone non-increasing as the world universe
expands.

A larger universe may:

- preserve an identified target;
- turn an identified target into an unresolved target;
- preserve an already unresolved target.

It cannot resolve target disagreement without additional evidence or by removing
previously admissible worlds.

## T3 — Robustness profile rather than one robustness label

For a fixed target, define the universe profile

[
r_i=|T(S_i)|.
]

The target is identified exactly over those levels where (r_i=1).

This yields a more informative statement than a single robust/not-robust label.

For the frozen BAM programme the three levels are:

1. (W_0): original 64-world declared family;
2. (W_1(G)): same-G members of the preregistered 2,592-world ecological expansion
   lattice;
3. (W_2(G)=\mathcal C(G)): complete same-G binary decomposition closure.

The observed truth-weighted identification counts are:

[
A:652\rightarrow646\rightarrow34,
]

[
B:705\rightarrow693\rightarrow34,
]

[
M:732\rightarrow691\rightarrow34.
]

## Interpretation

The large drop from the structured ecological lattice to complete decomposition closure
does not imply that the W1 certificate is incorrect.

It means:

> **target robustness is conditional on the semantics of the admissible-world
> expansion.**

A logical counterexample and an ecologically admitted counterexample are different
objects.

This is especially important for EOG-style inference, whose strong claims are already
conditional on an explicitly declared model universe.

## Claim boundary

The monotonicity identities are elementary finite-set consequences and are not claimed
as new mathematics.

The BAM contribution under investigation is the explicit use of a nested
occurrence-conditioned world-universe ladder to report where a counterfactual target
first becomes unresolved and which ecological expansion dimensions create that loss.
