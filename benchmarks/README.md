# Benchmark map

This directory contains EOG validation, frozen reproduction and prior-art boundary work. It is **not** a catalogue of separate EOG methods.

For the active scientific direction, start with:

- [`../docs/development_mainline.md`](../docs/development_mainline.md)
- [`../docs/eog_v2_progress.md`](../docs/eog_v2_progress.md)

## Active decision path

The integrated line is no longer in operator growth. Its current evidence status is **exploratory-supported but independently unconfirmed**.

1. `finite_world_archetype_matrix.py` — known-truth finite-world architecture gate.
2. `inverse_estimand_comparator.py` — prerequisite comparator showing what set/world identity can retain relative to compressed summaries.
3. `aislands_worldset_adapter.py` + `run_aislands_worldset_exploratory.py` — exploratory response-free real-data world-set representation.
4. SIVFLORA independent attempt — frozen and stopped pre-outcome at climate coverage.
5. Azores independent attempt — frozen through source/node/climate/world/outcome-contract gates, then stopped pre-model at the literal `Tracheophyta` taxon-scope gate.

Do not add another comparator merely because an adjacent method can be named. Add one only when it tests a claim not already bounded below.

## Azores durable reproduction surface

The completed Azores attempt is preserved without keeping its one-time Actions workflows active.

Contracts:

- `azores_confirmation_node_contract.json`
- `azores_confirmation_climate_contract.json`
- `azores_confirmation_world_contract.json`
- `azores_confirmation_outcome_contract.json`

Reproduction scripts:

- `freeze_azores_climate.py`
- `freeze_azores_world_universe.py`
- `run_azores_confirmation_estimability_gate.py`

Frozen evidence lives under `../validation/azores_confirmation/`; matching tests live under `../tests/`.

Final Azores status: `non_estimable_pre_model_taxon_scope_zero`. The frozen stop must not be repaired post hoc by broadening the taxonomic rule on the already opened source.

## Prior-art / negative-boundary comparators

| File | Boundary established |
|---|---|
| `bridge_vs_temporal_reconstruction.py` | Static bridge/connectivity and time-constrained realizability are different estimands; bridge logic itself is not new. |
| `dynamic_connectivity_negative_boundary.py` | Time-respecting dynamic connectivity / reachability is prior art. |
| `consensus_vs_universal_certificate.py` | High scenario agreement is not invariance over every declared world. |
| `keitt_critical_distance_boundary.py` | Critical geographic thresholds/component merger are prior art. |
| `mce_environmental_exposure_boundary.py` | Minimum cumulative environmental exposure / least-exposure paths are prior art. |
| `circuit_world_aggregation_boundary.py` | Multiple-path redundancy is prior art; premature union of mutually exclusive worlds is the EOG-specific caution. |
| `functional_habitat_world_boundary.py` | Suitable + accessible habitat is prior art; explicit alternative-world identity is a separate uncertainty object. |
| `history_matching_nroy_boundary.py` | Generic compatible/NROY model filtering is prior art. |
| `falsification_frontier_boundary.py` | Generic minimum-relaxation/Pareto frontier mathematics is prior art. |

Detailed values stay in benchmark scripts/tests; the authoritative summary lives in `docs/eog_v2_progress.md`.

## Frozen empirical/reproduction material

A-Islands, Tanzania, Finland and older benchmark files may remain when frozen evidence or reproduction depends on them. Their presence does not make them active architecture.

Do not physically delete older benchmark material until repository search shows no frozen reproduction path, expected artifact, manuscript bundle or fingerprint depends on it.

## Cleanup rules

- Keep one active narrative in canonical docs.
- Keep comparators small and claim-specific.
- Keep system-specific code out of production APIs.
- Preserve blocked/null/adverse results and exact hashes.
- Remove completed one-time workflow scaffolding once durable evidence and reproduction paths are preserved.
- Do not weaken a frozen contract to make a blocked confirmation run.
