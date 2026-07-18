# Multiaxial environmental occupancy geometry

## Core methodological position

EOG is a descriptive framework for the geometry of observed ecological states in a predeclared environmental feature space. It is not a species-distribution model, a universal fragmentation test, or a replacement for clustering or topological data analysis.

The method should be reported as four separate axes.

| Axis | Primary summary | Supported interpretation | Unsupported interpretation |
|---|---|---|---|
| Extent | `span` | How broadly observed states are dispersed after robust scaling | Occupied range boundary, suitability, or environmental tolerance |
| Path directness | `continuity` and its reciprocal path inefficiency | Whether the MST path connecting observed states is direct or tortuous | A dispersal path, temporal trajectory, or causal mechanism |
| Separation evidence | raw `gap_strength`, K-means silhouette, and density-trimmed core bridge in benchmark work | Whether different summaries identify strong separation or bridge structure | A universal fragmentation probability or proof of missing support |
| Sampling stability | repeated subsampling intervals | Whether a descriptive quantity is stable under reduced occurrence sampling | Correction for sampling bias or imperfect detection |

## Consequences of the negative validations

1. Raw `gap_strength` is sample-size dependent and has no universal threshold.
2. Gaussian matched-null calibration is not recommended for general confirmatory use. Alternative connected nulls either over-reject non-Gaussian connected clouds or absorb fragmented clouds.
3. Persistent largest-edge splits improve on raw largest-edge evidence but do not reliably distinguish narrow support interruption from connected curved manifolds.
4. The density-trimmed core bridge score is useful for separated dense modes, but it is not a missing-bridge statistic.
5. K-means silhouette and core bridge evidence are complementary. Their disagreement is an interpretable result, not an error to be removed by fitting an ensemble.

## Required reporting

A confirmatory EOG analysis should report:

- the ecological rationale for the primary feature set;
- sample size and robust-scaling rule;
- span and continuity;
- raw gap strength as a descriptive legacy quantity only;
- subsampling medians and intervals for topology-sensitive quantities;
- any clustering or core-bridge diagnostic separately;
- explicit ambiguity when diagnostics disagree.

## Prohibited headline claims

Do not claim that EOG:

- detects all forms of environmental fragmentation;
- identifies missing support from a largest MST edge alone;
- provides a posterior probability of fragmentation;
- is robust to arbitrary irrelevant dimensions;
- proves multiple niches, barriers, dispersal routes, or causal processes.

## Manuscript-level novelty

The defensible contribution is the ecological organization of several geometric summaries into an auditable occupancy-geometry profile with explicit failure boundaries. Novelty does not rest on inventing the MST, single linkage, largest-edge cuts, or K-means.