# Response-blind world-universe scale design

## Purpose

The first independent EOG-WF attempt on STOC exposed a structural design failure before heldout prediction: every frozen world inherited a local site-spacing scale, and the entire 20-world universe was incapable of realizing the calibration distributions.

This document defines the prospective correction. It does **not** reopen STOC and it does not introduce a new ecological connectivity operator.

## Core rule

> **A candidate EOG-WF world universe must bracket the spatial scale of the intended forecast before species responses are opened.**

Response-blind is necessary but not sufficient. A threshold may be chosen without response leakage and still be structurally incapable of representing the domain on which the forecast claim is made.

## Two legitimate routes to world scale

### 1. Externally calibrated process scale

Use an independently justified dispersal, movement, transport, barrier or transition scale when one is available and scientifically appropriate.

Such a scale may be called biological/process-calibrated only to the extent supported by that external evidence.

### 2. Response-blind structural coverage ladder

When a defensible biological transition scale is unavailable, EOG may construct **analyst-choice structural worlds** from the node geometry or another declared metric space.

For target largest-component fractions

```text
c1 < c2 < ... < ck
```

the structural ladder chooses, for each target `ci`, the smallest pairwise-distance threshold `ri` for which the threshold graph reaches

```text
largest weak component / number of nodes >= ci.
```

All equal-distance edges are admitted together. The resulting thresholds are non-decreasing and the graph edge sets are nested.

The targets are **not universal constants**. They must be declared before response access and justified by the intended forecast scale. For example, a study may deliberately bracket local, regional and near-spanning regimes, but EOG does not prescribe fixed fractions for all studies.

The implementation is:

- `src/eog/v2/world_scale_ladder.py`
- `StructuralScaleLadderDeclaration`
- `build_structural_scale_ladder(...)`
- `structural_scale_adjacencies(...)`

The API takes node IDs and a distance matrix. It has no species, occurrence or response argument.

## Why this is not a novelty claim

The mathematical ingredients are established:

- graph connectivity changes as critical distance is varied;
- threshold sensitivity and abrupt changes in graph structure are standard concerns in landscape connectivity;
- minimum spanning trees are established tools for identifying connectivity structure;
- percolation/critical-connectivity ideas are established in ecology and random geometric graphs.

Relevant prior-art anchors include:

- Urban & Keitt (2001), *Landscape Connectivity: A Graph-Theoretic Perspective*, Ecology 82:1205–1218, DOI `10.1890/0012-9658(2001)082[1205:LCAGTP]2.0.CO;2`.
- Moilanen (2011), *On the limitations of graph-theoretic connectivity in spatial ecology and conservation*, Journal of Applied Ecology 48, DOI `10.1111/j.1365-2664.2011.02062.x`.
- With & Crist (1995/1997 structural-threshold/percolation tradition; see also the 1997 Acta Oecologica structural connectivity threshold paper), DOI `10.1016/S1146-609X(97)80075-6`.
- Pascual-Hortal & Saura (2006), graph-based landscape connectivity indices, DOI `10.1007/s10980-006-0013-z`.

EOG's use is methodological discipline, not new graph theory:

> use an established threshold filtration before response access to ensure that the declared world universe contains structurally distinct scales relevant to the intended forecast, then retain those scale identities as worlds rather than choosing one scale after seeing species outcomes.

## Primary scale axis versus secondary filters

The structural ladder is most important for the **primary spatial transition axis**. Secondary axes may represent environmental continuity, barriers, products, preprocessing choices or process alternatives.

Hard intersections can fragment graphs substantially. Therefore EOG should not force every world to be a geography × environment intersection when that would erase the broad structural scale bracket.

`compose_intersection_worlds(...)` can retain:

1. primary-only structural worlds; and
2. primary × secondary intersection worlds.

This preserves both questions:

- what is reachable under the declared spatial scale alone?;
- what remains reachable after an environmental/barrier constraint is imposed?

The second is not allowed to silently replace the first.

## Structural adequacy is a separate gate

Scale construction and scale certification are separate.

After all declared world axes are composed, run the response-blind structural audit in `src/eog/v2/world_adequacy.py`.

The audit reports, without accepting species responses:

- weak component count;
- largest-component fraction;
- isolated-node fraction;
- degree summaries;
- directed horizon-reachable fractions.

A prospectively declared `StructuralAdequacyDeclaration` then decides whether the universe is eligible for the intended forecast.

Not every world must be spanning. Local or fragmented worlds can be scientifically meaningful alternatives and may later be falsified by occurrence evidence. The adequacy question is whether the **declared universe as a whole contains the structural regimes required by the forecast claim**.

## What must be frozen before response access

For every prospective independent EOG-WF study record:

1. node universe and metric provenance;
2. whether each scale is externally process-calibrated or analyst-choice structural;
3. structural target fractions or external distance values;
4. secondary environmental/barrier axes and their construction rules;
5. whether primary-only worlds are retained;
6. forecast horizon and its interpretation;
7. structural adequacy declaration;
8. resulting world IDs, thresholds, fingerprints and structural audit;
9. plausible process/scale alternatives outside the certificate;
10. the rule that a failed structural gate stops the study before response access.

## STOC lesson, not rescue

The frozen STOC nearest-neighbour q90 geography world used `18.110714907817556 km` yet had 231 weak components, 101 isolated sites and a largest component of only 87/1003 sites (8.67%). Across species, 8,702 positive calibration targets were disconnected from all fixed anchors, versus only 48 targets that were connected but required more than the frozen eight-hop horizon.

Therefore the dominant failure was graph-scale fragmentation rather than horizon length.

No threshold produced by the new ladder is permitted to replace the frozen STOC world universe for confirmatory interpretation. STOC remains `independent_world_universe_falsified_on_calibration`.

## Stop boundary

Do not:

- select structural target fractions after viewing species outcomes;
- call structurally derived thresholds biological dispersal limits;
- delete fragmented worlds merely because they are inconvenient;
- require every world to pass a spanning criterion when fragmentation is a declared hypothesis;
- reopen a failed independent dataset with a redesigned ladder and call it independent confirmation.

The purpose of this layer is to make the **next** independent EOG-WF test structurally eligible before its ecological response is opened.
