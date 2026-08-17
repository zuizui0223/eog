# EOG development mainline

## Status

This file is the **single source of truth for active scientific development**.

Current empirical state:

> **EOG-WF is algorithmically implemented, but its first independent forecast attempt (STOC) failed at world-universe calibration before heldout prediction. Independent identity-preserving value and predictive superiority remain unconfirmed.**

Frozen STOC status:

> **`independent_world_universe_falsified_on_calibration`**

Current algorithmic state:

> **EOG-WF remains a valid inverse-conditioned, identity-preserving, set-valued forecasting algorithm. The STOC failure reveals that the first generic response-blind world-generation recipe is not structurally adequate across scales.**

Generic operator growth remains stopped. The active scientific mainline is now **world-universe adequacy + independent prediction validation**, not further graph/connectivity invention.

Canonical sources:

- [`worldset_forecast_algorithm.md`](worldset_forecast_algorithm.md)
- [`method_validation_protocol.md`](method_validation_protocol.md)
- [`../validation/stoc_eogwf/README.md`](../validation/stoc_eogwf/README.md)

Frozen earlier empirical contracts remain evidence and are not rewritten to match later protocol improvements.

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

and EOG-WF carries the surviving exact world identities forward into prediction rather than averaging them away.

## EOG-WF: prediction algorithm

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

For each node/horizon EOG-WF retains lower/upper support, exact supporting world IDs, supporting-world fraction, earliest possible step, earliest all-world step, and robust/contingent/excluded status. The world-indexed cube is canonical; scalarization is a declared decision projection, not internal state.

## Known-truth algorithm gate — PASS

Canonical collision fixture:

```text
left:   a -> b -> c
right:  a -> d -> c
```

With positives `a,c`, both worlds survive. `b` and `d` both have scalar frequency 0.5 but exact support `{left}` and `{right}`. A later positive `b` eliminates `right`, making `b` robust and `d` all-world excluded.

Known-truth tests also verify horizon monotonicity, separate local gates, exact world contraction, whole-universe falsification, and distinct robust/possible/discriminating forecast summaries.

Algorithmic correctness therefore remains **supported** after the STOC failure.

## Fixed novelty boundary

EOG-WF is not new general mathematics for set-valued forecasting. Do not claim novelty for dynamic reachability, critical thresholds/stepping stones, least-cost/exposure, circuit redundancy, accessible habitat, dynamic/mechanistic SDMs, ensemble/model averaging, credal prediction, viability kernels, history matching/NROY, Pareto/min-relaxation, multiverse analysis, or generic adaptive survey design.

The candidate contribution remains the biogeographic inverse-to-forward composition:

> current positive distributions filter explicit ecological/analytical transition worlds; surviving exact world identities are propagated through horizon and retained as state for later evidence to contract or falsify the frozen universe without post-outcome retuning.

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
11. A world universe must pass response-blind structural adequacy before species outcomes are opened.

## Validation targets

### A. Algorithmic correctness

Current state: **PASS** on known truth and package regression.

### B. World-universe adequacy

Can the response-blind declared world family represent the intended spatial/horizon scale before species responses are used?

Current state: **not solved generically**. STOC is the first decisive failure.

### C. Identity-preserving forecast value

Does exact world identity preserve a predeclared forecast distinction that scalar/union/mean compression erases, and does later independent evidence discriminate it?

Current state: **known-truth PASS; independent ecological unconfirmed**.

### D. Predictive added value

Does EOG-WF improve genuinely heldout ecological prediction relative to same-world compression and strong external ecological comparators?

Current state: **unconfirmed for EOG-WF**. STOC never reached this comparison.

Predictive success would not identify historical truth. Predictive failure would not erase algorithmic correctness, but would bound practical claims.

## World-universe adequacy

Finite enumeration makes set operations exact but does not make the world universe ecologically or structurally adequate.

Every empirical dimension must be typed as natural/process uncertainty or analyst-choice uncertainty, with provenance, admissibility rationale, missing alternatives and universe-expansion sensitivity recorded.

### Response-blind structural gate

Before species outcomes are opened, candidate worlds must be assessed using only node geometry, non-response environmental inputs, external process knowledge and the declared horizon.

For graph worlds the structural certificate should report at least:

- component count;
- largest-component fraction;
- isolated-node fraction;
- degree/edge-density summaries;
- whether the declared horizon can traverse the intended support;
- whether intersecting environmental/barrier constraints collapse the graph beyond the intended estimand.

