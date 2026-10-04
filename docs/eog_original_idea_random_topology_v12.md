# Original EOG random static-equivalent topology — v12

## Question

v10 showed the static-map/topology distinction with controlled chain, star, branching
and redundant archetypes.

v12 asks whether that distinction persists in a randomized transition-graph ensemble.

## Frozen ensemble

Each row contains 12 independently generated rooted DAGs on the same active-node set.

Every DAG:

- has the same source-accessible M mask;
- therefore has the same complete G mask;
- shares the same A and B masks;
- shares the same continuous nodewise marginal-score vector.

Only the edge topology changes.

A random rooted arborescence guarantees common source accessibility.  Additional
forward edges are then added at frozen probabilities 0, 0.10, 0.25 or 0.50.

## Generality targets

The benchmark asks how often the static-equivalent worlds differ in:

- ordered-pair reachability;
- first-passage depth;
- single-node knockout response.

It also asks whether edge-rich worlds are, on average:

- more robust to node knockout;
- structurally shallower from source to targets.

## Why this matters

If the v10 result disappears under random topology, the old mosaic-versus-landscape
argument would be an artifact of four hand-designed examples.

If it persists, the insufficiency of the nodewise representation becomes a general
property of this static-equivalent graph ensemble rather than one crafted contrast.
