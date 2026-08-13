# EOG v2: dynamic island reachability beyond cellwise suitability

## Status

Prospective method-development line implemented in draft PR #142. This line does **not** modify, rescue, rerun, reinterpret or retune frozen EOG v0.1 A-Islands or Tanzania outcomes.

Frozen boundaries:

- estimand/terminology: `docs/eog_v2_estimand_contract.md`;
- fixed-source occurrence comparator confirmation: `docs/eog_v2_occurrence_comparator_contract.md`.

## Core biological distinction

EOG v2 separates:

- **V** — local viability/environmental support;
- **R** — source-conditioned dynamic reachability support;
- **C** — optional target-capture support;
- **P** — post-arrival establishment/persistence support;
- **O** — observation/detection support when data permit.

Without external calibration, `R` and its first-passage summaries remain model support, not colonisation or migration probabilities.

## Primary domain

Islands and declared habitat patches are the primary nodes. A raster can provide local environmental support or backdrop information, but the required prediction object is a graph. This makes sea gaps, stepping-stone structure, small-island context, and directional movement hypotheses explicit rather than forcing every conclusion into a cellwise map.

## Dynamic EOG-R core

For a directed edge `i -> j`:

`W_ij = K_geo(i,j) * K_env(i,j) * B_ij * D_ij * C_j`.

The implemented operator is explicit-loss and sub-stochastic:

`Q_ij = W_ij / (loss_i + sum_k W_ik)`.

Initial mass is placed on declared sources only; no source reinjection occurs after step zero. Weak or repeated transitions therefore lose support rather than being renormalized into guaranteed arrival.

Implemented outputs include:

- node reachability trajectories;
- finite-horizon first-passage support;
- relative first-arrival depth;
- source attribution;
- integrated edge flux;
- outgoing flux entropy;
- bridge-node importance under frozen-operator blocking;
- separate V/R/C/P/O state layers and mismatch classes.

## Deterministic synthetic archipelagos

Development fixtures cover geography-only structure, environmental isolation, stepping stones, missing intermediates, bottlenecks, redundant routes, area/persistence, directionality, rare long jumps, local extinction, unsurveyed intermediates and multiple sources.

Survey status, current occurrence, historical reach and source status are independent metadata, so an unsurveyed or currently empty island is not silently converted into a barrier.

## Matched endpoint proof of estimand

Holding endpoint environmental support and straight-line endpoint distance fixed:

- open stepping-stone chain: first-passage support `0.2656705539`;
- same-hop severe bottleneck: `0.0375695733`;
- missing intermediate: `0.0`.

Both connected cases first reach the target at propagation step `3`; the difference is transition support, not hop depth.

## Fixed-source occurrence comparator confirmation

A development-informed confirmation was frozen before outcome inspection and executed once on seeds `(907, 1009, 1103, 1201, 1301, 1409, 1511, 1601)`. Contract fingerprint:

`1b2c5e550019c1e73e8f7199dfcc952dfeed3bbbbc3232d173e811fcd21438e6`.

All gates passed. Reference-complete regimes retained simpler methods:

- environment-only: environment = dynamic `0.545359` mean log loss;
- nearest-source: nearest `0.477056`, dynamic `0.680349`;
- source-pressure: pressure `0.472929`, dynamic `0.696843`;
- geography-current-flow: current flow `0.526028`, + dynamic `0.528485`;
- static topology: static `0.517191`, + dynamic `0.518616`.

Dynamic information remained when the truth specifically contained information absent from those references:

- bottleneck: best simple `0.705355` versus dynamic `0.453377`, favourable `8/8` seeds;
- directionality: best simple `0.706028` versus dynamic `0.543223`, favourable `8/8` seeds.

This is synthetic evidence for a conditional estimand, not empirical superiority.

## Genetic validation development

The genetic layer keeps `D_geo` (IBD), `D_env` (IBE), and EOG-derived connectivity distinct. Genetic outcomes are absent from distance constructors.

Development known-truth boundaries already show:

- structured two-chain truth: candidate `D_eog` improves over Euclidean IBD in `8/8` seeds, mean delta MSE `-0.0012208032`;
- geography-only current-flow truth: mean EOG increment `+9.0302e-08` — no added information;
- bottleneck/disconnection omitted from that reference: mean increment `-0.001345032`, favourable `8/8`;
- smooth IBD+IBE truth: strong geography+environment current flow reaches `1.08932e-4` MSE and adding finite-horizon EOG worsens it to `1.09502e-4`.

### Finite-horizon non-identifiability

A 24-candidate development screen over four propagation horizons, three numerical floors and two log-space symmetrisations found **24/24 candidates eligible** under the initial three known-truth boundaries. The toy system therefore did not identify a unique finite horizon. A shortest-step choice would be arbitrary and scale-dependent.

### Exact eventual first-passage genetics

Long-term genetic validation is therefore being separated from finite-horizon colonisation questions. The new exact-eventual implementation solves, for each target,

`h = q_target + Q_without_target h`,

or `h = (I - Q_without_target)^(-1) q_target`.

This sums all direct and indirect first-passage paths under the same lossy frozen operator and removes the propagation-horizon tuning parameter. Directional support remains explicit; genetic symmetrisation is being developed using symmetric and asymmetric neutral-migration truths before it is frozen.

## Remaining gates

1. finish exact-eventual genetic development and freeze one synthetic confirmation contract;
2. run that fresh synthetic genetic confirmation on unused seeds;
3. implement nested self-excluded source-set expansion sensitivity;
4. add dynamic-occupancy comparison where repeated incidence exists;
5. run an independently frozen empirical occurrence benchmark;
6. run an independent empirical genetic validation;
7. implement graph-native dynamic visualisation;
8. make the predeclared method-paper GO/NO-GO decision.

## Hard boundary

Failed, adverse, or no-added-information outcomes are retained. No v2 development step may reopen or weaken frozen v0.1 evidence.
