# Environmental Occupancy Geometry (EOG)

EOG is Chapter **N3** of the fixed four-chapter programme:

> **WHERE can it become real?**  
> **住める場所と、辿り着ける場所は違う。**

It is an auditable biogeographic inference and forecasting framework for asking a broader question than local suitability alone:

> Given an observed distribution and a declared set of ecological and analytical worlds, which worlds remain compatible, what future or unsampled states do they support, and which predictions survive disagreement among those worlds?

## Current scientific status

There is **one scientific mainline**.

Current EOG-WF status:

`replicated_candidate_general_predictive_complement`

Two genuinely fresh heterogeneous paired endpoints reached valid favorable heldout results under the unchanged two-layer architecture and unchanged `symmetric_world_support_summary_v1`:

1. **Azores yellow eel telemetry** — augmented same-learner arm won 5/5 heldout blocks; authoritative once-only run `32807155541`.
2. **Southwest Louisiana King Rail passive acoustics** — augmented same-learner arm won 7/8 heldout occasions; authoritative once-only run `32812052801`.

The paper-ready candidate search is now **closed without obtaining a third scored predictive endpoint**. The frozen manuscript funnel contains:

- **2** fresh predictive endpoints with scores;
- **25** protocol-integrity candidate STOPs;
- **2** administrative exclusions.

The third predictive replication is `unresolved_not_obtained` — **not null and not adverse**. The prospectively declared MICA / Australian cassowary / Norway shortlist was exhausted with all three attempts stopping before biological response/model scoring. Issue #357 freezes the decision not to continue screening datasets until a score appears.

Exact world identity remains the latent sequential update/falsification state (**Layer A**). The default predictive interface remains the world-label-invariant surviving-support summary (**Layer B**).

The repository does **not** claim generic predictive superiority over SDMs, metapopulation models, occupancy models, ensembles, or other strong comparators.

Canonical current records:

- chapter spine: [`N1_N4_SPINE.md`](N1_N4_SPINE.md)
- chapter contract: [`CHAPTER_CONTRACT.json`](CHAPTER_CONTRACT.json)
- scientific mainline: [`docs/development_mainline.md`](docs/development_mainline.md)
- forecast algorithm: [`docs/worldset_forecast_algorithm.md`](docs/worldset_forecast_algorithm.md)
- two-layer architecture: [`docs/two_layer_forecast_architecture.md`](docs/two_layer_forecast_architecture.md)
- validation protocol: [`docs/method_validation_protocol.md`](docs/method_validation_protocol.md)
- candidate funnel: [`validation/paper_ready_replication/candidate_flow_ledger.json`](validation/paper_ready_replication/candidate_flow_ledger.json)
- endpoint-3 search closure: [`validation/paper_ready_replication/endpoint3_search_closure.json`](validation/paper_ready_replication/endpoint3_search_closure.json)
- closure rationale: [`manuscript/submission/endpoint3_search_closure_2026-09-03.md`](manuscript/submission/endpoint3_search_closure_2026-09-03.md)
- publication route: [`manuscript/submission/eog_wf_publication_decision_ladder.md`](manuscript/submission/eog_wf_publication_decision_ladder.md)

## Scientific center

EOG keeps four objects distinct:

1. **local possibility** — locally supported under a declared representation;
2. **reachability** — reachable from declared current sources under a declared transition rule;
3. **distributional realizability** — compatible with observed positive states inside a declared world;
4. **historical truth** — the actual route, sequence, ancestry, movement rate or demographic process in nature.

Observed occurrences are positive realized evidence. They can constrain a declared finite world set but do not, by themselves, identify one true historical route.

For finite world universe `W` and positive evidence `O`:

```text
W(O) = {w in W : w is compatible with O}
```

## EOG-WF loop

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

Repeated-transition implementation:

- `src/eog/v2/sequential_world_forecast.py`

These remain lazily exposed through `eog.v2.reachability`.

## Two-layer architecture

### Layer A — exact latent/update state

EOG preserves exact world/rule IDs, fingerprints and per-world support for:

- evidence compatibility;
- sequential rule contraction;
- robust/contingent interpretation;
- finite-universe falsification.

Exact world identity is therefore retained even when it is not useful as a direct supervised feature.

### Layer B — label-invariant predictive representation

Independent Glanville validation showed that exposing arbitrary exact world labels directly to a supervised model was adverse. The predictive interface therefore uses `src/eog/v2/world_predictive_summary.py`.

Version 1 returns ten symmetric world-set features per node/horizon:

- surviving-world fraction;
- support mean and standard deviation;
- minimum and maximum;
- q25, q50 and q75;
- positive-support fraction;
- support range.

The numerical representation is invariant to world-ID renaming and member order while upstream exact-world provenance remains separately auditable. This is not a novelty claim for generic permutation-invariant summaries.

## What the current fresh evidence supports

Supported:

> A label-invariant summary of surviving accessibility-compatible worlds contained non-redundant heldout predictive information beyond the same strong conventional learner in two genuinely fresh heterogeneous observation systems.

Not supported:

- universal predictive superiority;
- standalone Layer-B superiority;
- a third-system replication;
- causal identification;
- truth of any exact Layer-A world;
- recovered dispersal history;
- confirmation of a particular movement/connectivity mechanism from a favorable Layer-B result.

The 25 protocol STOPs are not Layer-B failures. They document where strict prospective source, registry, effort, structural, schema or response-access requirements prevented a valid predictive test.

## Publication and development boundary

Scientific candidate development for this manuscript is **closed**.

The absence of a third score does not authorize more dataset hunting. Continuing after the frozen shortlist was exhausted would turn a bounded replication programme into open-ended data-availability selection.

Primary submission target: **Methods in Ecology and Evolution**.

Conditional fallback: **Ecography** if the final paper is primarily biogeographic/spatiotemporal rather than methodological.

The Nature Ecology & Evolution route is closed for this manuscript because the prospectively required valid favorable third endpoint was not obtained. Do not reopen the science to recover a journal tier.

From this point:

- do not add fresh candidates for this manuscript;
- do not repair or rerun terminal candidates;
- do not add a fourth/prestige dataset;
- do not add generic connectivity operators;
- do not use post-hoc Azores/Louisiana robustness to upgrade the claim;
- move to manuscript figures, evidence tables and submission-package assembly.

The manuscript evidence spine is:

1. **architecture** — local viability versus accessibility-compatible realization;
2. **prospective funnel** — 2 scored / 25 protocol STOPs / 2 administrative exclusions;
3. **paired performance** — Azores and Louisiana shown separately, without pooled significance;
4. **Layer-A / Layer-B decoupling** — structural falsification and predictive complementarity are different inferential objects.

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

> **A prospectively source- and scale-certified set of biogeographic transition worlds is conditioned by positive evidence; exact identities remain auditable sequential update state; a label-invariant projection is used for prediction; later evidence contracts or falsifies the same frozen rule universe without post-outcome retuning.**

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
