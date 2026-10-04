# Original EOG marginal-topology equivalence — v10 result

## Result

All eight preregistered hypotheses were supported across **192/192** virtual-world
replicates.

The central result is simple:

> **The same complete static BAM/raster map can correspond to very different
> distribution-forming topologies.**

Within every replicate the four worlds had exactly the same:

- A mask;
- B mask;
- M accessibility mask;
- realised G;
- continuous nodewise marginal-score vector.

Only the internal movement graph differed.

## Pairwise relations were different

The static representation formed one equivalence class of four worlds.

Yet the directed occurrence-to-occurrence relation signature split that class in every
replicate.

For 10 active nodes, all 64 replicates had four distinct relation signatures.

Mean relation Hamming distances included:

- chain versus star: **36**;
- chain versus balanced branching: **26**;
- star versus balanced branching: **10**.

For 14 active nodes:

- chain versus star: **78**;
- chain versus branching: **60**;
- star versus branching: **18**.

So the relational difference grew with the size of the distribution even though the
static nodewise map remained exactly unchanged.

## First-passage history was different

Mean source-to-node first-passage depth:

| active nodes | chain | branching | star | redundant |
|---|---:|---:|---:|---:|
| 6 | 3.00 | 1.60 | 1.00 | 1.00 |
| 10 | 5.00 | 2.11 | 1.00 | 1.00 |
| 14 | 7.00 | 2.38 | 1.00 | 1.00 |

Thus even complete knowledge of the final M/G mask does not determine whether the
distribution was structurally shallow, deep, branching or direct.

## Intervention response was different

At 14 active nodes, the mean number of critical non-source nodes was:

- chain: **12**;
- balanced branching: **6**;
- star: **0**;
- redundant: **0**.

Mean fraction of remaining active nodes still reachable after single-node knockout:

- chain: **0.538**;
- branching: **0.893**;
- star: **1.000**;
- redundant: **1.000**.

The same accessibility mask can therefore imply very different vulnerability to local
loss or barrier formation.

## What BAM masks retain and what they discard

The shared M mask correctly records the set of nodes accessible from the source.

It does **not** identify:

- which occurrence can reach which other occurrence;
- how many transition steps separate source and target;
- whether accessibility depends on one critical node;
- whether alternative routes exist;
- how a local knockout changes downstream reachability.

Those are topology/history quantities.

## Direct implication for the original EOG idea

The old contrast between a flat distribution mosaic and a flowing landscape can now be
stated exactly:

> A nodewise representation can be sufficient for a nodewise target and still be
> information-theoretically insufficient for a relational or intervention target.

BAM remains useful for separating A/B/M mechanisms, but an M accessibility set alone is
not the full movement process.

For topology-sensitive questions, EOG must retain the transition structure inside M,
not only its reachable-node mask.

## Boundary

This is known-truth information sufficiency, not an empirical comparison against a
fitted SDM.

The next useful experiment should ask how much relational information is minimally
needed to recover specific topology-sensitive targets, rather than merely showing that
the full static map is insufficient.
