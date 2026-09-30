# BAM decision robustness margin v1

## Why this successor exists

Phase II showed that complete current (G) can leave the BAM mechanism unresolved while
a binary counterfactual decision is already invariant inside the declared finite world
universe.

That conclusion is exact, but conditional on which BAM worlds were declared.

The next question is therefore:

> **How close is the declared survivor fiber to an undeclared same-G BAM decomposition
> that would reverse the decision?**

## Complete same-G decomposition closure

For finite node universe (X), define

[
\mathcal C(G)
=
\{(A,B,M): A\cap B\cap M=G\}.
]

If (G\subset X), then for every single-axis release probe, (mathcal C(G)) contains
both binary outcomes.

For example, for release A and any (x\notin G):

- a no-expansion completion can set (B\cap M=G);
- an expansion completion can set (B_x=M_x=1) and (A_x=0), preserving current
  (G) while making (x) appear after A is released.

Therefore a binary release conclusion can be identified from current (G) only because
the admissible BAM family excludes at least some same-G decompositions.

This does **not** make the finite-universe result wrong.  It exposes exactly what its
certificate is conditional on.

## Completion flip margin

Distance between two BAM states is Hamming distance across all binary A/B/M node states.

For a declared decision-identified survivor fiber, define the completion flip margin as
the minimum distance from any survivor to any same-G BAM completion with the opposite
binary decision.

Interpretation:

- margin 1 — one undeclared axis-node state flip can reverse the conclusion;
- margin 2 — at least two coordinated state changes are required;
- larger margin — stronger structural dependence is required to reverse the decision;
- margin 0 — the declared survivor fiber already contains decision disagreement.

This is a **logical model-universe sensitivity margin**.  It is not a probability that
the undeclared completion is ecologically realistic.

## Closed form

For release A, with current state ((A,B,M)):

### Current decision = expansion

Let

[
E_A=(B\cap M)\setminus G.
]

Every node in (E_A) must be removed from either B or M to eliminate expansion.
Therefore

[
\rho_A=|E_A|.
]

### Current decision = no expansion

For any (x\notin G), an expansion completion requires the local pattern

[
(A_x,B_x,M_x)=(0,1,1).
]

The exact margin is the minimum Hamming mismatch to this pattern over all
(x\notin G).

Release B and M follow by permutation of the axes.

The implementation is exhaustively checked against enumeration of every three-node BAM
decomposition.

## Scientific boundary

Generic robust decision making under structural model uncertainty is established in
adaptive management and decision analysis.  This module does not claim otherwise.

The BAM-specific question is narrower: how much must the **same-G decomposition
boundary** be relaxed before an occurrence-conditioned counterfactual conclusion
changes?
