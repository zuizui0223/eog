# Multiaxial environmental occupancy geometry

## Core methodological position

EOG is a descriptive framework for the geometry of observed ecological states in a predeclared environmental feature space. It is not a species-distribution model, a universal fragmentation test, or a replacement for clustering or topological data analysis.

The first frozen multiaxial benchmark showed that the originally proposed four-axis interpretation was too broad. EOG should therefore report separate summaries, but each summary must retain its mathematical scaling and support-class boundary.

| Summary family | Primary summary | Supported interpretation | Unsupported interpretation |
|---|---|---|---|
| Standardized dispersion | `span` after within-cloud robust scaling | Pairwise dispersion of the standardized cloud | Absolute ecological breadth or between-cloud extent when each cloud is scaled independently |
| Tree compactness | `continuity` or reciprocal tree inefficiency | Compactness of the MST relative to cloud diameter under the stated sampling and support class | Generic path tortuosity across arbitrary point clouds, a dispersal path, or a temporal trajectory |
| Separation evidence | raw `gap_strength`, K-means silhouette, and density-trimmed core bridge in benchmark work | Whether different summaries identify strong mode or bridge separation | A universal fragmentation probability or proof of missing support |
| Sampling stability | repeated subsampling intervals | Whether a descriptive quantity is stable under reduced occurrence sampling | Correction for sampling bias or imperfect detection |

## Consequences of the negative validations

1. Raw `gap_strength` is sample-size dependent and has no universal threshold.
2. Gaussian matched-null calibration is not recommended for general confirmatory use. Alternative connected nulls either over-reject non-Gaussian connected clouds or absorb fragmented clouds.
3. Persistent largest-edge splits improve on raw largest-edge evidence but do not reliably distinguish narrow support interruption from connected curved manifolds.
4. The density-trimmed core bridge score is useful for separated dense modes, but it is not a missing-bridge statistic.
5. K-means silhouette and core bridge evidence are complementary. Their disagreement is an interpretable result, not an error to be removed by fitting an ensemble.
6. `span` is scale invariant when every cloud is robust-scaled separately. It cannot support an absolute or comparative breadth claim without a shared external scaling reference.
7. `continuity` is influenced by sample size, support dimension, and cloud filling. Compact clouds can have longer MSTs relative to diameter than sampled curves, so the statistic is not a generic tortuosity index across support classes.

## Required reporting

A confirmatory EOG analysis should report:

- the ecological rationale for the primary feature set;
- sample size and the exact scaling reference;
- whether scaling was fitted independently, jointly, or from an external reference set;
- standardized span and tree compactness using restrained names;
- raw gap strength as a descriptive legacy quantity only;
- subsampling medians and intervals for topology-sensitive quantities;
- any clustering or core-bridge diagnostic separately;
- explicit ambiguity when diagnostics disagree.

Comparisons of breadth across taxa, regions, or times require a common feature transformation fitted without using the group labels being compared. Independently standardized clouds may be compared for shape, but not for absolute environmental extent.

## Prohibited headline claims

Do not claim that EOG:

- detects all forms of environmental fragmentation;
- identifies missing support from a largest MST edge alone;
- provides a posterior probability of fragmentation;
- is robust to arbitrary irrelevant dimensions;
- measures absolute niche breadth after independent within-cloud scaling;
- measures generic path tortuosity across arbitrary point-cloud support classes;
- proves multiple niches, barriers, dispersal routes, or causal processes.

## Manuscript-level novelty

The defensible contribution is an auditable protocol for reporting standardized cloud dispersion, MST compactness, complementary separation evidence, and sampling stability with explicit transformation and support-class boundaries. Novelty does not rest on inventing the MST, single linkage, largest-edge cuts, or K-means.