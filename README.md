# Environmental Occupancy Geometry (EOG)

EOG is a layered, model-agnostic framework for auditable ecological support analysis. It connects three distinct objects without treating them as interchangeable:

1. **environmental-state geometry** of observed occurrence clouds in feature space;
2. **spatial support topology** of frozen pointwise support fields in geographical grids;
3. **bridge inference and hypothesis-discriminating surveys** between declared populations or support components.

EOG does **not** fit a species-distribution model, estimate latent occupancy, or claim that a structural component proves demographic or dispersal isolation.

```text
SDM, environmental similarity model, or expert support surface
    -> frozen pointwise support field
    -> EOG spatial support topology
    -> occurrence-anchored and detached support components
    -> EOG bridge and reachability hypotheses
    -> EOG hypothesis-discrimination survey workflow
    -> optional external finite-site optimization by ACSP
```

## Status

Version `0.1.0` began as a frozen extraction of environmental-state geometry from `zuizui0223/acsp` PR #35. Subsequent validation narrowed the defensible interpretation and added bridge, sensitivity, survey, verification, and reporting layers. The spatial support-topology layer absorbs the scientifically defensible component work from `zuizui0223/odsp`; ODSP's widest-path and path-classification implementation is deliberately not duplicated because EOG already owns bridge and bottleneck inference.

## Layer 1: environmental-state geometry

For occurrence-by-feature matrices, EOG reports:

- **standardized span**: a declared quantile of positive pairwise distances after robust scaling;
- **MST compactness** (legacy API name `continuity`): environmental diameter divided by minimum-spanning-tree length;
- **gap strength**: largest positive MST edge divided by the median positive MST edge.

These are descriptions of observed environmental-state clouds. They are not suitability, occupancy, fragmentation, or dispersal estimates. Comparative breadth requires a shared, frozen transformation.

## Layer 2: spatial support topology

For a frozen 2D support array `s(x)`, EOG evaluates connected components of superlevel sets

```text
R_tau = {x : s(x) >= tau}
```

across a predeclared threshold sequence. It reports deterministic component lineages, persistence, occurrence-anchor membership, lower-threshold mergers into anchored components, cell count or area, support summaries, hard masks, and explicit four- or eight-neighbour connectivity.

```python
import numpy as np
from eog import SupportTopologyConfig, infer_support_topology

support = np.array([[0.9, 0.8, 0.0, 0.9, 0.9]])
sea_mask = np.array([[False, False, True, False, False]])

result = infer_support_topology(
    support,
    {"historical_population": (0, 0)},
    SupportTopologyConfig(
        thresholds=(0.8, 0.6, 0.4),
        neighbourhood=4,
        minimum_persistence_steps=2,
    ),
    missing_mask=sea_mask,
)

for component in result.components:
    print(component.component_id, component.component_class)
```

The identical high local support on the two islands does not imply identical structure: one component is occurrence anchored and the other is detached. Sea cells are unavailable, not merely low-support cells.

See [`docs/sdm_support_topology_positioning.md`](docs/sdm_support_topology_positioning.md) and [`examples/support_topology/synthetic_islands.py`](examples/support_topology/synthetic_islands.py).

## Layer 3: bridge inference and survey decisions

Bridge analysis asks a different question: under declared geographical, environmental, and barrier assumptions, what cumulative-cost or minimax path connects declared nodes or components? The support-topology module does not implement paths, bottlenecks, stepping stones, route redundancy, or hypothesis ranking.

The bridge workflow converts predeclared sensitivity scenarios into hypothesis-specific path support and ranks candidate field sites by how strongly hypotheses disagree there. The score is decision support, not occurrence probability, posterior model probability, or expected information gain.

```bash
eog-hypothesis-survey \
  --scenarios examples/hypothesis_survey/scenarios.csv \
  --families examples/hypothesis_survey/families.csv \
  --candidates examples/hypothesis_survey/candidates.csv \
  --output-dir results/hypothesis_survey
```

The canonical example and audit contract are documented in [`docs/hypothesis_survey_contract.md`](docs/hypothesis_survey_contract.md).

## Installation

```bash
python -m pip install .
```

For direct CHELSA raster sampling used in benchmark work:

```bash
python -m pip install ".[raster]"
```

## Public API

Environmental-state geometry:

- `OccupancyGeometry`
- `infer_occupancy_geometry`
- `fit_robust_reference`
- `infer_comparative_geometry`
- `compare_geometry`

Spatial support topology:

- `SupportGridMetadata`
- `SupportTopologyConfig`
- `OccurrenceAnchor`
- `SupportComponent`
- `SupportTopologyResult`
- `assign_occurrence_anchors`
- `infer_support_topology`
- `summarize_support_components`
- `evaluate_component_recovery`
- `evaluate_support_topology_sensitivity`

Bridge inference and survey decisions:

- `BridgeInference`
- `BridgeSensitivityResult`
- `HypothesisFamilyDeclaration`
- `HypothesisSurveyPipelineResult`
- `infer_bridge`
- `evaluate_bridge_sensitivity`
- `run_hypothesis_survey_pipeline`
- `verify_hypothesis_survey_bundle`
- `render_hypothesis_survey_report`

## Validation and manuscript materials

- `docs/sdm_support_topology_positioning.md`: SDM, topology, bridge, and survey distinctions;
- `docs/odsp_migration_map.md`: copy/adapt/replace/retire decisions and archival plan;
- `examples/support_topology/synthetic_islands.py`: hard-mask island demonstration;
- `tests/test_support_topology.py`: component, persistence, masking, recovery, and determinism tests;
- `docs/multiaxial_methodology.md`: restrained environmental-state geometry position;
- `docs/evidence_ledger.md`: verified results and unsupported claims;
- `docs/frozen_comparison_tutorial.md`: canonical manifest-to-result workflow;
- `docs/hypothesis_survey_contract.md`: bridge-hypothesis CSV and output contract.

## Scientific boundary

EOG converts pointwise environmental support into occurrence-conditioned spatial components and explicit reachability hypotheses. It does not claim to replace standard, dynamic, mechanistic, or process-based SDMs. A support component does not establish occupancy, colonisation probability, historical dispersal, demographic connectivity, genetic isolation, or causal barriers without additional data.

The central manuscript question is:

> How can pointwise species-distribution support be transformed into occurrence-conditioned spatial components and competing reachability hypotheses in fragmented landscapes?

## Provenance

The original environmental-state implementation was copied from ACSP main commit `cfa24ba30fa0607e530d5cf716ce8729d54d773e`. The support-topology design adapts ODSP's defensible frozen-field, anchor, component, recovery, and audit concepts while retiring its duplicated widest-path layer.

## License

MIT.
