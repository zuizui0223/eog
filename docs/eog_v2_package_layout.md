# EOG v2 package layout

## Status

`eog.v2` is a **compatibility namespace over three explicit prospective facades**, not a second independent EOG identity. The active integrated scientific direction is defined in [`development_mainline.md`](development_mainline.md).

Repository reorganization must not alter, rerun, rescue or reinterpret frozen v0.1/v2 results, contracts or fingerprints.

## Public boundary

The repository keeps the frozen v0.1 compatibility API under root `eog`. Prospective work is grouped behind:

- `eog.v2.reachability` — transition propagation, first passage, finite-world reconstruction, declared relaxation families, temporal world-flow/reconstruction and positive survey discrimination;
- `eog.v2.traversability` — geographic/IBD, environmental/IBE, barrier and pathwise transition constraints;
- `eog.v2.validation` — independent occurrence, genetic and directional-evidence validation;
- `eog.v2.cli` — routing for already-existing console commands only.

Historical `from eog.v2 import ...` convenience names remain available through a lazy compatibility facade. **New prospective names do not automatically get mirrored onto `eog.v2` root.**

## Reachability internals

The explicit reachability facade currently composes these internal modules:

- `world_reconstruction.py` — exact finite `W(O)`, world-indexed flow sets, non-dominated relaxation frontier and static positive survey discrimination;
- `relaxation_family.py` — predeclared monotone one-dimensional `lambda` families and first-possible / first-robust basin merge;
- `temporal_reachability.py` — ordered time-varying transition worlds and finite temporal flow sets;
- `temporal_reconstruction.py` — time-stamped **positive** occurrences as necessary `reached by time` constraints;
- `temporal_survey.py` — positive `(node, time)` candidate discrimination among still-compatible temporal worlds.

These are implementation layers under **one reachability estimand family**, not separate public EOG subdisciplines.

## Current prospective reachability surface

Static finite-world names on `eog.v2.reachability` include:

- `FiniteWorld`, `FiniteWorldReconstruction`, `FiniteWorldFlowSet`;
- `RelaxationFrontier`, `ReconstructionUpdate`, `PositiveOccurrenceSurveyRanking`;
- `forward_reachable_configuration`, `reconstruct_compatible_worlds`, `build_world_flow_set`;
- `minimum_relaxation_frontier`, `compare_reconstructions`, `rank_positive_occurrence_candidates`.

Declared basin-merge names:

- `MonotoneRelaxationFamily`, `BasinMergeResult`;
- `build_monotone_relaxation_family`, `infer_basin_merge`.

Temporal names:

- `TemporalWorld`, `TemporalFlowSet`, `build_temporal_flow_set`;
- `TemporalWorldReconstruction`, `TemporalReconstructionUpdate`;
- `reconstruct_temporal_worlds`, `compare_temporal_reconstructions`;
- `PositiveTemporalSurveyRanking`, `rank_positive_temporal_occurrence_candidates`.

Row-level helper dataclasses/status aliases remain internal.

## Scientific contracts

### Separate IBD / IBE / barrier axes

Geographic, environmental and barrier relaxation remain separately inspectable. They are not silently converted to one weighted distance.

### Scalar water level only when declared

A scalar `lambda` is accepted only for a predeclared monotone one-dimensional family. Within each analytical variant, node/source/loss contracts stay fixed and transition support cannot decrease as `lambda` increases.

### Time is ordered, not calibrated

Temporal `time_labels` are ordered state labels. They are not calendar time, generation length or demographic duration unless externally calibrated.

### Positive temporal evidence only

A time-stamped positive occurrence requires that the node was reached **by** the declared time. It is not an exact-time occupancy likelihood. Non-detection is not absence without a detection model.

### Support is not automatically probability

Existing transition/reachability quantities are model support. Package naming or reorganization must not promote them into colonisation, dispersal, migration or occupancy probabilities without external calibration.

### Claim strength follows coverage

`robustly_unreachable` means unreachable over the exhaustively declared finite world set relevant to that result. It is not universal biological impossibility.

## Compatibility and cleanup rules

1. Reuse an existing facade before creating a new namespace.
2. Keep system-specific A-Islands/Tanzania/Finland/Ryukyu/Zhoushan code out of generic API names.
3. Do not duplicate transition, first-passage, bottleneck or reconstruction logic for a new narrative.
4. Keep new prospective names off `eog.v2` root unless an actual compatibility obligation exists.
5. Search frozen reproduction paths before any physical module move/delete.
6. Preserve compatibility aliases where frozen workflows need them.
7. Package-wide regression belongs to Package checks; scientific confirmation workflows keep narrow path scopes.
8. Presentation/manuscript code must not become a core dependency.
9. Cleanup must not change frozen inputs, results, seeds, fingerprints, promotion gates or claim directions.

## Console boundary

Existing `eog-v2-*` console commands continue to route through `eog.v2.cli`. No finite-world, temporal-flow, basin-merge or temporal-survey CLI is added while those prospective APIs are still being falsified and consolidated.

## Scientific boundary

Package layout is an implementation-maintenance concern. Reorganization must never be used to obtain a more favourable empirical result or conceal adverse/null/indeterminate evidence.
