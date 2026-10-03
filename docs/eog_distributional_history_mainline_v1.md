# EOG distributional-history mainline v1

## Status

This is the active post-closure method-development direction after the finite-BAM and
target-quotient programmes.

It does not reopen the frozen EOG-WF three-endpoint manuscript denominator and does not
change any historical empirical result.

## Scientific center

The primary EOG question is not:

Which BAM decomposition is the true one?

It is:

Given locally supported states, observed occurrence anchors, and a declared family of
geographic/environmental/barrier transition worlds, which occurrence-to-occurrence
relations and distributional histories remain possible, robust, unresolved, or
excluded?

An occurrence carries at least two kinds of structural evidence:

1. the state was locally realizable under some admissible world;
2. the state was reached inside some admissible distribution-forming history.

EOG therefore treats the spatial relations between occurrences as first-class objects
rather than reducing the distribution to independent cellwise support values.

## Core representation

For positive occurrence anchors O and a finite declared world universe W:

W(O) = {w in W : w is compatible with O}.

For each compatible world, EOG keeps its full transition operator and propagates
source-conditioned flow.

The relation layer then evaluates every ordered occurrence pair o_i -> o_j.

For a pair, EOG reports:

- reachable in all worlds;
- contingent on which compatible world is used;
- robustly unreachable;
- fixed first-arrival propagation depth;
- variable first-arrival depth;
- partial arrival depth when the relation itself is world-dependent.

Propagation depth is structural graph depth, not calibrated years or generations.

## Why this restores the original EOG idea

The method now explicitly preserves the objects that motivated EOG before the BAM
identifiability detour:

- occurrence-to-occurrence reachability;
- IBD-like geographic constraints;
- IBE-like environmental continuity;
- barriers and stepping stones;
- branching and confluence;
- bottlenecks;
- source-conditioned first passage;
- edge flux and route diversification;
- basin merge under monotone relaxation;
- time-stamped positive occurrence history;
- later comparison with genetic distance.

This is the distributional-watershed idea: a realised distribution is treated as an
outcome of flow through a structured landscape, with alternative admissible histories
retained rather than one history selected.

## Existing implementation assets

No new transition model is required.

Existing EOG components already provide:

- dynamic_island_reachability.py
  - first-passage support;
  - first-arrival depth;
  - source attribution;
  - edge flux;
- world_reconstruction.py
  - exact compatible-world reconstruction;
  - possible / robust / unresolved / excluded state;
- relaxation_family.py
  - geographic/environmental/barrier relaxation;
  - basin merge;
- temporal_reconstruction.py
  - time-stamped positive reachability constraints;
- ecological_traversability.py
  - environmental continuity and transit-viability primitives;
- reachability_genetics.py
  - frozen geographic / environmental / EOG-R distance bundles for genetic validation;
- distributional_history.py
  - occurrence-to-occurrence relation envelopes over compatible worlds.

## Role of BAM

BAM remains useful, but it is no longer the top-level representation of EOG.

Its role is optional mechanism-coordinate / diagnostic layer for constructing or
interpreting ecological worlds.

A, B and M may explain why an edge, node or world exists or is eliminated. They do not
replace the richer EOG objects: route, ordering, branching, source, bottleneck, first
passage, landscape flow and temporal history.

The finite-BAM and target-quotient results remain valid and frozen. They supply a
warning against over-interpreting current occurrence patterns as unique mechanisms.

## Output hierarchy

The active EOG output hierarchy is now:

local support / viability
-> declared transition worlds
-> positive occurrence conditioning
-> compatible world set
-> per-world dynamic flow
-> occurrence-to-occurrence relation graph
-> possible / robust / unresolved distributional-history structure
-> target-specific quotient when a declared decision is supplied.

The target quotient is downstream of the history representation. It is not a
replacement for it.

## Validation strategy

The next scientific validation should not ask whether another synthetic BAM factorial
behaves similarly.

Priority order:

1. relation validation:
   does frozen EOG reachability between sampled populations explain independent genetic
   differentiation beyond geographic distance and environmental distance?
2. temporal validation:
   do earlier occurrences constrain later occurrence relations under a frozen
   transition family?
3. intervention validation:
   after a real barrier change, do predeclared relation/world certificates contract or
   fail as predicted?

The strongest direct return to the original idea is the genetics route because it tests
whether an occurrence-derived reachability relation contains information about realised
between-population connection not reducible to IBD or IBE.

## Claim boundary

EOG does not infer a unique historical route unless independent evidence identifies it.

Occurrence-pair relation support is not observed migration, ancestry, colonisation
probability, dispersal probability or demographic connectivity.

The contribution is to retain a set of admissible distribution-forming histories and
report which relational properties survive disagreement among those histories.

## Development stop

Do not create another BAM factorial or synthetic ecological transformation to improve a
pattern already established in the closed known-truth programme.

New work must either expose an existing relational/history quantity through the unified
EOG interface or test that quantity against an independent external evidence class.
