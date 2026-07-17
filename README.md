# Environmental Occupancy Geometry (EOG)

EOG describes how observed ecological states span, connect, and fragment in arbitrary environmental feature space. It operates on occurrence-by-feature matrices and does **not** fit raster suitability or presence probability.

## Status

Version `0.1.0` is the frozen extraction of the environmental occupancy geometry implementation first developed and validated in `zuizui0223/acsp` PR #35. Numerical definitions and edge-case behavior are intentionally kept compatible with the ACSP implementation during migration.

## Primary quantities

- **span**: the 0.90 quantile by default of positive pairwise distances after robust feature scaling.
- **continuity**: environmental diameter divided by minimum-spanning-tree length. Lower values indicate a less direct occupied path.
- **gap strength**: largest positive MST edge divided by the median positive MST edge. Larger values indicate a stronger internal discontinuity.

`component_count` and component labels are diagnostic. Candidate projection is also diagnostic and is not a suitability score.

## Installation

```bash
python -m pip install .
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

The initial contract supports one-dimensional matrices, duplicate states, constant features, and empty candidate projections with matching feature dimension. Non-finite values and occurrence matrices with fewer than two rows are rejected.

## Scientific boundary

EOG currently supports the claim that MST-derived continuity and gap strength describe occupied environmental structure not represented by breadth or covariance volume alone in the included synthetic benchmarks. It does not claim universal superiority over clustering, hypervolume, topological-data-analysis, or species-distribution methods.

## Provenance

The initial implementation was copied from `acsp/occupancy_geometry.py` at ACSP main commit `cfa24ba30fa0607e530d5cf716ce8729d54d773e`, with the API contract frozen in ACSP PR #37. Cross-repository parity must be verified before ACSP imports this standalone package.

## License

MIT.
