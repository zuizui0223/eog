# EOG v2 prospective estimand and terminology contract

## Status

This contract is frozen **before any empirical genetic validation** of EOG v2. It is a prospective method-development boundary. It does not alter, rerun, rescue, or reinterpret the frozen EOG v0.1 A-Islands or Tanzania results.

## Primary domain and unit

EOG v2 is designed first for discrete archipelagos and declared habitat-patch networks. The primary prediction object is a node-and-edge graph, not a raster cell. A raster may supply local environmental support or visual context, but it is not the required output unit.

## Separate estimands

### V — local viability support

`V_i` is a declared environmental or ecological support quantity for node `i`, usually produced by an independently specified SDM, environmental model, mechanistic model, or expert support surface. `V_i` is **not** redefined as reachability, occupancy probability, demographic persistence, or observation probability.

### R — source-conditioned dynamic reachability support

`R_i(t)` describes relative support propagated from declared training sources to node `i` through a frozen directed transition graph. The transition operator is sub-stochastic: propagation mass may be lost at each step instead of being normalized into guaranteed eventual arrival.

Unless calibrated by independent movement or colonisation-time data:

- `t` is propagation depth, not years or generations;
- `R` is relative reachability support, not dispersal probability;
- finite-horizon first-passage support is not colonisation probability;
- source attribution is not ancestry or historical-route inference.

Finite-horizon `R_i(t)` remains the primary object for colonisation-wave, current reachability and survey questions.

### C — target-capture support

Target-capture support is an optional arrival-side node effect that may represent an explicitly declared interception/target-size hypothesis. Island area can contribute to this layer through a predeclared sensitivity transform. Capture is part of the arrival hypothesis and is **not** persistence.

### P — establishment/persistence support

`P_i` is a separately declared node-level support for post-arrival establishment or persistence. Island area, habitat amount, demographic context, or other patch-level properties may contribute here. `P` is not folded into the reachability transition operator by default.

### O — observation/detection support

Survey effort, repeat-detection information, accessibility, and observation processes belong to a separate `O` layer when data permit. Unsurveyed nodes are not absences and must not be removed from the potential transition graph solely because they lack an occurrence record.

## Directed transition support

For a declared directed edge `i -> j`, EOG v2 keeps transition components auditable:

`W_ij = K_geo(i,j) * K_env(i,j) * B_ij * D_ij * C_j`.

The default dynamic operator is:

`Q_ij = W_ij / (loss_i + sum_k W_ik)`, with `loss_i > 0`.

Every row of `Q` is strictly sub-stochastic, so weak/sparse transitions lose support rather than being renormalized into certain eventual arrival.

## Primary graph-native outputs

EOG v2 may report, under a frozen operator:

- node reachability trajectories;
- finite-horizon first-passage support and relative first-arrival depth;
- source-attribution support;
- integrated edge flux;
- outgoing flux entropy / route diversification;
- bottleneck and alternative-route diagnostics;
- bridge-node importance under frozen-operator node blocking;
- high-V/low-R, low-V/high-R, high-V/high-R, and low-V/low-R states;
- survey candidates whose observation would discriminate declared hypotheses.

These are structural/model-support outputs. They do not by themselves establish a historical dispersal route, gene flow, demographic connectivity, or realised occupancy.

## Genetic-validation quantities

Three information sources remain distinct:

- `D_geo` — geographic isolation / IBD reference;
- `D_env` — environmental isolation / IBE reference;
- `D_eog` — an isolation quantity derived from the frozen EOG-R network.

### Finite-horizon versus long-term genetic reachability

Finite propagation depth is retained for colonisation/reachability questions. Development sensitivity showed that the tested small synthetic archipelago did **not identify a unique finite horizon**: all 24 combinations of horizon, numerical floor and log-space symmetrisation satisfied the initial known-truth boundaries. A shortest-horizon selection would therefore be arbitrary and potentially scale-dependent on larger archipelagos.

For long-term genetic validation, EOG v2 consequently develops a separate **exact eventual first-passage** quantity under the same frozen sub-stochastic operator. For target `j`, non-target first-passage support solves

`h = q_to_j + Q_without_j h`,

so `h = (I - Q_without_j)^(-1) q_to_j`.

Because `Q` is strictly sub-stochastic, this exactly sums direct and arbitrarily long indirect paths while retaining loss, without choosing a propagation horizon. This eventual quantity is still uncalibrated model support, not a migration probability.

Directional eventual support remains separate from the symmetric quantity used for pairwise genetic differentiation. Current development explicitly compares log-space symmetrisations with arithmetic mean support because one-way migration can still exchange genes. The final symmetrisation and disconnected-pair treatment must be frozen in a fresh synthetic confirmation before any empirical genetic outcome is inspected.

Genetic data must not tune the first empirical EOG-R network. IBD, IBE, conventional resistance/current-flow, and other supported references remain explicit competitors.

## Required negative controls

EOG v2 is not promoted by showing improvement only where graph structure was designed to matter. Development and confirmatory evaluation must include regimes where:

- geography alone is sufficient;
- smooth IBD + IBE connectivity is sufficient;
- a stronger conventional resistance/current-flow reference is sufficient;
- local environment, direct source proximity, incidence/source pressure or static topology is sufficient;
- irrelevant graph complexity is present.

The method must be allowed to return no added information or adverse performance in those regimes.

## Terminology prohibited without calibration

Do not call the uncalibrated EOG-R quantities occupancy probability, colonisation probability, dispersal probability, migration rate, realised migrant abundance, demographic connectivity, historical dispersal route, exact ancestry/source population, or predicted FST.

Empirical genetics may validate isolation rankings, discontinuity/bridge hypotheses, or incremental predictive information, but exact demographic quantities require an explicitly calibrated process model.

## Separation from EOG v0.1 and v0.2 development

This v2 contract does not change any frozen v0.1 result or fingerprint. It also remains conceptually separable from the experimental v0.2 static distribution-support fusion: EOG v2's primary object is a dynamic graph field with separately reportable V/R/P/O layers rather than a requirement to collapse them into one cellwise prediction.
