# EOG-WF two-layer forecast architecture

## Why this architecture exists

The first independent EOG-WF system to reach heldout prediction, the Åland Glanville fritillary metapopulation, produced a clear adverse result for the original product hypothesis:

> **feeding exact world identity directly into the supervised prediction head did not improve prediction.**

On the six predeclared heldout annual transitions, exact identity had macro-year log loss `0.230197`, versus `0.187983` for the declared symmetric compression of the same world-set information. Exact identity was worse in all 6/6 heldout transitions.

The result does **not** imply that world identity should be discarded. The same independent run sequentially eliminated four structurally truncated worlds while retaining the full exponential process world. Exact rule identity therefore remained meaningful for falsification/update even when its direct predictive encoding was harmful.

The product boundary is consequently narrowed to two layers.

## Layer A — exact latent epistemic/update state

This layer retains:

- exact frozen world/rule IDs;
- exact transition-rule fingerprints;
- current source state;
- per-world support through forecast horizon;
- compatibility/survival state;
- evidence-driven world contraction;
- finite-universe falsification.

This is the state needed to answer:

- which declared explanations remain compatible?;
- which world was eliminated by new evidence?;
- which forecast is robust versus contingent?;
- has the declared universe been falsified?

Canonical implementations:

- `src/eog/v2/world_reconstruction.py`
- `src/eog/v2/world_forecast.py`
- `src/eog/v2/sequential_world_forecast.py`

World identity remains scientifically inspectable here.

## Layer B — world-label-invariant predictive representation

A supervised predictive head should not assume that arbitrary world labels are useful numerical covariates.

EOG therefore exposes a symmetric projection of the exact latent state through:

`src/eog/v2/world_predictive_summary.py`

For each node and declared forecast step, version 1 reports exactly ten EOG-specific features:

1. surviving-world fraction;
2. support mean;
3. support standard deviation;
4. support minimum;
5. support maximum;
6. support q25;
7. support q50;
8. support q75;
9. positive-support fraction;
10. support range.

These are the same **type** of world-label-invariant quantities that formed the predeclared Glanville compression comparator. The implementation is now a generic product interface rather than a Glanville-specific benchmark feature block.

The exact upstream forecast remains attached by provenance fingerprint, but world IDs are not predictive columns.

## Required invariance

The Layer-B feature representation must be unchanged when:

- world IDs are renamed;
- surviving world members are enumerated in a different order.

The exact Layer-A latent fingerprint may change under world renaming because it is an auditable scientific identity. Layer B deliberately separates numerical prediction invariance from Layer-A provenance identity.

Tests in `tests/test_world_predictive_summary.py` enforce this distinction.

## What this does not claim

This architecture does **not** claim novelty for:

- permutation-invariant set functions;
- distributional summaries;
- ensemble moments/quantiles;
- model averaging;
- DeepSets or other learned set encoders;
- generic uncertainty compression.

Nor does the Glanville result confirm that the current ten-feature summary is optimal or externally superior. In Glanville it was a frozen comparator and descriptively had the best macro log loss, but external superiority of that compression was **not** the prospectively declared external endpoint.

The only current methodological claim is narrower:

> **exact world identity should be retained as EOG's auditable sequential update state, while the default predictive interface should be invariant to arbitrary world labels unless future independent evidence establishes a reason to expose identity directly.**

## Validation status

### Exact latent/update layer

- known-truth sequential-update behavior: supported;
- independent Glanville rule contraction: observed;
- historical truth: not implied.

### Exact-identity predictive head

- independent Glanville result: **adverse**;
- product status: rejected as default prediction representation.

### Symmetric predictive summary

- implementation/invariance tests: pending/current development on PR #196;
- independent predictive added value: **not established**;
- Glanville may not be reused as fresh confirmation.

## Next valid test

A future fresh independent system must prospectively freeze:

1. source/process closure;
2. world-scale construction and structural adequacy;
3. exact latent world/rule state;
4. world-label-invariant predictive representation;
5. strong external comparator;
6. heldout design and metrics;
7. null/adverse stop rules.

Then open the response once.

Do not re-engineer the symmetric summary on Glanville heldout results and relabel the rerun independent confirmation.
