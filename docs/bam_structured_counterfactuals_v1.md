# BAM structured counterfactuals v1

## Purpose

The earlier BAM successor used idealised axis-release probes.

Phase V replaces those targets with three prospectively frozen ecological
transformations while preserving the same occurrence-conditioned inverse framework.

## Transformation 1 — synthetic climate shift

Every node environment is transformed by

[
\Delta temperature=+0.08,
\qquad
\Delta moisture=-0.04.
]

Each world keeps its own frozen abiotic niche center and radius.  A is recomputed under
the shifted environment; B and M are unchanged.

Targets:

- exact future occupied map;
- binary **net range loss**, defined by fewer occupied nodes than current (G).

This is a synthetic perturbation, not an emissions scenario.

## Transformation 2 — biotic stress

For each world:

- current partner range receives one additional 4-neighbour erosion;
- current antagonist range receives one additional 4-neighbour dilation;
- the world's existing interaction-mode bits are unchanged.

A and M stay fixed.

Targets:

- exact future occupied map;
- binary **range loss**, defined by a strict subset of current (G).

The operator is monotone restrictive by construction.

## Transformation 3 — barrier restoration

Each world keeps its own dispersal radius and horizon, but barrier permeability is
forced to true.

A and B remain fixed.

Targets:

- exact future occupied map;
- binary **range gain**, defined by at least one newly occupied node outside current
  (G).

The operator is monotone non-decreasing in accessibility.

## Two current-world universes

### W0

The original frozen 64 BAM parameter worlds.

### W1

The Phase-IV 2,592-world ecological parameter lattice.

For a current E1 fiber, both universes are filtered to worlds reproducing the exact same
current (G).

## Four levels of identity

The audit keeps separate:

1. parameter-world identity;
2. current BAM-state identity;
3. exact transformed-distribution identity;
4. binary decision identity.

The distinction matters because a transformation can reactivate parameter differences
that are dormant in the current A/B/M/tau state.

## Pre-score protocol amendment

Before implementation, design audit recognized that counterfactual outcomes are not
necessarily functions of current BAM-state equivalence: two parameter worlds can share
the same current A/B/M/tau but respond differently after a transformation.

Therefore the guaranteed coarsening hierarchy is:

[
\text{parameter world}
\rightarrow
\text{exact counterfactual map}
\rightarrow
\text{binary decision},
]

while current BAM-state identity is audited separately for **dormant-alias
reactivation**.

No counterfactual result was inspected before this amendment.
