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

Islands are a natural graph domain because:

- island/patch nodes are discrete and interpretable;
- sea gaps are explicit geographic barriers;
- very small islands may be smaller than a typical environmental raster cell;
- island area is a node-level persistence/establishment property;
- mainland distance, nearest source, surrounding landmass and stepping-stone structure are naturally graph-level rather than cell-level quantities;
- alternative colonisation routes and source attribution can be represented without forcing predictions onto an arbitrary continuous raster.

The method should not claim that SDMs are generally unsuitable for islands. The narrower claim is that cellwise suitability maps can be awkward for small, discrete archipelagos where reachability and patch-level context are primary scientific questions.

## Proposed model: EOG Reachability Field (EOG-R)

### 1. Node system

Primary nodes are islands or declared habitat patches, not raster cells. Each node `j` carries:

- coordinates / polygon geometry;
- local environmental vector `x_j`;
- viability support `V_j` from an independently specified SDM or environmental model;
- area `A_j` and other establishment/persistence covariates;
- survey/detection metadata where available;
- occurrence state only when the node belongs to the current training set.

All held-out occurrence labels remain unavailable during feature construction.

### 2. Directed transition support

For each ordered pair `i -> j`, define an unnormalised transition support

`W_ij = K_geo(d_ij) * K_env(e_ij) * B_ij * D_ij`,

where:

- `K_geo` is a predeclared dispersal-distance kernel or scale ensemble;
- `K_env` describes environmental transition cost / isolation-by-environment support;
- `B_ij` represents explicit hard or soft barriers such as sea gap or unsuitable matrix;
- `D_ij` is an optional directional modifier (ocean currents, prevailing wind, asymmetric dispersal) and must be omitted unless independently justified.

Target-node viability and establishment are not silently folded into the edge. They remain separately reportable quantities.

### 3. Sub-stochastic propagation

Convert `W` into a sub-stochastic transition operator `Q` rather than a fully normalised random walk. A non-zero loss term represents failed dispersal / mortality so that distant or repeatedly difficult routes lose mass instead of guaranteeing eventual arrival.

Initial mass is placed only on outer-training occurrence sources. Propagation then yields a graph-supported field over pseudo-time / propagation depth:

`m_(t+1) = Q^T m_t`.

Unless calibrated by independent temporal or movement data, `t` is a propagation step, not a year, and `m` is relative reachability support, not realised migrant abundance.

### 4. Viability-gated arrival

Maintain two distinct outputs:

- `R_j(T)`: cumulative reachability support by propagation depth `T`;
- `V_j`: local viability support.

A combined establishment-support quantity may be reported only as a declared composition such as `E_j = f(V_j, R_j, A_j)` and must not be called occupancy probability without calibration.

### 5. Non-cellwise / fluid outputs

The primary prediction object is a dynamic graph, not a raster. Required outputs:

- node-level viability support;
- node-level reachability support curve across propagation depth;
- relative first-passage / arrival-depth summary;
- source-attribution distribution for each target;
- path/bottleneck ensemble rather than one reconstructed historical route;
- route entropy / redundancy;
- bridge-node importance;
- islands with high viability but low reachability;
- islands with low viability but high reachability;
- unresolved unsurveyed nodes with high hypothesis-discrimination value.

Visualisation should use island nodes, weighted edges, animated or stepped reachability mass, source-attribution ribbons and arrival-depth contours on the archipelago graph. A raster may be shown only as an optional environmental backdrop.

## IBD / IBE / IBR decomposition

The model should explicitly distinguish three pairwise quantities between observed populations:

- `D_geo`: geographic isolation (IBD hypothesis);
- `D_env`: environmental isolation (IBE hypothesis);
- `D_eog`: effective graph/reachability distance implied by the frozen EOG-R transition network.

`D_eog` can be represented by effective resistance, commute / first-passage summaries, or negative log reachability. The exact primary metric must be fixed before genetic validation.

IBE is not treated as a dispersal model. Environmental differences may affect immigrant survival, reproduction, or local adaptation and therefore can generate genetic differentiation independently of geographic distance.

## Genetic-structure validation

### Primary validation principle

