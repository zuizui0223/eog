# EOG v2 concept: dynamic island reachability beyond cellwise suitability

## Status

Prospective method-development concept with executable core and synthetic confirmation in PR #142. This document does **not** modify, rescue, rerun, reinterpret, or retune the frozen v0.1 structural manuscript outcomes. In particular, the prospectively frozen A-Islands `C − R3` adverse result and the frozen Tanzania strong-reference result remain unchanged.

The estimand/terminology boundary is frozen in `docs/eog_v2_estimand_contract.md`. The fixed-source occurrence-comparator confirmation and its one-time result are frozen in `docs/eog_v2_occurrence_comparator_contract.md`.

## Core biological distinction

An observed occurrence is not evidence of local environmental viability alone. Presence at a location reflects a mixture of local environmental conditions, arrival/history, establishment and persistence, biotic effects, sampling and detection. EOG v2 therefore keeps separately reportable:

1. **V — viability support**: local environmental/ecological compatibility;
2. **R — reachability support**: source-conditioned support propagated through a declared island/patch network;
3. **C — target-capture support**: optional arrival-side target-size/interception effect;
4. **P — persistence support**: post-arrival establishment/persistence context;
5. **O — observation/detection support** when survey data permit.

Without direct colonisation-time or movement calibration, `R` is relative model support, not a dispersal or colonisation probability.

## Why islands are the primary domain

Islands are a natural graph domain because island/patch nodes are discrete and interpretable, sea gaps are explicit barriers, small islands can be awkward relative to raster resolution, island area can have distinct arrival and persistence roles, and stepping-stone configuration is naturally a network property.

The method does not claim that SDMs are generally unsuitable for islands. The narrower claim is that cellwise local support can be an incomplete prediction object when source-conditioned reachability and patch-level context are primary questions.

## Implemented EOG Reachability Field (EOG-R)

### Directed transition support

For a declared edge `i -> j`, the executable core stores separate support components:

`W_ij = K_geo(i,j) * K_env(i,j) * B_ij * D_ij * C_j`.

The components represent geographic/dispersal support, environmental-transition support, explicit barrier support, independently justified directionality, and optional target-capture support. Persistence is not silently folded into the edge.

### Sub-stochastic propagation

`W` is converted to an explicit-loss sub-stochastic operator:

`Q_ij = W_ij / (loss_i + sum_k W_ik)`, with `loss_i > 0`.

Initial mass is placed only on declared sources. Propagation is finite-depth and sources are not reinjected after step zero. Thus repeatedly difficult routes lose support instead of being normalized into guaranteed eventual arrival.

### Graph-native outputs

The implementation reports:

- node reachability trajectories and mass decay;
- integrated edge flux;
- absorbing-target finite-horizon first-passage support;
- relative first-arrival depth;
- source-attribution support;
- outgoing flux entropy / route diversification;
- bridge-node importance under frozen-operator node blocking;
- high-V/low-R and related state mismatches;
- separate target-capture and persistence layers.

The primary object is therefore a dynamic graph rather than a required raster map.

## Synthetic archipelago programme

`src/eog/synthetic_archipelago.py` provides deterministic development fixtures for geography-only structure, environmental isolation, stepping-stone and missing-intermediate cases, bottlenecks, redundant routes, island area/persistence, directional dispersal, rare long jumps, local extinction after historical reach, unsurveyed intermediates and multiple sources.

Survey status, current occurrence, historical reach and source status are separate metadata. Lack of an occurrence record does not itself delete a potential transition node.

## Fixed-source occurrence comparator confirmation

The first independent synthetic occurrence confirmation was frozen before outcome inspection and run once on seeds `(907, 1009, 1103, 1201, 1301, 1409, 1511, 1601)`. Contract fingerprint:

`1b2c5e550019c1e73e8f7199dfcc952dfeed3bbbbc3232d173e811fcd21438e6`.

All predeclared gates passed. Reference-complete regimes correctly retained the simpler model:

- environment-only: environment and dynamic both `0.545359` mean log loss;
- nearest-source: nearest `0.477056`, dynamic `0.680349`;
- source-pressure: pressure `0.472929`, dynamic `0.696843`;
- geography-current-flow: current flow `0.526028`, current flow + dynamic `0.528485`;
- static topology: static `0.517191`, static + dynamic `0.518616`.

In contrast, known truths containing information unavailable to those references retained a dynamic signal:

- dynamic bottleneck: best simple `0.705355` versus dynamic `0.453377`, favourable in `8/8` seeds;
- dynamic directionality: best simple `0.706028` versus dynamic `0.543223`, favourable in `8/8` seeds.

This supports only the narrow synthetic claim that finite-depth source-conditioned reachability can contain information beyond local environment, direct source distance, source pressure, geography-only current flow and static connectivity when bottleneck magnitude or directionality is part of the truth. It is not empirical superiority evidence.

## IBD / IBE / genetic validation

The genetic layer keeps three information sources distinct:

- `D_geo`: geographic isolation / IBD;
- `D_env`: environmental isolation / IBE;
- `D_eog`: distance derived from a frozen EOG-R operator.

Directional first-passage distance is separate from the symmetric distance required for pairwise genetic differentiation. Genetic data are absent from the distance constructors and must not tune the first empirical EOG-R network.

Development known-truth results currently show:

- structured two-chain truth: `D_geo + candidate D_eog` improves over Euclidean `D_geo` in `8/8` seeds, mean delta MSE `-0.0012208032`;
- geography-only current-flow truth: EOG increment `+9.0302e-08`, i.e. no mean added information;
- bottleneck/disconnection absent from geography reference: EOG increment `-0.001345032`, favourable `8/8`;
- smooth IBD+IBE truth: geography+environment current flow already reaches mean MSE `1.08932e-4`; adding candidate EOG worsens it to `1.09502e-4`.

A 24-candidate development sensitivity over horizon, support floor and symmetrisation is now being used to select a single metric definition before a fresh synthetic genetic confirmation. No empirical genetic outcome will be inspected before that definition and confirmation contract are frozen.

## Remaining gates

1. complete self-excluded source-set expansion sensitivity;
2. finish the genetic-distance development sensitivity and freeze one `D_eog` definition;
3. run a fresh one-time synthetic genetic confirmation on unused seeds;
4. add temporal/dynamic-occupancy comparison only where repeated incidence data support that estimand;
5. run an independently frozen empirical occurrence benchmark;
6. run at least one independent empirical genetic validation;
7. implement graph-native dynamic visualisation;
8. make a predeclared method-paper GO/NO-GO decision.

## Hard boundary

No v2 development step may reopen or weaken the frozen v0.1 A-Islands or Tanzania evidence. Failed or no-added-information results are retained rather than tuned away.
