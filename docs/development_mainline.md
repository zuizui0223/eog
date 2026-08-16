# EOG development mainline

## Status

This file is the **single source of truth for active scientific development**.

Current empirical state:

> **exploratory-supported but independently unconfirmed**

Current algorithmic state:

> **EOG-WF is an implemented inverse-conditioned, identity-preserving, set-valued biogeographic forecasting algorithm. Its defining sequential-update behavior passes known-truth/package tests; independent ecological predictive superiority remains unconfirmed.**

Generic operator growth is stopped. The active scientific mainline is now **prediction-algorithm validation**, not further graph/connectivity invention.

Canonical algorithm and validation rules:

- [`worldset_forecast_algorithm.md`](worldset_forecast_algorithm.md)
- [`method_validation_protocol.md`](method_validation_protocol.md)

Frozen earlier empirical contracts remain evidence and are not rewritten to match the improved protocol.

## Scientific center

EOG keeps four objects separate:

1. **local possibility** — locally supported under a declared environmental/process representation;
2. **reachability** — reachable from declared realized anchors under a declared transition world;
3. **distributional realizability** — compatible with the observed positive distribution under that world;
4. **historical truth** — the actual route, sequence, ancestry, movement rate or demographic process in nature.

Observed occurrences are realized positive states. They constrain admissible distribution-forming worlds but do not identify one true route/history.

For a declared finite universe `W` and current positive observations `O`, EOG reconstructs

```text
W(O) = {w in W : w is compatible with O}
```

and then EOG-WF carries the surviving world identities forward into prediction rather than averaging them away.

## EOG-WF: active prediction algorithm

The main prediction/update loop is:

```text
positive observations O
      ↓
inverse world filtering W(O)
      ↓
forward first-passage propagation inside each retained world
      ↓
optional separately declared local viability/persistence gates
      ↓
world × horizon × node forecast cube
      ↓
robust / contingent / all-world-excluded projections
      ↓
new positive evidence O+
      ↓
W(O ∪ O+) ⊆ W(O), or finite-universe falsification
      ↓
revised forecast
```

The implementation is `src/eog/v2/world_forecast.py`, exposed lazily through `eog.v2.reachability`.

### Prediction object

For every node and forecast horizon, EOG-WF retains:

- lower and upper cumulative first-passage support across compatible worlds;
- exact world IDs supporting the node;
- supporting-world fraction;
- earliest step supported by any world;
- earliest step supported by every retained world when it exists;
- status: `robustly_supported`, `contingent`, or `excluded_in_all_worlds`.

The exact world-indexed cube is canonical. A scalar projection may be produced for a declared decision problem, but scalarization is not the internal state of the predictor.

### Sequential evidence update

New positive evidence is used to re-evaluate the **same frozen world universe**. World definitions, thresholds and gates are not retuned to rescue the prediction.

Adding positive constraints cannot create newly compatible worlds. It can:

- retain the same world set;
- eliminate one or more worlds and sharpen the forecast; or
- eliminate every declared world, returning `universe_falsified`.

That falsification state is a valid forecast outcome rather than an implementation failure.

## Known-truth algorithm gate — PASS

The canonical collision test constructs:

```text
left:   a -> b -> c
right:  a -> d -> c
```

With current positives `a` and `c`, both worlds remain compatible.

At the same horizon:

```text
b: 1/2 worlds, exact support {left}
d: 1/2 worlds, exact support {right}
```

A scalar support-frequency compression maps both nodes to `0.5` and erases the structural distinction.

After a new positive occurrence at `b`:

- `right` is eliminated;
- `left` remains;
- `b` becomes robustly supported;
- `d` becomes excluded in all retained worlds.

Therefore exact world identity is not merely explanatory metadata: it is state required for this exact sequential forecast update.

Additional known-truth tests verify:

- possible and robust forecast sets expand monotonically with a longer horizon under static gates;
- local viability can reject a geographically reachable node without multiplying V/R/P into an opaque occupancy score;
- impossible new positive evidence falsifies the whole declared finite universe;
- robust, possible-expansion and discriminating forecast views remain separate decision summaries.

## Fixed novelty boundary

EOG-WF is **not** positioned as new general mathematics for set-valued forecasting.

Established prior art/comparators include:

- dynamic/time-respecting reachability;
- critical thresholds and stepping stones;
- least-cost/minimum-exposure paths;
- circuit-style redundancy;
- suitable + accessible functional habitat;
- dynamic/mechanistic species-distribution models;
- ensemble forecasting and model averaging;
- Bayesian/credal/imprecise-probability classification in general;
- viability kernels and generic robust reachability;
- history matching / NROY filtering;
- minimum-relaxation/Pareto/falsification frontiers;
- multiverse analysis and generic adaptive survey design.

The candidate contribution is the **biogeographic composition and update state**:

> current positive distributions first filter explicit ecological/analytical transition worlds; surviving exact world identities are then propagated through forecast horizon and retained as the state needed for later occurrence evidence to contract or falsify the prediction universe without post-outcome retuning.

This is narrower and more defensible than claiming novelty for any ingredient alone.

## Core contracts

