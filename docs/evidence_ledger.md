# Environmental occupancy geometry evidence ledger

This file separates verified numerical results from interpretation. The original development history is preserved in `zuizui0223/acsp` PR #35. Later standalone benchmarks narrowed several early claims.

## Frozen public quantities

- `span`: 0.90 quantile of positive pairwise distances after the default within-cloud robust scaling;
- `continuity`: maximum pairwise distance divided by total MST length;
- `gap_strength`: largest positive MST edge divided by the median positive MST edge;
- `component_count`: diagnostic only.

The names above describe the frozen API. Their defensible interpretations are narrower than the original labels.

## Historical synthetic discrimination

Early matched-generator benchmarks found:

- two-mode gap strength / connected gap strength: about 2.33;
- missing-bridge gap strength / connected gap strength: about 3.38;
- curved-path continuity / straight-path continuity: about 0.49.

These results establish discrimination inside those controlled generator families. They do not establish universal fragmentation, missing-support, or tortuosity inference.

## Sample-size and irrelevant-dimension audit

With the intended clean two-feature generators:

- minimum two-mode versus connected `gap_strength` AUC: 0.9488;
- minimum curved versus straight `continuity` AUC: 1.0000.

With six irrelevant features:

- minimum gap-strength AUC: 0.2396;
- minimum continuity AUC: 0.5360.

Connected-cloud median raw gap strength increased substantially with sample size. Therefore:

- no universal raw gap threshold is supported;
- arbitrary all-variable matrices are unsupported;
- ecological feature preselection and sensitivity analysis are required.

## Matched-null calibration audit

Gaussian matched-null calibration performed well in some frozen Gaussian-like contrasts at n >= 60, but later null-family stress tests showed that no fitted connected family was generally satisfactory:

- restrictive nulls over-rejected skewed, heavy-tailed, curved, or contaminated connected clouds;
- flexible nulls could absorb fragmented or multimodal clouds;
- calibration therefore depends on an unverifiable connected-family assumption.

Gaussian matched-null calibration is retained as audit history but is no longer recommended as a general confirmatory fragmentation procedure.

## Independent separation investigations

Subsequent frozen work found:

- persistent largest-edge evidence improved over one raw largest edge but remained near chance for narrow missing bridges;
- the density-trimmed core-local-bridge score performed strongly for separated dense modes, including unequal modes;
- the same core-bridge score failed as a universal support-interruption statistic;
- K-means silhouette and core-bridge evidence answered different questions and disagreed in real-taxon clouds.

Consequently, no single separation or fragmentation score is promoted. Raw gap strength, silhouette, and core-bridge evidence must remain separate when used.

## Real-taxon stability audit

In the frozen six-pair CHELSA audit, all pairs completed. Silhouette was generally more stable under subsampling than the core-bridge score. The rankings of taxa differed between the diagnostics, confirming that they are not interchangeable.

This audit characterizes numerical behavior. It does not prove multiple niches, fragmentation, or missing support in any taxon.

## Multiaxial archetype benchmark

The first frozen multiaxial benchmark falsified the original broad four-axis interpretation:

- minimum broad-versus-compact `span` AUC: 0.4075;
- minimum curved-versus-compact tree-inefficiency AUC: 0.0000;
- minimum two-mode-versus-compact gap-strength AUC: 0.906875;
- minimum missing-bridge-versus-curved gap-strength AUC: 0.281875.

Interpretation:

1. Independent within-cloud robust scaling removes global dilation, so standardized `span` cannot measure absolute ecological breadth across clouds.
2. `continuity` is affected by support dimension and point-cloud filling. It is not a generic path-tortuosity measure across arbitrary support classes.
3. Gap strength retains useful descriptive evidence for separated modes in the tested family.
4. Largest-edge evidence remains unreliable for universal support-interruption inference.

## A-Islands confirmatory structural benchmark

The authoritative benchmark froze 886 APC-native plant taxa, 842 islands, five CHELSA variables, one shared five-fold spatial partition, deterministic L2 logistic pointwise support, and 12 island-chain scenarios before species outcomes were inspected.

The primary endpoint compared occupied and unoccupied held-out islands within the same 5 × 5 strata of pointwise support and nearest-training-presence distance. The frozen result was:

- estimable species: 845;
- combined conditional connected-frequency concordance: **0.6177466**;
- species-bootstrap 95% interval: **0.6086806–0.6269445**;
- species sign-flip diagnostic: approximately **1 × 10⁻⁵**.

The predeclared decomposition retained positive structural information:

- geography-only connected frequency: **0.6147456**, 95% CI **0.6059505–0.6235729**;
- environmentally constrained connected frequency: **0.6063727**, 95% CI **0.5974871–0.6154186**.

The frozen bottleneck secondary was weaker but above 0.5:

- concordance approximately **0.5288**;
- 95% CI approximately **0.5177–0.5396**;
- estimable species: 793.

Supported interpretation: among held-out islands with similar pointwise environmental support and similar distance to training occurrences, islands embedded in more robustly reachable frozen graph configurations were occupied more often.

This is evidence for added structural information conditional on the declared controls. It is not evidence that connected frequency is dispersal probability, that EOG replaces SDM, or that a historical colonisation route was recovered.

## Tanzania non-island external boundary benchmark

The Tanzania benchmark used 60 predeclared bird species and 14 forest fragments. It tested EOG against a stronger landscape-specific reference than the A-Islands benchmark.

For every species and outer fold, one of 512 matrix-resistance combinations was selected using outer-training labels only. The strict reference was:

`patch area + selected matrix-aware current flow + area × current flow + nearest training occurrence`

The candidate added only geography-based EOG connected frequency. The same current-flow selection and probability engine were used in both tiers.

The complete source-to-result workflow was independently reproduced. For primary leave-one-fragment-out validation:

- matched held-out predictions: 826;
- species: 60;
- species-macro candidate-minus-reference log-loss difference: **+0.0321131**;
- species-bootstrap 95% interval: **+0.0174580 to +0.0486750**;
- species sign-flip diagnostic: **p = 0.000030**;
- species-macro Brier difference: **+0.0047993**;
- Brier 95% interval: **+0.0022813 to +0.0073149**.

Positive differences are worse. The present EOG connected-frequency feature therefore worsened LOSO prediction relative to the already strong current-flow-plus-distance reference. The inverse-area source-weight sensitivity retained the same direction. Geometry-only spatial-block estimates were smaller and uncertain, with intervals spanning zero.

Supported interpretation: the tested generic geography-only structural feature was not a beneficial add-on once a species-adaptive matrix-aware connectivity quantity and nearest-source distance were already represented in this small forest-fragment benchmark.

This does not show that EOG is generally harmful or that current flow universally dominates graph methods.

## Cross-system structural conclusion

The two frozen empirical results reject both of the following universal positions:

1. pointwise support and direct source distance are always sufficient;
2. adding an EOG graph feature always improves prediction.

The supported position is conditional:

> Occurrence-anchored landscape configuration can carry information omitted by pointwise support and direct source distance, but its incremental value must be tested against the strongest landscape-specific connectivity reference available.

A-Islands supports the first half of that statement. Tanzania supplies the necessary negative boundary for the second half.

The systems differ in landscape, taxonomic group, sample size, graph representation, reference model, and endpoint. Their contrast does not identify which difference caused the opposite incremental result.

## Current supported position

EOG supports an auditable report of:

- standardized pairwise dispersion;
- MST compactness under stated sampling and support assumptions;
- separate separation diagnostics;
- subsampling stability;
- the exact feature transformation used;
- spatial support-component classes under a frozen field, mask, threshold sequence, neighbourhood rule, and anchor assignment;
- occurrence-anchored connected frequency and bottleneck diagnostics under frozen graph scenarios;
- held-out incremental tests against pointwise support, nearest-source distance, and stronger connectivity competitors;
- explicit positive, null, negative, ambiguous, and non-estimable outcomes.

Absolute breadth comparisons require a shared external or pooled scaling reference. Generic path-shape comparisons require matched support classes and sampling designs. Structural reachability claims require frozen graph assumptions, training-only anchors, and a comparator hierarchy appropriate to the landscape.

## Unsupported claims

The current evidence does not establish that EOG:

- replaces species-distribution or occupancy models;
- outperforms every hypervolume, clustering, topological, resistance, or circuit-theory method;
- introduces the MST, single-linkage, largest-edge, graph-connectivity, or minimax statistic;
- proves causal ecological mechanisms;
- detects all forms of fragmentation or missing support;
- provides a posterior fragmentation probability;
- supports a universal raw `gap_strength` threshold;
- is robust to arbitrary irrelevant environmental dimensions;
- measures absolute niche breadth after independent within-cloud scaling;
- measures generic path tortuosity across arbitrary point-cloud support classes;
- universally improves held-out prediction when appended to an SDM or connectivity model;
- estimates dispersal, colonisation, demographic connectivity, or historical routes from connected frequency;
- explains why A-Islands and Tanzania produced different incremental results;
- permits post-outcome trait, directionality, scale, or shrinkage changes to replace the frozen Tanzania result.
