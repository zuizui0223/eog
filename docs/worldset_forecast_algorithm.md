# EOG inverse-conditioned world-set forecasting

## Status

This document defines the first EOG **prediction algorithm** built directly from the finite-world reconstruction core.

Working name:

> **EOG-WF — inverse-conditioned world-set forecasting**

Current algorithmic status:

> **Implemented and known-truth validated. Independent ecological predictive superiority is not established.**

EOG-WF maps a current positive distribution plus a declared finite world universe to future/unsampled node states through a finite propagation horizon, then updates that forecast when later positive evidence arrives.

It does **not** claim that uncalibrated support values are occupancy or colonisation probabilities.

## 1. Prediction target

Classical sitewise SDMs typically produce a scalar suitability/occurrence surface. EOG-WF instead predicts a **world-indexed distributional-realizability set through horizon**.

Given:

- a finite declared world universe `W`;
- current positive occurrences `O`;
- a forecast horizon `H` in propagation steps;
- optional predeclared local viability/persistence gates;

EOG first reconstructs

```text
W(O) = {w in W : w is compatible with O}
```

and then forecasts every retained world separately.

For target node `x`, world `w`, and step `h`, let

```text
S_w(x, h)
```

be cumulative first-passage reachability support from the world's declared source set by step `h`.

If local state gates are active, a world supports the future state only when all declared gates pass separately:

```text
reachability > tau_R
viability    >= tau_V      # optional
persistence  >= tau_P      # optional
```

The layers are deliberately not multiplied into one opaque occupancy-like score.

## 2. Set-valued forecast

At each node and horizon EOG-WF returns:

- **robustly_supported** — every currently compatible world supports the node by that horizon;
- **contingent** — at least one but not every compatible world supports it;
- **excluded_in_all_worlds** — no compatible world supports it.

It additionally retains:

- lower and upper first-passage support across worlds;
- fraction of compatible worlds supporting the node;
- exact supporting world IDs;
- earliest step at which any world supports the node;
- earliest step at which all retained worlds support the node, when such a step exists.

Therefore the primary prediction object is a **forecast cube**:

```text
world × horizon × node
```

with robust/contingent/excluded projections derived from that cube.

A scalar summary may be generated for a declared decision problem, but it is not the canonical state of the algorithm.

## 3. Sequential update is part of the predictor

The algorithm is not a one-shot uncertainty map.

When new positive occurrence evidence `O+` arrives, EOG-WF does not retune the world definitions. It performs:

```text
W(O union O+) subseteq W(O)
```

and rebuilds the forecast over the contracted world set.

If no declared world remains compatible, the update returns:

```text
universe_falsified
```

rather than inventing a rescue world or silently moving a threshold.

This gives EOG-WF a closed prediction/update loop:

```text
observed distribution
    -> inverse world filtering
    -> forward world-specific forecast
    -> new positive evidence
    -> world contraction/falsification
    -> revised forecast
```

## 4. Why exact world identity matters algorithmically

A known-truth test in `tests/test_world_forecast.py` constructs two worlds:

```text
left:   a -> b -> c
right:  a -> d -> c
```

With positive observations `a` and `c`, both worlds are compatible.

At the forecast horizon:

```text
b: supported by 1/2 worlds
d: supported by 1/2 worlds
```

A scalar frequency compression gives both nodes the same value, `0.5`.

But their exact supporting identities differ:

```text
b -> {left}
d -> {right}
```

When a new positive occurrence at `b` is added, the right world is eliminated. The revised forecast becomes:

```text
b -> robustly_supported
d -> excluded_in_all_worlds
```

The old scalar `0.5` values are insufficient to perform this exact update because they erased which world generated each support value.

This is the operational reason world identity is retained: **it is state required for sequential prediction under structural uncertainty**, not decoration on an ensemble map.

## 5. Algorithmic invariants

The first EOG-WF implementation enforces:

1. **frozen-world identity** — world IDs and fingerprints cannot change between reconstruction, forecast and update;
2. **positive-evidence contraction** — adding positive constraints cannot create newly compatible worlds;
3. **horizon monotonicity** — cumulative first-passage support cannot decrease as forecast horizon increases;
4. **separate local gates** — reachability, viability and persistence remain separately declared;
5. **finite-universe falsification** — if every declared world is contradicted, the algorithm returns that failure explicitly;
6. **certificate-bounded claims** — robust/excluded classes are exact only over the declared compatible finite universe;
7. **deterministic reproducibility** — reconstruction, gate, member and forecast fingerprints bind the frozen inputs/state.

