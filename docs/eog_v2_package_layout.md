# EOG v2 package layout

## Public boundary

The repository keeps the frozen v0.1 API under root `eog` while prospective method development is grouped under the `eog.v2` subpackage.

The supported prospective v2 facades are:

- `eog.v2.reachability` — dynamic transition operators, first passage, flux, state layers and graph diagnostics;
- `eog.v2.traversability` — environmental continuity, transit viability and occurrence-conditioned transition-rule constraints;
- `eog.v2.validation` — occurrence/genetic validation and independent evidence discrimination;
- `eog.v2.cli` — console-script routing only.

The historical convenience import surface `from eog.v2 import ...` remains available for compatibility, but new prospective implementation should be placed behind the appropriate facade rather than adding another unrelated top-level namespace.

## Console scripts

All commands whose public name begins with `eog-v2-` route through `eog.v2.cli`:

- `eog-v2-genetic-validate`;
- `eog-v2-occurrence-freeze`;
- `eog-v2-occurrence-validate`.

The facade delegates lazily to the existing implementation modules. This changes package organization only; it does not alter CLI arguments, validation logic, frozen results or fingerprints.

## Compatibility boundary

Existing implementation modules remain in place because frozen workflows and external callers may import them directly. Consolidation therefore proceeds by introducing stable facades first rather than moving files destructively.

A later major-version migration may relocate internals only if compatibility aliases, release notes and frozen reproduction paths are handled explicitly.

## Development rule

New EOG v2 work should prefer:

1. implementation inside `eog.v2` when it is genuinely prospective v2 logic;
2. exposure through one of the existing facades;
3. no new top-level CLI entry module when `eog.v2.cli` can route it;
4. package-level regression through Package checks;
5. narrow estimand-specific workflows rather than duplicate package-wide CI.

## Scientific boundary

Package layout is an implementation-maintenance concern. Reorganization must not be used to change a scientific estimand, retune a benchmark, rewrite a frozen result, or bypass a response firewall.
