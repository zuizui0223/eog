# EOG v2 prospective progress ledger

## Status

This ledger tracks the **single active integrated method line**. Positive, adverse, blocked, null and non-estimable results remain evidence and are not retuned.

Current empirical phase:

> **first prospectively gated independent EOG-WF heldout forecast completed; exact world identity as a direct predictive representation was adverse.**

Current product phase:

> **exact world/rule identity remains the latent sequential update/falsification state; a world-label-invariant predictive projection is implemented and awaits fresh independent validation.**

Canonical documents:

- [`worldset_forecast_algorithm.md`](worldset_forecast_algorithm.md)
- [`two_layer_forecast_architecture.md`](two_layer_forecast_architecture.md)
- [`method_validation_protocol.md`](method_validation_protocol.md)
- [`world_universe_scale_design.md`](world_universe_scale_design.md)

## Implemented architecture

EOG v2 now includes:

- static/dynamic reachability;
- inverse compatible-world reconstruction;
- exact world-indexed support state;
- robust / contingent / all-world-excluded classes;
- sequential rule contraction and finite-universe falsification;
- changing-current-source sequential forecast with frozen rule identities;
- response-blind structural scale ladders;
- response-blind structural adequacy gates;
- **world-label-invariant predictive summary over exact latent forecast state**.

Main modules:

- `src/eog/v2/world_reconstruction.py`
- `src/eog/v2/world_forecast.py`
- `src/eog/v2/sequential_world_forecast.py`
- `src/eog/v2/world_predictive_summary.py`
- `src/eog/v2/world_scale_ladder.py`
- `src/eog/v2/world_adequacy.py`

No new public facade was created. Prediction-facing APIs remain under `eog.v2.reachability`; prospective validation infrastructure remains under `eog.v2.validation`.

## Two-layer product boundary

### Layer A — exact epistemic/update state

Keep exact world/rule identity for:

- compatibility;
- per-world support;
- evidence-driven rule elimination;
- robust/contingent interpretation;
- finite-universe falsification.

Known-truth tests and the independent Glanville rule history both support this role.

### Layer B — label-invariant predictive state

`world_predictive_summary.py` projects the exact state into ten symmetric features:

1. surviving-world fraction;
2. mean support;
3. support SD;
4. min;
5. max;
6. q25;
7. q50;
8. q75;
9. positive-support fraction;
10. range.

The feature representation is required to be invariant to world ID renaming and member order. Exact latent provenance remains separately fingerprinted.

This is a product-interface revision, not a novelty claim for set summaries/permutation-invariant functions.

## Validation ledger

### A-Islands

Exploratory exact-world structural distinction; not independent. Earlier predictive extension adverse.

### SIVFLORA

Independent pre-outcome non-estimable. Not rescued.

### Azores

Independent pre-model non-estimable. Not rescued.

### STOC

First independent EOG-WF attempt. Response balance passed, but frozen world universe was falsified during calibration for 20/20 species before heldout prediction.

This motivated:

- source/process-closure gate;
- response-blind scale construction;
- structural adequacy gate.

STOC remains frozen.

### Glanville fritillary — first completed independent heldout forecast

System: Åland *Melitaea cinxia* regional patch metapopulation.

Pre-response gates passed:

- source/schema/process closure;
- 4,656-patch frozen node universe;
- external 1-km mean-dispersal reference;
- response-blind structural ladder;
- structural adequacy;
- annual split `1999→2000 ... 2011→2012` calibration and six final heldout transitions;
- IFM/RF comparators;
- exact-identity vs symmetric-compression endpoint;
- response estimability;
- synthetic runner smoke.

A post-open schema correction filtered 755 survey rows / 417 historical IDs outside the frozen node universe. ID-only audit showed none had patch-area records, so the already-frozen finite-positive-area eligibility rule excluded them independently of population response. No world, split, response, metric or comparator changed.

Authoritative run:

- workflow `32017872743`;
- artifact `9284217174`;
- result fingerprint `628511ac3f42fe108d334a6458428bbf56f3c3fea1e753b2bee8d980b3d84c33`;
- calibration rows 35,217, positive colonisations 3,287;
- heldout rows 18,918, positives 900;
- six heldout annual transitions.

Identity was independently estimable beyond the declared compression (`max residual SD = 0.81584`).

Primary macro-year log loss:

| model | log loss |
|---|---:|
| **symmetric same-world compression** | **0.187983** |
| RF | 0.191725 |
| IFM logistic | 0.200242 |
| **exact identity** | **0.230197** |

Exact identity minus compression: **+0.042214**.

Identity beat compression: **0/6** years.

Identity beat the best external model: **1/6** years.

Frozen statuses:

- `adverse_identity_predictive_value`;
- `adverse_external_predictive_added_value`.

Rule contraction remained informative:

- three narrow structural worlds eliminated in `1999→2000`;
- 6.418-km world eliminated in `2010→2011`;
- full exponential process world survived into all heldout forecasts.

Canonical evidence: [`../validation/glanville_eogwf/README.md`](../validation/glanville_eogwf/README.md).

## Scientific consequence of Glanville

Rejected/narrowed claim:

> exact world labels should be the default supervised prediction representation.

Retained claim:

> exact world/rule identity is an auditable latent state for sequential evidence update and falsification.

Prospective product revision:

> prediction should consume a world-label-invariant representation of the surviving support set while exact identities remain behind that interface.

The Glanville compression descriptively had the best tested macro log loss, but external superiority of compression was **not** the prospectively frozen endpoint. It cannot be promoted to confirmed EOG superiority after the fact.

## Current implementation gate

`tests/test_world_predictive_summary.py` now checks:

- frozen ten-feature surface;
- invariance to world renaming;
- invariance to member order;
- horizon-specific projection;
- compatibility with sequential changing-source forecasts;
- no world IDs exposed as predictive columns.

Package-wide regression must remain green before PR #196 is ready.

## Next scientific milestone

Do **not** rerun Glanville with the revised prediction head and do not add a new connectivity primitive.

The next valid step is a **fresh independent test of the two-layer architecture** with pre-response freeze of:

1. source/process closure;
2. world scale and structural adequacy;
3. exact latent rule state;
4. label-invariant predictive representation;
5. strong external comparator;
6. heldout design and metrics;
7. adverse/null/no-added-value rules.

If the revised head is null/adverse, preserve it and narrow the general prediction-product claim further.
