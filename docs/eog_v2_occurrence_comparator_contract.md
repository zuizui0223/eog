# EOG v2 occurrence-comparator confirmation contract

## Status

This file freezes a **development-informed, outcome-blind confirmation** for the EOG v2 occurrence comparator ladder. The motif design and numerical gates were chosen after inspection of development seeds `(101, 211, 307, 401, 503, 601, 701, 809)`. Confirmation seeds `(907, 1009, 1103, 1201, 1301, 1409, 1511, 1601)` were committed before their outcomes were inspected.

The confirmation was executed once by the dedicated CI workflow and passed all predeclared gates. Contract fingerprint:

`1b2c5e550019c1e73e8f7199dfcc952dfeed3bbbbc3232d173e811fcd21438e6`.

Successful workflow run: `31597625261`; source head: `b22a53c586c045244aaf65b2ce8e9acc2db66661`; artifact digest: `sha256:f77d020cd2617d45894662bfc8f7fd88e522866832f4ae7dc6cd378d2d1479e7`.

This is synthetic method validation only and does not alter or rescue frozen EOG v0.1 results.

## Question

Can dynamic source-conditioned reachability add held-out occurrence information only when finite-depth path support, bottleneck magnitude, or directionality are part of the known truth, while correctly yielding no material gain when simpler references contain the relevant structure?

## Source and target policy

Each synthetic motif contains frozen known occurrence source nodes. Only target islands receive response labels, and target labels never enter source construction. This isolates the source-conditioned estimand without self-source leakage.

This confirmation does **not** test source-set expansion from additional positive training targets. That is a separate nested self-exclusion sensitivity.

## Design

- 48 motifs per regime;
- six deterministic spatial folds;
- independent target viability support `V`;
- common deterministic L2 logistic calibration, penalty `1.0`;
- primary score: held-out log loss; Brier and AUC secondary;
- source-distance scale `1.6` synthetic units;
- static thresholds `0.05, 0.10, 0.15, 0.20`;
- dynamic horizon five propagation steps;
- dynamic loss support `0.55`.

## Comparator ladder

1. `environment` — local viability only;
2. `env_nearest` — viability + nearest-source support;
3. `env_pressure` — viability + summed source-pressure kernel;
4. `env_currentflow` — viability + geography-only effective-resistance/current-flow support;
5. `env_static` — viability + multi-threshold static connected frequency;
6. `env_dynamic` — viability + finite-depth EOG-R integrated node support;
7. `env_currentflow_dynamic` — strong geography-current-flow reference + EOG-R;
8. `env_static_dynamic` — static-topology reference + EOG-R.

## Known-truth regimes

Reference-complete negative controls: `environment_only`, `nearest_source`, `source_pressure`, `currentflow`, `static_topology`.

Dynamic-information regimes: `dynamic_bottleneck` and `dynamic_directional`.

## Frozen confirmation gates

- appropriate simple reference improves environment-only by at least `0.05` where its signal is the truth;
- dynamic EOG-R may improve a reference-complete regime by at most `0.01` mean log loss;
- in each dynamic-information regime, dynamic must beat the best simple reference by at least `0.05` mean log loss and in at least `6/8` seeds;
- all folds must remain estimable.

## Frozen confirmation result

All gates passed.

| Regime | Appropriate / best simple reference | Reference log loss | Dynamic comparison | Result |
|---|---|---:|---:|---|
| environment-only | environment | `0.545359` | dynamic `0.545359` | no added information |
| nearest-source | env + nearest | `0.477056` | dynamic `0.680349` | nearest source sufficient |
| source-pressure | env + pressure | `0.472929` | dynamic `0.696843` | source pressure sufficient |
| current-flow | env + current flow | `0.526028` | current flow + dynamic `0.528485` | current flow sufficient |
| static-topology | env + static | `0.517191` | static + dynamic `0.518616` | static topology sufficient |
| dynamic-bottleneck | best simple `0.705355` | `0.705355` | dynamic `0.453377` | gain `0.251978`, `8/8` favourable |
| dynamic-directional | best simple `0.706028` | `0.706028` | dynamic `0.543223` | gain `0.162805`, `8/8` favourable |

Exact decision diagnostics:

- environment-null dynamic increment `0.0`;
- nearest-source signal `0.203293`, dynamic-minus-reference `+0.203293`;
- source-pressure signal `0.223914`, dynamic-minus-reference `+0.223914`;
- current-flow signal `0.181778`, dynamic-minus-reference `+0.00245667`;
- static-topology signal `0.191818`, dynamic-minus-reference `+0.00142546`;
- dynamic-bottleneck gain `0.251978`, favourable `8/8`;
- dynamic-directional gain `0.162805`, favourable `8/8`.

The defensible synthetic claim is therefore narrow: finite-depth EOG-R adds information beyond the tested local-environment, direct-source, source-pressure, geography-current-flow and static-connectivity references when bottleneck magnitude or directionality is part of the known truth, while correctly yielding no useful increment when simpler references are sufficient.

## Hard stop

The confirmation result is frozen. Seeds, thresholds, motif levels, fold allocation and decision tolerances must not be changed to improve the result.

## Next scope

1. nested self-excluded source-set expansion sensitivity;
2. dynamic-occupancy comparison when repeated incidence supports that estimand;
3. independently frozen empirical occurrence benchmark;
4. separately frozen genetic-distance confirmation before empirical genetic outcomes.