There is no universal required connectedness. A fragmented world can be scientifically admissible if fragmentation is itself the intended hypothesis. But at least one prospectively admissible world must be capable of representing the spatial scale required by the forecast claim, or the dataset/world design stops **before response access**.

## Frozen validation ledger

### A-Islands — exploratory structural PASS; predictive extension adverse

Exact world identity preserved distinctions erased by scalar `connected_frequency`, but the system had already been viewed. A separate strong-reference predictive extension was adverse.

### SIVFLORA — independent, non-estimable pre-outcome

Stopped because frozen WorldClim coverage failed at immutable nodes. No outcome model was run and no rescue was allowed.

### Azores — independent, non-estimable pre-model

Passed source/node/climate/world/outcome-contract gates, then stopped because the frozen literal `Tracheophyta` rule yielded zero eligible species. No Distribution rows/model/confirmation metric.

### STOC — independent world-universe falsification before heldout prediction

STOC was selected by a generic metadata-only screen before response access:

- 1,003 fixed French breeding-bird survey sites;
- 20 species;
- `2006-2011` calibration and `2012-2017` heldout periods;
- six environmental predictors;
- exact source bytes frozen from `biomodhub/biomod2` tag `v4.3-4-6`.

The predeclared 20 analyst-choice worlds used nearest-neighbour q25/q50/q75/q90 geographic thresholds plus geography × environment intersections, fixed 10-anchor farthest-first source policy, and `max_steps=8`.

All 20 species satisfied the predeclared response-class estimability thresholds. Nevertheless:

> **20/20 species eliminated every frozen world during calibration.**

No species reached identity-vs-frequency or EOG-vs-SDM heldout prediction. Therefore there is no favorable/null predictive comparison to report; the correct status is `non_estimable` after `declared_world_universe_falsified_on_calibration`.

Post-hoc diagnosis, without retuning STOC, showed the failure is overwhelmingly structural:

- most permissive world `geo_q90`: threshold `18.1107 km`;
- 231 connected components;
- 101 isolated sites;
- largest component 87/1003 = 8.67%;
- all 20 species' best world was `geo_q90`;
- median best calibration-positive target coverage from fixed anchors within eight steps: 8.63%;
- maximum: 25%;
- targets disconnected from all anchors across species: 8,702;
- connected but requiring >8 hops: only 48.

Thus graph fragmentation, not horizon length, is the primary failure mode. Environmental intersections fragmented the graphs further.

Authoritative details: `validation/stoc_eogwf/README.md`.

## Scientific decision after STOC

Do **not** loosen STOC thresholds, increase horizon, change anchor policy, alter species, or reuse STOC as a fresh independent confirmation.

The first independent EOG-WF test therefore changes the development priority:

> **The immediate unsolved problem is prospective world-universe construction/eligibility, not a new reachability operator and not another favorable-data search.**

The next independent outcome test is admissible only after a candidate universe passes the new response-blind structural adequacy gate.

## Repository architecture

- root `eog`: frozen v0.1 compatibility surface;
- `eog.v2`: thin lazy compatibility namespace;
- `eog.v2.reachability`: EOG-WF and reachability-facing scientific APIs;
- `eog.v2.traversability`: path/environment diagnostics;
- `eog.v2.validation`: empirical/genetic/directional validation facades;
- `benchmarks/` + `validation/`: system-specific evidence;
- `manuscript/`: frozen earlier structural publication line.

Do not create another facade or public EOG identity for the forecast algorithm.

## Cleanup / stop rules

1. Preserve positive, adverse, blocked, null and indeterminate evidence.
2. Do not add a new operator merely to rescue EOG-WF.
3. Do not retune an opened world universe and call it independent.
4. Reuse existing world/transition/state-layer machinery.
5. Do not weaken comparators after outcome inspection.
6. Do not repair SIVFLORA, Azores or STOC and relabel them independent confirmations.
7. Do not call a large row count independent replication when holdout units are few.
8. Do not promote support to calibrated probability without calibration.
9. Do not claim universal robustness outside the world-universe certificate.
10. If a future independently eligible forecast test is adverse, preserve it and narrow the claim rather than tune toward a favorable result.

The development mainline is now **response-blind world-universe adequacy → EOG-WF independent validation**, not additional generic connectivity machinery.
