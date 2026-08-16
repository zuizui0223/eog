# EOG inverse-conditioned world-set forecasting

## Status

This document defines the first EOG **prediction algorithm** built directly from the finite-world reconstruction core.

Working name:

> **EOG-WF — inverse-conditioned world-set forecasting**

It is a prediction algorithm in the sense that it maps a current observed positive distribution plus a declared world universe to future/unsampled node states over a finite propagation horizon. It does **not** claim that its uncalibrated support values are occupancy or colonisation probabilities.

## 1. Prediction target

Classical sitewise SDMs usually estimate a scalar suitability or occurrence quantity at each location. EOG-WF instead predicts a **world-indexed distributional-realizability set through horizon**.

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

The layers are deliberately not multiplied into one opaque score.

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

The old scalar `0.5` values are insufficient to perform this update because they erased which world generated each support value.

This is the operational reason world identity is retained: **it is state required for sequential prediction under structural uncertainty**, not decoration on an ensemble map.

## 5. Three forecast views

`rank_worldset_forecast_frontier` exposes three deliberately different views.

### Robust view

Prioritises nodes with high lower support that are supported across all retained worlds.

Use when the decision is conservative and the declared world universe is itself defensible.

### Possible-expansion view

Prioritises nodes with high upper support under at least one retained world.

Use for search or surveillance where missing a plausible expansion is more costly than investigating extra sites.

### Discriminating view

Prioritises contingent nodes whose world split is closest to 50:50 and whose support envelope is wide.

Use when the next observation should maximally distinguish still-compatible structural explanations.

The split score is an information-targeting heuristic, not an occurrence probability.

## 6. What is genuinely new versus prior art

EOG-WF must not claim generic novelty for any of the following:

- dynamic reachability or first-passage propagation;
- dynamic/process-based SDMs;
- ensemble SDMs;
- Bayesian model averaging;
- credal classifiers or imprecise-probability prediction sets;
- viability kernels or generic robust reachability;
- multiverse analysis;
- adaptive survey design.

These all have established literatures.

The **candidate domain-method contribution** is the specific biogeographic composition:

> observed positive distributions are first used as inverse consistency constraints on explicit ecological/analytical transition worlds; the surviving world identities are then carried forward as the state of a sequential, horizon-indexed distribution forecast instead of being averaged away; later positive evidence contracts or falsifies that world set without post-outcome retuning.

This is narrower than claiming a new general mathematics of set-valued forecasting.

## 7. Relationship to SDM

EOG-WF can consume local suitability/viability information rather than replacing it.

A useful decomposition is:

```text
local SDM or mechanistic layer
    -> local viability support

EOG transition world
    -> reachability support through landscape/history assumptions

optional persistence layer
    -> post-arrival support

EOG-WF
    -> world-indexed distributional-realizability forecast
```

Thus a locally suitable cell may remain unsupported because it is unreachable in all declared worlds, or contingent because accessibility depends on a subset of worlds.

Conversely, a reachable cell can be rejected by a declared viability gate.

This is the intended transition from a flat sitewise mosaic to a stateful landscape/flow forecast.

## 8. Current evidence level

The implementation establishes algorithmic behaviour on known-truth cases and preserves the earlier frozen empirical evidence.

It does **not yet establish** that EOG-WF predicts real independent distributions better than a strong SDM, dynamic SDM, or ensemble/credal comparator.

Required empirical validation is now explicit:

1. freeze a world universe before outcomes;
2. freeze local-state inputs and forecast gates;
3. hold out genuinely independent spatial or temporal units;
4. compare EOG-WF against:
   - local-only SDM;
   - same-world scalar/union/mean compression;
   - a strong dynamic/accessibility comparator appropriate to the system;
5. score both:
   - predictive performance when a calibrated response exists;
   - structural forecast utility, especially whether sequential observations discriminate world identities lost by compression;
6. accept adverse or null results without retuning.

## 9. Claim boundary

Until the empirical gate is passed, the strongest method claim is:

> **EOG-WF is an implemented inverse-conditioned, identity-preserving, set-valued forecasting algorithm for declared finite biogeographic worlds.**

It is not yet justified to claim universal predictive superiority, true colonisation routes, calibrated occupancy probabilities, or generic mathematical novelty.
