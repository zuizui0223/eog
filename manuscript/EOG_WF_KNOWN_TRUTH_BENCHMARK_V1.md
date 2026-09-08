# EOG-WF known-truth method benchmark — manuscript fragment v1

Purpose: recover already-implemented response-independent tests as a manuscript-level method demonstration. This fragment adds **no new biological endpoint** and cannot alter the frozen favorable/favorable/adverse empirical closure.

Evidence sources:

- `tests/test_sequential_world_forecast.py`
- `tests/test_world_predictive_summary.py`

## Methods — deterministic known-truth benchmark

Before the ecological applications, we evaluated the separation between Layer A and Layer B in small deterministic world universes with known transition structure.

For the first construction, five nodes (`a`–`e`) were connected under two exact rules, `left` and `right`. Both rules supported the first observed transition from source `a` to target `b`. After the declared current source changed to `d`, only `left` supported target `c`, whereas `right` supported `e`. A later transition used source `c`, from which the sole remaining `left` rule did not support target `e`. The benchmark therefore had a known sequence in which both rules initially survived, later evidence eliminated one exact rule, and subsequent evidence falsified the remaining declared universe.

For the second construction, four nodes (`a`–`d`) were represented by two exact worlds that connected the same source and endpoint through alternative intermediate nodes. We generated the Layer-B ten-feature projection from the exact forecast, then repeated the projection after (i) renaming the exact worlds and (ii) reversing world-member order. The benchmark was designed so that exact latent identity should change under renaming while the prediction-facing representation should remain unchanged.

These tests evaluate method contracts rather than predictive superiority. They ask whether exact identity is preserved where rule-specific falsification requires it, and removed where arbitrary labels should not alter supervised features.

## Results — exact contraction and label-invariant projection

### Layer A retains rule identity and contracts monotonically

In the five-node construction, both `left` and `right` survived the first update from `a` to observed target `b`. After the source changed to `d` and `c` was observed, `right` was eliminated and `left` alone survived. The surviving rule set was a subset of the previous set at each update. Under the subsequent source `c`, the remaining `left` rule could not support observed target `e`; the terminal status was therefore `universe_falsified` and the surviving world set became empty.

The implementation also distinguishes rule identity from current source state: changing the source changes the full world fingerprint but not the fingerprint of the frozen rule itself. Reusing a world ID after mutating its operator is rejected as a change to the rule universe.

### Layer B is invariant to arbitrary world labels and member order

In the four-node construction, renaming the two worlds from `left/right` to `banana/saffron` changed the exact latent forecast fingerprint, as expected, but left the Layer-B feature fingerprint and complete feature matrix unchanged. Reversing member order likewise left the feature fingerprint and feature matrix unchanged.

The ten predictive columns contain no `world_id` field and do not expose the exact labels. At the same time, the projection preserves declared support-set information: for a node supported by one of two surviving worlds, the positive-support fraction is 0.5 and the status is `contingent`.

### The two layers therefore preserve different information by construction

The deterministic examples establish three properties required for the EOG-WF architecture:

1. **Exact identity is necessary for auditable rule-specific contraction and finite-universe falsification.**
2. **Arbitrary exact-world names and member ordering are unnecessary for the prediction-facing representation.**
3. **Removing labels from Layer B does not remove the exact Layer-A state; the latent and prediction-facing fingerprints remain separately auditable.**

These are known-truth method properties. They do not establish that Layer B improves ecological prediction; that question is evaluated separately by the prospectively closed fresh ecological endpoints.

## Placement in the main manuscript

Recommended order for MEE Research Article framing:

1. Introduction
2. Two-layer estimand
3. **Deterministic known-truth benchmark (this fragment)**
4. Prospective endpoint funnel and paired complementarity design
5. Fresh ecological endpoints
6. Discussion

This satisfies the narrative requirement that the computational method be demonstrated before empirical applications without reopening the biological endpoint denominator.
