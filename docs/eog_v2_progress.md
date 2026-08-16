# EOG v2 prospective progress ledger

## Status

This ledger tracks the **single active integrated method line**. Frozen positive, adverse, blocked, null and indeterminate results remain evidence; they are not retuned here.

Current empirical phase:

> **exploratory-supported but independently unconfirmed**

Current algorithmic phase:

> **EOG-WF inverse-conditioned world-set forecasting is implemented and known-truth validated; independent ecological predictive value remains unresolved.**

Generic operator growth is stopped. The active phase is forecast validation and productization.

Canonical algorithm and validation documents:

- [`worldset_forecast_algorithm.md`](worldset_forecast_algorithm.md)
- [`method_validation_protocol.md`](method_validation_protocol.md)

## Implemented finite architecture

The finite-world engine now supports:

- exact static and temporal reachability;
- inverse compatible-world reconstruction from positive observations;
- world-indexed support/flow sets;
- finite-universe robust / contingent / all-world-excluded classes;
- separate geographic, environmental and barrier axes;
- declared one-dimensional monotone relaxation families;
- minimum-relaxation/Pareto diagnostics;
- positive-occurrence discrimination among underidentified worlds;
- temporal support, corridor and transition summaries;
- **inverse-conditioned world-set forecasting through propagation horizon**;
- **sequential forecast updating after new positive evidence**;
- **finite-world-universe falsification when no declared world survives**;
- optional separate viability and persistence forecast gates;
- robust, possible-expansion and world-discriminating forecast rankings.

The world-set forecast implementation is `src/eog/v2/world_forecast.py` and remains on the existing lazy `eog.v2.reachability` facade.

## EOG-WF algorithm state

The predictor takes current positive observations `O`, reconstructs the exact compatible subset `W(O)`, propagates each retained world separately, and returns a `world × horizon × node` forecast cube.

For each node/horizon it reports:

- exact supporting world IDs;
- lower/upper cumulative first-passage support;
- supporting-world fraction;
- robust/contingent/excluded class;
- earliest possible support step;
- earliest all-world support step when present.

When new positive evidence is added, the same frozen world universe is reconstructed again. The world set may stay equal, contract, or be fully falsified. The update cannot create new worlds and does not retune the transition definitions.

### Known-truth identity-update gate — PASS

Fixture:

```text
left:   a -> b -> c
right:  a -> d -> c
observed initially: a, c
```

At the forecast horizon, `b` and `d` each have scalar world-support frequency `0.5`, but exact identities differ:

```text
b -> {left}
d -> {right}
```

Adding a new positive observation at `b` eliminates `right`, leaves `left`, makes `b` robust and makes `d` excluded in all retained worlds.

This demonstrates the algorithmic point: a scalar world-frequency compression can erase state needed for the exact sequential forecast update.

Additional tests verify horizon monotonicity, finite-universe falsification, separate viability gating and the three forecast-ranking modes.

## Prior-art boundary

| Established comparator / prior art | EOG-WF boundary |
|---|---|
| endpoint/final-horizon/scalar summaries | exact horizon/world identity is retained as forecast state |
| static/dynamic graph reachability | reused operator; not EOG novelty |
| critical distance / stepping stones | prior art |
| least-cost / minimum exposure | prior art |
| circuit redundancy | prior art |
| suitable + accessible functional habitat | prior art |
| dynamic/mechanistic SDMs | prior art; must be an external comparator when relevant |
| ensemble forecasting/model averaging | prior art; EOG-WF does not claim novelty for multiple-model prediction |
| Bayesian/credal/imprecise classification | set-valued prediction itself is prior art |
| viability kernels / generic robust reachability | prior art |
| history matching / NROY | compatibility filtering is prior art |
| minimum-relaxation / Pareto frontiers | prior art |
| multiverse analysis | retaining analyst-choice alternatives is not by itself novelty |
| adaptive survey design | generic discrimination ranking is not by itself novelty |

The active contribution hypothesis is therefore a **biogeographic inverse-to-forward composition**:

> positive observed distributions constrain explicit ecological/analytical transition worlds; exact surviving world identities are retained through horizon as prediction state; later positive evidence contracts or falsifies those worlds without post-outcome retuning.

## Methodological audit remains binding

Algorithm correctness, identity-preserving forecast value, predictive superiority and historical identification are distinct.

### 1. Algorithm correctness

Current state: **supported** by known-truth tests and package regression.

### 2. Independent identity-preserving forecast value

Question: does exact world identity preserve a predeclared forecast distinction erased by scalar/union/mean compression, and does genuinely independent evidence discriminate those alternatives?

