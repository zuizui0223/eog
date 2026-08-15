# EOG development mainline

## Status

This document defines the active scientific and repository-development direction after the 2026-08 cleanup. It does **not** alter, rerun, rescue or reinterpret any frozen v0.1 result, empirical benchmark, manuscript fingerprint or prospective validation outcome recorded elsewhere.

Detailed implementation status belongs in [`eog_v2_progress.md`](eog_v2_progress.md). Frozen claims and negative results belong in their evidence ledgers/contracts. This file exists to keep **one scientific mainline** and prevent a new narrative/module family from appearing for every idea.

## Scientific center

EOG starts from one distinction:

> **Local possibility is not the same object as distributional realizability.**

Observed occurrences are realized outcomes that constrain distribution-forming processes, but they do not identify one true migration route, colonisation history, ancestry or movement rate.

The active EOG question is:

> **What declared ecological and analytical worlds could have produced the observed distribution, what minimum constraints must those worlds relax, and which reachability statements survive disagreement among them?**

EOG is therefore not defined by adding movement covariates to an SDM, by using graphs, or by making a 3D visualization. Local suitability/support may be a node property; the prospective EOG object is the **set of admissible state relations and distribution-forming worlds consistent with the observations**.

## Core inferential objects

### Compatible world set

For observations `O` and a declared admissible universe `W`, the inverse object is

`W(O) = { w in W : w is compatible with O }`.

If several worlds remain compatible, underidentification is an explicit result. Do not manufacture one historical answer.

### World-indexed flow set

For every compatible world retain its own flow/support trajectory:

`K_t = { p_t^(w) : w in W(O) }`.

Lower/upper envelopes are useful summaries but must not erase world identity. Uncalibrated transition support is not called a colonisation, dispersal, migration or occupancy probability.

### Robust / contingent / excluded structure

Across the declared certified universe, distinguish:

1. reachable/supported in all worlds;
2. contingent on world/representation choice;
3. unreachable/inactive in every enumerated world.

`robust` always means **robust under the declared certified universe**, not universal truth in nature.

Adding admissible worlds must make strong claims more conservative:

- robust sets may stay the same or shrink;
- possible sets may stay the same or expand;
- all-world exclusion may stay the same or shrink.

### Minimum required relaxation

For observations that cannot be realized under stricter worlds, ask what declared assumptions must be relaxed.

Keep at least these axes separately inspectable:

- geographic / IBD-like relaxation;
- environmental / IBE-like relaxation;
- barrier relaxation.

Return non-dominated alternatives as a Pareto set. Do not collapse them into a weighted scalar unless a genuinely one-dimensional monotone family was predeclared for a specific scientific reason.

Time-stamped positive observations may eliminate worlds that reach an endpoint too late and can therefore change the minimum-relaxation frontier.

## Distributional-watershed interpretation

The watershed language is structural, not decorative:

- occurrence = realized anchor;
- basin = reachable set under declared constraints;
- channel / tributary = supported transition sequence or edge family;
- confluence = route reconvergence;
- bottleneck = critical transition/state;
- divide = disconnected reachability boundary;
- water level `lambda` = only a predeclared monotone one-dimensional relaxation coordinate;
- basin merge = first declared relaxation level that jointly realizes previously separated occurrence groups.

A basin merge or Pareto-minimal rescue is a **necessary-condition diagnostic**, not evidence that the corresponding historical event actually occurred.

## Mosaic to landscape

Local viability/support `V_i` remains useful. The active representation is conceptually:

`distributional landscape = local node states + relations/transitions among states`.

Many existing methods already model dispersal, landscape configuration, least-cost paths, connectivity, dynamic occupancy and mechanistic range change. EOG must not claim novelty for those ingredients alone. The distinctive target is the **inverse, set-valued, occurrence-conditioned constraint/reconstruction problem**.

## Repository architecture

### Stable/frozen compatibility layer

Root `eog` remains the v0.1 compatibility surface for environmental geometry, shared-reference comparison, support topology, bridge inference and survey tooling. Frozen reproduction paths remain valid.

### Prospective operator layer

`eog.v2` remains a thin compatibility namespace. New work stays behind three explicit lazy facades:

- `eog.v2.reachability` — static/temporal transition flow, compatible-world reconstruction, relaxation/frontier diagnostics, survey discrimination and transition-landscape summaries;
- `eog.v2.traversability` — geographic/environmental/barrier/pathwise transition constraints;
- `eog.v2.validation` — independent occurrence, genetic and directional-evidence validation.

Do not create a fourth top-level scientific facade merely because a new conceptual phrase appears.

### Empirical/system-specific layer

A-Islands, Tanzania, Finland, Ryukyu, Zhoushan and similar code are validation/adapters, not the general API.

### Manuscript layer

`manuscript/` preserves the earlier structural-reachability empirical/submission line. It is publication provenance and evidence, not the current package architecture. See [`../manuscript/README.md`](../manuscript/README.md).

## Completed finite architecture

The finite known-truth program already covers:

- static and temporal compatible-world reconstruction;
- world-indexed flow/support sets;
- robust / contingent / finite-universe excluded node and edge structure;
- separate IBD/IBE/barrier minimum-relaxation frontiers;
- first-possible versus first-robust basin merge;
- positive occurrence and positive `(node,time)` discrimination;
- temporal corridor opening/closure;
- exact nested-world-universe monotonicity;
- temporal minimum-relaxation frontiers;
- archetype falsification covering IBD, IBE, hard barriers, niche deserts, stepping stones, rare low-support jumps, branching/reconvergence and analytical ambiguity.

This list is a capability boundary, **not an empirical superiority claim**.

## Current phase — comparator / validation, not feature growth

The next question is no longer “what operator is missing?” It is:

> **Does the inverse, set-valued, occurrence-conditioned EOG estimand add information that simpler or established methods do not already provide for the same scientific question?**

The validation order is deliberately conservative.

### Gate 1 — simple estimand separation

Passed by `benchmarks/inverse_estimand_comparator.py`:

- endpoint-only identity cannot distinguish `C@t2` from `C@t3`;
- final-horizon reachability retains slow and fast explanations together;
- scalarizing geographic/environmental/barrier relaxation loses axis identity;
- EOG retains the non-dominated explanation set and timing constraint without selecting one history.

This is **not** external-method superiority.

### Gate 2 — existing strong internal connectivity baseline

Current comparison: reuse the existing v0.1 bridge operator rather than weaken the baseline.

A time-aggregated A-B-C graph can have a correct cumulative/minimax bridge even when the temporal ordering of A→B and B→C makes one declared world unable to satisfy `C@t2`.

The intended result is not “bridge is wrong”; it is that **static connectivity and time-constrained realizability are different estimands**.

### Gate 3 — external established methods

Only after the first two gates remain coherent, freeze exact comparison contracts for methods such as:

- least-cost / circuit-style connectivity;
- functional or accessible habitat;
- dynamic connectivity;
- dynamic occupancy or mechanistic range models when repeated temporal data support their process estimands;
- single-model / consensus ensembles that collapse analytical world uncertainty.

Compare estimands and failure modes before comparing predictive scores. EOG does not need to win every metric.

## Cleanup rules

1. Preserve scientific evidence before removing implementation.
2. Do not retune adverse/null/indeterminate results.
3. Reuse an existing facade/operator before adding a module family.
4. Keep new workflows narrowly dependency-scoped; Package checks own package-wide regression.
5. Keep presentation/manuscript code out of eager scientific-core imports.
6. New prospective names stay off root compatibility namespaces unless compatibility requires them.
7. Physically remove or move legacy code only after repository search shows no frozen reproduction path depends on it.
8. A stale branch must not be merged wholesale across later scientific changes; salvage only still-valid changes onto current main.
9. Claim strength must never exceed the explicit coverage/certificate strength.

## Deferred until a concrete validation need exists

- surveyed absence / non-detection inference — requires an explicit detection model;
- calibrated calendar time / transition duration — only if duration is itself an estimand;
- unobserved historical sources — requires a declared latent-source contract;
- continuous/enormous world spaces — require explicit search/coverage/certification rather than finite enumeration;
- large-raster forecasting — only after a specific forecast question and comparator are frozen;
- new empirical promotion claims — only after endpoint, comparator and validation contracts are predeclared.

## Stop rule

Do not add another operator merely to complete the conceptual picture. Do not open another occurrence/genetic dataset merely to obtain a favourable result. Preserve genuinely different worlds as a set whenever the observations do not identify one history.
