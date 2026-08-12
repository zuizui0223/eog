# EOG v2 occurrence-comparator confirmation contract

## Status

This file freezes a **development-informed, outcome-blind confirmation** for the EOG v2 occurrence comparator ladder. The motif design and numerical gates below were chosen after inspection of the development seeds `(101, 211, 307, 401, 503, 601, 701, 809)`. The confirmation seeds `(907, 1009, 1103, 1201, 1301, 1409, 1511, 1601)` are separate and were committed before their outcomes were inspected.

The confirmation was executed once by the dedicated CI workflow and passed all predeclared gates. The frozen contract fingerprint is `1b2c5e550019c1e73e8f7199dfcc952dfeed3bbbbc3232d173e811fcd21438e6`. The successful confirmation artifact was produced by workflow run `31597625261` at source head `b22a53c586c045244aaf65b2ce8e9acc2db66661`.

This benchmark does not alter or rescue the frozen EOG v0.1 A-Islands or Tanzania results. It is synthetic method validation only.

## Question

Can dynamic source-conditioned reachability add held-out occurrence information only when finite-depth path support, bottleneck magnitude, or directionality are part of the known truth, while correctly yielding no material gain when simpler reference models contain the relevant structure?

## Source and target policy

The benchmark deliberately separates **known occurrence sources** from target outcomes. Each synthetic motif contains one or more source nodes that are frozen before any target incidence is generated. Only the target island in each motif receives a response label. Target labels never enter source construction.

This isolates the source-conditioned estimand without self-source leakage. It does **not** yet test a second question: whether adding further positive training targets to the source set improves prediction. Source-set expansion is a separate later sensitivity and must use self-exclusion/cross-fitting.

## Design

- 48 repeated archipelago motifs per regime.
- Six deterministic spatial folds; each fold holds out one motif column across all four structural levels.
- Independent pointwise viability support `V` at every target.
- Fixed L2 logistic calibration (`penalty = 1.0`) applied identically to every comparator.
- Primary score: held-out log loss. Brier score and AUC are secondary diagnostics.
- Fixed source-distance scale: `1.6` synthetic distance units.
- Static component thresholds: `0.05, 0.10, 0.15, 0.20`.
- Dynamic EOG-R horizon: five propagation steps.
- Dynamic loss support: `0.55`.

The synthetic coordinates are only method fixtures. Propagation depth is not a year or biological generation, and dynamic support is not a colonisation probability.

## Comparator ladder

Each candidate is calibrated on exactly the same training target rows and evaluated on the same held-out rows.

1. `environment`: local viability only.
2. `env_nearest`: viability + nearest-source distance support.
3. `env_pressure`: viability + summed incidence/source-pressure kernel.
4. `env_currentflow`: viability + geography-only effective-resistance/current-flow support.
5. `env_static`: viability + multi-threshold static connected frequency.
6. `env_dynamic`: viability + finite-depth EOG-R integrated node support.
7. `env_currentflow_dynamic`: strong geography-current-flow reference + EOG-R.
8. `env_static_dynamic`: static-topology reference + EOG-R.

## Known-truth regimes

### Reference-complete / negative-control regimes

- `environment_only`: response depends on `V` only.
- `nearest_source`: direct source proximity is sufficient.
- `source_pressure`: multiple-source pressure is sufficient while nearest-source support is intentionally uninformative.
- `currentflow`: geography-only route redundancy/effective resistance is sufficient.
- `static_topology`: multi-threshold component support is sufficient; within-category dynamic variation is deliberately removed.

### Dynamic-information regimes

- `dynamic_bottleneck`: direct distance, geography-only current flow, and static component status are held uninformative while a continuous middle-edge bottleneck changes finite-depth propagated support.
- `dynamic_directional`: the undirected/static graph and geography reference are held constant while forward transition support varies; reverse support remains high so a symmetrised static graph cannot recover the directional contrast.

## Development result used to choose the confirmation gates

Mean development-seed log loss showed the intended separation:

| Regime | Relevant simple reference | Mean log loss | Dynamic mean log loss | Interpretation |
|---|---|---:|---:|---|
| environment-only | environment | 0.5113 | 0.5113 | no dynamic information |
| nearest-source | env + nearest | 0.4983 | 0.6626 | direct proximity sufficient |
| source-pressure | env + pressure | 0.4436 | 0.6872 | pressure sufficient |
| current-flow | env + current flow | 0.4499 | 0.4563 | strong geography reference sufficient |
| static-topology | env + static | 0.4423 | 0.4422 | static support sufficient |
| dynamic-bottleneck | best simple = 0.6867 | 0.6867 | 0.3959 | dynamic support adds information |
| dynamic-directional | best simple = 0.6964 | 0.6964 | 0.4906 | dynamic support adds information |

These are development outcomes and are not confirmation evidence.

## Frozen confirmation gates

The confirmation used only the eight predeclared confirmation seeds.

### Required simple-reference signals

The appropriate simple reference had to improve mean log loss over `environment` by at least `0.05` in the nearest-source, source-pressure, current-flow, and static-topology regimes.

### Required no-added-information behaviour

Adding dynamic EOG-R was allowed to improve mean log loss by **at most 0.01** in a reference-complete regime. Equivalently, the dynamic-minus-reference mean log-loss difference had to be `>= -0.01` for environment-only, nearest-source, source-pressure, current-flow after the current-flow reference, and static-topology after the static reference.

### Required dynamic signal

For each of `dynamic_bottleneck` and `dynamic_directional`, `env_dynamic` had to beat the best of environment, nearest-source, source-pressure, current-flow, and static-topology by at least `0.05` mean log loss and beat that seed-specific best simple reference in at least `6/8` confirmation seeds.

All confirmation targets had to be estimable. A one-class training fold or other non-estimability was a failed confirmation, not a reason to silently drop a fold.

## Frozen confirmation result

All gates passed on the predeclared confirmation seeds.

| Regime | Appropriate / best simple reference | Reference mean log loss | Dynamic comparison | Confirmation result |
|---|---|---:|---:|---|
| environment-only | environment | `0.545359` | dynamic `0.545359` | no added information |
| nearest-source | env + nearest | `0.477056` | dynamic `0.680349` | nearest source sufficient |
| source-pressure | env + pressure | `0.472929` | dynamic `0.696843` | source pressure sufficient |
| current-flow | env + current flow | `0.526028` | current flow + dynamic `0.528485` | strong geography reference sufficient |
| static-topology | env + static | `0.517191` | static + dynamic `0.518616` | static topology sufficient |
| dynamic-bottleneck | best simple `0.705355` | `0.705355` | dynamic `0.453377` | dynamic gain `0.251978`, favourable `8/8` |
| dynamic-directional | best simple `0.706028` | `0.706028` | dynamic `0.543223` | dynamic gain `0.162805`, favourable `8/8` |

The exact frozen decision diagnostics were:

- environment-null dynamic increment `0.0`;
- nearest-source signal `0.203293`, dynamic-minus-reference `+0.203293`;
- source-pressure signal `0.223914`, dynamic-minus-reference `+0.223914`;
- current-flow signal `0.181778`, dynamic-minus-reference `+0.00245667`;
- static-topology signal `0.191818`, dynamic-minus-reference `+0.00142546`;
- dynamic-bottleneck gain over best simple reference `0.251978`, favourable seeds `8/8`;
- dynamic-directional gain over best simple reference `0.162805`, favourable seeds `8/8`.

Thus the fixed-source synthetic confirmation supports a narrow claim: finite-depth EOG-R contains information not recovered by the tested pointwise, direct-source, source-pressure, geography-current-flow, or static-connectivity references when the known truth contains intermediate bottleneck magnitude or directionality; it correctly returns no useful increment when those simpler references are sufficient.

## Hard stop

The confirmation result is frozen. Do not change seeds, thresholds, motif levels, fold allocation, or decision tolerances to improve it. A redesigned method must use a new explicit development/confirmation cycle.

## Next scope

Passing this synthetic confirmation does not establish empirical superiority. It justifies proceeding to:

1. self-excluded source-set expansion sensitivity;
2. temporal/dynamic-occupancy comparator work when repeated incidence exists;
3. an independently frozen empirical occurrence benchmark; and
4. the separately frozen genetic-distance confirmation before any empirical genetic outcome is inspected.
