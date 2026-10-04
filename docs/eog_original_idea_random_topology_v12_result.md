# Original EOG random static-equivalent topology — v12 result

## Result

All eight preregistered hypotheses were supported across **144** replicate panels.

Each replicate contained **12 different directed topology worlds** with exactly the
same static nodewise representation:

- A;
- B;
- M accessibility mask;
- realised G;
- static marginal-score vector.

The internal transition graph alone differed.

## The v10 result generalizes

The random worlds retained strong topology-specific differences.

At 12 and 16 active nodes, all 48 replicates had:

- 12 distinct edge topologies;
- 12 distinct pairwise relation signatures;
- 12 distinct first-passage signatures.

At 8 active nodes, relation and first-passage still had 12 distinct classes in 40/48
rows and 11 classes in the remaining 8.

So the separation between a static distribution map and a relational/history
representation is not peculiar to chain/star/tree archetypes.

## Intervention response is a coarser target

Intervention signatures were less identifying.

At 8 active nodes the 12 topology worlds collapsed to 8–12 intervention classes.
At 12 and 16 nodes they collapsed to 9–12 classes.

Median world-to-target compression:

- pairwise relation: **1.00×**;
- first passage: **1.00×**;
- intervention: **1.33×** at 8 nodes, about **1.09×** at 12/16 nodes.

Thus different relational targets discard different amounts of topology identity.

## Topological densification has predictable ecological consequences

As extra-edge probability increased from 0 to 0.50:

- mean edge count: **11.0 → 41.1**;
- mean first-passage depth: **2.263 → 1.368**;
- mean retained reachability after single-node knockout: **0.880 → 0.991**;
- mean critical-node count: **5.00 → 0.586**.

Pooled Spearman correlations:

- edge count vs knockout retained fraction: **+0.750**;
- edge count vs mean first-passage depth: **−0.405**.

So a denser transition topology can be shallower and much more robust even though the
entire static accessibility/occurrence map is unchanged.

## Main implication

The original EOG contrast can now be stated beyond hand-built examples:

> **A complete static distribution surface does not identify the internal relational
> architecture that determines flow depth, source-to-source relations, bottlenecks and
> intervention response.**

For nodewise questions the static map may be sufficient.
For topology-sensitive questions it is not.

## Next question

v11 showed that narrow topology targets can sometimes be identified with very little
relational information in the four-archetype panel.

The next generality test should ask the same question in these random 12-world panels:

> **How does the minimum relational evidence burden scale with node count and target
> breadth once topology worlds are no longer hand-picked archetypes?**
