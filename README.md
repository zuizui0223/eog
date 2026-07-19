# Environmental Occupancy Geometry (EOG)

EOG describes the geometry of observed ecological states in a predeclared environmental feature space. It operates on occurrence-by-feature matrices and does **not** fit raster suitability, presence probability, occupancy, or causal ecological mechanisms.

## Status

Version `0.1.0` is the frozen extraction of the method first developed in `zuizui0223/acsp` PR #35. Subsequent standalone validation has narrowed the defensible interpretation. EOG is maintained independently; ACSP no longer vendors the implementation or its method benchmarks.

## Primary quantities

- **standardized span**: the requested quantile, 0.90 by default, of positive pairwise distances after robust feature scaling;
- **tree compactness (`continuity`)**: environmental diameter divided by minimum-spanning-tree length;
- **gap strength**: largest positive MST edge divided by the median positive MST edge.

`component_count` and component labels are diagnostic. Candidate projection is also diagnostic and is not a suitability score.

## Interpretation boundaries

Each input cloud is robust-scaled by default. Consequently, `span` describes dispersion in the standardized cloud; it does **not** measure absolute environmental breadth across independently scaled taxa, regions, or times. Comparative breadth requires a shared transformation fitted from a common external or pooled reference without outcome-driven tuning.

`continuity` is best described as MST compactness. It is affected by sample size, support dimension, and cloud filling, and must not be interpreted as generic path tortuosity across arbitrary point-cloud types.

Raw `gap_strength` changes strongly with sample size and has no universal cutoff. It is retained as descriptive separation evidence. It does not establish fragmentation, missing support, or a posterior probability of either.

Gaussian matched-null calibration is retained for audit history but is no longer recommended as a general confirmatory procedure. Alternative connected-null families either over-reject non-Gaussian connected clouds or absorb fragmented clouds.

The primary feature set must be selected from ecological rationale before EOG outcomes are calculated. Correlation filtering at |r| >= 0.80 is a secondary sensitivity analysis. PCA90 and all-variable analyses are supplementary controls; adding every available environmental variable is not supported.

Topology-sensitive quantities should be reported with repeated subsampling medians and intervals. Clustering, core-bridge, and MST-edge diagnostics must remain separate when they answer different structural questions.

## Installation

```bash
python -m pip install .
```

For direct CHELSA raster sampling used in benchmark work:

```bash
python -m pip install ".[raster]"
```

## Usage

```python
import numpy as np
from eog import infer_occupancy_geometry

states = np.array([
    [10.1, 800.0],
    [10.4, 820.0],
    [16.0, 1400.0],
    [16.2, 1430.0],
])

geometry = infer_occupancy_geometry(states)
print(geometry.span)
print(geometry.continuity)
print(geometry.gap_strength)
```

## Frozen public API

- `OccupancyGeometry`
- `robust_scale`
- `pairwise_distances`
- `minimum_spanning_tree`
- `infer_occupancy_geometry`
- `project_states`

The initial contract supports one-dimensional matrices, duplicate states, constant features, all-identical rows, and empty candidate projections with matching feature dimension. Non-finite values and occurrence matrices with fewer than two rows are rejected.

## Validation and manuscript materials

- `benchmarks/topology_discrimination.py`: historical synthetic discrimination benchmark;
- `benchmarks/robustness_audit.py`: sample-size and irrelevant-dimension audit;
- `benchmarks/calibrated_gap_feature_selection.py`: matched-null calibration audit;
- `benchmarks/multiaxial_archetypes.py`: frozen archetype benchmark that falsified the original broad extent and path-directness interpretation;
- `docs/multiaxial_methodology.md`: current restrained methodological position;
- `docs/multiaxial_archetype_results.md`: negative archetype result and consequences;
- `docs/evidence_ledger.md`: verified results and unsupported claims;
- `tests/test_geometry.py`: API and edge-case tests;
- `tests/test_acsp_parity_fixture.py`: frozen numerical parity fixture.

## Scientific boundary

EOG currently supports an auditable description of standardized cloud dispersion, MST compactness, separation evidence, and sampling stability under explicitly stated transformations and support assumptions. It does not claim universal superiority over clustering, hypervolume, topological-data-analysis, or species-distribution methods. The MST, single-linkage, and largest-edge ideas themselves are not claimed as novel.

## Provenance

The initial implementation was copied from ACSP main commit `cfa24ba30fa0607e530d5cf716ce8729d54d773e`. The compatibility contract was frozen at ACSP commit `3d2017e9a342eca13f0a17f1d3c473a993c4335a` before the duplicate ACSP implementation was removed.

## License

MIT.