1. Occurrences are positive realized evidence, not route proof.
2. Anchor/source policy is conditioning information, not inferred ancestry.
3. Mutually exclusive worlds are not silently unioned before inference or forecast.
4. Per-world support remains attached to the generating world through prediction and update.
5. Geographic/IBD-like, environmental/IBE-like and barrier axes remain inspectable unless a one-dimensional family was declared in advance.
6. `Robust` and `excluded` mean over the declared certified universe only.
7. Uncalibrated support is not colonisation, dispersal, occupancy, migration or ancestry probability.
8. Analyst-choice worlds are not called biological process worlds without external calibration.
9. Catalogue non-record is not biological absence without an observation/detection interpretation.
10. Forecast horizons are propagation depth unless independently calibrated to physical time.

## Validation targets

The method audit remains binding. Three questions are distinct.

### A. Algorithmic correctness

Does inverse filtering + world-specific forward propagation + sequential update obey its declared invariants?

Current state: **PASS on known-truth tests and package regression**.

### B. Identity-preserving forecast value

Does exact world identity preserve a predeclared forecast distinction that a scalar/union/mean compression of the same worlds erases, and does later independent evidence discriminate those alternatives?

Current state: **demonstrated on known truth; independently ecological unconfirmed**.

### C. Predictive added value

Does EOG-WF improve genuinely held-out ecological prediction relative to:

- a strong compression of the same frozen world universe; and
- strong external SDM/dynamic/accessibility comparators appropriate to the system?

Current state: **not established**. Earlier frozen A-Islands and Tanzania strong-reference predictive extensions were adverse and remain preserved.

Predictive success would not identify historical truth. Predictive failure would not erase algorithmic correctness, but would bound practical predictive claims.

## World-universe adequacy

Finite enumeration makes the set operations exact but does not make the universe ecologically complete.

Every empirical world dimension must be typed as:

- **natural/process uncertainty**, or
- **analyst-choice uncertainty**.

The contract must state:

1. provenance/calibration;
2. why each level is admissible;
3. which plausible alternatives remain outside coverage;
4. forecast sensitivity to admissible universe expansion;
5. which gates are biological versus sensitivity choices.

Quantile thresholds are acceptable analyst-choice sensitivity levels but are not automatically species dispersal limits or physiological tolerances.

## Frozen validation ledger

### A-Islands — exploratory structural PASS; predictive extension adverse

A response-free explicit-world adapter showed that scalar `connected_frequency` can collapse distinct exact world identities and geography-versus-environment decompositions. Because the system had already been viewed, this is exploratory evidence only.

Separately, the prospectively frozen A-Islands strong-reference predictive extension was adverse. It remains evidence against claiming predictive superiority from that earlier structural augmentation.

### SIVFLORA — independent, non-estimable pre-outcome

The first independent attempt stopped because frozen WorldClim coverage failed at immutable nodes. No outcome model was run and no post-outcome rescue was allowed.

### Azores — independent, non-estimable pre-model

The second independent attempt passed source/node/climate/world/outcome-contract gates, then the once-only taxon estimability gate found zero species satisfying the frozen literal `Tracheophyta` rule.

Frozen status:

`non_estimable_pre_model_taxon_scope_zero`

No Distribution rows were read, no confirmation model was fit, and no confirmation metric was computed. The blocked contract is not reopened.

## Next scientific milestone

The next mainline milestone is **one independently eligible, pre-outcome EOG-WF forecast comparison**. It must be selected by generic eligibility rather than by favourable outcome search.

Before forecast outcomes are opened, freeze:

1. source, node and response semantics;
2. enough genuinely independent spatial or temporal holdout units;
3. local suitability/viability inputs;
4. the finite world universe and adequacy certificate;
5. forecast horizon and gates;
6. same-world scalar/union/mean compression comparators;
7. a strong external SDM/dynamic/accessibility comparator;
8. predictive metrics when a calibrated response exists;
9. a sequential identity-discrimination endpoint;
10. adverse/null/no-added-value stop rules.

Then run once without retuning.

## Repository architecture

- root `eog`: frozen v0.1 compatibility surface;
- `eog.v2`: thin lazy compatibility namespace;
- `eog.v2.reachability`: owns EOG-WF and reachability-facing scientific APIs;
- `eog.v2.traversability`: path/environment diagnostics;
- `eog.v2.validation`: empirical/genetic/directional validation facades;
- `benchmarks/` + `validation/`: system-specific evidence;
- `manuscript/`: frozen earlier structural publication line.

Do not create another facade or public EOG identity for the forecast algorithm.

## Cleanup / stop rules

1. Preserve positive, adverse, blocked, null and indeterminate evidence.
2. Do not add a new operator merely to rescue EOG-WF.
3. Reuse the existing world/transition/state-layer machinery.
4. Do not weaken comparators after outcome inspection.
5. Do not repair SIVFLORA or Azores and relabel them independent confirmations.
6. Do not call a large row count independent replication when holdout units are few.
7. Do not promote support to calibrated probability without calibration.
8. Do not claim universal robustness outside the world-universe certificate.
9. If an independently eligible forecast test is adverse, preserve it and narrow the product claim rather than retuning toward a favourable result.

The development mainline is now **EOG-WF validation and productization**, not additional generic connectivity machinery.
