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

## Current supported position

EOG supports an auditable report of:

- standardized pairwise dispersion;
- MST compactness under stated sampling and support assumptions;
- separate separation diagnostics;
- subsampling stability;
- the exact feature transformation used.

Absolute breadth comparisons require a shared external or pooled scaling reference. Generic path-shape comparisons require matched support classes and sampling designs.

## Unsupported claims

The current evidence does not establish that EOG:

- replaces species-distribution or occupancy models;
- outperforms every hypervolume, clustering, or topological method;
- introduces the MST, single-linkage, or largest-edge statistic;
- proves causal ecological mechanisms;
- detects all forms of fragmentation or missing support;
- provides a posterior fragmentation probability;
- supports a universal raw `gap_strength` threshold;
- is robust to arbitrary irrelevant environmental dimensions;
- measures absolute niche breadth after independent within-cloud scaling;
- measures generic path tortuosity across arbitrary point-cloud support classes.