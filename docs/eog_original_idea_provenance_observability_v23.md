# Original EOG provenance-observability experiment — v23

## Question

v21 showed that activation history can persist in equilibrium provenance after final
occupancy converges.

v22 showed that occupancy snapshots alone leave exact activation history unresolved in
189/768 design rows.

v23 asks:

> **Can source-provenance observations recover history information that spatial
> occupancy snapshots cannot?**

## Frozen evidence classes

### Occupancy

The unchanged v22 complete non-source occupancy snapshots at t4, t5, t6 and t8.

### Provenance

For each equilibrium-reachable non-source node, one idealized source-tag observation
returns the exact set of sources that tie for earliest arrival at that node.

This is a structural known-truth provenance tag. It is not empirical ancestry,
admixture or a claim that such an assay is directly available in nature.

## Targets

Two targets are separated:

1. exact activation-history identity;
2. equilibrium provenance class.

The second target deliberately ignores activation-history differences that have no
effect on the final earliest-origin map.

## Exact design

With only three activation histories, each measurement can be represented by which
target-discordant history pairs it separates.

The benchmark solves the exact minimum set cover for:

- occupancy-only;
- provenance-only;
- combined evidence.

## Structural negative control

A node reachable from only one final source has the same earliest-origin source under
every activation history.

Therefore a provenance tag at a static unique-origin node must carry zero history
information.

Only confluence nodes can make provenance history-sensitive.
