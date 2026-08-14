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

World reconstructability asks how tightly `O` constrains this set. A new occurrence, temporal occurrence, surveyed absence under an explicit detection model, movement observation or independent genetic datum can reduce `W(O)`; a useful survey target is therefore one expected to discriminate among still-compatible worlds.

## Distributional-watershed interpretation

The watershed language is a structural analogy that should be implemented only where its terms have declared mathematical meanings.

- **occurrence** — a realized state / anchor;
- **basin** — a set reachable from an anchor under declared constraints;
- **channel / tributary** — a supported transition sequence;
- **confluence** — route reconvergence;
- **bottleneck** — a transition or state whose removal/constraint sharply reduces reachability;
- **divide** — a boundary between otherwise disconnected reachable basins;
- **water level `lambda`** — a predeclared one-dimensional monotone relaxation coordinate; it must not be manufactured by weighting unrelated ecological axes after seeing outcomes;
- **basin merge** — the first declared relaxation level at which previously separated occurrence groups become jointly realizable.

The minimum merge level between occurrence groups is a minimum-required-relaxation diagnostic. It is not evidence that the corresponding historical event actually occurred. When several analytical representations are declared at every level, keep separate the first level where merge is possible in at least one representation from the first level where it is supported across all declared representations.

## IBD and IBE remain separate axes

Geographic isolation and environmental isolation must not be collapsed prematurely into one weighted distance.

- `D_geo` represents the geographic / IBD axis.
- `D_env` represents the environmental / IBE axis.

A long geographic jump and a large environmental transition are different ecological explanations. EOG should preserve that distinction through transition construction, rescue analysis and validation.

A scalar `lambda` is therefore valid only when a one-dimensional family has already been declared. It is not a license to estimate weights that combine `D_geo`, `D_env` and barrier terms into one post-hoc score.

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

- `eog.v2.reachability` — transition propagation, first passage, flux, graph diagnostics, finite-world reconstruction, declared finite-family basin merge, finite time-varying world-flow sets and positive temporal-world reconstruction;
- `eog.v2.traversability` — geographic/environmental transition constraints and pathwise ecological continuity;
- `eog.v2.validation` — independent occurrence/genetic/evidence validation.

New prospective names should prefer the explicit owning facade. Do not keep widening the `eog.v2` package root merely for convenience.

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
9. A new prospective API does not automatically belong on the compatibility package root.

## Finite-core checkpoints

The exact finite-world core, declared relaxation-family basin merge and finite archetype matrix are implemented and pass known-truth tests. The finite core can:

- reconstruct the exact compatible world set from positive occurrences;
- preserve world-indexed support-flow distributions rather than averaging worlds;
- classify reachable-in-all / contingent / robustly-unreachable states over an exhaustively enumerated finite universe;
- keep geographic/IBD, environmental/IBE and barrier relaxation axes separate;
- retain non-dominated alternative explanations;
- quantify compatible-world contraction after new positive observations;
- distinguish first-possible from first-robust basin merge under declared analytical variants;
- preserve rare low-support possibilities, branching/reconvergence and robust exclusions under declared universe expansion.

These are known-truth structural capabilities, not empirical superiority claims.

## Finite temporal-flow checkpoint

A `TemporalWorld` is an ordered sequence of already-declared `DynamicTransitionOperator` objects over a fixed node/source universe. Source mass is injected only at the initial state and each interval-specific operator is applied once in declared order.

`build_temporal_flow_set` retains one exact-time support trajectory per declared temporal world and reports exact-time support envelopes plus cumulative reached-by-time structure. It distinguishes `reachable_in_all`, `contingent` and `robustly_unreachable` states at each declared time and retains first-arrival/loss diagnostics by world.

Known-truth tests confirm temporal-order dependence, temporary bridge opening, no source reinjection, exact-time versus reached-by-time separation, robust reachability across support magnitudes and hard temporal barriers.

Time labels are ordered state labels only. They are not calibrated calendar time, generation length or demographic persistence.

## Positive temporal-world reconstruction checkpoint

Time-stamped **positive** occurrences now constrain the finite temporal-world set through `reconstruct_temporal_worlds`.

An observation `(node, time)` is treated only as the necessary condition that the node must have been reached **by** that declared time. It is not treated as an exact-time occupancy likelihood or persistence model. Non-detection remains non-evidence.

The temporal inverse layer:

- retains multiple temporal histories when they all satisfy the declared positive observations;
- eliminates worlds that reach an observed endpoint too late;
- reports unsupported positive observations per world;
- quantifies compatible temporal-world contraction after additional positive temporal evidence;
- canonicalizes observation order for deterministic fingerprints;
- preserves very low positive support above the declared tolerance;
- does not penalize a world merely because an unobserved node is also reachable.

The finite certificate is `exhaustive_declared_temporal_world_set_positive_observations`; it applies only to the declared temporal world universe.

## Current boundary and next gate

Still outside the integrated core:

- surveyed-absence likelihoods and detection models;
- calibrated calendar time or externally justified transition durations;
- unobserved/hypothetical historical source states;
- continuous or enormous world spaces requiring optimization/sampling/certification rather than exact enumeration;
- large-raster forecasting;
- empirical promotion claims.

Before opening absence/detection or empirical forecasting, the next finite gate is **positive temporal survey discrimination**: rank candidate `(node, time)` positive observations by how strongly they split the still-compatible temporal worlds. This should reuse the temporal reconstruction layer, preserve positive-only semantics, and add no new transition implementation, top-level namespace, CLI or workflow family.
