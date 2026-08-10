# Structural competitor matrix and novelty boundary

## Purpose

This document prevents the structural manuscript from claiming novelty merely because it uses spatial blocks, graph nodes, shortest paths, resistance surfaces, current flow, or occurrence anchors. All of those ideas have substantial prior literature.

The defensible contribution is narrower:

> EOG makes local environmental support, direct source proximity, occurrence-anchored graph configuration, and stronger landscape-specific connectivity models separate executable quantities, then tests the structural increment under frozen held-out contracts.

The table is a positioning tool, not a ranking. A method can be more appropriate than EOG when its estimand matches the biological question and its data requirements are met.

## Method-family comparison

| Method family | Primary estimand or task | Where spatial structure enters | Uses temporal transitions? | Represents matrix resistance? | Source-conditioned? | Main output | Relationship to EOG | Required manuscript wording |
|---|---|---|---:|---:|---:|---|---|---|
| Pointwise SDM / habitat-suitability model | Local support, occurrence intensity, probability, or suitability conditional on local predictors | Predictors and sometimes a spatial term | Usually no | Only if supplied as predictors or process components | Usually no | A value for each location | EOG can accept a frozen output as the local-support layer | Do not call all SDMs cell-independent or dispersal-free |
| Spatial block CV | Geographically stricter model evaluation | Allocation of records to training and testing folds | No | No | No | Cross-validated performance | Orthogonal to EOG: it changes evaluation, not the predicted structural quantity | “Spatial blocks address evaluation leakage; EOG represents configuration in the estimand” |
| NNDM and distance-aware CV | Match test–training distances to the intended prediction task | Fold construction and validation distance distribution | No | No | No | Prediction-error estimate | Useful for fair EOG and reference-model evaluation, not a reachability model | Do not describe distance-aware CV as a dispersal process |
| Spatial random fields / spatial eigenvectors | Residual spatial dependence, interpolation, or missing spatial covariates | Latent field or spatial basis functions | Usually no | Not inherently | No | Spatial effect and predictions | Can improve pointwise prediction; does not automatically represent an occurrence-anchored route through intermediate patches | Distinguish spatial dependence from source-conditioned propagation |
| Barrier SPDE | Non-stationary spatial dependence that does not smooth freely through physical barriers | Local dependence operator / mesh precision structure | Usually no | Barrier geometry rather than movement resistance | No | Barrier-aware latent spatial field | Closer to island problems than ordinary isotropic fields, but still primarily a correlation/interpolation model | Do not imply EOG invented barrier-aware spatial modelling |
| Dynamic occupancy / spatial metapopulation model | Colonisation, persistence, and extinction through time, often with imperfect detection | Neighbour occupancy, dispersal kernels, and transition probabilities | Yes | Sometimes | Yes, through occupied sites at the previous time | Transition probabilities and latent occupancy states | Stronger process model when repeated surveys exist; EOG is a static structural diagnostic unless extended prospectively | Do not call connected frequency colonisation probability |
| Dynamic mechanistic SDM / ecological diffusion | Population growth and spread through heterogeneous landscapes | Explicit dispersal, diffusion, demographic, or cellular processes | Yes | Often | Yes | Forecast distribution or density through time | Mechanistically richer than current EOG; answers a different question and needs additional data/assumptions | Position EOG as a lower-assumption structural layer, not a replacement |
| Least-cost path / cost distance | Minimum accumulated resistance between declared endpoints | Raster or graph edge/cell costs | No | Yes | Endpoints declared | One minimum-cost route or distance | EOG bridge inference overlaps directly; connected frequency instead summarizes reachability across a frozen scenario ensemble | Do not claim invention of cumulative-cost paths or corridors |
| Circuit theory / current flow | Multi-path connectivity or effective resistance through a landscape | Conductance network over a resistance surface | No | Yes | Focal nodes declared | Effective resistance, current density, isolation | A strong structural competitor. Tanzania shows that generic EOG can be redundant or harmful after current flow and source distance | Always benchmark against current flow when matrix-resistance data support it |
| Habitat-patch network / network occupancy model | Occurrence as a function of patch quality, weighted connectivity, and network topology | Patch nodes and movement/connectivity edges | Sometimes | Often | Sometimes | Patch occurrence, network quality, or centrality | The closest prior family. EOG novelty is not “quality plus network”; it is the frozen separation, training-only anchoring, scenario robustness, failure accounting, and explicit incremental tests | Cite network occupancy literature and state the remaining distinction precisely |
| Superlevel-set support topology | Components and persistence of a frozen support field across thresholds | Raster neighbourhood and threshold filtration | No | Hard masks; not usually graded resistance | Occurrence anchors may label components | Anchored/detached component lineages | EOG Layer 2; does not itself infer routes, colonisation, or demographic connectivity | Treat component classes as conditional on the frozen field and topology contract |
| EOG occurrence-anchored connected frequency | Robustness of target-to-training-anchor connection across predeclared graph scenarios | All nodes, edges, scenarios, and training-presence anchors | No | Optional through declared edge rules; absent in geography-only mode | Yes | Structural score in [0,1] | Current target method | Call it an assumption-robust structural diagnostic, never a probability of movement |
| EOG normalized bottleneck | Smallest maximum edge required by the best declared route, normalized by scenario scale | Minimax paths in the frozen graph | No | Optional | Yes | Relative bottleneck score | Secondary EOG quantity | Do not interpret as an observed barrier or realized movement threshold |

## Direct novelty comparison

