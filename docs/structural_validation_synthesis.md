# Structural validation synthesis: where EOG adds information and where it does not

## Purpose

This document places the two frozen empirical structural benchmarks in one evidence frame. The benchmarks were deliberately designed to answer different incremental questions, so their directions must not be collapsed into one universal performance claim.

The central distinction is:

> Pointwise environmental support asks whether a location has suitable local conditions. Occurrence-anchored structural reachability asks whether that location occupies a plausible position in the declared landscape graph relative to training occurrences.

Spatial cross-validation can make model evaluation geographically stricter, but it does not by itself insert landscape configuration into the predicted quantity. EOG adds an explicit structural layer. Whether that layer improves prediction depends on what the reference model already represents.

## Benchmark comparison

| Property | A-Islands plants | Tanzania forest birds |
|---|---|---|
| Landscape | 842 Australian continental islands | 14 East/West Usambara forest fragments |
| Taxa | 886 declared taxa; 845 with an estimable species statistic | 60 predeclared eligible bird species |
| Primary holdout | Shared five-fold 5-degree spatial partition | 14-fold leave-one-fragment-out |
| Local/reference information | Five-variable CHELSA pointwise support | Patch area and species-adaptive matrix-aware current flow |
| Simple proximity control | Nearest outer-training occurrence distance | Nearest outer-training occurrence distance |
| Structural addition | Connected frequency over 12 frozen island-chain scenarios | Geography-only connected frequency over a frozen four-scenario component ladder |
| Primary estimand | Conditional concordance within support × nearest-distance strata | Candidate-minus-reference paired held-out log loss |
| Primary result | 0.6177466; 95% CI 0.6086806–0.6269445 | +0.0321131; 95% CI +0.0174580 to +0.0486750 |
| Direction | Structural reachability retained added information | Adding EOG worsened prediction relative to the strong reference |

The metrics are different because the datasets support different designs. The valid comparison is not their numerical magnitude. It is the scientific question asked after controlling the strongest predeclared reference available in each system.

## A-Islands confirmatory result

The A-Islands benchmark used 886 APC-native plant taxa, 842 islands, five CHELSA predictors, a shared spatial five-fold partition, and 12 predeclared reachability scenarios. All support models and graph anchors were trained using outer-training islands only.

The primary statistic compared occupied and unoccupied held-out islands within the same 5 × 5 strata of pointwise support and nearest-training-presence distance. Therefore a positive result could not be attributed only to local climate support or simple source proximity.

The frozen result was:

- estimable species: 845;
- combined conditional reachability concordance: **0.6177466**;
- species-bootstrap 95% interval: **0.6086806–0.6269445**;
- two-sided species sign-flip diagnostic: approximately **1 × 10⁻⁵**.

The predeclared decomposition retained the same direction:

- geography-only connected frequency: **0.6147456**, 95% CI **0.6059505–0.6235729**;
- environmentally constrained connected frequency: **0.6063727**, 95% CI **0.5974871–0.6154186**.

The frozen bottleneck secondary was weaker but above its 0.5 null:

- median normalized geographic bottleneck concordance: approximately **0.5288**;
- 95% CI approximately **0.5177–0.5396**;
- estimable species: 793.

The supported claim is narrow: among held-out islands with similar environmental support and similar distance to known training occurrences, islands embedded in more robustly reachable island-chain configurations were occupied more often.

This is not evidence that EOG replaces SDM, estimates dispersal probability, or reconstructs colonisation history.

## Tanzania external boundary result

The Tanzania benchmark intentionally used a stronger structural reference. For every species and outer fold, one of 512 matrix-resistance combinations was selected using outer-training occurrence labels only. The same selected current-flow quantity was then used in both probability tiers.

Reference:

`patch area + selected current flow + area × current flow + nearest training occurrence`

Candidate:

`reference + EOG connected frequency`

The complete source-to-result workflow independently regenerated the official Dryad bytes, 1,024 regional current-flow candidates, EOG features, training-only selections, predictions, and species-cluster inference.

For primary leave-one-fragment-out validation:

- matched held-out predictions: 826;
- species: 60;
- species-macro candidate-minus-reference log-loss difference: **+0.0321131**;
- species-bootstrap 95% interval: **+0.0174580 to +0.0486750**;
- species sign-flip diagnostic: **p = 0.000030**;
- species-macro Brier difference: **+0.0047993**;
- Brier 95% interval: **+0.0022813 to +0.0073149**.

Positive differences are worse. Thus the present geography-only connected-frequency feature did not add information beyond the matrix-aware current-flow and nearest-occurrence reference; it measurably worsened LOSO prediction.

The prespecified inverse-area source-weight sensitivity had the same direction. The geometry-only spatial-block sensitivity was smaller and uncertain, with intervals spanning zero.

The supported claim is again narrow: in this 14-fragment bird system, a coarse occurrence-anchored geography-only graph feature was not a beneficial addition after a strong landscape-specific matrix connectivity model and simple occurrence proximity were already represented.

## What the contrast establishes

The two results jointly reject two overly broad positions.

### Rejected position 1: pointwise suitability is always sufficient

A-Islands contradicts this. Structural reachability retained held-out incidence information after conditioning on pointwise support and nearest-source distance.

### Rejected position 2: an EOG structural feature always improves prediction

Tanzania contradicts this. Once matrix-specific current flow and nearest-source distance were already present, the added connected-frequency feature was redundant or harmful in LOSO prediction.

The current evidence supports a conditional position:

> Occurrence-anchored landscape configuration can add information that pointwise support and direct source distance omit, but its incremental value is not universal and must be tested against the strongest landscape-specific connectivity reference available.

## What remains unresolved

The benchmarks differ in taxonomic group, landscape, number of sampled units, structural representation, reference model, graph scale, and endpoint. They do not identify which of those differences caused the contrasting results.

The following explanations are hypotheses, not findings:

- bird movement may be less compatible with an undirected coarse patch graph than island-plant occurrence;
- matrix-aware current flow may already absorb most relevant landscape configuration in Tanzania;
- four connected-frequency levels may be too coarse for 14 fragments;
- the extra feature may add variance when each fold has very little training information;
- trait-specific or directional movement may matter.

None may be introduced post hoc to rescue the frozen Tanzania contrast.

## Prospective development rule

Any extension involving trait-informed movement scales, directed edges, shrinkage, alternative graph ensembles, dynamic colonisation data, or new support producers must be:

1. motivated independently of the Tanzania outcome;
2. frozen before inspecting its new evaluation outcome;
3. compared against the same or a stronger reference;
4. reported alongside, not instead of, the frozen negative Tanzania result.

The next strongest evidence would come from a larger non-island fragmented-landscape dataset with explicit geometry, repeated colonisation or turnover observations, and enough sites to estimate structural increments without relying on a 14-fragment design.

## Reproducibility pointers

- A-Islands contract: `docs/aislands_authoritative_contracts.md`;
- A-Islands primary runner: `benchmarks/run_aislands_authoritative_benchmark.py`;
- A-Islands mode decomposition: `benchmarks/run_aislands_predeclared_secondary.py`;
- Tanzania result: `docs/tanzania_heldout_result.md`;
- Tanzania frozen projection: `benchmarks/tanzania_heldout_expected.json`;
- Tanzania result fingerprint: `6b555c28d61d3f39b9e672f5a97250de6870301871cf3e60378e97863cd109e4`.
