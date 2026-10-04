# Original EOG adaptive relational evidence — v14

## Question

v13 found that random static-equivalent topology panels usually require three, and
sometimes four, relational measurements when one **fixed panel** must resolve the
target for every possible outcome.

v14 asks whether that is unnecessarily expensive.

If the first relational measurement has different outcomes in different worlds, EOG can
contract the candidate set and choose a different second measurement on each branch.

## Frozen comparison

No new worlds, targets or measurement types are added.

The exact v13 REL / FP / KO library is reused.

For each row and target, compare:

1. v13 fixed nonadaptive minimum;
2. exact adaptive minimum worst-case depth.

The adaptive planner stops as soon as all surviving worlds share the target value.
For full-topology identity, that means one world. For a coarser ecological target,
multiple topology worlds may legitimately remain.

## Exact recursion

The decision-tree state is only the current subset of the 12 candidate worlds.

Because measurements are deterministic, an action already used on a branch is constant
inside the corresponding child subset and cannot split it again. Therefore the exact
memoized recursion does not need a separate used-action state.

## Main distinction

Adaptive evidence can help in two different ways:

- **worst-case saving** — every possible outcome path is shorter than the best fixed
  panel;
- **realized-path saving** — worst-case depth may be unchanged, but many outcomes stop
  earlier.

The second is reported as an equal-world descriptive average over the 12 finite worlds,
not as an ecological probability.

## Why this matters for the original EOG idea

The original concept was not only to retain multiple possible histories. It was also to
use the differences among surviving histories to decide what to observe next.

v14 tests that operationally in the random-topology world family.