### What is not novel

The structural manuscript must not claim novelty for:

- using spatial holdout;
- incorporating distance to known occurrences;
- converting habitat patches to graph nodes;
- thresholding a suitability raster;
- constructing connected components;
- computing shortest, least-cost, minimax, or current-flow paths;
- adding patch connectivity to a habitat-quality model;
- representing coastlines or barriers in a spatial model;
- modelling colonisation from neighbouring occupied patches.

### What EOG contributes in the present paper

The combined contribution is:

1. **estimand separation** — local environmental support, source distance, graph configuration, and matrix-aware connectivity are never silently treated as the same signal;
2. **training-only occurrence anchoring** — held-out labels cannot determine anchors or structural features;
3. **scenario-robust structural summaries** — connected frequency records persistence across predeclared graph assumptions rather than selecting one favourable graph from outcomes;
4. **symmetric competitor adaptation** — species-specific current-flow parameters and EOG anchors may adapt to outer-training labels only;
5. **matched incremental evaluation** — EOG is tested on the exact common held-out predictions against the strongest declared reference;
6. **failure visibility** — non-estimable species, folds, rows, and candidate selections remain explicit;
7. **positive and negative evidence retention** — A-Islands and Tanzania are reported together rather than selecting the favourable benchmark;
8. **claim-limited audit artifacts** — source, cohort, folds, graphs, model choices, results, and post-outcome corrections have independent fingerprints and timing labels.

This is an informatics and validation contribution built from established ecological modelling components.

## Comparator hierarchy for the manuscript

### Minimum hierarchy for a new EOG application

1. local support only;
2. local support + nearest training occurrence distance;
3. simple patch isolation or distance-based connectivity;
4. strongest available landscape-specific resistance or network model;
5. the same reference + EOG;
6. declared sensitivity analyses using unchanged outcomes and inference rules.

A positive result at tier 2 does not establish value beyond tier 4. A negative result at tier 4 does not invalidate a positive result against tier 2; it identifies a narrower incremental boundary.

### A-Islands hierarchy

The authoritative A-Islands endpoint conditions on pointwise CHELSA support and nearest-training-presence distance. It establishes added structural information beyond those quantities, but it does not benchmark a calibrated species-specific matrix-resistance model.

### Tanzania hierarchy

The Tanzania reference includes patch area, outer-training-selected matrix-aware current flow, its interaction with area, and nearest-training-occurrence distance. This is the stronger test of whether generic geography-only connected frequency adds anything after a landscape-specific connectivity model.

## Text approved for the Introduction

> Spatially structured species-distribution analyses address several different problems. Spatial cross-validation modifies model evaluation, spatial random fields represent residual dependence or interpolation, dynamic occupancy and mechanistic spread models estimate temporal population processes, and resistance or circuit models quantify movement through heterogeneous matrices. We address a narrower question: when the available prediction is a frozen pointwise support surface, does occurrence-anchored patch configuration retain held-out incidence information after local support, direct source proximity, and—where available—a strong landscape-specific connectivity model are represented?

## Text approved for the Discussion

> EOG identifies a potentially missing structural estimand; it does not guarantee a predictive gain. Its contribution is therefore evaluated conditionally. The A-Islands benchmark shows that graph configuration may add information beyond pointwise support and source distance, whereas the Tanzania benchmark shows that the tested generic graph feature can be redundant or harmful once species-adaptive matrix-aware current flow is already included.

## Core references

The final manuscript should cite the primary sources below and replace any website-only metadata with the journal-formatted reference record.

- Valavi, R. et al. (2019). `blockCV`: spatially or environmentally separated folds for SDM cross-validation. *Methods in Ecology and Evolution*. https://doi.org/10.1111/2041-210X.13107
- Milà, C. et al. (2022). Nearest-neighbour-distance-matching leave-one-out cross-validation. *Methods in Ecology and Evolution*. https://doi.org/10.1111/2041-210X.13851
- Bakka, H. et al. (2019). Non-stationary Gaussian models with physical barriers. *Spatial Statistics*. https://doi.org/10.1016/j.spasta.2019.01.002
- Broms, K. M. et al. (2016). Dynamic occupancy models for explicit colonization processes. *Ecology*. https://doi.org/10.1890/15-0416.1
- Merow, C. et al. (2011). Developing dynamic mechanistic species-distribution models. *The American Naturalist*. https://doi.org/10.1086/660295
- Adriaensen, F. et al. (2003). The application of least-cost modelling as a functional landscape model. *Landscape and Urban Planning*. https://doi.org/10.1016/S0169-2046(02)00242-6
- McRae, B. H. et al. (2008). Using circuit theory to model connectivity in ecology, evolution, and conservation. *Ecology*. https://doi.org/10.1890/07-1861.1
- Berlow, E. L. et al. (2013). A network extension of species-occupancy models in a patchy environment. *PLoS ONE*. https://doi.org/10.1371/journal.pone.0072200
- Ortiz-Rodríguez, I. A. et al. (2019). Predicting species occurrences with habitat-network models. *Ecology and Evolution*. https://doi.org/10.1002/ece3.5567

## Reference audit before submission

Before final submission:

- verify author order, article title, volume, issue, pages, and DOI from Crossref or the publisher;
- distinguish examples from systematic reviews;
- cite recent extensions where directly relevant, without claiming the list is exhaustive;
- ensure every competitor used in a benchmark has an implementation citation and parameter contract;
- ensure no cited method is described as solving a problem outside its stated estimand.
