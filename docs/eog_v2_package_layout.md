# EOG v2 package layout

## Status

`eog.v2` is a **prospective operator namespace**, not a second independent EOG identity. The active integrated scientific direction is defined in [`development_mainline.md`](development_mainline.md).

This layout does not alter, rerun, rescue or reinterpret frozen v0.1/v2 results, contracts or fingerprints.

## Public boundary

The repository keeps the frozen v0.1 compatibility API under root `eog`. Prospective implementation already developed for v2 is grouped behind three explicit facades:

- `eog.v2.reachability` — transition operators, first passage, flux, state layers, graph diagnostics, and exact finite-world reconstruction built from those operators;
- `eog.v2.traversability` — geographic/environmental transition constraints, transit viability and occurrence-conditioned rule compatibility;
- `eog.v2.validation` — independent occurrence, genetic and directional-evidence validation;
- `eog.v2.cli` — console-script routing only.

The historical convenience surface `from eog.v2 import ...` remains available for frozen workflows and external callers, but it is a **lazy compatibility facade**. Importing `eog.v2` alone does not eagerly import the reachability, traversability and validation implementation trees.

New prospective code should import from the explicit facade that owns its estimand.

## Active architectural role

The three facades are operators within the current integrated mainline:

- **reachability** supplies forward transition/flow operators and the finite inverse layer `observed occurrences -> compatible declared worlds`;
- **traversability** supplies IBD/IBE/barrier/pathwise ecological constraints used to construct or reject transitions;
- **validation** tests whether occurrence, genetic or directional evidence supports, rejects or fails to identify a declared rule/world.

The finite-world implementation lives internally in `eog.v2.world_reconstruction` but is exposed only through `eog.v2.reachability`. This is deliberate: world reconstruction is composition over existing transition and occurrence operators, not a fourth EOG subdiscipline.

Do not create another top-level package for watershed, probability-set or reconstructability ideas unless the finite core demonstrates a genuinely separate reusable estimand.

## Finite-world public surface

The public reconstruction surface is intentionally narrow:

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

Row-level helper dataclasses and status aliases remain implementation details instead of being promoted into the compatibility facade.

## Console scripts

Commands whose public name begins with `eog-v2-` continue to route through `eog.v2.cli`:

- `eog-v2-genetic-validate`;
- `eog-v2-occurrence-freeze`;
- `eog-v2-occurrence-validate`.

The CLI facade delegates to existing implementations. This is a package-maintenance boundary, not a change in scientific estimands.

## Compatibility boundary

Existing implementation modules remain in place because frozen workflows and reproduction paths may import them directly. Consolidation therefore proceeds in this order:

1. narrow/document the public facades;
2. remove eager/package-root coupling;
3. reuse existing first-passage and occurrence-compatibility logic rather than duplicating it in the world layer;
4. search all frozen reproduction paths before any physical module move/delete;
5. preserve compatibility aliases where needed;
6. allow package CI to prove that cleanup did not alter scientific code paths.

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

## Scientific boundary

Package layout is an implementation-maintenance concern. Reorganization must not be used to obtain a more favourable empirical result or to conceal a negative/indeterminate validation outcome.
