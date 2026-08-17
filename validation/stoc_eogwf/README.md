# STOC independent EOG-WF validation

## Final status

> **`independent_world_universe_falsified_on_calibration`**

This is the first independent EOG-WF forecast-validation attempt after the prediction algorithm was merged to `main`.

It did **not** reach heldout predictive comparison. The predeclared 20-world universe was falsified by the calibration-period positive distribution for **20/20 species** before any identity-vs-frequency or EOG-vs-SDM result could be estimated.

This result is preserved as an adverse world-universe adequacy result. It must not be rescued by retuning the opened STOC dataset.

## Frozen source

- dataset: DataSTOC / French Breeding Bird Survey STOC distributed by `biomodhub/biomod2`;
- immutable ref: `v4.3-4-6`;
- path: `inst/external/DATA_biomod2_STOC.csv`;
- Git blob SHA-1: `4bfa2cd39a7e90340ad6a319e5c611e8646462c8`;
- byte size: `330891`;
- source SHA-256 observed in the frozen run: `f8d6a01d31f03ca73c261309d39f7bb1d395b346b26141b2ef0acf49b06297f7`;
- rows: 2,006;
- fixed sites: 1,003;
- species: 20;
- periods: `2006-2011` calibration, `2012-2017` heldout.

## Pre-outcome design

The design was frozen before DataSTOC response values were fetched for EOG-WF.

Durable contracts:

- `eligibility_and_preoutcome_contract.json` — source, response, species gate, worlds, anchor rule, comparators and stop rules;
- `preoutcome_amendment_v1_1.json` — exact-world identity vs frequency-only prediction endpoint;
- `preoutcome_amendment_v1_2.json` — calibration-frozen thresholds with period-specific environmental operators;
- `preoutcome_amendment_v1_3.json` — fixed-anchor source policy aligned to merged EOG-WF semantics;
- `runtime_lock.txt` — frozen NumPy/Pandas/scikit-learn versions.

Key frozen choices:

- 20 analyst-choice sensitivity worlds: 4 geography-only + 16 geography × environment;
- geographic and environmental cutoffs: q25/q50/q75/q90 of calibration-period nearest-neighbour distances;
- fixed deterministic farthest-first anchor set, up to 10 calibration positives per species;
- all remaining calibration positives are compatibility targets;
- a world survives only if every compatibility target is reachable from the fixed anchors within `max_steps=8`;
- no heldout retuning;
- if worlds survive, compare exact world-bit identity against frequency-only compression and against frozen logistic/RF/ensemble/persistence references.

The geographic cutoffs frozen from the 1,003 sites were:

- q25: `5.648102238104288 km`;
- q50: `8.920388642088314 km`;
- q75: `13.95901805792781 km`;
- q90: `18.110714907817556 km`.

## First technical attempt

Workflow `31985198572` successfully installed the frozen runtime, downloaded the exact source and verified file size/Git blob identity. It then stopped before modelling because the real CSV uses lowercase `x_wgs84,y_wgs84` while the public documentation/frozen runner used uppercase labels.

Only a transparent in-memory header-case adapter was added. No source bytes, responses, worlds, thresholds, anchors, horizon, models, metrics or decision rules changed.

## Authoritative independent run

Workflow: `31985291050`  
Artifact: `9273564113`  
Artifact ZIP SHA-256: `a900fada68f61e084e749a1206d7fce397892de41a15ab821a7232e09128aa89`  
Result fingerprint: `1ec6e5beb0cfc791b1edec94d14dd416fc14de4426cdc73975a2bbcf388a779b`

Outcome:

- response-class non-estimability: **0/20 species**;
- calibration world-universe falsification: **20/20 species**;
- species reaching heldout predictive modelling: **0/20**;
- identity predictive value status: `non_estimable`;
- external predictive added value status: `non_estimable`.

Exact species-level statuses are in `stoc_eogwf_species_summary.csv`; the authoritative result is `stoc_eogwf_result.json`.

## Post-hoc structural diagnosis

The post-outcome diagnostic is explicitly **non-confirmatory**. It did not change or retry the STOC world universe.

Workflow: `31985516490`  
Artifact: `9273640879`  
Artifact ZIP SHA-256: `2439afc62630e6906726c12c474747bc68e9178b2d37b46ea16d2a0ec6c543bd`  
Diagnostic fingerprint: `5aa1885f682663aea28c25877f36b3ea1fb7225bd299d9447a51555928aff453`

The least fragmented frozen world was `geo_q90`:

- 231 connected components across 1,003 sites;
- 101 isolated sites;
- largest component: 87 sites, only 8.67% of the site universe;
- mean degree: 3.46;
- median degree: 2.

Adding environmental thresholds fragmented the graph further. Across species' best world, 8,702 calibration-positive targets were disconnected from every fixed anchor, while only 48 were connected but beyond the eight-hop horizon. Thus the main failure is **graph fragmentation, not horizon length**.

Compact diagnostic evidence is preserved in `posthoc_failure_diagnostic.json`.

## Prospective method correction

The independent STOC attempt revealed:

> **response-blind is necessary but not sufficient; a candidate world universe can avoid outcome leakage and still occupy the wrong structural scale for the intended forecast.**

The repository now contains:

- `src/eog/v2/world_scale_ladder.py` — response-blind local-to-spanning scale construction when no externally calibrated process distance is defensible;
- `src/eog/v2/world_adequacy.py` — response-blind structural certification before ecological outcomes are opened;
- `docs/world_universe_scale_design.md` — canonical prospective design rules.

Neither validation API accepts a species-response vector. Structurally derived thresholds remain analyst-choice worlds unless external biological evidence calibrates them.

## STOC response-blind scale-ladder demonstration — method evidence only

After STOC was already frozen as failed, a separate post-hoc demonstration explicitly parsed only site IDs, period, coordinates and environmental columns. Species-response columns were not parsed.

With demonstration targets 0.25 / 0.50 / 0.75 / 0.90, the geography ladder was:

- `20.398 km` -> largest component **29.8%**;
- `24.390 km` -> **53.0%**;
- `34.970 km` -> **87.0%**;
- `41.640 km` -> **90.0%**.

The jump from approximately `24.4 km / 53%` to `35.0 km / 87%` shows a major structural transition that the frozen `18.11 km` q90 nearest-neighbour world did not bracket.

Durable evidence:

- `posthoc_scale_ladder_declaration.json`;
- `posthoc_scale_ladder_result.json`;
- `posthoc_scale_ladder_provenance.json`;
- result fingerprint `2e04d84f29b0ec71e66cec43ecb047e783c1ebcab3a78da625635d54413dcc3c`;
- workflow run `32013352759`;
- artifact `9282581381`;
- artifact ZIP SHA-256 `c2d5bd06f78a6eb1ddf40d8307f9cc02cf358e06b9c2e945d37a0a57aa13c119`.

This is method evidence only. It cannot replace the frozen STOC worlds or relabel STOC as independent confirmation.

## No-rescue boundary

Do not increase STOC thresholds/horizon, alter anchors/species/realization rules, change comparators/metrics, or rerun a redesigned STOC universe as independent confirmation.

The next independent system must pass a prospectively declared response-blind scale-construction + structural-adequacy gate **before its ecological response is opened**.
