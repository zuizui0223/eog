# SDM and spatial support-topology positioning

## Pointwise support is an input, not an EOG fit

A species-distribution model may estimate relative suitability, occurrence intensity, occurrence probability, or another pointwise quantity depending on its sampling design, likelihood, link function, calibration, and treatment of detection. EOG does not relabel all such outputs as probability and does not fit an SDM.

The spatial support-topology layer accepts a **frozen** two-dimensional support field produced independently by, for example:

- MaxEnt or another presence-background model;
- GLM, GAM, random forest, or ensemble SDM;
- an environmental-distance or analogue model;
- a mechanistic model whose output is suitable as a pointwise support field;
- an expert-defined or rule-based support surface.

Thresholds, neighbourhood rules, masks, occurrence anchors, and held-out detections must be declared without consulting the held-out outcomes used for evaluation.

## Spatial cross-validation is not a dispersal model

Spatial cross-validation changes the evaluation design and can reduce leakage caused by spatial dependence. It does not, by itself, estimate dispersal limitation, island reachability, colonisation history, or demographic connectivity. Dynamic, mechanistic, diffusion, occupancy, and process-based SDMs can model some of those processes; EOG therefore avoids the simplistic claim that “SDMs do not include dispersal.”

The narrower distinction is:

> A standard pointwise support surface does not by itself identify occurrence-anchored components, persistent detached support regions, or competing reachability hypotheses.

Two cells with the same local support value can belong to different structural classes because one lies in an occurrence-anchored superlevel component and the other lies in a detached component separated by unavailable cells or lower-support regions.

## Three related but non-interchangeable EOG layers

### 1. Environmental-state geometry

Input: observed occurrences represented in environmental feature space.

Question: how dispersed, compact, or separated is the observed environmental-state cloud under a declared transformation?

Typical outputs: standardized span, MST compactness, gap diagnostics, shared-reference contrasts.

This layer is not geographical connected-component analysis.

### 2. Spatial support topology

Input: a frozen pointwise support raster or regular grid, a hard availability mask, thresholds, neighbourhood rule, and explicit occurrence-to-cell anchors.

Question: how do superlevel sets decompose into stable occurrence-anchored or detached geographical components?

Typical outputs: component birth threshold, persistence, anchor assignment, lower-threshold merger, cell count or area, support summaries, and held-out component recovery.

This layer is not a path optimizer. It does not calculate shortest paths, weighted paths, minimax bottlenecks, stepping stones, route redundancy, or barrier-cost routes.

### 3. Environmental–geographical bridge inference

Input: declared nodes or components and explicit geographic, environmental, and structural barrier costs.

Question: under which assumptions can a declared source and target be connected, and where are cumulative-cost or minimax bottlenecks?

Typical outputs: minimum cumulative-cost path, minimax path, redundancy, sensitivity, hypothesis-family support, and hypothesis-discriminating survey priorities.

The interface is explicit: support topology may create component summaries or representative nodes that are later supplied to bridge analysis. A component is not automatically a bridge node, and no implicit path is inferred by the topology layer.

## Interpretation limits

EOG support topology does not infer:

- latent occupancy;
- occurrence or colonisation probability;
- abundance or demographic persistence;
- historical dispersal routes;
- genetic or demographic isolation;
- a causal environmental or physical barrier;
- true absence in unobserved gaps.

A `persistent_detached_component` means only that, under the frozen support field, hard mask, threshold sequence, and neighbourhood rule, a detached superlevel component remained identifiable across the declared thresholds. Its ecological meaning requires external evidence.

## Fragmented and island systems

The framework is motivated by fragmented and island landscapes because hard unavailable cells, stepping-stone structure, and repeated high-support regions make local support and spatial structure especially easy to confuse. It is not limited to islands. The same contract applies to terrestrial fragments, river networks represented on suitable grids, urban habitat islands, restoration mosaics, or temporal slices of a frozen geographical support field.

Sea, inaccessible substrate, or excluded domain cells should be represented as unavailable mask cells when they are outside the graph. Encoding them merely as low support answers a different question and may create artificial low-threshold mergers.

## Evaluation

AUC alone is not the primary validation target. Minimum comparisons should include:

1. local support only;
2. distance to the nearest known occurrence;
3. support plus distance;
4. a single-threshold component rule;
5. multi-threshold persistent support topology.

Useful endpoints include held-out occurrence recovery by component class, detection yield among matched-support cells, component-level calibration, stability across thresholds and neighbourhood rules, and island- or region-level complete holdout. Empirical superiority must not be claimed until topology adds information after controlling for local support and geographic distance.
