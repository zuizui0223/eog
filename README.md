# Environmental Occupancy Geometry (EOG)

EOG is an auditable biogeographic inference and forecasting framework for asking a broader question than local suitability alone:

> **Given an observed distribution and a declared set of ecological and analytical worlds, which worlds remain compatible, what future/unsampled states do they support, and which predictions survive disagreement among those worlds?**

## Current status

There is **one EOG scientific mainline**.

Current empirical evidence status:

> **algorithmically valid; first independent EOG-WF attempt stopped because its frozen world universe was structurally inadequate before heldout prediction**

Current algorithmic status:

> **EOG-WF, an inverse-conditioned world-set forecasting algorithm, is implemented and passes known-truth/package tests. Independent predictive superiority is not established.**

The method audit remains in force: method coherence, world-universe adequacy, identity-preserving inferential value, predictive added value, and historical identification are different claims.

- **A-Islands**: response-free exploratory work showed that retaining exact world identity can preserve structure erased by scalar `connected_frequency`; this is not independent confirmation because the system had already been viewed.
- **A-Islands strong-reference predictive extension**: a separate prospectively frozen candidate-vs-R3 test was adverse; it did not establish predictive superiority.
- **SIVFLORA**: independent attempt stopped pre-outcome because the frozen WorldClim representation had nodata at four frozen nodes. It was not rescued.
- **Azores**: independent attempt passed source, node, climate, world-universe and outcome-contract gates, then stopped pre-model because the frozen literal `Tracheophyta` taxon rule yielded zero eligible species. Distribution rows were not read and no predictive model or confirmation metric was computed.
- **STOC**: the first independent EOG-WF forecast attempt reached response estimability but all 20 frozen worlds were falsified during calibration for all 20 species before heldout scoring. Post-hoc diagnosis showed that the broadest frozen geography world had only an 8.67% largest component. STOC is not retuned or reopened.

The repository therefore does **not** currently claim that EOG-WF outperforms strong SDM, dynamic-SDM, occupancy, dispersal, ensemble, or credal-model comparators on independent ecological data.

Canonical project state:

- scientific mainline: [`docs/development_mainline.md`](docs/development_mainline.md)
- forecast algorithm: [`docs/worldset_forecast_algorithm.md`](docs/worldset_forecast_algorithm.md)
- method-validation protocol: [`docs/method_validation_protocol.md`](docs/method_validation_protocol.md)
- response-blind world scale design: [`docs/world_universe_scale_design.md`](docs/world_universe_scale_design.md)
- implementation / prior-art ledger: [`docs/eog_v2_progress.md`](docs/eog_v2_progress.md)
- package boundary: [`docs/eog_v2_package_layout.md`](docs/eog_v2_package_layout.md)
- frozen evidence: [`docs/evidence_ledger.md`](docs/evidence_ledger.md), [`docs/claim_matrix.md`](docs/claim_matrix.md)
- Azores independent-attempt evidence: [`validation/azores_confirmation/README.md`](validation/azores_confirmation/README.md)
- STOC independent-attempt evidence: [`validation/stoc_eogwf/README.md`](validation/stoc_eogwf/README.md)

## Scientific center

EOG keeps four objects separate:

1. **local possibility** — a state is locally supported by a declared representation;
2. **reachability** — a declared transition process can reach that state from a declared anchor/source set;
3. **distributional realizability** — a distributional state is compatible with a declared world;
4. **historical truth** — what actually happened in nature.

Occurrences are realized positive states. They constrain admissible worlds but do not identify one true route, colonisation history, ancestry, migration rate or movement process.

For a declared world universe,

```text
W(O) = { declared worlds compatible with observations O }
```

World identity is retained rather than averaged away by default.

## EOG-WF prediction algorithm

EOG-WF turns the inverse finite-world core into a forward prediction/update loop:

```text
current positive occurrences
        ↓
inverse compatible-world reconstruction
        ↓
per-world first-passage propagation through horizon
        ↓
optional separate viability / persistence gates
        ↓
robust / contingent / all-world-excluded forecast cube
        ↓
new positive evidence
        ↓
world contraction or finite-universe falsification
        ↓
revised forecast
```

The canonical output is **world × horizon × node**, not one flat scalar raster.

For every node EOG-WF retains:

- lower and upper cumulative reachability support across compatible worlds;
- exact world identities supporting the node;
- the fraction of compatible worlds supporting it;
- earliest step supported by any world;
- earliest step supported by all retained worlds, when such a step exists;
- final status: `robustly_supported`, `contingent`, or `excluded_in_all_worlds`.

The predictor is implemented in `src/eog/v2/world_forecast.py` and exposed lazily through `eog.v2.reachability`.

### Why identity is predictive state, not decoration

The known-truth test contains two worlds:

```text
left:   a -> b -> c
right:  a -> d -> c
```

Given positive observations `a` and `c`, both worlds survive. At the same horizon, both `b` and `d` have scalar support frequency `0.5`, but `b` is supported by `{left}` and `d` by `{right}`.

After a new positive observation at `b`, `{right}` is eliminated. The revised forecast makes `b` robust and `d` all-world excluded.

A frequency-only or averaged representation cannot reproduce this exact sequential update because it discarded which world produced each support state. This is the algorithmic role of world identity.

## Response-blind world-universe construction

STOC exposed that **response-blind does not automatically mean structurally adequate**. A world rule can avoid outcome leakage yet still live at the wrong spatial scale for the forecast domain.

Future independent EOG-WF work therefore separates:

