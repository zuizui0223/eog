# EOG v2 prospective progress ledger

## Status

This ledger tracks the **single active integrated method line**. Frozen positive, adverse, blocked, null and indeterminate results remain evidence; they are not retuned here.

Current state:

> **EOG-WF is implemented and known-truth validated. Its first independent ecological attempt, STOC, failed because the frozen response-blind world universe was structurally incapable of realizing the calibration distributions for all 20 species. Heldout predictive comparison was never reached.**

Frozen STOC status:

`independent_world_universe_falsified_on_calibration`

Generic operator growth remains stopped. The active phase is now **response-blind world-universe adequacy + independent forecast validation**.

Canonical documents:

- [`worldset_forecast_algorithm.md`](worldset_forecast_algorithm.md)
- [`method_validation_protocol.md`](method_validation_protocol.md)
- [`../validation/stoc_eogwf/README.md`](../validation/stoc_eogwf/README.md)

## Implemented finite architecture

The finite-world engine supports:

- static and temporal reachability;
- inverse compatible-world reconstruction from positive observations;
- world-indexed flow/support sets;
- robust / contingent / all-world-excluded finite-universe classes;
- separate geographic, environmental and barrier axes;
- monotone relaxation and Pareto diagnostics;
- positive-occurrence discrimination;
- EOG-WF inverse-conditioned forecasting through horizon;
- sequential update after new positive evidence;
- finite-universe falsification;
- optional separate viability/persistence gates;
- robust, possible-expansion and discriminating forecast rankings.

The predictor lives at `src/eog/v2/world_forecast.py` on `eog.v2.reachability`.

After the STOC failure, response-blind structural validation infrastructure is also implemented at `src/eog/v2/world_adequacy.py`, exposed through `eog.v2.validation`. It accepts node/world structure and a prospectively declared structural gate, but **no species/response/occurrence input**.

## EOG-WF known-truth state — PASS

Canonical fixture:

```text
left:   a -> b -> c
right:  a -> d -> c
initial positives: a, c
```

`b` and `d` each have scalar support frequency 0.5 but exact identities `{left}` and `{right}`. A later positive `b` eliminates `right`, leaving `b` robust and `d` all-world excluded.

This establishes algorithmic use of exact world identity for sequential update. Horizon monotonicity, separate viability gating and whole-universe falsification are also tested.

## Methodological state

Keep these claims separate:

1. **algorithmic correctness** — supported;
2. **world-universe structural adequacy** — not solved generically; STOC failed;
3. **independent identity-preserving forecast value** — unconfirmed;
4. **predictive added value** — unconfirmed for EOG-WF;
5. **historical identification** — not claimed.

The method does not claim novelty for dynamic reachability, critical distance, least-cost, circuit theory, accessible habitat, dynamic SDMs, ensemble/model averaging, credal/set-valued prediction, viability kernels, NROY/history matching, Pareto/min-relaxation, multiverse analysis or generic adaptive survey design.

## World-universe adequacy correction

Finite enumeration gives exact set operations but does not guarantee that the declared worlds can represent the prediction scale.

Future validation now requires a **response-blind structural gate before species outcomes are opened**. For graph worlds this gate records component count, largest-component fraction, isolated nodes, degree/edge density, horizon reachability and fragmentation caused by intersecting environmental/barrier rules.

There is no library-default pass threshold. A `StructuralAdequacyDeclaration` must be prospectively justified for the target system. This prevents a post-outcome rescue while avoiding a fake universal connectedness rule.

## Empirical validation ledger

### A-Islands

- exact-world structural analysis: exploratory support only;
- separate strong-reference predictive extension: adverse.

### Tanzania

Earlier strong-reference boundary adverse; preserved unchanged.

### SIVFLORA

Independent but non-estimable pre-outcome because frozen climate coverage failed.

### Azores

Independent but non-estimable pre-model because the frozen literal `Tracheophyta` scope yielded zero eligible species. No Distribution rows, model or confirmation metric.

### STOC — first independent EOG-WF attempt

Frozen source:

- `biomodhub/biomod2` tag `v4.3-4-6`;
- exact Git blob `4bfa2cd39a7e90340ad6a319e5c611e8646462c8`;
- 1,003 fixed sites;
- 20 bird species;
- calibration `2006-2011`;
- heldout `2012-2017`;
- six environmental predictors.

Pre-outcome design froze 20 analyst-choice worlds, q25/q50/q75/q90 geographic/environmental nearest-neighbour thresholds, deterministic 10-anchor farthest-first source policy, `max_steps=8`, identity-vs-frequency comparison, strong external SDM/ensemble comparators and no-retuning rules.

Authoritative run `31985291050`:

- 20/20 species passed response-class estimability;
- 20/20 species falsified every declared world during calibration;
- estimable heldout forecast species: 0;
- identity predictive value: `non_estimable`;
- external predictive added value: `non_estimable`;
- result fingerprint: `1ec6e5beb0cfc791b1edec94d14dd416fc14de4426cdc73975a2bbcf388a779b`.

Post-hoc diagnostic `31985516490`, explicitly non-confirmatory:

- least fragmented world = `geo_q90` at 18.1107 km;
- 231 connected components;
- 101 isolated sites;
- largest component = 87/1003 = 8.67%;
- all 20 species' best frozen world = `geo_q90`;
- median best fixed-anchor positive-target coverage within eight steps = 8.63%;
- maximum = 25%;
- disconnected targets across species = 8,702;
- connected but >8 hops = 48.

Diagnosis: **world-graph fragmentation dominates; horizon length is secondary.** Environmental intersection fragments the universe further.

The STOC world family is not retuned or rerun as independent confirmation.

## Repository state

Completed on the STOC validation branch:

- pre-outcome contracts and runtime lock;
- exact source provenance;
- successful independent result preserved;
- post-hoc failure diagnostic preserved;
- one-time validation/diagnostic workflows removed after evidence preservation;
- generic response-blind structural adequacy audit/gate implemented;
- structural-gate tests added;
- canonical method/mainline docs updated.

## Next scientific milestone

Do not search for another dataset merely to obtain a favorable result.

Before any future independent response is opened:

1. source/schema/input/holdout eligibility must pass;
2. the proposed world universe must be constructed response-blind;
3. a prospectively justified structural adequacy declaration must be applied;
4. only a structurally admissible system proceeds to frozen world/forecast/comparator contracts;
5. then the response is opened once without retuning.

The unresolved scientific problem is therefore **prospective construction of ecologically defensible, structurally adequate world universes across spatial scales**, followed by independent EOG-WF prediction testing.

## Stop rule

Do not rescue STOC by changing thresholds, horizon, anchors or species. Do not add generic connectivity machinery simply to make worlds denser. Improve the *prospective design rule* for future world universes, then test it on a genuinely independent eligible system.
