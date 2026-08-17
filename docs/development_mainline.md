# EOG development mainline

## Status

This file is the **single source of truth for active scientific development**.

Current empirical state:

> **EOG-WF is algorithmically valid, while the first independent empirical attempt (STOC) falsified its frozen world universe before heldout prediction.**

Current algorithmic/method state:

> **EOG-WF prediction, response-blind world-scale construction, and response-blind structural adequacy certification are implemented. Independent identity-preserving and predictive added value remain unconfirmed.**

Generic operator growth is stopped. The active scientific mainline is now **fresh independent forecast validation after prospective structural certification**.

Canonical method documents:

- [`worldset_forecast_algorithm.md`](worldset_forecast_algorithm.md)
- [`method_validation_protocol.md`](method_validation_protocol.md)
- [`world_universe_scale_design.md`](world_universe_scale_design.md)

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

and EOG-WF carries surviving world identities forward into prediction rather than averaging them away.

## EOG-WF prediction/update loop

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

Exact world identity is prediction state. In the known-truth fixture, two nodes can both have scalar support frequency 0.5 while being supported by mutually exclusive worlds; a later positive observation eliminates one world and changes the two forecasts in opposite directions. This behavior is covered by `tests/test_world_forecast.py`.

## World-universe scale is now a prospective gate

STOC established a method-design failure that occurs **before** prediction quality can be judged: a response-blind threshold rule may still generate worlds at the wrong structural scale for the forecast domain.

The repository therefore separates:

### A. World-scale construction

Preferred route: externally calibrated movement/dispersal/transition scale when scientifically defensible.

Fallback route: prospectively declared **analyst-choice structural scale ladder** using `src/eog/v2/world_scale_ladder.py`.

For each predeclared target largest-component fraction, the ladder selects the minimum metric threshold that reaches that structural regime. This is graph-threshold/percolation prior art used as design discipline, not a new connectivity theorem or biological dispersal estimator.

### B. World-universe structural certification

`src/eog/v2/world_adequacy.py` audits the fully composed world universe before ecological responses are opened. It reports component structure, isolation, degree and horizon reachability, and applies only prospectively declared criteria.

Both scale-construction and adequacy APIs are response-blind by design and accept no species-response vector.

### C. Outcome opening

Only a structurally eligible independent system may proceed to occurrence-conditioned world filtering, identity-vs-compression comparison, and external predictive comparison.

## Fixed novelty boundary

Do not claim novelty for:

- graph threshold filtration, critical connectivity, percolation or minimum spanning trees;
- dynamic/time-respecting reachability;
- stepping-stone or least-cost methods;
- circuit redundancy;
- suitable + accessible functional habitat;
- dynamic/mechanistic SDMs;
- ensemble/model averaging;
- credal/imprecise prediction generally;
- viability kernels;
- history matching/NROY;
- minimum-relaxation/Pareto frontiers;
- multiverse analysis or generic adaptive survey design.

The candidate contribution remains the **biogeographic composition and update state**:

> current positive distributions filter a prospectively scale-certified set of ecological/analytical transition worlds; exact surviving world identities are propagated through forecast horizon and retained as the state needed for later evidence to contract or falsify the prediction universe without post-outcome retuning.

## Validation targets

### 1. Algorithmic correctness

Current state: **PASS** on known-truth tests and package regression.

### 2. Prospective world-universe adequacy

Current infrastructure: **implemented and regression-tested**.

The next independent system must pass this before response access.

### 3. Independent identity-preserving forecast value

Current state: **known-truth PASS; independently ecological unconfirmed**.

### 4. Predictive added value

Current state: **not established**.

A valid comparison requires both:

- matched same-world compression; and
- strong external ecological comparator appropriate to the system.

### 5. Historical identification

Current state: **not claimed**.

## Frozen validation ledger

### A-Islands

Exploratory structural support for exact world identity; separate frozen strong-reference predictive extension adverse. Not independent EOG-WF confirmation.

### SIVFLORA

Independent attempt stopped pre-outcome because frozen climate coverage failed. Not rescued.

### Azores

Independent attempt stopped pre-model under frozen taxonomic scope. Response rows were not scored. Not rescued.

### STOC

First independent EOG-WF forecast attempt.

Status:

`independent_world_universe_falsified_on_calibration`

Authoritative run `31985291050`:

- response-estimability failure: 0/20 species;
- calibration world-universe falsification: 20/20 species;
- heldout prediction: 0/20 species;
- identity predictive endpoint: non-estimable;
- external predictive endpoint: non-estimable.

Post-hoc diagnosis showed the most permissive frozen geography world (`18.1107 km`) still had 231 components and largest component only 8.67% of 1,003 sites. Across species, 8,702 positive targets were disconnected from all fixed anchors while only 48 were connected but beyond the eight-hop horizon. The dominant problem was world-scale fragmentation, not horizon length.

STOC is frozen and cannot be redesigned as independent confirmation.

A response-blind post-hoc method demonstration then showed that the same site geometry has major structural transitions around:

- 20.398 km → LCC 29.8%;
- 24.390 km → 53.0%;
- 34.970 km → 87.0%;
- 41.640 km → 90.0%.

This validates the scale-ladder construction as a structural diagnostic only; it does not change STOC's result.

## Next scientific milestone

Proceed only with a **fresh independent system** that passes all pre-response gates.

Required sequence:

1. immutable source/provenance freeze;
2. node and non-response input freeze;
3. response semantics documented but response content unopened;
4. process-closure/source semantics check — internal anchors must plausibly represent the distribution-forming process, or externally entering source states must be explicitly represented prospectively;
5. response-blind world-scale construction;
6. response-blind structural adequacy gate;
7. forecast horizon/gates/compression/external comparator freeze;
8. one-time response opening;
9. preserve favourable, null, adverse or non-estimable outcomes without rescue.

The **process-closure/source semantics check** is now explicit because a system can have excellent repeated detection data yet still be inappropriate for anchor-conditioned spatial propagation if states are replenished freely from outside the declared node universe.

## Repository architecture

- root `eog`: frozen v0.1 compatibility surface;
- `eog.v2`: thin lazy compatibility namespace;
- `eog.v2.reachability`: EOG-WF and reachability-facing scientific APIs;
- `eog.v2.traversability`: path/environment diagnostics;
- `eog.v2.validation`: empirical validation plus response-blind scale/adequacy infrastructure;
- `benchmarks/` + `validation/`: system-specific evidence;
- `manuscript/`: frozen earlier structural publication line.

Do not create another facade or public EOG identity.

## Cleanup / stop rules

1. Preserve positive, adverse, blocked, null and indeterminate evidence.
2. Do not add a generic operator to rescue EOG-WF.
3. Do not weaken comparators after outcome inspection.
4. Do not repair/reuse STOC, SIVFLORA or Azores as fresh independent confirmation.
5. Do not call structural ladder thresholds biological dispersal constants without external calibration.
6. Do not open ecological response before source/process, scale and structural gates are frozen.
7. Do not promote uncalibrated support to occupancy/colonisation probability.
8. Do not claim universal robustness outside the world-universe certificate.
9. If a fresh structurally eligible independent test is null/adverse, preserve it and narrow the product claim.

The development mainline is now **prospective, structurally certified independent EOG-WF validation**.
