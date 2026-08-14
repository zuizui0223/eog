# CI scope policy

## Purpose

EOG retains frozen historical benchmarks as reproducible scientific evidence while keeping the active development loop focused and tractable.

The package-level test workflow is responsible for broad implementation regression. Frozen development benchmarks should not all rerun merely because an unrelated package facade, documentation file or module under `src/eog/` changes.

## Frozen legacy benchmark policy

The following v0.1 development/evidence workflows remain in the repository and keep `workflow_dispatch` for explicit reproduction:

- `real-taxon-pilot.yml`
- `robustness-audit.yml`
- `persistent-split.yml`
- `core-local-bridge.yml`
- `real-taxon-mode-audit.yml`
- `multiaxial-archetypes.yml`
- `null-family-comparison.yml`
- `mode-separation-comparators.yml`
- `core-local-bridge-confirmation.yml`
- `calibrated-gap-feature-selection.yml`

Their automatic pull-request triggers are limited to their own benchmark inputs, protocol documents, manifests and workflow definitions. They must not use a blanket `src/eog/**` trigger.

The following older v0.1 contract/reproduction workflows are also dependency-scoped instead of running on every pull request:

- `reference-choice-audit.yml`
- `comparative-uncertainty.yml`
- `competitor-comparison.yml`
- `analysis-manifest.yml`
- `shared-scaling-contract.yml`
- `frozen-comparison-example.yml`
- `audited-runner.yml`

These workflows name their direct geometry/comparative/manifest/runner dependencies explicitly and retain `workflow_dispatch` for intentional reproduction. A prospective `eog.v2`-only change therefore does not need to rerun the frozen v0.1 geometry stack.

This does not deprecate, delete or reinterpret any benchmark. It only prevents unrelated development from repeatedly executing historical exploratory/frozen benchmark suites.

## Prospective operator policy

Prospective workflows should use narrow path filters for the scientific operator or frozen contract they test, for example:

- dynamic reachability;
- ecological traversability;
- occurrence-rule compatibility;
- directional evidence;
- validation-specific code and frozen contracts.

A scientific confirmation workflow should not become a second package-wide test suite.

Changes that only reorganize the compatibility facades (`src/eog/__init__.py` or `src/eog/v2/__init__.py`) belong to Package checks unless they also change the scientific implementation or contract owned by a confirmation workflow. The package suite is responsible for verifying that all preserved public imports still resolve.

Where a confirmation module depends directly on another scientific implementation, that dependency should be named explicitly in the path filter rather than approximated with a broad subtree glob. For example, occurrence-rule and directional-evidence confirmation depend on the dynamic transition operator, while traversability confirmation depends on the ecological-traversability implementation.

The finite-world reconstruction core is currently covered by Package checks and dedicated unit tests. It composes already-tested first-passage and occurrence-compatibility operators and does not receive a separate scientific confirmation workflow until a predeclared frozen confirmation contract exists. This avoids creating a workflow family merely because a new internal module was added.

## Global regression boundary

Broad Python-version compatibility, full unit tests, public compatibility imports and wheel construction remain the responsibility of the existing Package checks workflow. Frozen benchmark workflows remain manually reproducible when an implementation-level historical audit is intentionally requested.

## Scientific boundary

CI scope is operational metadata. Narrowing an automatic trigger must not change:

- benchmark code;
- benchmark inputs or seeds;
- frozen result files;
- result fingerprints;
- promotion gates;
- claim boundaries.

If any of those scientific objects change, the corresponding benchmark workflow must be run deliberately and the scientific change reviewed on its own merits.
