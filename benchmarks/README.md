# Benchmark map

This directory contains several generations of EOG validation, frozen reproduction, and prior-art boundary work. It is **not** a list of independent EOG methods.

For the active scientific direction, start from [`../docs/development_mainline.md`](../docs/development_mainline.md) and [`../docs/eog_v2_progress.md`](../docs/eog_v2_progress.md).

## Active decision path

The current integrated line is in ecological validation, not operator growth.

1. `finite_world_archetype_matrix.py` — internal known-truth gate for the finite world architecture.
2. `inverse_estimand_comparator.py` — compact prerequisite comparator showing what timing / axis identity / set-valued output retain relative to deliberately compressed summaries. This is the preferred synthetic entry point for the current inverse estimand.
3. `aislands_worldset_adapter.py` + `run_aislands_worldset_exploratory.py` — response-free exploratory real-data representation of the frozen A-Islands scenario universe.
4. A-Islands exploratory gate — preserved scenario identity passed the predeclared development gate; this is exploratory because A-Islands had already been viewed.
5. Independent confirmation — must be frozen before outcome access. A blocked confirmation is evidence and must not be repaired after outcome inspection.

Do not add a new comparator merely because another adjacent method can be named. Add one only when it tests a claim not already bounded below.

## Prior-art / negative-boundary comparators

These files are preserved because they document claims EOG **must not** present as algorithmic novelty. They are supporting boundary evidence, not separate active method lines.

| File | Boundary established |
|---|---|
| `bridge_vs_temporal_reconstruction.py` | Static bridge/connectivity and time-constrained realizability are different estimands; bridge logic itself is not new. |
| `dynamic_connectivity_negative_boundary.py` | Time-respecting dynamic connectivity / reachability structure is prior art. |
| `consensus_vs_universal_certificate.py` | High scenario agreement is not the same statement as invariance over every declared world. |
| `keitt_critical_distance_boundary.py` | Critical geographic thresholds, component merger and stepping-stone critical distances are prior art. |
| `mce_environmental_exposure_boundary.py` | Minimum cumulative environmental exposure / least-exposure paths are prior art. |
| `circuit_world_aggregation_boundary.py` | Multiple-path integration and redundancy are prior art; the EOG-specific caution is not to union mutually exclusive worlds before inference. |
| `functional_habitat_world_boundary.py` | Suitable + accessible habitat and E/G/T-space integration are prior art; explicit alternative-world identity is a separate uncertainty object. |
| `history_matching_nroy_boundary.py` | Generic filtering to a compatible / NROY model set and sequential contraction are prior art. |
| `falsification_frontier_boundary.py` | Generic minimum-relaxation / Pareto falsification-frontier mathematics are prior art. |

The concise authoritative summary of these boundaries lives in `docs/eog_v2_progress.md`; detailed values live here and in matching tests.

## Frozen empirical/reproduction material

A-Islands, Tanzania, Finland and other older benchmark files may still be required by frozen workflows, manuscripts, or evidence ledgers. Their presence does not make them active architecture.

Do not physically delete an older benchmark solely because its narrative is obsolete. First verify that no frozen reproduction path, expected artifact, workflow, manuscript bundle, or fingerprint depends on it.

## Cleanup rule for this directory

- Keep one active narrative in the mainline/progress docs.
- Keep synthetic comparators small and claim-specific.
- Prefer one index entry over another narrative markdown file.
- Keep system-specific exploratory/confirmation code out of production APIs.
- Close blocked confirmation branches rather than weakening a pre-outcome contract to make them run.
- Preserve failures, nulls and exact hashes as evidence.