1. **world scale construction** — use externally calibrated process distances when justified, otherwise build predeclared analyst-choice structural scale ladders;
2. **structural adequacy certification** — audit components, isolation and directed horizon reach before response access;
3. **outcome validation** — only after the world universe passes the prospective structural gate.

The generic implementation lives in:

- `src/eog/v2/world_scale_ladder.py`
- `src/eog/v2/world_adequacy.py`

The scale-ladder and adequacy APIs accept no species-response vector. Structural thresholds derived from node geometry remain analyst-choice scales unless independently calibrated as biological dispersal/process parameters.

## What EOG does not claim as new

The prior-art audit removes generic novelty claims for:

- dynamic / time-respecting reachability;
- critical geographic thresholds and stepping stones;
- graph threshold filtration, percolation thresholds or minimum spanning trees;
- least-cost / minimum cumulative environmental exposure;
- circuit-style multiple-path redundancy;
- suitability + accessibility / functional habitat;
- consensus / ensemble prediction;
- Bayesian model averaging or credal/set-valued classification in general;
- viability kernels or generic robust reachability;
- history matching / NROY filtering;
- minimum-relaxation / Pareto falsification-frontier mathematics;
- multiverse analysis or adaptive survey design in general.

These are established operators, prediction paradigms, or comparators.

## Remaining contribution hypothesis

The active algorithmic hypothesis is now:

> **A biogeographic forecast can preserve more actionable structural information when observed occurrences first constrain an explicit, prospectively scale-certified set of ecological/analytical transition worlds, and the surviving world identities are carried forward as prediction state so that future observations contract or falsify those worlds instead of requiring premature averaging or post-outcome retuning.**

This is a domain-specific composition claim, not a claim of new general mathematics for set-valued prediction or graph connectivity.

The method audit separates three empirical questions:

1. **world-universe adequacy** — was the candidate world set structurally capable of representing the declared forecast scale before responses were opened?;
2. **identity-preserving inferential value** — does exact world identity retain an independently testable distinction that a predeclared compression of the same worlds erases?;
3. **predictive added value** — does EOG-WF improve genuinely held-out prediction over matched same-world compression and external ecological comparators?

The first now has reusable prospective infrastructure. The latter two remain independently unconfirmed.

## Robust, contingent and excluded structure

Within an explicitly declared finite universe, EOG distinguishes future/unsampled structure that is:

- supported in every compatible world;
- contingent on ecological or analytical representation;
- unsupported in every enumerated compatible world.

`Robust` and `excluded` mean robust/excluded over the **declared certified universe**, not universally true in nature.

World-universe adequacy is therefore part of the method. Empirical worlds must distinguish biologically intended process uncertainty from analyst-choice sensitivity worlds and state which plausible alternatives lie outside the certificate.

## Watershed language

The watershed vocabulary remains an interpretation of the forecast geometry:

- occurrence = realized anchor;
- basin = reachable set under a declared world;
- channel / tributary = supported transition sequence;
- confluence = reconvergence;
- bottleneck = critical transition/state;
- divide = reachability boundary;
- horizon = propagation depth unless externally calibrated to time;
- `lambda` = a predeclared one-dimensional monotone relaxation coordinate only.

Geographic/IBD-like, environmental/IBE-like and barrier axes remain separate unless a one-dimensional family was declared in advance.

## Package architecture

Root `eog` preserves the frozen v0.1 compatibility surface. `eog.v2` remains a thin lazy namespace over:

- `eog.v2.reachability`
- `eog.v2.traversability`
- `eog.v2.validation`

EOG-WF lives under the existing reachability facade. Response-blind world adequacy and scale-construction utilities live on the existing validation facade. No fourth public facade or parallel EOG identity is created.

System-specific validation code belongs in `benchmarks/`, `validation/` and tests.

## Development rule now

The mainline is now **prospective independent validation of the implemented predictor using a structurally certified world universe**, not generic operator growth.

Do not add another graph/path/connectivity primitive merely to make EOG look more complex. A valid future empirical test must predeclare:

- source, nodes, response semantics and independent holdout;
- the world universe and its ecological/analytical scale certificate;
- local viability/persistence inputs and forecast gates when used;
- a response-blind structural adequacy gate;
- a same-world scalar/union/mean compression comparator;
- a strong external SDM/dynamic/accessibility comparator appropriate to the system;
- predictive scoring and an identity-preserving sequential-update endpoint;
- a no-added-value rule accepted without retuning.

## Repository rules

- Preserve adverse, null, blocked and indeterminate evidence.
- Reuse existing operators/facades before adding modules.
- Keep system-specific validation outside eager package imports.
- Do not infer biological absence without an explicit response/detection interpretation.
- Do not return one history when several worlds remain compatible.
- Do not call analyst-choice thresholds biological dispersal/tolerance constants without external calibration.
- Do not call uncalibrated support occupancy or colonisation probability.
- Do not use a large number of bootstrap draws to disguise a small number of genuinely independent holdout units.
- Claim strength must not exceed coverage/certificate strength.

## Installation

```bash
python -m pip install .
```

For raster benchmark work:

```bash
python -m pip install ".[raster]"
```

## Scientific boundary

EOG-WF is now an implemented prediction algorithm, but its support values remain model-conditioned diagnostics unless externally calibrated.

The strongest current claim is:

> **Observed positive distributions can constrain a prospectively scale-certified finite set of distribution-forming worlds, and the surviving world identities can be propagated forward as a sequential set-valued forecast that is updated or falsified by later positive evidence.**

Independent ecological predictive superiority remains to be demonstrated.

## License

MIT.
