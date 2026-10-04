# Original EOG marginal-topology equivalence — v10

## Question

Can two ecological worlds look identical in every static nodewise representation and
still differ in the distribution-forming structure that matters biologically?

v10 fixes, within each replicate:

- A;
- B;
- M accessibility mask;
- realised G;
- a continuous static marginal score at every node.

Only the internal directed transition topology differs.

## Four topology worlds

- chain;
- star;
- balanced branching tree;
- redundant network.

Every topology has the same source-reachable active-node set and therefore the same
nodewise BAM state and complete occurrence mask.

## What the static representation does not contain

The static representation deliberately omits:

- pairwise occurrence-to-occurrence reachability;
- source-to-node first-passage depth;
- route redundancy;
- response to node removal.

These are then scored as separate topology-sensitive targets.

## Main conceptual test

If worlds share exactly the same static representation but differ in a declared target,
that target is not identifiable from the static representation alone.

The mathematical statement is generic.  The ecological question is which
distributional-history quantities are discarded when BAM/SDM-like node masks are used
without transition topology.

## Why this returns to the original EOG idea

This is the direct virtual-world version of the old contrast:

- SDM-like output: a mosaic of nodewise values;
- EOG-like output: a landscape with routes, ordering, bottlenecks and flow.

A favorable result does not mean a real SDM is wrong.  It shows precisely which
questions cannot be answered from a nodewise surface when relational topology is not
represented.
