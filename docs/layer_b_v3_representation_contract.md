# Layer-B v3 representation and mechanism contract

## Status

This is a **post-closure mechanism line**. It does not reopen, repair, rescore, or reinterpret
the three frozen EOG-WF endpoints. Azores remains favorable, Southwest Louisiana remains
favorable, and Tampa remains adverse under the consumed v1 endpoint contracts.

The purpose of v3 is narrower:

> Remove known prediction-interface defects before asking, in a future independent design,
> whether world-set information itself adds or harms heldout prediction.

No consumed response may be reopened for v3 confirmation.

## Why v3 is needed

### 1. The v1 ten-column summary overstates the dimensionality of a small world set

The frozen v1 prediction interface exposes ten columns:

- surviving-world fraction;
- mean;
- standard deviation;
- minimum;
- maximum;
- q25;
- q50;
- q75;
- positive-support fraction;
- range.

In Tampa the declared world set contains five worlds. A per-node support vector with at
most five surviving values cannot supply ten independent continuous degrees of freedom.
For five values and NumPy linear quantiles, min/q25/q50/q75/max reproduce the five order
statistics, while mean, standard deviation and range are deterministic functions of the
same values. In addition, surviving-world fraction is constant across nodes within one
common reconstruction.

This does not invalidate the frozen Tampa score. It means the adverse result is evidence
against the **frozen v1 augmentation**, not a clean causal estimate of the value of EOG
world-set information independent of representation design.

### 2. The historical placebo did not preserve joint feature structure

The Tampa placebo independently permuted feature columns. It therefore preserved each
column marginal but destroyed the cross-column dependence induced by summarizing one
small latent world-support vector.

The historical placebo still rules out a simple feature-count explanation. It does not
establish that the real Layer-B block and placebo had the same multivariate structure.

### 3. Primary learner randomness was not propagated symmetrically with the placebo

The frozen primary baseline/augmented comparison used one declared RF seed. The secondary
placebo used repeated seeds. The primary result remains the result of that frozen paired
experiment, but it is not an estimate averaged over learner stochasticity.

### 4. Arbitrary single-source anchoring created a discontinuity

The post-closure Tampa audit already established that lexicographic source selection
changed from S1T1 to S1T10 in one fold and changed the Layer-B fingerprint. Existing
source-symmetric v2 removes source-label dependence by construction. v3 retains that
requirement.

## v3 prospective contracts

### A. Compact prediction-facing projection

New module:

src/eog/v2/compact_source_symmetric_summary.py

Prediction still first aggregates equally across the declared source set inside each
surviving world. It then exposes only four prospectively declared columns:

1. surviving-world fraction;
2. support mean;
3. support standard deviation;
4. minimum support.

The compact representation is deliberately lossy. It is not claimed to be sufficient for
the latent world-support vector. It is chosen to avoid deterministic expansion such as
range = max - min and the simultaneous use of five order statistics plus their moments.

The module reports constant columns and centered matrix rank as diagnostics. A constant
column may remain in the frozen interface if it can vary across sequential contexts, but
its zero within-state variation is explicit rather than hidden.

Increasing the number of worlds is **not** a feature-engineering remedy. Any larger world
universe must be justified by the ecological/analytical world contract independently of
the desired predictor dimensionality.

### B. Structure-preserving placebo

New module:

src/eog/v2/structure_preserving_placebo.py

Two prospective placebo modes are available.

- joint-row permutation: permutes complete feature vectors and therefore preserves the
  exact row multiset and all cross-column dependence;
- grouped-vector permutation: for static repeated-measure features, permutes one complete
  vector among declared groups and reuses it for every row in that group.

For repeated-node endpoints, grouped-vector permutation is preferred when the real
representation is intentionally static within node. For sequentially refreshed states,
the placebo unit must match the declared state-generation unit prospectively.

Column-wise independent permutation is not an admissible v3 structural placebo.

### C. Paired multi-seed primary evaluation

New module:

src/eog/v2/paired_seed_evaluation.py

A future predictive mechanism experiment must evaluate baseline and augmented arms under
the identical declared learner-seed sequence. Multiple learner seeds are required by
default. Each seed produces a paired delta; the protocol reports at least:

- baseline scores by seed;
- augmented scores by seed;
- paired deltas;
- mean delta;
- median delta;
- augmented-win fraction.

A placebo experiment must not receive a richer learner-randomness treatment than the
primary comparison.

### D. Source symmetry

Prediction-facing source choice must be invariant to source order and arbitrary source-ID
spelling. Exact source identities remain in Layer A for audit and scientific state.

The v2 source-symmetric source-by-world-by-node projection remains the required upstream
source aggregation logic. v3 changes the downstream summary, not Layer A.

## What v3 does not claim

v3 does not claim that any of these defects caused the Tampa adverse score.

The current evidence cannot partition the +0.1010 Tampa delta among:

- redundant feature expansion;
- static spatial/node redundancy;
- train/serve generator shift;
- single-source discontinuity;
- learner stochasticity;
- learner-specific calibration interactions;
- genuine lack of useful Layer-B information.

Those are mechanism hypotheses.

## Confirmatory order

Any future independent v3 test must freeze the following before outcome access:

1. ecological/analytical world universe;
2. source-symmetric aggregation policy;
3. compact four-column representation;
4. train/serve feature-generator parity;
5. sequential/static refresh policy;
6. learner family and hyperparameters;
7. learner seed set;
8. placebo unit and permutation seed set;
9. heldout split and primary metric;
10. favorable/null/adverse decision rule.

The primary comparison is baseline versus compact-v3 augmentation over the same learner
seeds. The structure-preserving placebo is secondary and must preserve the multivariate
feature block at the declared permutation unit.

## Relationship to open fresh-real protocol PR #445

PR #445 froze a separate fresh-real protocol before candidate search. It currently names
the source-symmetric v2 ten-column candidate representation and a single RF random state.

This v3 mechanism line **does not silently amend that frozen protocol**.

If the fresh-real programme is to use v3, it requires an explicit new protocol version
locked before roster capture and before any candidate data payload is opened. Otherwise
PR #445 remains a test of its own v1 protocol exactly as frozen.

## Scientific interpretation after this audit

The frozen EOG-WF conclusion remains:

> Layer A is an auditable structural compatibility / contraction / falsification state.
> Layer B is a context-dependent predictive complement whose added value is not uniformly
> beneficial.

The additional post-closure conclusion is:

> The current evidence does not identify whether Tampa's adverse Layer-B result reflects
> the information content of the world set itself or defects in the v1 prediction-facing
> representation. Future mechanism tests must remove known representation asymmetries
> before attributing predictive gain or harm to EOG world-set information.
