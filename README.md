# Environmental Occupancy Geometry (EOG)

EOG is an auditable ecological framework for asking a broader question than local suitability alone:

> **Given an observed distribution, what distribution-forming worlds are compatible with it, and which reachability structures remain robust, contingent or excluded across those worlds?**

The repository contains a frozen evidence line plus a prospective finite-world reachability framework. The single active development direction is documented in [`docs/development_mainline.md`](docs/development_mainline.md).

## Core distinction

EOG keeps these objects separate:

1. local environmental viability/support;
2. geometry of observed environmental states;
3. geographic topology of frozen support fields;
4. state-to-state geographic/environmental/barrier transitions;
5. distributional realizability of observed occurrence configurations;
6. reconstructability of the compatible world set.

Observed occurrences are realized constraints, **not proof of one historical route**.

## Distributional-watershed view

The active model is relational and flow-based:

```text
observed occurrences
        ↓
compatible ecological / analytical worlds
        ↓
one transition landscape per world
        ↓
branching / merging reachability flow
        ↓
robust / contingent / excluded structure
        ↓
next positive observation that can discriminate remaining worlds
```

Watershed terminology is used only with explicit structural meanings: occurrence anchors, reachable basins, transition channels, confluences, bottlenecks/divides and predeclared monotone relaxation levels.

Geographic/IBD-like, environmental/IBE-like and explicit barrier constraints remain separate. EOG does not automatically combine them into one weighted distance.

## What is implemented

### Stable root `eog`

The frozen/stable compatibility layer contains:

- environmental-state geometry and shared-reference comparison;
- support topology over frozen 2D support fields;
- bridge/bottleneck operators;
- hypothesis-discriminating survey tooling;
- manifests, fingerprints and audit contracts.

These historical operators remain reproducible and are not silently rewritten to fit the newer world-reconstruction narrative.

### Prospective `eog.v2.reachability`

The explicit reachability facade now provides a finite known-truth framework for:

- exact finite forward reachability;
- positive-occurrence `O -> W(O)` world reconstruction;
- world-indexed flow sets and support envelopes;
- finite-universe `reachable_in_all`, `contingent`, and `robustly_unreachable` classes;
- separate geographic/environmental/barrier relaxation axes and non-dominated frontiers;
- predeclared monotone `lambda` families and first-possible / first-robust basin merge;
- positive static survey discrimination;
- finite time-varying worlds built from ordered transition operators;
- exact-time temporal support and cumulative `reached by time` structure;
- time-stamped positive occurrence reconstruction;
- positive `(node,time)` survey discrimination among compatible temporal worlds.

New prospective names stay on this explicit facade rather than widening `eog.v2` root.

### `eog.v2.traversability`

Provides geographic/IBD, environmental/IBE, barrier and pathwise ecological transition constraints used to construct/test candidate transition worlds.

### `eog.v2.validation`

Keeps independent occurrence, genetic and directional-evidence validation separate from the reachability estimand.

## Positive-only temporal feedback loop

The finite temporal framework currently closes this loop:

```text
declared temporal worlds
  -> temporal flow
  -> positive timed observations
  -> compatible temporal worlds
  -> ranked positive (node,time) discriminator
  -> added positive evidence
  -> contracted world set
```

No non-detection evidence is used. A time-stamped positive occurrence is only a necessary requirement that the node was reachable **by** that declared time; it is not an exact-time occupancy/persistence likelihood.

## Known-truth falsification

The static finite archetype matrix covers:

- IBD-dominated, IBE-dominated and barrier-dominated rescue;
- niche-desert tradeoffs with multiple non-dominated explanations;
- stepping-stone versus direct-route underidentification;
- rare low-support long-distance reachability;
- branching and reconvergence;
- analytical-representation-dependent versus robust basin merge;
- robust exclusion under explicit finite-universe expansion.

Temporal tests additionally cover transition ordering, temporary bridge opening, no source reinjection, timed positive reconstruction and positive timed survey discrimination.

Passing these gates is **structural known-truth validation**, not empirical superiority evidence.

## Scientific boundaries

EOG does not currently justify calling uncalibrated transition/reachability support:

- occupancy probability;
- colonisation/dispersal probability;
- migration rate;
- demographic connectivity;
- ancestry or a historical route.

Keep these rules explicit:

- low positive support is not impossibility;
- multiple compatible worlds remain underidentified;
- non-detection is not absence without a detection model;
- `reached by time` is not persistence;
- time labels are ordered states, not calibrated dates/generations;
- a scalar relaxation level is valid only inside a predeclared monotone family;
- `robustly_unreachable` is relative to the declared/certified finite universe.

## Frozen evidence and manuscript provenance

Positive, adverse, null and indeterminate historical results are retained. They are evidence boundaries, not dead code.

See:

- [`docs/evidence_ledger.md`](docs/evidence_ledger.md)
- [`docs/claim_matrix.md`](docs/claim_matrix.md)
- [`docs/eog_v2_progress.md`](docs/eog_v2_progress.md)
- [`docs/eog_v2_package_layout.md`](docs/eog_v2_package_layout.md)
- [`manuscript/README.md`](manuscript/README.md)

`manuscript/` preserves the earlier structural empirical paper line and does not define the active package architecture.

## Cleanup / development rule

Feature growth is currently paused after closing the positive-only finite temporal loop. The next task is consolidation and an end-to-end temporal feedback falsification benchmark before opening imperfect detection, calibrated time, continuous-world certification, large-raster forecasting or another empirical promotion dataset.

## Installation

```bash
python -m pip install .
```

For raster/CHELSA benchmark utilities:

```bash
python -m pip install ".[raster]"
```

## License

MIT.
