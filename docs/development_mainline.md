# EOG development mainline

## Status

This document defines the active scientific and repository-development direction after the 2026-08 cleanup. It does **not** alter, rerun, rescue, or reinterpret any frozen v0.1 result, empirical benchmark, manuscript fingerprint, or prospective validation outcome already recorded elsewhere in the repository.

The purpose of this document is to stop further proliferation of parallel EOG stories and to give existing modules one coherent role.

## Scientific center

EOG starts from a distinction that must remain explicit:

> **Local possibility is not the same object as distributional realizability.**

Observed occurrences are treated as realized states of an unknown distribution-forming process. They constrain the ecological worlds that could have produced the observed configuration, but they do not identify a unique historical route.

The active EOG question is therefore:

> **What ecological worlds could have made the observed distribution possible, how tightly can those worlds be reconstructed from the observations, and which distributional flows remain possible or impossible across them?**

This is not equivalent to adding a movement covariate to an SDM. Local environmental support remains useful, but it becomes one node property inside a relational and dynamic distributional landscape.

## Three integrated layers

### 1. Distributional realizability

For an observed occurrence configuration `O`, determine which declared geographic, environmental, barrier, movement and temporal assumptions are compatible with a distribution-forming process that can realize `O`.

Do not infer a unique history when several histories remain compatible.

### 2. Probability-set dynamics

For each admissible world `w`, define an auditable transition operator over ecological states and propagate branching probability/support flow through it.

The primary uncertainty object is not one averaged probability surface. It is the set

`K_t = { p_t^(w) : w in W(O) }`,

where `W(O)` is the set of worlds compatible with the observations.

Retain the association between a world and the distribution it generates. Lower/upper envelopes may be reported, but they must not erase which assumptions produced them.

### 3. World reconstructability

Treat the forward mapping schematically as `F(w) -> O`. The inverse object is

`W(O) = { w : F(w) is compatible with O }`.

World reconstructability asks how tightly `O` constrains this set. A new occurrence, surveyed absence, temporal observation, movement observation or independent genetic datum can reduce `W(O)`; a useful survey target is therefore one expected to discriminate among still-compatible worlds.

## Distributional-watershed interpretation

The watershed language is a structural analogy that should be implemented only where its terms have declared mathematical meanings.

- **occurrence** — a realized state / anchor;
- **basin** — a set reachable from an anchor under declared constraints;
- **channel / tributary** — a supported transition sequence;
- **confluence** — route reconvergence;
- **bottleneck** — a transition or state whose removal/constraint sharply reduces reachability;
- **divide** — a boundary between otherwise disconnected reachable basins;
- **water level `lambda`** — declared relaxation of ecological, geographic, barrier, temporal or analytical constraints;
- **basin merge** — the first relaxation level at which previously disconnected occurrence basins become jointly realizable.

The minimum merge level between occurrence groups is a minimum-required-relaxation diagnostic. It is not evidence that the corresponding historical event actually occurred.

## IBD and IBE remain separate axes

Geographic isolation and environmental isolation must not be collapsed prematurely into one weighted distance.

- `D_geo` represents the geographic / IBD axis.
- `D_env` represents the environmental / IBE axis.

A long geographic jump and a large environmental transition are different ecological explanations. EOG should preserve that distinction through transition construction, rescue analysis and validation.

## Mosaic to landscape

Local viability/support `V_i` is retained rather than discarded. The active representation is conceptually

`distributional landscape = local node states + relations/transitions among states`.

Thus a raster or SDM may supply local support, but EOG's main object is the configuration and flow of relationships among states, not another flat local-support surface.

## Robust impossibility

Natural uncertainty and analyst-choice uncertainty are both declared explicitly. Let the admissible universe include, for example, alternative dispersal assumptions, environmental tolerances, barriers, raster products, resolutions, thresholds and preprocessing choices.

A transition or state can be called robustly unreachable only when it is unreachable in **every** declared admissible world. Failure to find a route in a finite search is not automatically a universal exclusion.

Keep these outcomes distinct:

1. high-support / probable under a world;
2. possible but low-support;
3. contingent or unresolved across worlds;
4. robustly unreachable under the declared universe.

Claim strength must never exceed coverage/certificate strength.

## Repository roles

Existing implementation is retained, but its role is narrowed.

### Frozen/stable evidence layer

Do not delete or retune:

