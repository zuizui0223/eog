# ODSP to EOG migration map

## Decision

ODSP is not retained as a separate publication or a second path-analysis package. Its defensible support-field concepts are integrated into EOG as the spatial support-topology layer. ODSP remains unarchived until the EOG integration PR passes all tests and is merged.

## Confirmed overlap

EOG already contains graph construction, geographical and environmental edge costs, structural barriers, minimum cumulative-cost paths, minimax bottleneck paths, path redundancy, sensitivity scenarios, hypothesis-family aggregation, and hypothesis-discriminating survey ranking.

ODSP PR #5 introduced maximum-bottleneck paths from occurrence anchors and classes based on that path capacity. That implementation answers an EOG bridge question and would duplicate existing machinery. It is therefore not transplanted.

## Migration table

| ODSP element | Decision | EOG destination or reason |
|---|---|---|
| Frozen externally produced support field | Adapt | `infer_support_topology` input contract |
| Explicit support validation | Adapt | finite 2D array, hard mask, shape validation |
| Predeclared support thresholds | Adapt | `SupportTopologyConfig.thresholds` |
| Geographic connected components | Replace | regular-grid four/eight-neighbour superlevel components |
| Occurrence-anchor assignment | Adapt | explicit occurrence-to-cell mapping; no silent snapping |
| Component summaries | Adapt | deterministic `SupportComponent` records |
| Multi-threshold persistence | Expand | component birth, identifiable range, persistence, merge threshold |
| Held-out detection recovery | Adapt | `evaluate_component_recovery` |
| Sensitivity and audit tables | Adapt | threshold/neighbourhood scenario audit and fingerprints |
| Deterministic manifests/fingerprints | Adapt | canonical result fingerprint |
| Widest-path environmental continuity | Retire from migration | overlaps EOG minimax/bridge analysis |
| Weak-neck extension class | Retire | path/bottleneck interpretation belongs to bridge modules |
| Distance-only occurrence patch extension | Retire | not a headline EOG estimand |
| Near-disconnected and remote patch labels | Retire | replaced by multi-threshold anchored/detached components |
| ODSP shortest-path/minimax functions | Retire | duplicate EOG bridge code |
| ODSP ACSP export adapters | Retire | ACSP remains an optional downstream optimizer |
| ODSP hypothesis ranking | Retire | EOG already has one verified hypothesis-survey workflow |

## New EOG classes

- `occurrence_anchored_component`: contains an explicitly assigned occurrence anchor when the component lineage appears;
- `persistent_detached_component`: detached lineage identifiable for at least the predeclared persistence steps;
- `transient_detached_component`: detached lineage appearing too briefly to meet the persistence rule;
- `low_support_or_unresolved`: component first appearing at or below an optional predeclared unresolved cutoff.

These are structural labels under a frozen support field, mask, threshold sequence, and neighbourhood rule. They do not prove fragmentation, absence, genetic isolation, demographic independence, or dispersal limitation.

## Layer interface

The topology layer may export component summaries, centroids, representative cells, or aggregate support attributes for later graph declaration. It does not automatically build bridge edges or run a path algorithm. Any later bridge analysis must explicitly declare nodes, geographic/environmental/barrier costs, source and target, and sensitivity assumptions using existing EOG modules.

## Empirical work remaining

The Campanula microdonta / シマホタルブクロ case should be migrated only after freezing:

1. historical occurrence anchors;
2. a training-only support surface;
3. thresholds, neighbourhood rule, mask, and resolution;
4. held-out or later detections.

Because earlier field outcomes have already influenced method development, the existing case must be labelled exploratory. A future confirmatory analysis should use island- or region-level holdout and compare topology against local support, nearest-anchor distance, support plus distance, and single-threshold components.

## ODSP archival plan

After the EOG integration PR is merged and CI passes:

1. update the ODSP README to state that its defensible support-topology work is superseded by EOG;
2. link the exact EOG merge commit and documentation;
3. mark ODSP PR #5's widest-path layer as not migrated because it duplicates EOG bridge inference;
4. preserve ODSP history read-only for provenance;
5. archive the GitHub repository only after the supersession notice is committed.
