# Environmental Occupancy Geometry (EOG)

EOG is an auditable biogeographic inference and forecasting framework for asking a broader question than local suitability alone:

> **Given an observed distribution and a declared set of ecological and analytical worlds, which worlds remain compatible, what future/unsampled states do they support, and which predictions survive disagreement among those worlds?**

## Current status

There is **one EOG scientific mainline**.

Current algorithmic status:

> **EOG-WF is implemented and passes known-truth/package tests. Its first independent ecological forecast attempt (STOC) failed because the frozen world universe was structurally inadequate before heldout prediction.**

Frozen STOC status:

> **`independent_world_universe_falsified_on_calibration`**

Therefore EOG-WF still has **no independent confirmation of identity-preserving forecast value or predictive superiority**.

Evidence boundaries:

- **A-Islands**: exploratory exact-world structure preserved information erased by scalar `connected_frequency`; not independent confirmation.
- **A-Islands strong-reference extension**: adverse predictive result.
- **SIVFLORA**: independent attempt stopped pre-outcome on frozen climate coverage.
- **Azores**: independent attempt stopped pre-model on frozen taxonomic-scope incompatibility.
- **STOC**: first independent EOG-WF attempt; all 20 species passed response-class gates but all 20 falsified the frozen 20-world universe during calibration, so no heldout prediction comparison was reached.

Canonical state:

- scientific mainline: [`docs/development_mainline.md`](docs/development_mainline.md)
- forecast algorithm: [`docs/worldset_forecast_algorithm.md`](docs/worldset_forecast_algorithm.md)
- method-validation protocol: [`docs/method_validation_protocol.md`](docs/method_validation_protocol.md)
- implementation / evidence ledger: [`docs/eog_v2_progress.md`](docs/eog_v2_progress.md)
- STOC independent attempt: [`validation/stoc_eogwf/README.md`](validation/stoc_eogwf/README.md)
- Azores independent attempt: [`validation/azores_confirmation/README.md`](validation/azores_confirmation/README.md)

## Scientific center

EOG keeps four objects separate:

1. **local possibility** — locally supported by a declared representation;
2. **reachability** — a declared transition process can reach a state from declared anchors;
3. **distributional realizability** — a distributional state is compatible with a declared world;
4. **historical truth** — what actually happened in nature.

Occurrences are positive realized evidence. They constrain admissible worlds but do not identify one true route, ancestry, colonisation history, migration rate or movement process.

For a declared universe,

```text
W(O) = { declared worlds compatible with observations O }
```

World identity is retained rather than averaged away by default.

## EOG-WF prediction algorithm

```text
current positive occurrences
        ↓
inverse compatible-world reconstruction
        ↓
per-world first-passage propagation through horizon
        ↓
optional separate viability / persistence gates
        ↓
world × horizon × node forecast cube
        ↓
robust / contingent / all-world-excluded projections
        ↓
new positive evidence
        ↓
world contraction or finite-universe falsification
        ↓
revised forecast
```

For every node EOG-WF retains lower/upper reachability support, exact supporting world identities, supporting-world fraction, earliest possible step, earliest all-world step, and `robustly_supported` / `contingent` / `excluded_in_all_worlds` status.

The predictor is `src/eog/v2/world_forecast.py`, exposed lazily through `eog.v2.reachability`.

### Why identity is prediction state

Known-truth fixture:

```text
left:   a -> b -> c
right:  a -> d -> c
```

Given positives `a,c`, both `b` and `d` have scalar frequency 0.5 but exact support `{left}` and `{right}`. A later positive `b` eliminates `right`, making `b` robust and `d` all-world excluded. A scalar-only representation cannot reproduce this exact update after world identity has been discarded.

## First independent stress result: STOC

STOC used 1,003 fixed French breeding-bird monitoring sites, 20 species, calibration `2006-2011`, heldout `2012-2017`, and six environmental inputs from one frozen public source.

Before response access, the contract froze 20 analyst-choice worlds based on q25/q50/q75/q90 nearest-neighbour geographic/environmental thresholds, fixed farthest-first anchors, `max_steps=8`, identity-vs-frequency comparison, strong logistic/RF/ensemble/persistence references, and no-retuning rules.

Authoritative result:

- response-class non-estimability: 0/20 species;
- calibration world-universe falsification: **20/20 species**;
- species reaching heldout predictive modelling: **0/20**;
- identity predictive value: `non_estimable`;
- external predictive added value: `non_estimable`.

