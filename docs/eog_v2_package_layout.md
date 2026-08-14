# EOG v2 package layout

## Status

`eog.v2` is a **prospective operator namespace**, not a second independent EOG identity. The active integrated scientific direction is defined in [`development_mainline.md`](development_mainline.md).

This layout does not alter, rerun, rescue or reinterpret frozen v0.1/v2 results, contracts or fingerprints.

## Public boundary

The repository keeps the frozen v0.1 compatibility API under root `eog`. Prospective implementation already developed for v2 is grouped behind three explicit facades:

- `eog.v2.reachability` — transition operators, first passage, flux, state layers, graph diagnostics, exact finite-world reconstruction, and declared monotone basin-merge diagnostics;
- `eog.v2.traversability` — geographic/environmental transition constraints, transit viability and occurrence-conditioned rule compatibility;
- `eog.v2.validation` — independent occurrence, genetic and directional-evidence validation;
- `eog.v2.cli` — console-script routing only.

The historical convenience surface `from eog.v2 import ...` remains available for already-published compatibility names, but it is a **lazy compatibility facade**. Importing `eog.v2` alone does not eagerly import the reachability, traversability and validation implementation trees.

New prospective names should stay on the explicit owning facade instead of automatically widening the `eog.v2` package root. The basin-merge API follows this stricter rule and is available from `eog.v2.reachability`, not from `eog.v2` directly.

## Active architectural role

The three facades are operators within the current integrated mainline:

- **reachability** supplies forward transition/flow operators, the finite inverse layer `observed occurrences -> compatible declared worlds`, and finite-family joint-realization diagnostics;
- **traversability** supplies IBD/IBE/barrier/pathwise ecological constraints used to construct or reject transitions;
- **validation** tests whether occurrence, genetic or directional evidence supports, rejects or fails to identify a declared rule/world.

Finite-world implementation lives internally in `eog.v2.world_reconstruction`; explicitly one-dimensional relaxation-family logic lives in `eog.v2.relaxation_family`. Both are exposed only through `eog.v2.reachability`. They are compositions over existing transition/occurrence operators, not additional public EOG subdisciplines.

Do not create another top-level package for watershed, probability-set or reconstructability ideas unless the finite core demonstrates a genuinely separate reusable estimand.

## Finite-world public surface

The reconstruction surface is intentionally narrow:

- `FiniteWorld`;
- `FiniteWorldReconstruction`;
- `FiniteWorldFlowSet`;
- `RelaxationFrontier`;
- `ReconstructionUpdate`;
- `PositiveOccurrenceSurveyRanking`;
- `forward_reachable_configuration`;
- `reconstruct_compatible_worlds`;
- `build_world_flow_set`;
- `minimum_relaxation_frontier`;
- `compare_reconstructions`;
- `rank_positive_occurrence_candidates`.

The declared one-dimensional basin-merge surface adds only:

- `MonotoneRelaxationFamily`;
- `BasinMergeResult`;
- `build_monotone_relaxation_family`;
- `infer_basin_merge`.

Row-level helper dataclasses and status aliases remain implementation details instead of being promoted into compatibility facades.

## Why basin merge requires a declared family

EOG must not manufacture a scalar water level by assigning arbitrary weights to geographic/IBD, environmental/IBE and barrier axes. `build_monotone_relaxation_family` therefore accepts an explicit level-by-analytical-variant grid and requires:

- the same analytical variants at every level;
- fixed node and source contracts within each variant;
- fixed loss support;
- elementwise non-decreasing raw transition support;
- non-decreasing declared geographic, environmental and barrier relaxation coordinates.

`infer_basin_merge` then distinguishes:

- the first level where **at least one** declared analytical variant jointly realizes all occurrence groups (`first_possible_level`);
- the first level where **all** declared analytical variants do so (`first_robust_level`).

Both are finite-family structural diagnostics, not historical event estimates or biological time.

## Console scripts

Commands whose public name begins with `eog-v2-` continue to route through `eog.v2.cli`:

- `eog-v2-genetic-validate`;
- `eog-v2-occurrence-freeze`;
- `eog-v2-occurrence-validate`.

No basin-merge CLI is added at this stage. The finite API should stabilize before another command surface is justified.

## Compatibility boundary

Existing implementation modules remain in place because frozen workflows and reproduction paths may import them directly. Consolidation therefore proceeds in this order:

1. narrow/document the public facades;
2. remove eager/package-root coupling;
3. reuse existing first-passage and occurrence-compatibility logic rather than duplicating it in the world layer;
4. keep new prospective names off the compatibility package root unless compatibility requires them;
5. search all frozen reproduction paths before any physical module move/delete;
6. preserve compatibility aliases where needed;
7. allow package CI to prove that cleanup did not alter scientific code paths.

A later major-version migration may relocate internals only when release notes, compatibility aliases and frozen reproduction paths are handled explicitly.

## Development rules

1. Reuse an existing facade before creating a new namespace.
2. Keep system-specific A-Islands/Tanzania/Finland/Ryukyu/Zhoushan logic out of generic API names.
3. Keep IBD/geographic and IBE/environmental quantities separately inspectable.
4. Do not promote an uncalibrated reachability support into probability/process terminology by package reorganization.
5. Package-wide regression belongs to Package checks; estimand-specific workflows should remain narrowly scoped.
6. Presentation/manuscript code must not become a dependency of core operators.
7. A cleanup PR must not change frozen benchmark inputs, results, seeds, fingerprints, promotion gates or claim directions.
8. Exact finite-universe exclusion must remain labelled as finite-universe coverage, not universal ecological impossibility.
9. A scalar relaxation level is valid only inside a predeclared monotone one-dimensional family; otherwise retain the separate relaxation frontier.

## Scientific boundary

Package layout is an implementation-maintenance concern. Reorganization must not be used to obtain a more favourable empirical result or to conceal a negative/indeterminate validation outcome.
