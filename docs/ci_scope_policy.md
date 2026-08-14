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

Prospective workflows use narrow path filters for the scientific implementation or frozen contract they test, for example:

- dynamic reachability implementation;
- ecological traversability implementation;
- occurrence-rule compatibility implementation;
- directional-evidence implementation;
- validation-specific code and frozen contracts.

A scientific confirmation workflow must not become a second package-wide test suite.

Facade-only changes belong to Package checks. This includes:

- `src/eog/__init__.py`;
- `src/eog/v2/__init__.py`;
- `src/eog/v2/reachability.py`;
- `src/eog/v2/traversability.py`;
- `src/eog/v2/validation.py`.

Those files route public names but do not own frozen scientific estimands. Their compatibility, lazy loading, and full symbol resolution are tested by the package suite. The traversability, occurrence-rule, and directional-evidence confirmation workflows therefore watch the owning implementation modules and contracts, not the facade files or package-layout tests.

Where a confirmation module depends directly on another scientific implementation, that dependency is named explicitly in the path filter rather than approximated with a broad subtree glob. For example, occurrence-rule and directional-evidence confirmation depend on the dynamic transition operator, while traversability confirmation depends on `ecological_traversability.py`.

The finite-world reconstruction and temporal transition-landscape layers are currently covered by Package checks and dedicated known-truth tests. They compose already-declared transition operators and do not receive separate scientific confirmation workflow families merely because new internal modules were added.

## Global regression boundary

Broad Python-version compatibility, full unit tests, public compatibility imports, lazy-facade contracts and wheel construction remain the responsibility of Package checks. Frozen benchmark workflows remain manually reproducible when an implementation-level historical audit is intentionally requested.

## Scientific boundary

CI scope is operational metadata. Narrowing an automatic trigger must not change:

- benchmark code;
- benchmark inputs or seeds;
- frozen result files;
- result fingerprints;
- promotion gates;
- claim boundaries.

If any of those scientific objects change, the corresponding benchmark workflow must be run deliberately and the scientific change reviewed on its own merits.