Post-hoc diagnosis did not retune STOC. The least fragmented frozen world, `geo_q90`, used an 18.11 km threshold but still had:

- 231 connected components;
- 101 isolated sites;
- largest component only 87/1003 sites = 8.67%;
- median best species target coverage from anchors within eight steps = 8.63%;
- 8,702 positive targets disconnected from all anchors versus only 48 connected targets needing >8 hops.

So the primary failure is **world-graph fragmentation, not horizon length**.

This is a useful adverse result: the algorithm correctly refused to manufacture a forecast after its declared universe was contradicted, but the first generic world-generation recipe is not suitable across spatial scales.

## Response-blind world-universe adequacy gate

The STOC result changes the validation protocol prospectively.

Before future species responses are opened, candidate world graphs must be structurally audited using only node geometry, non-response inputs, external process knowledge and declared horizon. The reusable validator is:

- `src/eog/v2/world_adequacy.py`
- exposed through `eog.v2.validation`.

It reports component structure, isolated nodes, degree summaries and directed horizon-reachable fractions. A caller may apply a prospectively justified `StructuralAdequacyDeclaration`.

**There are no library-default pass thresholds.** Adequacy criteria are study-design declarations, not inferred biological constants. The API intentionally accepts no species/occurrence/response vector.

## What EOG does not claim as new

Do not claim novelty for:

- dynamic/time-respecting reachability;
- critical geographic thresholds and stepping stones;
- least-cost/minimum exposure;
- circuit redundancy;
- suitable + accessible habitat;
- dynamic/mechanistic SDMs;
- ensemble/model averaging;
- Bayesian/credal/set-valued prediction in general;
- viability kernels;
- history matching/NROY;
- Pareto/minimum-relaxation mathematics;
- multiverse analysis or generic adaptive survey design.

The candidate EOG contribution is the domain-specific inverse-to-forward composition in which observed positive distributions filter explicit transition worlds, exact surviving identities remain forecast state, and later evidence contracts or falsifies the frozen universe.

## Claim boundaries

Current status by claim:

- algorithmic correctness: **supported**;
- generic world-universe adequacy: **unresolved; STOC failed**;
- ecological interpretation: **conditional on explicit world/anchor/gate/response contracts**;
- independent identity-preserving forecast value: **unconfirmed**;
- independent predictive superiority: **unconfirmed**;
- historical route/ancestry identification: **not claimed**.

`Robust` and `excluded` always mean within the declared certified universe, not universally true in nature. Uncalibrated support is not occupancy/colonisation probability, and propagation depth is not physical time without calibration.

## Package architecture

Root `eog` preserves the frozen v0.1 compatibility surface. `eog.v2` remains a thin lazy namespace over:

- `eog.v2.reachability`
- `eog.v2.traversability`
- `eog.v2.validation`

EOG-WF stays under reachability. Structural world adequacy stays under validation. No new public EOG identity/facade is created.

## Development rule now

The mainline is:

```text
response-blind source/schema eligibility
        ↓
response-blind world structural adequacy
        ↓
freeze world / forecast / comparator contract
        ↓
open independent response once
        ↓
identity + predictive comparison
```

Do not rescue STOC by increasing thresholds/horizon, changing anchors/species or weakening realization rules. Do not open another dataset merely to obtain a favorable result.

## Repository rules

- Preserve positive, adverse, blocked, null and non-estimable evidence.
- Reuse existing operators/facades before adding modules.
- Keep system-specific validation outside eager package imports.
- Do not infer biological absence without explicit observation/detection semantics.
- Do not return one history when several worlds remain compatible.
- Do not call analyst-choice thresholds biological dispersal/tolerance constants without calibration.
- Do not call uncalibrated support occupancy or colonisation probability.
- Claim strength must not exceed world-universe/response/validation certificates.

## Installation

```bash
python -m pip install .
```

For raster benchmark work:

```bash
python -m pip install ".[raster]"
```

## Scientific boundary

The strongest current claim is:

> **Observed positive distributions can constrain a declared finite set of distribution-forming worlds, and surviving world identities can be propagated as a sequential set-valued forecast; however, an independent forecast is admissible only when the response-blind world universe is itself structurally adequate for the prediction scale.**

## License

MIT.
