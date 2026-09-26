# When does structural accessibility add ecological information?

**Working target:** Ecography  
**Status:** cross-system synthesis spine v1  
**Core systems:** A-Islands, Tanzania forest fragments, Azores yellow eel, Southwest Louisiana King Rail, Tampa Bay seagrass

## One-sentence claim

Structural accessibility has predictive value only to the extent that it contributes **information not already represented by the reference model and is updated at the spatiotemporal scale at which the response is generated**.

## Why this is one ecological paper

The five closed systems do not support a universal "connectivity helps" claim.

Instead they form a boundary:

- A-Islands: landscape configuration retained held-out occupancy information after conditioning on pointwise climate support and nearest known occurrence.
- Tanzania: a generic graph-reachability feature was adverse after a species-adaptive matrix-aware current-flow reference had already represented landscape connectivity.
- Azores eel: a sequentially refreshed structural state improved held-out prediction in all 5 temporal units.
- Louisiana King Rail: a sequentially refreshed structural state produced a small favorable increment in 7/8 held-out occasions while the local world set contracted strongly.
- Tampa Bay seagrass: a static node-level structural representation reused across repeated visits was strongly adverse.

The ecological question is therefore not whether structural configuration matters in the abstract. It is **when structural information remains novel and response-aligned after the local ecological baseline is specified**.

## Current closed evidence

### A-Islands — residual structural novelty

845 estimable plant taxa across 842 islands.

Conditional connected-frequency concordance:
- 0.6177466
- species-bootstrap 95% interval 0.6086806-0.6269445

The comparison conditioned on pointwise environmental support and nearest-training-occurrence distance. Structural configuration therefore retained information absent from those simpler local/reference quantities.

This is evidence for residual structural information, not dispersal probability or historical route reconstruction.

### Tanzania — structural redundancy with a strong reference

60 bird species across 14 forest fragments.

Reference:
patch area + training-selected matrix-aware current flow + interaction + nearest training occurrence.

Adding geography-only connected frequency:
- macro log-loss delta = +0.0321131
- 95% interval +0.0174580 to +0.0486750

Positive is worse.

The relevant contrast is not "islands positive, fragments negative." It is that the Tanzania reference already contained a species-adaptive connectivity representation that was absent from the A-Islands reference.

### Azores eel — context-refreshed structural state

Held-out temporal blocks: 5.

Macro log loss:
- baseline 0.1422727
- augmented 0.1322871
- delta -0.0099856
- augmented wins 5/5

Layer-A/Layer-B state was recomputed sequentially before each scored week from the currently surviving worlds and source state.

### Southwest Louisiana King Rail — context-refreshed structural state

Held-out chronological occasions: 8.

Macro log loss:
- baseline 0.2463173
- augmented 0.2453455
- delta -0.0009718
- augmented wins 7/8

All six frozen local worlds were eventually falsified, leaving external_open only. The predictive result is small but directionally favorable.

### Tampa Bay seagrass — static reused structural state

Held-out spatial folds: 5.

Macro log loss:
- baseline 0.3377354
- augmented 0.4387640
- delta +0.1010287
- augmented wins 1/5

The same node-level Layer-B representation was reused across repeated visits/years. The baseline already contained longitude, latitude, survey year and day of year. All declared worlds survived in the recoverable structural audit.

## Two candidate moderators

### 1. Residual structural novelty

A structural feature should add little or no information when the reference model already contains a strong representation of the same spatial constraint.

This is the A-Islands/Tanzania contrast.

Operational future definition:
- **low reference saturation:** no explicit matrix/connectivity/path representation in the baseline beyond local environment and simple source distance;
- **high reference saturation:** baseline contains a landscape-specific connectivity/path/current-flow/resistance term selected without held-out leakage.

### 2. Response-aligned updating

A structural representation should be more useful when its state can change at the same scale as the response-generating process, rather than being a static feature reused across heterogeneous temporal occasions.

This is motivated by the Azores/Louisiana/Tampa contrast.

Operational future definition:
- **aligned:** structural state is recomputed prospectively before each response unit using only information available before that response;
- **static/reused:** one structural representation is reused across response occasions whose ecological state can change.

## What the five systems already establish

They reject two universal claims:

1. local environmental support plus distance is always sufficient;
2. adding a generic structural representation always improves held-out prediction.

They also show that favorable and adverse structural increments occur in real ecological systems under frozen evaluation.

