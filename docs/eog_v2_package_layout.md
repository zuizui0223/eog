# EOG v2 package layout

## Status

`eog.v2` is a **prospective operator namespace**, not a second independent EOG identity. The active integrated scientific direction is defined in [`development_mainline.md`](development_mainline.md).

This layout does not alter, rerun, rescue or reinterpret frozen v0.1/v2 results, contracts or fingerprints.

## Public boundary

The repository keeps the frozen v0.1 compatibility API under root `eog`. Prospective implementation already developed for v2 is grouped behind three explicit facades:

- `eog.v2.reachability` — transition operators, finite/static and temporal world reconstruction, probability/support-set summaries, basin-merge diagnostics and transition-landscape summaries;
- `eog.v2.traversability` — geographic/environmental transition constraints, transit viability and occurrence-conditioned rule compatibility;
- `eog.v2.validation` — independent occurrence, genetic and directional-evidence validation;
- `eog.v2.cli` — console-script routing only.

The historical convenience surface `from eog.v2 import ...` remains available for already-published compatibility names, but it is a **lazy compatibility facade**. Importing `eog.v2` alone does not eagerly import the reachability, traversability and validation implementation trees.

New prospective names stay on the explicit owning facade instead of automatically widening the `eog.v2` package root.

## Reachability facade is also lazy

`eog.v2.reachability` is now itself a lazy facade. Importing it does not automatically load:

- HTML/report rendering;
- visualization payload builders;
- synthetic archipelago fixtures;
- static finite-world reconstruction internals;
- temporal reconstruction/survey/transition-landscape internals;
- system-specific state-layer helpers.

A public symbol loads only its owning implementation module when accessed. This keeps presentation and synthetic/system-specific code from becoming an eager dependency of the active scientific core while preserving the existing reachability public names.

## Active architectural role

The three facades are operators within the current integrated mainline:

- **reachability** supplies forward transition/flow operators, static and temporal compatible-world reconstruction, finite-world support sets, declared relaxation families and dynamic transition-landscape summaries;
- **traversability** supplies IBD/IBE/barrier/pathwise ecological constraints used to construct or reject transitions;
- **validation** tests whether occurrence, genetic or directional evidence supports, rejects or fails to identify a declared rule/world.

Finite-world, relaxation-family and temporal implementations remain internal modules exposed through `eog.v2.reachability`. They are components of one reachability estimand family, not separate public EOG subdisciplines.

Do not create another top-level package for watershed, probability-set, temporal-flow or reconstructability ideas unless the finite core demonstrates a genuinely separate reusable estimand.

## Prospective reachability surface

The explicit reachability facade currently includes:

- finite `FiniteWorld` reconstruction and world-indexed flow sets;
- non-dominated geographic/IBD, environmental/IBE and barrier relaxation frontiers;
- declared one-dimensional monotone basin-merge families;
- `TemporalWorld` flow sets;
- positive temporal-world reconstruction;
- positive temporal survey discrimination;
- finite-world transition-landscape edge classes and opening/closure summaries.

Row-level helper dataclasses and status aliases remain implementation details rather than package-root compatibility names.

## Why basin merge requires a declared family

EOG must not manufacture a scalar water level by assigning arbitrary weights to geographic/IBD, environmental/IBE and barrier axes. A scalar lambda is valid only when the caller predeclares a genuinely one-dimensional monotone relaxation family. Otherwise the separate Pareto-style relaxation frontier remains the appropriate output.

## Console scripts

Commands whose public name begins with `eog-v2-` continue to route through `eog.v2.cli`:

- `eog-v2-genetic-validate`;
- `eog-v2-occurrence-freeze`;
- `eog-v2-occurrence-validate`.

No finite-world, basin-merge or temporal-flow CLI is added at this stage. The scientific APIs should stabilize before another command surface is justified.

## Compatibility boundary

Existing implementation modules remain in place because frozen workflows and reproduction paths may import them directly. Consolidation proceeds in this order:

1. narrow/document public facades;
2. remove eager package-root and facade coupling;
3. reuse first-passage, occurrence-compatibility and transition logic rather than duplicating it;
4. keep new prospective names off the compatibility package root unless compatibility requires them;
5. keep presentation/system-specific code out of eager scientific-core imports;
6. search all frozen reproduction paths before any physical module move/delete;
7. preserve compatibility aliases where needed;
8. let package CI prove that cleanup did not alter scientific code paths.

A later major-version migration may relocate internals only when release notes, compatibility aliases and frozen reproduction paths are handled explicitly.

## Development rules

1. Reuse an existing facade before creating a new namespace.
2. Keep system-specific A-Islands/Tanzania/Finland/Ryukyu/Zhoushan logic out of generic API names.
3. Keep IBD/geographic and IBE/environmental quantities separately inspectable.
4. Do not promote uncalibrated reachability support into dispersal/colonisation/migration probability terminology.
5. Package-wide regression belongs to Package checks; estimand-specific workflows remain narrowly scoped.
6. Presentation/manuscript code must not become an eager dependency of core scientific imports.
7. Cleanup must not change frozen benchmark inputs, results, seeds, fingerprints, promotion gates or claim directions.
8. Exact finite-universe exclusion remains labelled as finite-universe coverage, not universal ecological impossibility.
9. Scalar relaxation levels are valid only inside predeclared monotone one-dimensional families.
10. New temporal summaries describe declared transition structure, not observed historical movement events.

## Scientific boundary

Package layout is an implementation-maintenance concern. Reorganization must not be used to obtain a more favourable empirical result or to conceal a negative/indeterminate validation outcome.
