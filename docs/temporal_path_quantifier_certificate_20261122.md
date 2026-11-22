# Time-coherent path quantifiers for finite EOG worlds — 2026-11-22

## Target

The static certificate [world_path_quantifier_certificate_20261122.md](world_path_quantifier_certificate_20261122.md) distinguishes **every world has some path** from **one path works in every world**. Temporal-world reachability requires an additional constraint: the complete directed path must follow the *same world's ordered operators*, never a convenient mixture of edges from different worlds or intervals.

The new optional API is eog.v2.reachability.audit_temporal_path_quantifiers(flow, worlds, source_id="A", target_id="C", horizon_index=None, edge_support_floor=0.0), where flow is the existing frozen TemporalFlowSet produced by build_temporal_flow_set(worlds).

The result, TemporalPathCertificate, is an exact structural graph statement for the **exhaustively supplied finite temporal universe** only. It does not infer actual migration history or real colonization probabilities.

## Separate claims

1. **Each-world temporal reachability**: for every world w, some sequence of declared consecutive transitions leads from the selected source to the target by the frozen horizon. Different worlds may use different routes and arrival times.
2. **Common time-indexed path**: one single sequence (t0,A), (t1,B), (t2,C) (or another complete time-respecting sequence) exists **in every declared world**, with the same directed edge during the same interval. This is strictly stronger than (1).
3. **Necessary spatial waypoint**: removing a non-source/non-target node from *every time slice* eliminates all source-target paths within a specified world. Universal necessity requires this in every world and is withheld if any world cannot reach the target.
4. **Necessary time-specific state**: removing one (time, node) state eliminates all target paths. A node can be necessary in every world even when visited at different times across worlds; such a node has no universally necessary (time, node) pair.

These quantities are not substitutes for the forecast's mass support or the temporal landscape's robust/contingent edge classification.

## Controlled counterexamples

| Case | Every world reaches target | Common timed path | Universal waypoint | Universal timed state |
|---|---|---|---|---|
| Different A-B-C and A-D-C pathways in t0-t2 | Yes | No | None | None |
| Shared A-B-C plus optional A-D-C in one world | Yes | Yes | None | None |
| World 1 A-X-C (t2), world 2 A-D-X-C (t3) | Yes | No | X | None |
| Both worlds require X at t1 | Yes | Yes | X | (t1, X) |
| World 1 has A-B at t0, world 2 has B-C at t1 | No | No | Withheld | Withheld |

The last case is the no-splicing failure documented in [world_coherent_reachability_boundary_20261122.md](world_coherent_reachability_boundary_20261122.md). Pooling interval-by-interval possible edges manufactures an A-B-C route supported in no individual world.

A 16-by-16 (256-pair) exhaustive two-corridor truth-table test independently checks the quantifiers against Boolean path algebra. Other tests cover gaps without implicit waiting, spatial revisits at later times, shortened horizons, universe expansion, fingerprint order invariance, support-floor sensitivity and fail-closed validation.

## Operational and scientific limits

- **No waiting or automatic persistence.** Each path must take exactly one positive directed edge per interval until first arrival. No waiting edges are added. The route can revisit a geographic node at a later interval through positive transitions.
- **Arrived by** the target horizon is cumulative first arrival, not necessarily being located at the target in the final snapshot. This matches EOG reached_by_time, rather than exact-time mass_by_world.
- **Raw structural edge threshold** uses raw_support > edge_support_floor. EOG's existing forecast instead uses propagation mass and support_tolerance. A series of weak positive edges can be structurally traversable while its mass is numerically below the forecast cutoff. The certificate exposes mass_based_target_status and structural_mass_status_agreement to reveal disagreement.
- With **multiple initial sources**, TemporalFlowSet summarises the full source mixture. A path conditioned on one source cannot be equated to the mixture's mass status. The API reports mass_status_comparable=False and structural_mass_status_agreement=None. A selected source with zero declared mass is rejected.
- Time labels are index order only; no physical-time calibration is assumed.
- The complete world list, fingerprints, time labels and node identities are checked against the frozen TemporalFlowSet. Any strong claim is conditional on that finite world universe. This is not a universal theorem about biological impossibility nor evidence of empirical predictive superiority.
- The frozen EOG-WF denominator remains **three scored, two favorable, one adverse; 31 scientific STOPs and three administrative exclusions**. No empirical endpoint was opened or rescored.

## Verification

    python -m pytest tests/test_temporal_path_certificates.py -q

Implementation: [temporal_path_certificates.py](../src/eog/v2/temporal_path_certificates.py); public entrypoint: eog.v2.reachability.