## What they do not yet establish

The five systems do **not** identify the two moderators causally.

Differences among ecosystems, taxa, endpoint definitions, baseline learners, spatial grain and temporal design are confounded.

Therefore the current five-system comparison is a **hypothesis-generating cross-system synthesis**, not the confirmatory moderator test.

## Prospective next test

Future candidate endpoints are classified *before response opening* on two axes:

| Axis | Level 0 | Level 1 |
|---|---|---|
| Reference saturation | weak/local baseline | explicit strong structural baseline |
| Temporal alignment | prospectively refreshed | static/reused |

Primary prediction:

- favorable structural increments should be concentrated in **weak-reference + refreshed/aligned** endpoints;
- non-positive increments should be more common when the reference is structurally saturated or the structural representation is temporally misaligned.

No endpoint may be moved between cells after predictive outcomes are read.

## Manuscript architecture

1. Why structural connectivity effects are expected to be context dependent.
2. Five closed systems as the empirical boundary.
3. Residual structural novelty: A-Islands vs Tanzania.
4. Response-aligned updating: Azores/Louisiana vs Tampa.
5. A preregisterable two-axis theory of structural added value.
6. Prospective validation as the final confirmatory step.

## Claim boundary

Allowed now:
- structural information can be beneficial, negligible, or adverse depending on system/reference design;
- A-Islands contains residual information beyond local support + source distance;
- Tanzania's generic graph feature is adverse relative to a matrix-aware reference;
- the two favorable dynamic endpoints used sequentially refreshed representations;
- Tampa used a static reused representation and was adverse;
- these patterns motivate the two-axis hypothesis.

Not allowed now:
- residual novelty is proven to cause the A-Islands/Tanzania difference;
- temporal updating is proven to cause the Azores/Louisiana/Tampa difference;
- mobility or life history explains the endpoint signs;
- effect sizes from concordance and log loss are directly comparable;
- structural accessibility is universally beneficial or harmful.


## Known-truth moderator test — result

The preregistered response-free 2×2 known-truth experiment crossed reference saturation with response alignment across 64 paired replicates. All seven predeclared checks passed.

### Weak reference + refreshed structural state

When the baseline omitted the generating structural state and the structural representation tracked the current context:

- mean augmented-minus-baseline log loss = **-0.17961**;
- median = **-0.17959**;
- 63/64 replicates were favorable (0.9844).

This was the best median cell, as predicted before opening.

### Reference saturation

Adding the exact generating structural state to the reference removed the incremental advantage of the refreshed structural representation.

Under the strong reference, refreshed augmentation had:

- mean added value = **+0.00786**;
- median = **+0.00697**;
- favorable fraction = 0.3281.

The within-replicate saturation moderation,
`added_value(strong, refreshed) - added_value(weak, refreshed)`,
had:

- mean **+0.18748**;
- median **+0.18797**;
- 64/64 positive;
- 2.5-97.5% quantiles **[+0.08587, +0.29213]**.

Thus, under known truth, structural added value causally shrinks when the reference already contains the relevant structural information.

### Response alignment

Under the weak reference, replacing the context-refreshed representation with a node-level state averaged over fitting contexts reversed the benefit:

- static-reused mean added value = **+0.04253**;
- median = **+0.03937**;
- favorable fraction = 0.0469.

The within-replicate alignment moderation,
`added_value(weak, static) - added_value(weak, refreshed)`,
had:

- mean **+0.22215**;
- median **+0.22242**;
- 64/64 positive;
- 2.5-97.5% quantiles **[+0.09714, +0.35769]**.

This independently reproduces the earlier static-reuse mechanism result in a factorial explicitly paired with reference saturation.

### Updated scientific position

The known-truth evidence now supports two causal moderators:

1. **Residual structural novelty:** structural augmentation loses value when the reference already contains the generating structural signal.
2. **Response alignment:** structural augmentation loses value when a changing structural state is replaced by a static representation reused across response contexts.

The historical ecological systems remain observational examples, not causal assignments. A-Islands/Tanzania and Azores/Louisiana/Tampa are consistent with these moderators, but the historical sign differences are not claimed to be caused by them.

The next empirical step is therefore narrower than generic candidate hunting: a future separately preregistered real-data programme should classify candidate systems on these two axes **before** response opening and test whether the predicted sign pattern transfers.
