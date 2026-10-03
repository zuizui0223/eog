# Environmental Occupancy Geometry (EOG)

EOG is an auditable biogeographic inference and forecasting framework for asking a broader question than local suitability alone:

> **Given an observed distribution and a declared set of ecological and analytical worlds, which worlds remain compatible, what future/unsampled states do they support, and which predictions survive disagreement among those worlds?**

## Current status

There is **one scientific mainline**.

Current empirical state:

> **The paper-ready fresh programme is closed with three valid paired predictive endpoints under the unchanged `symmetric_world_support_summary_v1`: Azores yellow eel and Southwest Louisiana King Rail are favorable, while Tampa Bay seagrass is adverse. The preregistered endpoint-3 mapping therefore fixes the supported boundary at `structural_diagnostic_plus_context_dependent_predictive_complement`.**

Current product state:

> **Layer A remains the exact auditable world-compatibility / contraction / falsification state. Layer B remains the unchanged world-label-invariant support summary, but its added predictive value is explicitly context dependent rather than uniformly beneficial. Candidate hunting is hard-stopped after the valid Tampa endpoint.**

The repository does **not** claim generic predictive superiority over SDMs, metapopulation models, occupancy models, ensembles, or other strong comparators.

Canonical state:

- scientific mainline: [`docs/development_mainline.md`](docs/development_mainline.md)
- active post-closure virtual-world programme: validation/eog_original_idea_virtual_worlds_v1/protocol_v1.json
- forecast algorithm: [`docs/worldset_forecast_algorithm.md`](docs/worldset_forecast_algorithm.md)
- two-layer architecture: [`docs/two_layer_forecast_architecture.md`](docs/two_layer_forecast_architecture.md)
- validation protocol: [`docs/method_validation_protocol.md`](docs/method_validation_protocol.md)
- response-blind world-scale design: [`docs/world_universe_scale_design.md`](docs/world_universe_scale_design.md)
- progress ledger: [`docs/eog_v2_progress.md`](docs/eog_v2_progress.md)
- active scientific issue and closure ledger: [issue #141](https://github.com/zuizui0223/eog/issues/141)
- third-endpoint pre-response boundary: [`manuscript/third_fresh_endpoint_selection_boundary_2026-08-27.md`](manuscript/third_fresh_endpoint_selection_boundary_2026-08-27.md)
- publication decision ladder and hard stop: [`manuscript/submission/eog_wf_publication_decision_ladder.md`](manuscript/submission/eog_wf_publication_decision_ladder.md)
- manuscript candidate funnel: [`validation/paper_ready_replication/candidate_flow_ledger.json`](validation/paper_ready_replication/candidate_flow_ledger.json)
- Glanville independent evidence: [`validation/glanville_eogwf/README.md`](validation/glanville_eogwf/README.md)
- STOC independent evidence: [`validation/stoc_eogwf/README.md`](validation/stoc_eogwf/README.md)

## Scientific center

EOG keeps four objects distinct:

1. **local possibility** — locally supported under a declared representation;
2. **reachability** — reachable from declared current sources under a declared transition rule;
3. **distributional realizability** — compatible with observed positive states inside a declared world;
4. **historical truth** — the actual route, sequence, ancestry, movement rate or demographic process in nature.

Observed occurrences are positive realized evidence. They constrain admissible worlds but do not identify one true historical route.

The active post-closure scientific programme uses BAM and related finite virtual worlds
to test the original EOG ideas under known truth.  The target claims are not BAM
decomposition counts alone: the programme explicitly tests viability versus
reachability, pathwise IBE-like continuity, stepping stones, bottlenecks, alternative
distribution histories, temporal contraction and robust impossibility.  BAM supplies
the A/B/M mechanism coordinates; dynamic reachability and temporal world machinery
supply the history-level quantities when required.

For finite world universe `W` and positive evidence `O`:

```text
W(O) = {w in W : w is compatible with O}
```

## EOG-WF

The core loop is:

```text
positive observations
    ↓
compatible-world reconstruction
    ↓
per-world forward propagation
    ↓
world × horizon × node support state
    ↓
possible / robust / unresolved / finite-world-excluded projection
    ↓
new positive evidence
    ↓
world contraction or finite-universe falsification
```

Static implementation:

- `src/eog/v2/world_reconstruction.py`
- `src/eog/v2/world_forecast.py`

Repeated-transition implementation with changing current sources and frozen rules:

- `src/eog/v2/sequential_world_forecast.py`

All remain lazily exposed through `eog.v2.reachability`.

For the exhaustively retained compatible-world set, `possible` is the union of
per-world reachable nodes, `robust` is their intersection, `unresolved` is the
possible-minus-robust disagreement set, and `robustly unreachable` is the complement
inside the declared node universe. `compare_world_flow_universes` verifies the exact
set-inclusion contract when a fingerprint-preserving compatible-world universe is
expanded; these labels remain conditional on the declared finite universe.

## Two-layer prediction architecture

### Layer A — exact latent/update state

EOG preserves exact world/rule IDs, fingerprints and per-world support for:

- evidence compatibility;
- sequential rule contraction;
- robust/contingent interpretation;
- finite-universe falsification.

Exact identity is therefore **not discarded**.

### Layer B — label-invariant predictive representation

Independent Glanville validation showed that exposing exact world labels directly to a supervised predictive model was adverse.

The default prediction representation now uses:

`src/eog/v2/world_predictive_summary.py`

Version 1 returns ten symmetric world-set features per node/horizon:

- surviving-world fraction;
- support mean and standard deviation;
- minimum and maximum;
- q25, q50 and q75;
- positive-support fraction;
- support range.

The numerical predictive representation is invariant to world ID renaming and member order. The exact upstream forecast fingerprint remains separately auditable.

This is **not** a novelty claim for permutation-invariant set functions or statistical summaries.

## Independent Glanville result

The Glanville system passed source/process, response-blind world-scale, structural-adequacy, temporal-split and response-balance gates before the authoritative heldout result was interpreted.

Authoritative run: `32017872743`  
Result fingerprint: `628511ac3f42fe108d334a6458428bbf56f3c3fea1e753b2bee8d980b3d84c33`

Primary macro-year binary log loss:

| model/representation | log loss |
|---|---:|
| **same-world symmetric compression** | **0.187983** |
| random forest | 0.191725 |
| IFM logistic | 0.200242 |
| **exact world identity** | **0.230197** |

Exact identity was worse than compression by `+0.042214` log-loss units and lost to compression in **6/6 heldout annual transitions**.

Frozen statuses:

- `adverse_identity_predictive_value`
- `adverse_external_predictive_added_value`

The exact rule state nevertheless eliminated four truncated structural worlds during calibration and retained the full exponential process world. This is why exact identity stays in Layer A even though direct identity features are removed from the default Layer-B interface.

The descriptive success of the frozen compression is **not** retroactive confirmation of external EOG superiority: that was not the prospectively declared external endpoint. The revised prediction head requires a fresh independent test.

## Prospective world-universe gates

STOC had previously shown that response-blind thresholds can still occupy the wrong structural scale. EOG therefore requires before response access:

1. process/source-closure justification;
2. externally calibrated process scales when defensible;
3. otherwise response-blind structural scale ladders;
4. response-blind structural adequacy certification.

Implementations:

- `src/eog/v2/world_scale_ladder.py`
- `src/eog/v2/world_adequacy.py`

These APIs do not accept species-response vectors. Structurally derived thresholds remain analyst-choice scales unless externally biologically calibrated.

## Current fresh two-layer evidence

- **Azores yellow eel telemetry** — favorable paired complementarity; baseline macro log loss `0.1422727`, augmented `0.1322871`, delta `-0.0099856`; augmented won 5/5 heldout blocks; run `32807155541`.
- **Southwest Louisiana King Rail passive acoustics** — favorable paired complementarity; baseline `0.2463173`, augmented `0.2453455`, delta `-0.0009718`; augmented won 7/8 heldout occasions; run `32812052801`.
- **Tampa Bay seagrass transect monitoring** — valid adverse endpoint 3; baseline `0.3377354`, augmented `0.4387640`, delta `+0.1010287` (~29.9% higher log loss); baseline won 4/5 folds; run `34028447227`. The 20-replicate ten-feature placebo median (`0.3361758`) also outperformed the real augmented arm.

The manuscript-facing denominator is now **3 scored predictive endpoints / 31 scientific-protocol STOPs / 3 administrative exclusions**. STOPs remain methods-integrity evidence rather than negative Layer-B results.

The preregistered adverse mapping fixes the product boundary at:

`structural_diagnostic_plus_context_dependent_predictive_complement`

This supports Layer A as a structural falsification framework and shows that Layer B can add predictive information in some systems but is not uniformly beneficial. It does not support universal superiority, a standalone Layer-B predictor, causal identification, or the truth of an exact Layer-A world.

Candidate hunting is closed. No fourth dataset may be added to improve the apparent result or journal rank.

## Post-closure known-truth programme and EOG v3

A separate simulation/theory programme is developed **outside the frozen EOG-WF
empirical denominator**. It does not add a fourth endpoint or change the MEE
submission claim.

The current known-truth result is:

> **Occurrence data are useful for finite-world falsification, but even complete
> positive distributions need not identify the generating A/B/M mechanism. EOG
> therefore keeps unresolved worlds explicit and uses their differences to design
> the next observation, calibration or intervention.**

Key frozen results include:

- complete positive occurrences uniquely identified **0/64** truths in the first BAM factorial;
- after orthogonal A/B/M activation, unique recovery remained **0/64** from positives,
  **2/64** with perfect negatives and **6/64** with occupied-node arrival times;
- across **12 deterministic systems / 768 truths**, positive-only BAM-state uniqueness
  remained **0/768**;
- an independent stochastic generator reproduced non-identification and showed that
  stronger joint A+B+M restriction can create **more**, not less, positive-only ambiguity;
- time-stamped occurrence history can refine static support, while unordered accumulated
  positive history need not;
- imperfect detection is an explicit observation-world axis: finite nondetection at
  `p < 1` is low-probability evidence, not exact absence;
- exact finite evidence design can return a minimum discriminating intervention set,
  or fail closed when the declared evidence library is insufficient;
- adaptive planning separates worst-case experimental burden from the realized path.

### Experimental EOG v3 API

EOG v3 represents:

```text
ecological worlds × observation-process worlds
                    ↓ evidence
           surviving joint worlds
                    ↓
 ecological / observation projections
                    ↓
 robust or adaptive next-evidence design
```

Commands:

```bash
eog-v3-joint-evaluate \
  --input examples/eog_v3/joint_evaluation_input.json \
  --output joint_result.json

eog-v3-plan-evidence \
  --input examples/eog_v3/evidence_planning_input.json \
  --output evidence_plan.json \
  --objective ecological

eog-v3-plan-adaptive \
  --input examples/eog_v3/evidence_planning_input.json \
  --output adaptive_plan.json
```

Canonical post-closure state:

- [`docs/known_truth_development_mainline.md`](docs/known_truth_development_mainline.md)
- [`validation/known_truth_programme_manifest_v1.json`](validation/known_truth_programme_manifest_v1.json)
- [`docs/eog_v3_joint_world_engine.md`](docs/eog_v3_joint_world_engine.md)

**Boundary:** surviving v3 worlds are compatible hypotheses inside declared finite
ecological/observation universes. They are not certified historical truth.

## Historical evidence ledger

- **A-Islands** — exploratory exact-world structural information; not independent confirmation; earlier predictive extension adverse.
- **SIVFLORA** — independent pre-outcome non-estimable; not rescued.
- **Azores** — independent pre-model non-estimable; not rescued.
- **STOC** — independent world universe falsified before prediction; motivated structural scale/adequacy gates; not rescued.
- **Glanville** — first completed independent heldout EOG-WF test; direct exact-identity prediction adverse; drives current two-layer architecture.

## What EOG does not claim as new

The prior-art boundary excludes generic novelty claims for:

- graph threshold filtration, percolation, MST or critical connectivity;
- dynamic/time-respecting reachability;
- stepping-stone, least-cost or circuit methods;
- suitability + accessibility / functional habitat;
- dynamic/mechanistic SDMs;
- model averaging and ensembles;
- permutation-invariant set functions or generic uncertainty summaries;
- Bayesian/credal/imprecise prediction generally;
- viability kernels;
- history matching/NROY;
- Pareto/minimum-relaxation frontiers;
- multiverse analysis and generic adaptive survey design.

The candidate contribution is narrower:

> **a prospectively source- and scale-certified set of biogeographic transition worlds is conditioned by positive evidence; exact identities remain auditable sequential update state; a label-invariant projection is used for prediction; later evidence contracts or falsifies the same frozen rule universe without post-outcome retuning.**

## Development rule

The paper-ready fresh replication programme is scientifically closed. A valid third predictive terminal was reached in Tampa Bay and was adverse under the frozen decision rule.

Therefore:

- do not search for a fourth or prestige-driven favorable dataset;
- do not repair or rerun any consumed fresh endpoint;
- do not add generic connectivity operators to rescue predictive performance;
- keep Layer A and `symmetric_world_support_summary_v1` unchanged for the manuscript evidence;
- complete the already-frozen cross-ecosystem synthesis, endpoint-wise performance figure, candidate-funnel evidence table, Methods/Results text, and submission package.

The observed product boundary is `structural_diagnostic_plus_context_dependent_predictive_complement`. The default strong submission route is **Methods in Ecology and Evolution**; the Nature Ecology & Evolution trigger is closed by the adverse third endpoint.

Public API/CLI/package-surface freeze follows manuscript scientific closure rather than reopening model development.

## Package architecture

Root `eog` preserves the v0.1 compatibility surface. `eog.v2` stays thin and lazy over:

- `eog.v2.reachability`
- `eog.v2.traversability`
- `eog.v2.validation`

No fourth public facade or parallel EOG identity is introduced.

## Installation

```bash
python -m pip install .
```

For raster work:

```bash
python -m pip install ".[raster]"
```

## License

MIT.