## 6. Three forecast views

`rank_worldset_forecast_frontier` exposes three deliberately different decision views.

### Robust view

Prioritises nodes with high lower support that are supported across all retained worlds.

Use when decisions are conservative and the declared world universe is itself defensible.

### Possible-expansion view

Prioritises nodes with high upper support under at least one retained world.

Use for surveillance/search where missing a plausible expansion is more costly than investigating extra sites.

### Discriminating view

Prioritises contingent nodes whose world split is closest to 50:50 and whose support envelope is wide.

Use when the next positive observation should distinguish still-compatible structural explanations.

The split score is an information-targeting heuristic, not an occurrence probability.

## 7. What is genuinely new versus prior art

EOG-WF must not claim generic novelty for:

- dynamic reachability or first-passage propagation;
- dynamic/process-based SDMs;
- ensemble SDMs or model averaging;
- Bayesian/credal/imprecise-probability classification or prediction sets in general;
- viability kernels or generic robust reachability;
- multiverse analysis;
- adaptive survey design;
- history matching / compatible-set filtering in general.

These all have established literatures.

The **candidate domain-method contribution** is the specific biogeographic inverse-to-forward composition:

> observed positive distributions are first used as inverse consistency constraints on explicit ecological/analytical transition worlds; the surviving exact world identities are then carried forward as the state of a horizon-indexed distribution forecast instead of being averaged away; later positive evidence contracts or falsifies that frozen world set without post-outcome retuning.

This is narrower than claiming new general mathematics for set-valued forecasting.

## 8. Relationship to SDM

EOG-WF can consume local suitability/viability information rather than replacing it.

A useful decomposition is:

```text
local SDM or mechanistic layer
    -> local viability support

EOG transition world
    -> reachability support through landscape/process assumptions

optional persistence layer
    -> post-arrival support

EOG-WF
    -> world-indexed distributional-realizability forecast
```

Thus a locally suitable cell may remain unsupported because it is unreachable in all declared worlds, or contingent because accessibility depends on a subset of worlds.

Conversely, a reachable cell can be rejected by a declared viability gate.

This is the intended transition from a flat sitewise mosaic to a stateful landscape/flow forecast.

## 9. Current evidence level

The implementation establishes algorithmic behavior on known-truth cases and preserves all earlier frozen empirical evidence.

The known-truth suite demonstrates:

- world-identity collision despite equal scalar support frequency;
- exact forecast sharpening after later positive evidence;
- finite-universe falsification;
- horizon monotonicity;
- separate local viability gating;
- robust/possible/discriminating forecast views.

Package regression is required on Python 3.10/3.11/3.12 plus the frozen topology benchmark.

This does **not yet establish** that EOG-WF predicts real independent distributions better than a strong SDM, dynamic SDM, ensemble/credal comparator, or matched scalar compression.

## 10. Required empirical validation

A future independent forecast test must freeze, before outcome inspection:

1. a generically eligible ecological system with enough independent spatial/temporal units;
2. world universe and adequacy certificate;
3. local viability/persistence inputs and gates when used;
4. forecast horizon and whether it is physical-time calibrated;
5. a same-world scalar/union/mean compression comparator;
6. a strong external SDM/dynamic/accessibility comparator appropriate to the system;
7. predictive scoring when a calibrated response exists;
8. an identity-preserving sequential-update endpoint;
9. dependence-aware inference;
10. a null/adverse/no-added-value stop rule.

Run once without retuning after outcomes/evidence are opened.

## 11. Product threshold

EOG-WF has crossed the **algorithm threshold** when all of the following hold:

- a deterministic forecast API exists;
- output semantics and finite-world certificate are explicit;
- sequential update/falsification exists;
- exact world identity demonstrably changes a future update relative to scalar compression;
- known-truth and package tests are green.

It crosses the stronger **validated ecological prediction-product threshold** only after an independent eligible system demonstrates useful forecast behavior relative to the frozen matched comparators.

These thresholds must not be conflated.

## 12. Claim boundary

The strongest current algorithm claim is:

> **EOG-WF is an implemented inverse-conditioned, identity-preserving, set-valued forecasting algorithm for declared finite biogeographic worlds.**

The strongest current scientific boundary is:

> **Independent ecological predictive superiority, calibrated occupancy/colonisation probability, true historical routes, and generic mathematical novelty are not yet established.**