Genetic data must **not** be used to tune the EOG-R network in the first validation. Build the network from occurrence, geography and environmental information only, freeze it, then ask whether its effective distances explain independent genetic differentiation.

For taxa with population-genetic data, compare pairwise genetic distance (for example `F_ST/(1-F_ST)` or another justified genetic dissimilarity) against:

1. IBD-only: `D_geo`;
2. IBD + IBE: `D_geo + D_env`;
3. IBD + conventional landscape resistance/connectivity where available;
4. IBD + IBE + frozen `D_eog`.

Prefer MLPE, appropriate mixed-effects pairwise models, dbRDA/RDA, GDM or another predeclared framework over relying on partial Mantel tests as the sole primary analysis.

### Genetic predictions EOG-R may legitimately make

Before seeing genetic data, EOG-R may predict:

- ranking of population pairs expected to be more genetically isolated;
- locations of likely genetic discontinuities / bridge zones;
- which populations should share stronger source connectivity;
- whether geography-only IBD should be insufficient;
- whether environmental difference (IBE) or graph reachability adds explanatory power.

It should **not** claim to predict exact `F_ST`, migration rate, historical colonisation route or demographic history without explicit calibration and demographic assumptions.

### Strong external comparison

Where feasible, compare frozen EOG-R predictions with EEMS/FEEMS-style effective migration surfaces, resistance models, or independently inferred phylogeographic relationships. Agreement is external support; disagreement is scientifically informative and must not trigger retuning of the frozen EOG-R network.

## Simulation programme

Use synthetic archipelagos before empirical genetics.

Required scenarios:

1. equal local viability, direct geographic isolation only;
2. equal geographic distances but strong environmental isolation;
3. stepping-stone chain versus same endpoint distance without intermediate islands;
4. one narrow bottleneck versus multiple redundant routes;
5. small high-viability islands with low persistence;
6. directional wind/current dispersal;
7. rare long-distance jump process;
8. local extinction after historical colonisation;
9. unsurveyed intermediate islands;
10. source misidentification / multiple source clusters.

Generate occurrence snapshots and, in a separate simulator, neutral genetic differentiation under known migration networks. Evaluate whether EOG-R recovers relative reachability and whether `D_eog` predicts genetic structure beyond IBD/IBE.

## Required benchmark competitors

- conventional local-environment SDM / support only;
- SDM + nearest source distance;
- incidence-function / metapopulation pressure;
- least-cost / resistance distance;
- circuit-theory connectivity;
- current static EOG connected frequency;
- dynamic occupancy or colonisation model when temporal occupancy is available.

EOG-R does not need to outperform all competitors. Its target contribution is to separate viability from source-conditioned reachability and to provide graph-native, leakage-safe, uncertainty-aware predictions for discrete archipelagos.

## Relationship to the current EOG codebase

Reuse:

- `island_reachability.py` for frozen island graph construction and source anchoring;
- `conditional_reachability.py` for leakage-safe held-out diagnostics;
- support-topology and bottleneck utilities;
- hypothesis-discrimination survey framework;
- fingerprints, manifests and one-time/frozen evidence contracts.

New modules should be separate, for example:

- `dynamic_island_reachability.py`;
- `reachability_first_passage.py`;
- `reachability_genetics.py`;
- `benchmarks/dynamic_archipelago_simulation.py`.

Do not change the frozen v0.1 manuscript estimands or results.

## Go/no-go criteria for a new method paper

A future EOG-R paper becomes methodologically strong only if all of the following hold:

1. simulation shows the dynamic reachability layer separates viability from accessibility under known truth;
2. leakage-safe held-out occurrence tests beat or complement simple source distance in at least the scenarios where intermediate configuration truly matters;
3. the method correctly returns no added information when source distance or conventional resistance is sufficient;
4. at least one independent genetic dataset shows pre-frozen `D_eog` adds information beyond IBD/IBE or correctly predicts a genetic barrier/bridge pattern;
5. failure cases and non-identifiability are reported explicitly.

If these criteria fail, retain EOG-R as an exploratory simulation framework rather than weakening comparators or retuning to obtain a positive result.
