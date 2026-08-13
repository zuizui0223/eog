# Environmental Occupancy Geometry (EOG)

EOG is a layered, model-agnostic framework for auditable ecological support analysis. It connects distinct objects without treating them as interchangeable:

1. **environmental-state geometry** of observed occurrence clouds in feature space;
2. **spatial support topology** of frozen pointwise support fields in geographical grids;
3. **bridge inference and hypothesis-discriminating surveys** between declared populations or support components.

A separate prospective **EOG v2** line is now under development for dynamic source-conditioned island reachability. It keeps local viability, reachability, target capture, persistence and observation processes separate and uses a graph-native rather than necessarily raster-native prediction object.

EOG does **not** fit a species-distribution model by default, estimate latent occupancy, or claim that a structural component proves demographic or dispersal isolation.

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

Empirical structural validation includes both a positive limited-reference result and adverse strong-reference boundaries:

- **A-Islands limited reference:** connected frequency retained held-out incidence ordering after conditioning on pointwise climatic support and nearest-training-occurrence distance; conditional concordance `0.6177466` for 845 estimable species.
- **A-Islands prospective strong reference:** the pre-frozen `C − R3` extension was adverse (`+0.00348518` log loss), so the generic static connected-frequency addition is not promoted beyond the strong island-isolation reference.
- **Tanzania forest fragments:** adding frozen geography-only EOG connected frequency to a patch-area/current-flow reference worsened primary leave-one-fragment-out log loss by `0.0321131`; spatial-block sensitivity remains weaker and uncertain.

These results establish a conditional boundary rather than universal superiority.

### EOG v2 prospective development

Issue #141 and draft PR #142 develop a separate dynamic island-reachability method without reopening the frozen v0.1 results. Current v2 components include:

- directed geography/environment/barrier/direction/target-capture transition support;
- explicit-loss sub-stochastic propagation;
- finite-horizon first-passage support and source attribution;
- integrated edge flux, route entropy and bridge-node importance;
- separate V/R/C/P/O state layers;
- deterministic synthetic archipelago and neutral-genetic validation infrastructure;
- fixed-source occurrence comparator confirmation;
- exact-eventual first-passage development for long-term genetic connectivity.

The frozen fixed-source occurrence confirmation showed no useful dynamic increment when environment, nearest source, source pressure, geography-current-flow or static topology contained the known truth, while dynamic EOG-R retained substantial held-out signal for bottleneck and directional truths. This remains synthetic method validation, not empirical superiority evidence.

See `docs/eog_v2_dynamic_island_reachability.md`, `docs/eog_v2_estimand_contract.md`, and `docs/eog_v2_occurrence_comparator_contract.md`.

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

The identical high local support on two islands does not imply identical structure: one component can be occurrence anchored while another remains detached. Sea cells are unavailable, not merely low-support cells.

## Layer 3: bridge inference and survey decisions

Bridge analysis asks a different question: under declared geographical, environmental, and barrier assumptions, what cumulative-cost or minimax path connects declared nodes or components? The support-topology module does not itself implement paths, bottlenecks, stepping stones, route redundancy, or hypothesis ranking.

The bridge workflow converts predeclared sensitivity scenarios into hypothesis-specific path support and ranks candidate field sites by how strongly hypotheses disagree there. The score is decision support, not occurrence probability, posterior model probability, or expected information gain.

```bash
eog-hypothesis-survey \
  --scenarios examples/hypothesis_survey/scenarios.csv \
  --families examples/hypothesis_survey/families.csv \
  --candidates examples/hypothesis_survey/candidates.csv \
  --output-dir results/hypothesis_survey
```

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

## Scientific boundary

EOG converts pointwise environmental support into occurrence-conditioned spatial components and explicit reachability hypotheses. It does not claim to replace standard, dynamic, mechanistic, resistance, circuit-theory, or process-based models. A support component or uncalibrated EOG-R value does not establish occupancy, colonisation probability, historical dispersal, demographic connectivity, genetic isolation, or causal barriers without additional data.

## Provenance

The original environmental-state implementation was copied from ACSP main commit `cfa24ba30fa0607e530d5cf716ce8729d54d773e`. The support-topology design adapts ODSP's defensible frozen-field, anchor, component, recovery, and audit concepts while retiring its duplicated widest-path layer.

## License

MIT.
