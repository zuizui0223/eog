# EOG v2 package layout

## Status

`eog.v2` is a **prospective operator namespace**, not a second independent EOG identity. The active integrated scientific direction is defined in [`development_mainline.md`](development_mainline.md).

This layout change does not alter, rerun, rescue or reinterpret frozen v0.1/v2 results, contracts or fingerprints.

## Public boundary

The repository keeps the frozen v0.1 compatibility API under root `eog`. Prospective implementation already developed for v2 is grouped behind three explicit facades:

- `eog.v2.reachability` — transition operators, first passage, flux, state layers and graph diagnostics;
- `eog.v2.traversability` — geographic/environmental transition constraints, transit viability and occurrence-conditioned rule compatibility;
- `eog.v2.validation` — independent occurrence, genetic and directional-evidence validation;
- `eog.v2.cli` — console-script routing only.

The historical convenience surface `from eog.v2 import ...` remains available for frozen workflows and external callers, but it is now a **lazy compatibility facade**. Importing `eog.v2` alone no longer eagerly imports the reachability, traversability and validation implementation trees.

New prospective code should import from the explicit facade that owns its estimand.

## Active architectural role

The three facades are operators within the current integrated mainline:

- **reachability** supplies forward transition/flow operators for candidate worlds;
- **traversability** supplies IBD/IBE/barrier/pathwise ecological constraints used to construct or reject transitions;
- **validation** tests whether occurrence, genetic or directional evidence supports, rejects or fails to identify a declared rule/world.

Do not create another top-level package for watershed, probability-set or world-reconstruction ideas until the minimal finite-world engine demonstrates that a genuinely new reusable abstraction is required.

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
3. search all frozen reproduction paths before any physical module move/delete;
4. preserve compatibility aliases where needed;
5. allow package CI to prove that the cleanup did not alter scientific code paths.

A later major-version migration may relocate internals only when release notes, compatibility aliases and frozen reproduction paths are handled explicitly.

## Development rules

1. Reuse an existing facade before creating a new namespace.
2. Keep system-specific A-Islands/Tanzania/Finland/Ryukyu/Zhoushan logic out of generic API names.
3. Keep IBD/geographic and IBE/environmental quantities separately inspectable.
4. Do not promote an uncalibrated reachability support into probability/process terminology by package reorganization.
5. Package-wide regression belongs to Package checks; estimand-specific workflows should remain narrowly scoped.
6. Presentation/manuscript code must not become a dependency of core operators.
7. A cleanup PR must not change frozen benchmark inputs, results, seeds, fingerprints, promotion gates or claim directions.

## Scientific boundary

Package layout is an implementation-maintenance concern. Reorganization must not be used to obtain a more favourable empirical result or to conceal a negative/indeterminate validation outcome.
