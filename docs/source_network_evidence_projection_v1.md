# When can externally declared network evidence identify a source under graph uncertainty?

## Result: source identity can be distinguished without knowing the exact graph

The previous EOG fixed-source-hypothesis audit on all 64 possible directed simple A/B/C graphs found 48 compatible graph/source assignments, retaining all three possible source hypotheses A, B and C. This source ambiguity is NOT resolved by arbitrarily selecting a graph that happens to have one unique source. The new audit asks what additional information about the directed network could change the *projection over ALL compatible graph/source assignments*.

In the same frozen toy universe (six possible directed edges, all three nodes recorded positive, one-step reachability, 64 possible graph rules, alternative singleton source hypotheses A/B/C), the exact results are:

| Additional declared directed-edge statements | Graph rules matching network declarations | Graphs also compatible with some fixed-source hypothesis | Compatible graph/source pairs | Still-possible sources |
| --- | ---: | ---: | ---: | --- |
| None | 64 | 37 | 48 | A, B, C |
| A>B structurally unavailable | 32 | 14 | 16 | B, C |
| A>B and B>A both structurally unavailable | 16 | 4 | 4 | C ONLY |
| A>B and B>A both PRESENT | 16 | 13 | 20 | A, B, C |
| Both outgoing A edges unavailable (A>B, A>C) | 16 | 7 | 8 | B, C |
| ALL SIX directed edges PRESENT | 1 | 1 | 3 | A, B, C |

The unique C case does NOT recover a unique full graph: FOUR distinct graph rules remain compatible with C, while A and B cannot each reach all other positive nodes in one step. This separates *source identification within the declared rule universe* from *graph rule identification*.

The two explicit network-nonedge declarations from different source nodes are structurally important: they independently eliminate two alternative candidate sources. A second nonedge from the SAME source does not eliminate a second candidate source and therefore leaves ambiguity.

Across all 15 unordered pairs of different edge labels (six choose two) asserted structurally unavailable, 12 pairs involve TWO different source tails, and all 12 give one possible source; the other 3 are two outgoing nonedges from the SAME source and leave two source hypotheses possible. All results are exact enumerations of the specified synthetic graph candidate universe.

## Why positive edge evidence alone does not identify a source

Whenever only positive edge-presence observations are added, the complete graph with all six edges remains admissible. That fully connected graph is compatible with A, B and C as the putative sole source under one-step propagation. Thus ANY collection of only positive edges is insufficient to identify a unique source within this unrestricted graph family.

This is a logical property of the declared universe, NOT a claim that field evidence for positive movement edges is uninformative for other questions. For example it could constrain permeability, calibrate edge probabilities or distinguish classes of graph histories under different modeling assumptions.

## Observation-process distinction is mandatory

The function distinguishes a declared edge status (present versus structurally_unavailable) from a recorded biological occurrence. A survey *nondetection* is NEVER an authenticated structural nonedge, an absence of a corridor or proof that an immigrant cannot cross. A status of structurally_unavailable is a **strong graph-level assertion** that must be supported by independent external evidence if used on real systems.

The API accepts two provenance-basis labels, synthetic_known_truth and declared_external_structural_assessment. Both represent **caller declarations**. The second does NOT automatically certify field validation; neither the code nor this report checks raw biological data to authenticate barriers, impermeability, historic source status, spatial completeness, zero movement probabilities or mechanism A/B/M. The output explicitly sets input_structural_edge_truth_independently_verified=False and source_historical_origin_verified=False.

In a real ecological system, a transport route apparently absent from a sampled network can remain possible through unsurveyed stepping-stones, historic connections, rare long-distance dispersal or directional nonstationarity. A definitive structural nonedge therefore requires stronger evidence than site-level occupancy or detection data. With only source positivity and no truly independent directional network evidence, A/B/C remain unidentified.

## New opt-in EOG v2 API

The new public method is:

    eog.v2.traversability.audit_declared_directed_network_evidence(
        operators,
        positive_occurrence_ids,
        source_hypotheses,
        evidence,
        max_steps=1,
    )

Each evidence entry is a DeclaredDirectedEdgeEvidence(source_id, target_id, status, evidence_basis, evidence_ref). Status is exactly present or structurally_unavailable. The evidence_basis is exactly synthetic_known_truth or declared_external_structural_assessment, and a nonblank evidence_ref is required for audit trail. Generic strings such as species_nondetection, unsurveyed and model_prediction are rejected as evidence basis.

The function retains ORIGINAL candidate transition operator objects and fingerprints. It first invokes the existing EOG audit_fixed_source_hypotheses and summarize_fixed_source_hypothesis_identifiability, then filters the immutable operator roster by all declared directed edge statements, and invokes the same native EOG source-hypothesis functions on the retained graph subset.

Returned data include:
- Exact admitted and excluded rule IDs, with the original frozen graph fingerprint inventory
- All original and post-evidence compatible graph/source pair counts and possible source IDs
- Original and post-evidence source projection objects with rule and source identities intact
- Dedicated status for one source conditionally supported, multiple possible, no compatible pair, empty graph universe or one previously declared source candidate
- False flags for independent validation of network structural evidence and historical origin
- Deterministic SHA-256 fingerprint of explicit evidence declarations and both finite projections

No graph edge, source origin or posterior is estimated by this method. It is a finite rule-constraint operation on declared objects.

## Exact tests, nonredundancy, and scientific STOP

Pre-computation post-exposure protocol: validation/source_network_evidence_projection_v1/protocol.json.

Implementation: src/eog/v2/declared_network_edge_evidence.py, exported through native eog.v2.traversability and historical lazy eog.v2.

Tests: tests/test_declared_network_edge_evidence.py. They verify zero/one/two declared nonedges, 12/15 two-nonedge source-identifying pairs, both outgoing edges from one source, two or all six positive-edge records, an empty graph universe, a universe with graph rules but no compatible source, canonical evidence order, and refusal to silently substitute nondetection or model predictions for structural nonedges.

Earlier EOG v7 target-specific adaptive evidence planning already explored source/order/barrier observations as separate *hypothetical* measurement actions; its frozen results are NOT rerun or counted as new evidence. This new result instead supplies an operational contract for how exactly stated directed-edge data affect the *joint graph/source compatibility projection* and marks the field-validation limit.

No new empirical response payload, biological true absence, transport model calibration, verified founder, causal restoration benefit, EOG A/B/M mechanism, source posterior, fresh EOG-WF endpoint or automatic PR merge is claimed. The existing EOG-WF 3 scored endpoints / 31 scientific STOPs / three administrative exclusions remain frozen. PR #697 and PR #698 both remain Draft/unmerged.
