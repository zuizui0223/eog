# Layer-B mechanism recovery and v2 upgrade

## Status

This is a **post-closure research line**. It does not reopen the three-endpoint EOG-WF result and cannot change the frozen favorable / favorable / adverse synthesis.

The immediate question is narrower:

> Why could the same frozen Layer-B v1 representation add heldout information in Azores/Louisiana yet substantially degrade Tampa, and which representation contracts should prevent the same failure mode prospectively?

## What is now recovered

The previous claim that the Azores and Louisiana feature-generation contracts were no longer recoverable from the repository is incorrect. They remain recoverable from immutable GitHub history.

- **Azores yellow eel**: issue #289, historical PR #290, frozen `full_freeze_spec.json` at head `dff4554d1b95e6df1676ad09f0d80e94f40adff4`.
- **Southwest Louisiana King Rail**: issue #292 and frozen `full_freeze_spec.json` at commit `92aacb1b35ac68463a2f0afb941996bfe5e2d8c6`.
- **Tampa seagrass**: current main frozen contract and terminal artifact.

The recovered design contrast is qualitative, not just a difference in effect size.

| Endpoint | Layer-A/B state | Heldout design | Frozen result |
|---|---|---|---:|
| Azores | sequentially refreshed before each week; source state uses release anchors / previous detections | future calendar blocks | −7.0% log loss |
| Louisiana | sequentially refreshed before each occasion; world set contracts after positive evidence | future occasions | −0.39% |
| Tampa | one static node-level reconstruction per spatial fold, reused across 29 years of visits | heldout nodes | +29.9% |

This does **not** prove that sequential refresh causes favorable prediction. It identifies the highest-value mechanism contrast that had previously been missing from the evidence record.

## Tampa: what the frozen artifact actually shows

The placebo already rules out a simple feature-count story: a 20-replicate, ten-column permutation placebo had median macro log loss `0.336176`, close to the baseline `0.337735`, while the real Layer-B augmentation was `0.438764`. The real augmentation beat 0% of placebo replicates.

The newly recovered fold artifact adds stronger structural facts:

1. **All five Tampa worlds survive in every fold.** There is no fold-level compatible-world contraction for Layer B to report.
2. **Folds 1, 2, 3 and 5 have exactly the same heldout Layer-B feature fingerprint** (`ab5caf...`) despite having 45, 46, 38 and 43 calibration ever-positive nodes respectively. They also share the same sole source, `S1T1`.
3. Fold 4 changes the lexicographically selected source to `S1T10` and is the only fold with a different feature fingerprint (`71a56e...`).
4. Fold 1 accounts for 68.8% of the total adverse delta, but removing fold 1 still leaves mean delta `+0.03939`, about **14.0% relative degradation**. Fold concentration amplifies but does not explain away the problem.

## Geometry-only reconstruction

Using only the frozen 71-node coordinate registry, four Haversine threshold worlds, `external_open`, and the source identity already recorded in the consumed artifact, the heldout Layer-B matrices can be reconstructed exactly.

For both `S1T1` and `S1T10` source anchors:

- all **71/71 nodes have unique Layer-B vectors**;
- centered feature rank is 6;
- `surviving_world_fraction` and `positive_support_fraction` are constant;
- the remaining variation is a deterministic geometry/topology signature;
- the reconstructed feature fingerprints exactly equal the consumed endpoint artifact fingerprints.

Therefore the strongest structural diagnosis is now:

> In Tampa, once all worlds survive and one source is fixed, Layer B v1 ceases to encode changing world-set contraction and becomes an injective static node-level spatial signature that is reused across repeated visits.

The baseline already contains longitude and latitude. This makes spatial/node redundancy a concrete mechanism candidate. It is still **not** causal proof that the RF harmed calibration because of node memorization.

## A second problem: training-serving feature generation is not the same function

Tampa also has a prospective design asymmetry that was known before outcome access:

- calibration rows: remove the row's **entire stable node** from the calibration ever-positive node set, reconstruct, and reuse that resulting node vector for all visits from the node;
- heldout rows: use **one common reconstruction** from all calibration ever-positive nodes and read each heldout node vector from it.

This is leakage-averse but it means the augmented learner is trained under one feature generator and served under another. The v2 architecture now treats this as a first-class `feature_generation_shift`, not an implementation detail.

## v2-A — predictive-state eligibility gate

New module: `src/eog/v2/predictive_state_gate.py`.

Before Layer B is allowed into a supervised augmentation, the design declares:

- train feature-generator identity;
- serving feature-generator identity;
- whether repeated observations receive sequential/context-specific refresh or reuse one static state;
- source-selection policy and whether it is invariant to arbitrary source labels;
- whether the baseline already contains spatial coordinates.

The conservative default rules are:

1. train/serve generator mismatch → `ineligible_generation_shift`;
2. prediction-facing source choice depending on arbitrary labels → `ineligible_source_label_dependence`;
3. repeated-measure endpoint + static reused state → `structural_only_static_reuse` unless explicitly opted in before outcome access;
4. coordinate overlap is a warning requiring response-independent redundancy auditing, not an automatic biological exclusion.

A failed gate does **not** invalidate Layer A. It only withholds Layer B from default supervised use.

Under this v2 gate, the frozen Tampa design would have been stopped before response access for multiple independent design reasons. That retrospective observation motivates the rule; it does not erase the adverse endpoint.

## v2-B — source-symmetric candidate projection

New experimental module: `src/eog/v2/source_symmetric_predictive_summary.py`.

Layer A keeps exact source identities. For prediction only, v2 can accept support with dimensions

`source × surviving world × node`

and first equal-weight average across the **declared source set** inside each world, then apply the symmetric world summary. This makes the prediction-facing matrix invariant to:

- source order;
- source-ID spelling;
- world order;
- world-ID spelling.

This directly removes the Tampa v1 discontinuity in which lexicographically smallest node ID becomes the sole source. The v2 projection is a candidate interface, not a validated predictor.

## Mechanism ranking after recovery

### M1 — static state + train/serve generation shift

Highest priority. Both are contract facts and both can be tested without changing Layer A.

### M2 — world-set saturation becomes a spatial signature

High priority. All worlds survived every Tampa fold and exact geometry reconstruction produces a unique vector for every node.

### M3 — arbitrary single-source anchoring

High priority representation flaw. Fold 4 changed source solely because the lexicographic minimum changed; source-symmetric v2 removes label dependence by construction.

### M4 — fold concentration

Important instability, but not sufficient: the remaining four folds are still adverse on average.

## What is still not identified

We still cannot claim which mechanism contributed how much to Tampa's `+0.1010` log-loss delta. In particular, the current evidence cannot separate:

- static-state redundancy from train/serve generator shift;
- source-anchor discontinuity from broader spatial signature effects;
- RF calibration failure from other learner-specific interactions.

That requires a **new prospective mechanism experiment**, not a repaired Tampa rerun.

## Next confirmatory experiment

The next experiment belongs to the v2 mechanism line, not the closed paper denominator. Freeze a factorial known-truth or independent system design before outcomes with:

1. static vs sequentially refreshed Layer-A/B state;
2. matched vs mismatched train/serve feature generator;
3. lexicographic single source vs source-symmetric projection;
4. temporal vs node-block heldout where scientifically meaningful;
5. unchanged strong baseline and calibration-sensitive metrics.

Primary mechanism endpoints should be representation diagnostics first (generator parity, refresh fraction, source-label invariance, saturation), with predictive score changes secondary. The experiment cannot be counted as a fourth fresh EOG-WF endpoint and cannot alter the current manuscript's frozen conclusion.
