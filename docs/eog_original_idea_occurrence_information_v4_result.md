# Original EOG occurrence information — v4 result

## Result

Six of seven preregistered hypotheses were supported.

The most useful result is the failed one.

## Positive occurrence contains information beyond local viability

All candidate worlds shared the same A/B-permissive nodes.  Therefore interpreting an
occurrence only as "this node is locally viable" retained 100% of the candidate
source × barrier × analyst-rule worlds.

Reachability-aware positive evidence did not.

Mean surviving-world fractions were:

| coverage | clustered | dispersed |
|---|---:|---:|
| 10% | 0.580 | 0.496 |
| 25% | 0.537 | 0.470 |
| 50% | 0.502 | 0.456 |
| 100% | 0.447 | 0.447 |

So the same occurrence point carried extra information once its realized reachability
meaning was used.

## The spatial arrangement of occurrence points matters

In **211/314** eligible randomized landscapes, clustered and dispersed anchors with the
same point count retained different numbers of candidate worlds.

The preregistered directional contrasts were favorable:

- 25% coverage, dispersed minus clustered survivor fraction: **-0.067**;
- 50% coverage: **-0.045**.

Thus information depended not only on the number of occurrences but on their spatial
configuration.

## Complete positive coverage still did not identify the history

At 100% of the truth-positive non-source occurrence set:

- median surviving candidate worlds: **104**;
- median surviving candidate sources: **30**;
- exact world recovery: **0/314**;
- exact source recovery: **0/314**.

So even a complete positive distribution did not tell the model which source, barrier
state and analyst rule generated it.

This is very close to the original EOG intuition: observed points constrain histories,
but do not collapse the distribution to one history.

## Robust impossibility was sound

Across all coverages and both spatial designs:

- false robust exclusions of a truth-reachable locally permissive node: **0**.

Because the truth world remains among the survivors, a node declared unreachable in
every surviving world cannot be reachable in the truth world.

## The surprising refutation: more positives did not recover more impossibility

O5 predicted that robust-impossibility recovery would increase as more truth-positive
anchors were revealed.

It did not.

Mean recovery fraction was **0.393854** at 10%, 25%, 50% and 100% coverage under both
sampling designs.

A post-result structural diagnostic, which does not reclassify O5, found:

- recovery fraction was constant in **314/314** eligible rows for clustered anchors;
- constant in **314/314** for dispersed anchors;
- yet survivor-world count still shrank from 10% to full coverage in 221 clustered rows
  and 114 dispersed rows.

So additional occurrence evidence was often informative about which world/source
remained possible, while being completely uninformative about the robust-impossibility
envelope.

## Why this matters

In a static undirected reachability world, once a positive anchor lies in a connected
component, any candidate source in that component generates the same reachable
component. Additional positive anchors can reject some worlds or sources, but they need
not change the union of reachable components across the survivors.

This exposes a limitation of static undirected occurrence inference.

The next test should therefore restore two parts of the original "flow" idea that v4
deliberately omitted:

1. **directionality**;
2. **temporal arrival order**.

The next question is:

> Does directed/temporal flow convert additional occurrence information into new
> source discrimination and new robust-impossibility information, rather than merely
> shrinking labels inside a fixed connectivity envelope?
