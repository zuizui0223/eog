# Environmental Occupancy Geometry (EOG)

EOG is an auditable biogeographic inference and forecasting framework for asking a broader question than local suitability alone:

> **Given an observed distribution and a declared set of ecological and analytical worlds, which worlds remain compatible, what future/unsampled states do they support, and which predictions survive disagreement among those worlds?**

## Current status

There is **one scientific mainline**.

Current empirical state:

> **EOG-WF completed a prospectively gated independent heldout forecast on the Åland Glanville fritillary metapopulation. Exact world identity was adverse as a direct predictive representation.**

Current product state:

> **Exact world identity is retained as the latent sequential update/falsification state. The default prediction interface is now world-label-invariant and summarizes the surviving support set. Independent validation of this revised two-layer predictive head remains future work.**

The repository does **not** claim generic predictive superiority over SDMs, metapopulation models, occupancy models, ensembles, or other strong comparators.

Canonical state:

- scientific mainline: [`docs/development_mainline.md`](docs/development_mainline.md)
- forecast algorithm: [`docs/worldset_forecast_algorithm.md`](docs/worldset_forecast_algorithm.md)
- two-layer architecture: [`docs/two_layer_forecast_architecture.md`](docs/two_layer_forecast_architecture.md)
- validation protocol: [`docs/method_validation_protocol.md`](docs/method_validation_protocol.md)
- response-blind world-scale design: [`docs/world_universe_scale_design.md`](docs/world_universe_scale_design.md)
- progress ledger: [`docs/eog_v2_progress.md`](docs/eog_v2_progress.md)
- Glanville independent evidence: [`validation/glanville_eogwf/README.md`](validation/glanville_eogwf/README.md)
- STOC independent evidence: [`validation/stoc_eogwf/README.md`](validation/stoc_eogwf/README.md)

## Scientific center

EOG keeps four objects distinct:

1. **local possibility** — locally supported under a declared representation;
2. **reachability** — reachable from declared current sources under a declared transition rule;
3. **distributional realizability** — compatible with observed positive states inside a declared world;
4. **historical truth** — the actual route, sequence, ancestry, movement rate or demographic process in nature.

Observed occurrences are positive realized evidence. They constrain admissible worlds but do not identify one true historical route.

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

## Frozen evidence ledger

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

Do not add another generic connectivity operator merely to make EOG more complex, and do not rerun Glanville with the new prediction summary as though it were independent confirmation.

The next valid scientific milestone is a **fresh independent test of the two-layer EOG-WF architecture**, with the exact latent state, label-invariant prediction representation, external comparator, holdout design and adverse/null rules all frozen before response access.

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