- frozen benchmark inputs and results;
- fingerprints and manifests;
- evidence ledgers and claim matrices;
- adverse, null, failed and indeterminate validation results;
- frozen manuscript evidence required to reproduce earlier conclusions.

### Stable v0.1 operator layer

The root `eog` API remains the compatibility surface for environmental geometry, shared-reference comparison, support topology, bridge inference and survey tooling. It is not the location for new prospective scientific subfields.

### Prospective operator layer

`eog.v2` remains a compatibility namespace for the already implemented reachability, traversability and validation facades. These modules become operators supporting the integrated mainline rather than separate competing scientific stories.

- `eog.v2.reachability` — transition propagation, first passage, flux, graph diagnostics and finite-world reconstruction;
- `eog.v2.traversability` — geographic/environmental transition constraints and pathwise ecological continuity;
- `eog.v2.validation` — independent occurrence/genetic/evidence validation.

Do not add another top-level namespace for each new ecological idea.

### System-specific adapters and experiments

A-Islands, Tanzania, Finland, Ryukyu, Zhoushan and other system-specific code/results are empirical or validation adapters. They are not the general EOG API and must not drive generic names or estimands unless the result has been independently promoted.

### Manuscript/presentation layer

Submission bundles, figures and journal-specific material preserve publication provenance. They must not define the active package architecture.

## Cleanup rules

1. Preserve scientific evidence before removing implementation.
2. Prefer a facade or adapter over another top-level module.
3. Do not duplicate path, bottleneck, reachability or validation logic for a new narrative.
4. New workflows must have narrow path scopes; package-wide regression belongs to the package test workflow.
5. Generated/presentation code must not become a dependency of core scientific modules.
6. Compatibility imports may remain while public documentation stops promoting obsolete surfaces.
7. Physical deletion of legacy modules is allowed only after repository search shows no frozen reproduction path depends on them and package CI remains green.
8. A historical negative result is evidence, not dead code to be erased.

## Minimal next implementation

Do not begin with a new SPDE, PDE, ABM or deep graph model. First prove the integrated architecture on a small finite graph with exact enumeration of a finite world set:

1. forward `world -> transition operator -> occurrence-compatible reachability envelope`;
2. inverse `occurrence configuration -> compatible world set`;
3. probability/support-distribution set retained by world;
4. basin merge / minimum-relaxation diagnostic;
5. separate IBD and IBE constraints;
6. reconstructability diagnostic;
7. robust-impossibility classification;
8. observation/survey discrimination among compatible worlds.

The first success condition is deliberately conservative:

> **When multiple genuinely different worlds produce the same observed distribution, EOG must preserve them as a set instead of manufacturing one historical answer.**

Only after this finite, falsifiable core is stable should time-dependent large-raster forecasting be expanded.

## Finite-core implementation checkpoint — 2026-08-14

The first exact-enumeration implementation is now being developed behind the existing `eog.v2.reachability` facade. It composes existing first-passage and occurrence-compatibility operators instead of duplicating them.

Implemented in the finite core:

- a `FiniteWorld` declaration containing a frozen transition operator, observed fixed sources and separately declared geographic/environmental/barrier relaxation axes;
- a positive-support forward reachability envelope for each world;
- exhaustive inverse enumeration of `W(O)` with explicit compatible and incompatible world IDs;
- an `identifiable` flag that is true only when exactly one declared world remains compatible;
- world-indexed propagation results and lower/upper envelopes without averaging away world identity;
- exact finite-universe node classes: `reachable_in_all`, `contingent`, and `robustly_unreachable`;
- a non-dominated relaxation frontier that preserves geographic/IBD, environmental/IBE and barrier axes rather than inventing one weighted water level;
- reconstructability contraction after adding a new positive occurrence;
- positive-occurrence candidate ranking by how strongly an observation would split the still-compatible world set.

The finite-universe certificate is deliberately narrow: `robustly_unreachable` means unreachable in every **enumerated compatible world**, not impossible in nature.

Still outside this first core:

- unobserved/hypothetical historical source states;
- surveyed-absence likelihoods and detection models;
- temporal observations and calibrated calendar time;
- scalar basin-merge water levels unless a one-dimensional relaxation family is declared in advance;
- continuous or enormous world spaces requiring optimization/sampling/certification rather than exact enumeration;
- empirical promotion claims.

These omissions are current boundaries, not invitations to add complexity before the finite known-truth tests pass.
