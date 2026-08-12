# EOG v2 concept: dynamic island reachability beyond cellwise suitability

## Status

Prospective method-development concept. This document does **not** modify, rescue, rerun, reinterpret, or retune the frozen v0.1 structural manuscript outcomes. In particular, the prospectively frozen A-Islands `C − R3` adverse result and the frozen Tanzania strong-reference result remain unchanged.

## Core biological distinction

An observed occurrence is not evidence of local environmental viability alone. Presence at a location reflects a mixture of local environmental conditions, arrival/history, establishment and persistence, biotic effects, sampling and detection. Conventional correlative SDMs mainly summarize the association between observations and local predictors and often return a cellwise suitability/support surface. EOG v2 should explicitly separate:

1. **Viability support** — whether the environmental state at a node is locally compatible with occurrence;
2. **Reachability support** — whether a node is accessible from declared source occurrences through the intervening island network under a declared transition model;
3. **Establishment/persistence support** — whether a reached island is large or otherwise capable of sustaining a population;
4. **Observation/detection** — a separate layer when survey effort or repeat-detection data exist.

Without direct colonisation-time or movement data, `reachability` must remain a model-based support quantity, not a calibrated dispersal or colonisation probability.

## Why islands are the primary domain

Islands are a natural graph domain because island/patch nodes are discrete and interpretable, sea gaps are explicit geographic barriers, very small islands may be smaller than a typical environmental raster cell, island area is a node-level persistence/establishment property, and mainland distance / source proximity / surrounding landmass / stepping-stone structure are naturally graph-level quantities.

The method should not claim that SDMs are generally unsuitable for islands. The narrower claim is that cellwise suitability maps can be awkward for small, discrete archipelagos where reachability and patch-level context are primary scientific questions.

## Proposed model: EOG Reachability Field (EOG-R)

### Node system

Primary nodes are islands or declared habitat patches, not raster cells. Each node carries coordinates/polygon geometry, a local environmental vector, viability support from an independently specified SDM or environmental model, island area and other establishment/persistence covariates, survey/detection metadata where available, and occurrence state only when the node belongs to the current training set. Held-out occurrence labels remain unavailable during feature construction.

### Directed transition support

For each ordered pair `i -> j`, define an unnormalised transition support

`W_ij = K_geo(d_ij) * K_env(e_ij) * B_ij * D_ij`,

where `K_geo` is a predeclared dispersal-distance kernel or scale ensemble, `K_env` describes environmental transition cost / isolation-by-environment support, `B_ij` represents explicit hard or soft barriers, and `D_ij` is an optional directional modifier such as current or prevailing wind that is omitted unless independently justified.

Target-node viability and establishment remain separately reportable instead of being silently folded into the edge.

### Sub-stochastic propagation

Convert `W` into a sub-stochastic transition operator `Q` rather than a fully normalised random walk. A non-zero loss term represents failed dispersal/mortality so that distant or repeatedly difficult routes lose mass instead of guaranteeing eventual arrival.

Initial mass is placed only on outer-training occurrence sources. Propagation yields a graph-supported field over pseudo-time / propagation depth:

`m_(t+1) = Q^T m_t`.

Unless calibrated by independent temporal or movement data, `t` is a propagation step rather than a year and `m` is relative reachability support rather than realised migrant abundance.

### Viability-gated arrival

Maintain separate outputs `R_j(T)` for cumulative reachability support and `V_j` for local viability support. A combined establishment-support quantity may be reported only as a declared composition such as `E_j = f(V_j, R_j, A_j)` and must not be called occupancy probability without calibration.

### Non-cellwise / fluid outputs

The primary prediction object is a dynamic graph, not a raster. Required outputs include node-level viability, node-level reachability curves, relative first-arrival depth, source-attribution distribution, path/bottleneck ensemble, route entropy/redundancy, bridge-node importance, high-viability/low-reachability islands, low-viability/high-reachability islands, and unsurveyed nodes with high hypothesis-discrimination value.

Visualisation should use island nodes, weighted edges, stepped reachability mass, source-attribution ribbons and arrival-depth contours on the archipelago graph. A raster may be shown only as an optional environmental backdrop.

## IBD / IBE / IBR decomposition

Distinguish `D_geo` (geographic isolation / IBD), `D_env` (environmental isolation / IBE), and `D_eog` (effective graph/reachability distance implied by the frozen EOG-R transition network). `D_eog` can be based on effective resistance, commute/first-passage summaries, or negative log reachability; the primary metric must be fixed before genetic validation.

IBE is not treated as a movement model. Environmental differences may affect immigrant survival, reproduction or local adaptation and therefore can generate genetic differentiation independently of geographic distance.

## Genetic validation

Genetic data must not tune the EOG-R network in the first validation. Build and freeze the network from occurrence, geography and environmental information, then test whether its effective distances explain independent genetic differentiation.

For taxa with population-genetic data, compare pairwise genetic distance against: IBD-only `D_geo`; IBD + IBE; IBD + conventional resistance/connectivity where available; and IBD + IBE + frozen `D_eog`. Prefer MLPE, appropriate mixed-effects pairwise models, dbRDA/RDA, GDM or another predeclared framework over relying on partial Mantel tests as the sole primary analysis.

EOG-R may prospectively predict rankings of population-pair isolation, likely genetic discontinuities/bridge zones, source-connectivity groupings and cases where IBD alone should be insufficient. It should not claim exact FST, migration rate, historical colonisation route or demographic history without explicit calibration.

Where feasible, compare frozen EOG-R predictions with EEMS/FEEMS-style effective migration surfaces, resistance models or independently inferred phylogeographic relationships. Agreement is external support; disagreement is informative and must not trigger retuning of the frozen network.

## Simulation programme

Use synthetic archipelagos before empirical genetics. Required scenarios: geographic isolation only; equal geographic distance but strong environmental isolation; stepping-stone chain versus identical endpoint distance without intermediates; one bottleneck versus redundant routes; small high-viability islands with low persistence; directional wind/current dispersal; rare long-distance jumps; local extinction after historical colonisation; unsurveyed intermediates; and multiple source clusters.

Generate occurrence snapshots and, separately, neutral genetic differentiation under known migration networks. Evaluate whether EOG-R recovers relative reachability and whether `D_eog` predicts genetic structure beyond IBD/IBE.

## Competitors

Compare against conventional local-environment SDM/support only, SDM + nearest source distance, incidence-function/metapopulation pressure, least-cost/resistance distance, circuit-theory connectivity, current static EOG connected frequency, and dynamic occupancy/colonisation models when temporal occupancy exists.

EOG-R does not need to outperform all competitors. Its target contribution is to separate viability from source-conditioned reachability and to provide graph-native, leakage-safe, uncertainty-aware predictions for discrete archipelagos.

## Relationship to current EOG

Reuse `island_reachability.py` for frozen graph/source construction, `conditional_reachability.py` for leakage-safe held-out diagnostics, support-topology/bottleneck utilities, hypothesis-discrimination survey code, and fingerprints/manifests. Add separate modules such as `dynamic_island_reachability.py`, `reachability_first_passage.py`, `reachability_genetics.py`, and `benchmarks/dynamic_archipelago_simulation.py`.

Do not change frozen v0.1 manuscript estimands or results.

## Go/no-go for a separate method paper

Proceed only if simulation separates viability from accessibility under known truth, held-out tests show added value in scenarios where intermediate configuration truly matters, the method correctly returns no added information when simpler references are sufficient, at least one independent genetic dataset supports a pre-frozen `D_eog` increment or barrier/bridge prediction, and failure/non-identifiability cases remain explicit.
