# Environmental Occupancy Geometry (EOG)

EOG describes how observed ecological states span, connect, and fragment in arbitrary environmental feature space. It operates on occurrence-by-feature matrices and does **not** fit raster suitability or presence probability.

## Status

Version `0.1.0` is the frozen extraction of the method first developed and validated in `zuizui0223/acsp` PR #35. EOG is now maintained independently; ACSP no longer vendors the implementation or its method benchmarks.

## Primary quantities

- **span**: the requested quantile, 0.90 by default, of positive pairwise distances after robust feature scaling.
- **continuity**: environmental diameter divided by minimum-spanning-tree length. Lower values indicate a less direct occupied path.
- **gap strength**: largest positive MST edge divided by the median positive MST edge. Larger values indicate a stronger internal discontinuity.

`component_count` and component labels are diagnostic. Candidate projection is also diagnostic and is not a suitability score.

## Important analysis constraints

Raw `gap_strength` changes strongly with sample size and must not be compared using one universal cutoff. The issue #3 calibration audit therefore requires raw and matched-null calibrated gap values to be reported together.

Confirmatory fragmentation comparisons currently require at least **60 occurrence states**. Analyses with 30–59 states are exploratory.

The primary feature set must be selected from ecological rationale before EOG outcomes are calculated. Correlation filtering at |r| >= 0.80 is a secondary sensitivity analysis. PCA90 and all-variable analyses are supplementary controls; adding every available environmental variable is not supported.

The calibrated gap percentile compares an observed cloud with connected reference clouds matched on sample size, dimension, mean, and covariance. It is not a posterior probability that the cloud is fragmented.

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

- `benchmarks/topology_discrimination.py`: frozen synthetic discrimination benchmark.
- `benchmarks/robustness_audit.py`: sample-size and irrelevant-dimension audit.
- `benchmarks/calibrated_gap_feature_selection.py`: matched-null calibration and predeclared feature-strategy audit.
- `docs/robustness_audit_protocol.md`: predeclared robustness design and interpretation rules.
- `docs/calibrated_gap_feature_selection_protocol.md`: failed original gate, revised n>=60 rule, and frozen feature protocol.
- `docs/evidence_ledger.md`: verified results and unsupported claims.
- `docs/migration_provenance.md`: extraction checkpoints and ownership boundary.
- `tests/test_geometry.py`: API and edge-case tests.
- `tests/test_acsp_parity_fixture.py`: frozen numerical parity fixture.

The historical random-taxon CHELSA artifacts remain auditable through ACSP PR #35 and its Actions artifacts. New development, expanded cohorts, comparator analyses, novelty review, and manuscript outputs belong in this repository.

## Scientific boundary

EOG currently supports the claim that MST-derived continuity and gap strength describe occupied environmental structure not represented by breadth or covariance volume alone in the included synthetic benchmarks. It does not claim universal superiority over clustering, hypervolume, topological-data-analysis, or species-distribution methods. The MST, single-linkage, and largest-edge ideas themselves are not claimed as novel.

## Provenance

The initial implementation was copied from ACSP main commit `cfa24ba30fa0607e530d5cf716ce8729d54d773e`. The compatibility contract was frozen at ACSP commit `3d2017e9a342eca13f0a17f1d3c473a993c4335a` before the duplicate ACSP implementation was removed.

## License

MIT.
