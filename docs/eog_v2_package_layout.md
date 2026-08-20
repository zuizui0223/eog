# EOG v2 package layout

## Status

`eog.v2` is a **prospective operator namespace**, not a second independent EOG identity. The active scientific direction is defined in [`development_mainline.md`](development_mainline.md), while implementation status is tracked in [`eog_v2_progress.md`](eog_v2_progress.md).

This package layout does not alter, rerun, rescue or reinterpret frozen results, contracts or fingerprints.

## Public boundary

Root `eog` remains the frozen v0.1 compatibility API. Prospective work is grouped behind three explicit lazy scientific facades:

- `eog.v2.reachability` — forward transition/flow, static and temporal compatible-world reconstruction, world-indexed support sets, minimum-relaxation/frontier diagnostics, basin merge, positive survey discrimination and temporal transition-landscape summaries;
- `eog.v2.traversability` — geographic/environmental/barrier transition constraints and pathwise ecological continuity;
- `eog.v2.validation` — independent occurrence, genetic and directional-evidence validation;
- `eog.v2.cli` — console-script routing only.

Historical `from eog.v2 import ...` names remain available lazily for compatibility. **New prospective names do not automatically belong on the `eog.v2` package root.**

## All scientific facades are lazy

Plain imports of `eog.v2.reachability`, `traversability`, or `validation` do not eagerly load every owning implementation tree.

This keeps the following out of unrelated imports until requested:

- HTML/report rendering and visualization;
- synthetic/system-specific fixtures;
- finite and temporal reconstruction internals;
- occurrence-rule constraints when only traversability is needed;
- genetic, directional, or empirical occurrence validation families when another validation family is requested.

The purpose is dependency hygiene only. Public scientific meanings are not changed by lazy routing.

## Reachability facade ownership

The current explicit reachability surface includes operators for:

- `FiniteWorld` forward/inverse reconstruction;
- world-indexed support/flow sets with explicit possible, robust, unresolved and
  finite-world robustly-unreachable views;
- static non-dominated geographic/IBD, environmental/IBE and barrier relaxation frontiers;
- declared monotone one-dimensional basin-merge families;
- `TemporalWorld` flow sets;
- positive time-stamped occurrence reconstruction;
- positive `(node,time)` survey discrimination;
- temporal transition edge classes and opening/closure summaries;
- exact nested static compatible-world and temporal-world-universe monotonicity;
- temporal minimum-relaxation frontiers with IBD/IBE/barrier axes preserved.

These implementations remain internal modules routed through `eog.v2.reachability`; they are not separate public EOG subdisciplines.

Benchmark/comparator scripts remain under `benchmarks/` and `tests/`. **A validation benchmark is not a reason to add a public API.**

## Scalar water-level rule

EOG does not manufacture one relaxation score by assigning post-hoc weights to geographic/IBD, environmental/IBE and barrier axes.

A scalar `lambda` is valid only inside a scientifically predeclared one-dimensional monotone family. Otherwise the non-dominated multi-axis frontier is the appropriate output.

## Console scripts

Existing public commands remain routed through `eog.v2.cli`:

- `eog-v2-genetic-validate`;
- `eog-v2-occurrence-freeze`;
- `eog-v2-occurrence-validate`.

No finite-world, temporal-world, basin-merge or relaxation-frontier CLI is added merely for completeness.

## Compatibility / cleanup order

Existing implementation modules remain because frozen workflows and reproduction paths may import them directly. Consolidation follows this order:

1. keep public facades narrow and documented;
2. keep compatibility imports lazy;
3. reuse first-passage, bridge, occurrence-compatibility and transition logic rather than duplicate it;
4. keep presentation/system-specific code out of eager scientific imports;
5. keep independent validation families decoupled until requested;
6. search frozen reproduction paths before physical move/delete;
7. keep new prospective names off root compatibility namespaces unless release compatibility requires them;
8. use Package checks for package-wide regression and narrowly scope claim-specific workflows.

## Development rules

1. Reuse an existing facade/operator before creating a namespace.
2. Keep system-specific A-Islands/Tanzania/Finland/Ryukyu/Zhoushan logic out of generic API names.
3. Keep IBD/geographic and IBE/environmental quantities separately inspectable.
4. Do not rename uncalibrated support as dispersal/colonisation/migration probability.
5. Do not use package reorganization to hide adverse/null/indeterminate evidence.
6. New comparator work belongs in benchmark/test layers unless it exposes a genuinely reusable new estimand.
7. Exact finite-universe `robust`/`excluded` labels must retain their finite-coverage qualification.
8. Temporal summaries describe declared transition structure; they are not historical movement observations.

## Scientific boundary

Package layout is an implementation-maintenance concern. Scientific promotion requires independent comparator/validation evidence; moving symbols between modules cannot create such evidence.
