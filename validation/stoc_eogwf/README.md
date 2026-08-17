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

Workflow `31985198572` successfully:

1. installed the frozen runtime;
2. downloaded the exact source;
3. verified file size and Git blob identity.

It then stopped before modelling because the real CSV uses lowercase `x_wgs84,y_wgs84` while the public documentation/frozen runner used `X_WGS84,Y_WGS84`.

Only a transparent in-memory header-case adapter was added. No source bytes, responses, worlds, thresholds, anchors, horizon, models, metrics or decision rules changed.

## Authoritative independent run

Workflow: `31985291050`  
Artifact: `9273564113`  
Artifact ZIP SHA-256: `a900fada68f61e084e749a1206d7fce397892de41a15ab821a7232e09128aa89`  
Result fingerprint: `1ec6e5beb0cfc791b1edec94d14dd416fc14de4426cdc73975a2bbcf388a779b`

Runtime:

- NumPy `2.1.3`;
- pandas `2.2.3`;
- scikit-learn `1.5.2`.

Outcome:

- response-class non-estimability: **0/20 species**;
- calibration world-universe falsification: **20/20 species**;
- species reaching heldout predictive modelling: **0/20**;
- identity predictive value status: `non_estimable`;
- external predictive added value status: `non_estimable`.

Even the rarest frozen species gate example, *Sylvia melanocephala*, had 58 calibration positives / 945 zeros and 58 heldout positives / 945 zeros. The failure is therefore not caused by insufficient positive/negative responses.

Exact species-level statuses are in `stoc_eogwf_species_summary.csv`; the authoritative result is `stoc_eogwf_result.json`.

## Post-hoc structural diagnosis

The post-outcome diagnostic is explicitly **non-confirmatory**. It did not change or retry the STOC world universe.

Workflow: `31985516490`  
Artifact: `9273640879`  
Artifact ZIP SHA-256: `2439afc62630e6906726c12c474747bc68e9178b2d37b46ea16d2a0ec6c543bd`  
Diagnostic fingerprint: `5aa1885f682663aea28c25877f36b3ea1fb7225bd299d9447a51555928aff453`

The least fragmented frozen world was the most permissive geography-only world, `geo_q90`:

- 231 connected components across 1,003 sites;
- 101 isolated sites;
- largest component: 87 sites, only 8.67% of the site universe;
- mean degree: 3.46;
- median degree: 2.

Adding environmental thresholds made fragmentation substantially worse. For example `geo_q90_env_q90` had 725 components, 588 isolated sites, and a largest component of only 18 sites.

For **all 20 species**, the best frozen world was `geo_q90`, yet fixed-anchor coverage of calibration positive targets within eight steps was:

- median: **8.63%**;
- minimum: **4.46%**;
- maximum: **25.0%**;
- full coverage in any frozen world: **0 species**.

Across the species' best frozen world:

- 8,702 positive targets were in components disconnected from every fixed anchor;
- only 48 targets were connected to an anchor but required more than eight hops.

Therefore the main failure is **graph fragmentation, not the eight-step horizon**.

Compact diagnostic evidence is preserved in `posthoc_failure_diagnostic.json`.

## Scientific interpretation

The independent STOC attempt revealed a critical limitation in the first generic world-generation recipe:

> nearest-neighbour quantiles of monitoring-site spacing are response-blind, but they do not automatically define an ecologically or structurally adequate transition-world universe at the spatial scale of the prediction problem.

The q90 geographic threshold was only 18.11 km across a country-scale 1,003-site system. That produced hundreds of disconnected components before species responses were considered. Environmental intersection only fragmented those graphs further.

This is **not** evidence that exact world identity lacks predictive value, because no species reached that comparison. It is also **not** a successful EOG-WF prediction result.

It is evidence that EOG-WF needs a generic, response-blind **world-universe structural adequacy gate** before response access.

## No-rescue boundary

For this STOC attempt, do not:

- increase geographic/environmental thresholds;
- increase `max_steps`;
- change the anchor count or anchor rule;
- promote compatibility targets into forecast sources;
- weaken the requirement that calibration positives be realizable;
- alter species inclusion;
- change comparator models or favourable rules;
- reuse STOC as a fresh independent confirmation after redesigning worlds.

A future system may use an improved prospectively justified world-universe construction, but STOC remains frozen as the adverse calibration-falsification result above.
