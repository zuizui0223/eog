# Multiaxial archetype benchmark result

## Decision

The first frozen multiaxial archetype benchmark did **not** support the original four-axis interpretation.

Machine-readable decision:

- minimum extent AUC: 0.4075;
- minimum path AUC: 0.0000;
- minimum two-mode gap AUC: 0.906875;
- minimum missing-bridge gap AUC: 0.281875;
- composite score fitted: false;
- supports original multiaxial position: false;
- supports universal support-interruption claim: false.

## Interpretation

### Standardized span

The broad-versus-compact contrast was not discriminated by `span` after each cloud was robust-scaled independently. This is expected from the transformation: global dilation is removed by within-cloud scaling. Therefore standardized `span` cannot be interpreted as absolute ecological breadth or used for between-cloud extent comparisons unless all clouds share a scaling reference.

### Continuity / tree inefficiency

The curved-versus-compact contrast reversed the intended direction at every tested sample size. A compact two-dimensional cloud can require a long MST relative to its diameter, whereas a sampled one-dimensional curve may have a comparatively efficient tree. Thus `continuity` is not a generic path-tortuosity statistic across arbitrary support classes. It is better described as MST compactness and interpreted only under controlled sampling and support assumptions.

### Gap strength

Two separated modes were consistently distinguished from compact clouds, with minimum AUC 0.906875. This supports use of `gap_strength` as descriptive separation evidence in that archetype family, not as a universal fragmentation test.

The missing-bridge-versus-curved contrast was unstable across sample size, with AUC ranging from 0.281875 to 0.955625. This confirms that the largest MST edge does not identify support interruption uniformly.

## Consequence

The benchmark is retained as a negative methodological result. The manuscript and software documentation must:

1. replace `extent` with `standardized dispersion` unless a common external scaler is used;
2. replace generic `path directness` claims with the narrower term `tree compactness`;
3. keep separation diagnostics separate;
4. require subsampling stability;
5. avoid a composite occupancy-geometry score.