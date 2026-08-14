# Environmental Occupancy Geometry (EOG)

EOG is an auditable ecological framework for asking a broader question than local suitability alone:

> **Given an observed distribution, what geographic–environmental distribution-forming structures are compatible with it, and which structures remain possible, unresolved, or excluded?**

The repository contains a frozen v0.1 evidence line plus prospective reachability/traversability operators. The active development direction is now to integrate those operators into a single **distributional-realizability / world-reconstruction** framework rather than continue adding parallel EOG variants.

See [`docs/development_mainline.md`](docs/development_mainline.md) for the active scientific and cleanup contract.

## Core distinction

EOG keeps the following objects separate:

1. **local viability/support** — whether a state is locally compatible with a declared environmental model;
2. **environmental-state geometry** — how observed occurrences occupy environmental feature space;
3. **spatial support topology** — how frozen support fields form geographic components;
4. **reachability/traversability** — which state-to-state transitions are compatible with declared geographic, environmental and barrier assumptions;
5. **distributional realizability** — whether an observed occurrence configuration can be produced under those assumptions;
6. **world reconstructability** — how tightly the observations constrain the set of compatible distribution-forming worlds.

Observed occurrences are treated as realized states that constrain possible distribution-forming processes. They are **not** treated as proof of one unique historical route.

## Active development direction

The current conceptual target is a distributional-watershed representation:

```text
observed occurrences
        ↓
compatible ecological / analytical worlds
        ↓
one auditable transition landscape per world
        ↓
branching and merging reachability flow
        ↓
set of defensible flow distributions
        ↓
robust / contingent / unresolved / excluded structure
        ↓
next observation that best discriminates remaining worlds
```

The watershed language is structural, not decorative:

- occurrence anchors define realized states;
- reachable components act as basins;
- supported transition sequences act as channels or tributaries;
- bottlenecks and divides limit basin connection;
- a declared relaxation level acts as a water level;
- the first level at which disconnected occurrence basins merge is a minimum-required-relaxation diagnostic.

Geographic isolation (IBD-like) and environmental isolation (IBE-like) are retained as separate axes rather than being collapsed automatically into one weighted distance.

This integrated world-set / probability-set engine is **active development**, not yet a completed or empirically promoted EOG claim.

## Implemented layers

### Environmental-state geometry

For occurrence-by-feature matrices EOG provides standardized extent, MST compactness, gap diagnostics, shared-reference comparisons and sampling/uncertainty audits. These describe observed environmental-state clouds; they are not suitability, occupancy or dispersal estimates.

### Spatial support topology

For a frozen 2D support field, EOG tracks superlevel-set components across declared thresholds, including occurrence anchoring, persistence, mergers, masks and deterministic fingerprints.

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
```

Identical local support on two islands does not imply identical distributional structure: one component may be occurrence anchored while another remains detached.

### Bridge and survey operators

Bridge analysis evaluates declared geographic, environmental and barrier transition hypotheses between nodes/components. Survey tooling ranks observations that discriminate among declared hypotheses. These outputs are decision/structural support, not posterior historical-route probabilities.

### Prospective `eog.v2` operators

The existing v2 namespace is retained as a compatibility layer with three facades:

- `eog.v2.reachability` — dynamic transition operators, first passage, flux and graph diagnostics;
- `eog.v2.traversability` — geographic/environmental transition constraints and pathwise ecological continuity;
- `eog.v2.validation` — independent occurrence, genetic and directional-evidence validation.

These are now treated as operators supporting the integrated mainline, not as separate competing EOG identities. Existing v2 quantities remain uncalibrated model support unless independent calibration justifies stronger probability/process language.

## Frozen evidence is preserved

EOG has accumulated positive, adverse, null and indeterminate benchmarks. Cleanup must not erase or retune them. In particular, previously frozen A-Islands, Tanzania, Finland, genetic/reference and synthetic validation outcomes remain evidence boundaries even when they do not support promotion.

The repository keeps those results, fingerprints and protocols for reproducibility. See:

- [`docs/evidence_ledger.md`](docs/evidence_ledger.md)
- [`docs/claim_matrix.md`](docs/claim_matrix.md)
- [`docs/ci_scope_policy.md`](docs/ci_scope_policy.md)
- [`docs/eog_v2_progress.md`](docs/eog_v2_progress.md)

A negative result is not a legacy implementation to be deleted merely because the scientific story changes.

## Repository architecture

The cleanup policy is intentionally conservative:

- root `eog` remains the frozen/stable compatibility API;
- `eog.v2` contains prospective operator facades;
- system-specific A-Islands/Tanzania/Finland/Ryukyu/Zhoushan code is validation/adapter material, not generic core API;
- `benchmarks/frozen/`, manifests, fingerprints and evidence documents are preservation targets;
- manuscript/submission assets preserve publication provenance and do not define package architecture;
- new scientific ideas should reuse existing operators instead of creating another top-level EOG branch, module family or workflow suite.

## Installation

```bash
python -m pip install .
```

For CHELSA/raster benchmark work:

```bash
python -m pip install ".[raster]"
```

## Stable root API

The root compatibility API includes environmental geometry, comparative references, support topology, bridge inference and hypothesis-discriminating survey utilities. Existing direct imports remain supported for frozen reproduction paths; new prospective work should prefer the documented facades rather than widen the root namespace.

Examples include:

- `OccupancyGeometry`, `infer_occupancy_geometry`
- `fit_robust_reference`, `infer_comparative_geometry`, `compare_geometry`
- `SupportTopologyConfig`, `infer_support_topology`
- `BridgeInference`, `infer_bridge`, `evaluate_bridge_sensitivity`
- `run_hypothesis_survey_pipeline`, `verify_hypothesis_survey_bundle`

## Scientific boundary

EOG does not currently justify calling uncalibrated reachability support an occupancy probability, colonisation probability, dispersal probability, migration rate, historical route, demographic connectivity or ancestry estimate.

The active direction is explicitly conservative: preserve alternative compatible worlds when they cannot be distinguished, and make a strong impossibility claim only when it survives the declared admissible world set with appropriate coverage/certification.

## Provenance

The original environmental-state implementation was extracted from ACSP. The support-topology design incorporates the defensible frozen-field, occurrence-anchor, component, recovery and audit concepts previously developed in ODSP while avoiding duplicate path implementations. Later prospective validation layers remain reproducible through their frozen contracts and evidence ledgers.

## License

MIT.
