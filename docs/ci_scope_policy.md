# CI scope policy

## Purpose

EOG retains frozen historical benchmarks as reproducible scientific evidence while keeping the prospective EOG v2 development loop focused and tractable.

The package-level test workflow is responsible for broad implementation regression. Frozen development benchmarks should not all rerun merely because an unrelated module under `src/eog/` changes.

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

This change does not deprecate, delete or reinterpret any benchmark. It only prevents unrelated prospective v2 development from repeatedly executing historical exploratory/frozen benchmark suites.

## Prospective v2 policy

Prospective v2 workflows should use narrow path filters for the v2 estimand they test, for example:

- dynamic reachability;
- ecological traversability;
- occurrence-rule compatibility;
- validation-specific code and frozen contracts.

A v2 workflow should not become a second package-wide test suite.

## Global regression boundary

Broad Python-version compatibility, unit tests and wheel construction remain the responsibility of the existing Package checks workflow. The v0.1 frozen benchmark workflows remain manually reproducible when an implementation-level historical audit is intentionally requested.

## Scientific boundary

CI scope is operational metadata. Narrowing an automatic trigger must not change:

- benchmark code;
- benchmark inputs or seeds;
- frozen result files;
- result fingerprints;
- promotion gates;
- claim boundaries.

If any of those scientific objects change, the corresponding benchmark workflow must be run deliberately and the scientific change reviewed on its own merits.