Current state: **known-truth PASS; independent ecology unconfirmed**.

### 3. Predictive added value

Question: does EOG-WF improve held-out prediction over matched same-world compression and appropriate strong external ecological predictors?

Current state: **not established**. Frozen earlier strong-reference extensions include adverse evidence.

### 4. Historical identification

Current state: **not claimed**.

## World-universe adequacy boundary

A finite world universe makes set operations exact but does not make the universe ecologically complete.

Every empirical world dimension must be typed as:

- **natural/process uncertainty**, or
- **analyst-choice uncertainty**.

Quantile thresholds, product choices, preprocessing alternatives and uncalibrated graph thresholds remain analyst-choice worlds unless externally calibrated as biological process parameters.

Every empirical forecast must record:

- provenance/calibration;
- admissible level rationale;
- plausible alternatives outside the certificate;
- universe-expansion sensitivity;
- forecast-gate semantics;
- whether horizon has physical-time calibration.

## Empirical validation ledger

### A-Islands — exploratory structural support

The response-free 12-world adapter showed that exact world identity and geography-vs-environment decomposition can retain distinctions erased by scalar `connected_frequency`. A-Islands had already been viewed, so this remains exploratory.

### A-Islands — frozen strong-reference predictive extension adverse

A separate prospectively frozen predictive extension compared candidate `C` with strong island-isolation reference `R3`. The primary held-out log-loss contrast was adverse. It remains evidence against predictive-superiority claims for that earlier augmentation.

It is not retroactively relabelled as an EOG-WF forecast test.

### Tanzania — frozen strong-reference boundary adverse

The earlier external strong-reference boundary likewise did not establish predictive superiority and remains preserved rather than retuned.

### SIVFLORA — independent, blocked pre-outcome

The frozen independent design stopped before outcome modelling because WorldClim coverage failed at immutable nodes. No rescue was allowed.

### Azores — independent, blocked pre-model

Azores passed source, node, climate, exact 20-world and outcome-contract gates, then the once-only estimability run found zero species satisfying the frozen literal `Tracheophyta` scope.

Authoritative facts remain:

- 15,256 canonical taxa;
- 8,078 canonical species;
- 2,455 canonical Plantae species;
- eligible under frozen literal `Tracheophyta` rule: **0**;
- Distribution rows read: **0**;
- response scored: **false**;
- predictive models fitted: **false**;
- confirmation metric computed: **false**.

Status: `non_estimable_pre_model_taxon_scope_zero`.

This source is not repaired and relabelled independent confirmation.

## Response/absence boundary

Catalogue non-record may be a negative class only for an explicitly stated catalogue-record target. It is not biological absence by default.

Occupancy, failed colonisation, extinction or unsuitable-habitat claims require an appropriate observation/detection or survey-completeness interpretation.

EOG-WF itself can operate on positive occurrence evidence alone; calibrated binary prediction claims require stronger response semantics.

## Dependence / validation-unit boundary

Validation units must match the intended generalisation. Many species-island rows do not create many independent islands.

A large number of bootstrap draws does not replace independent outer units. Small-cluster confirmatory inference requires design-specific pre-outcome calibration/simulation or must be reported descriptively.

## Next independent forecast gate

A future EOG-WF test is admissible only through a generic pre-outcome eligibility screen.

Before EOG-specific forecast outcomes are opened, require:

1. exact source identity and provenance;
2. unambiguous nodes/spatial units;
3. environmental/local-state input coverage;
4. deterministic taxonomic/response semantics;
5. enough genuinely independent spatial or temporal holdouts;
6. frozen world universe and adequacy certificate;
7. frozen forecast horizon and local gates;
8. same-world scalar/mean/union compression comparator;
9. strong external SDM/dynamic/accessibility comparator appropriate to the system;
10. predictive and identity-update endpoints plus no-added-value stop rules.

Then run once without retuning.

## Repository state

Completed:

- one active EOG narrative;
- lazy root/v2 compatibility surfaces;
- explicit reachability/traversability/validation owners;
- prior-art claims separated from candidate contribution;
- durable preservation of adverse/blocked validation evidence;
- EOG-WF implemented on the existing reachability facade;
- known-truth sequential-update tests added;
- prediction algorithm documented without creating a new EOG namespace.

Still conservative:

- frozen reproduction modules are not deleted without reference audit;
- historical branch refs are not active scientific lines merely because they exist.

## Stop rule

Do not add more generic connectivity machinery merely to make EOG-WF richer. The mainline is now **independent validation of the implemented forecast algorithm**.

If the next eligible empirical test is null/adverse, preserve it and narrow the prediction-product claim rather than retuning toward a favourable result.
