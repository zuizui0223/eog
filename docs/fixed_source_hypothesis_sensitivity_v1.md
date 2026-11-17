# Fixed-source hypothesis sensitivity: shared and source-dependent EOG rule support

## What was added

The opt-in eog.v2.traversability.audit_fixed_source_hypotheses API answers a narrower question than the original positive-observation filter guard: when the **positive occurrence set and all candidate transition rules stay fixed**, what changes if a different **declared fixed-source hypothesis** is used?

Inputs are one mapping of named DynamicTransitionOperator rules, one positive occurrence roster and explicitly named alternative source-ID sets, with one shared max_steps, support floor and tolerance. The native compare_occurrence_transition_rules API evaluates each fixed-source hypothesis independently on that **same** frozen rule universe.

The result partitions candidate-rule identities into three mutually exclusive statuses:

1. **source_robust**: compatible under **every** declared source hypothesis (intersection).
2. **source_dependent**: compatible under **some but not all** source hypotheses (union minus intersection).
3. **unsupported_under_all_declared_sources**: compatible under **none** of the listed hypotheses (complement within the fixed candidate rules).

The source_possible union is the first two categories combined. There is NO inference of historical origin, posterior probability, truly occupied source state, dispersal or ecological viability outside the frozen rule candidates. The output includes each rule's supporting hypothesis IDs, native EOG comparison fingerprints, and an explicit not-historically-verified source flag.

## Exact synthetic three-node counts

Freeze all 64 possible simple directed graphs on A/B/C (six directed non-self edges, one-step reachability, equal positive edge support and fixed loss support 1). Use all three abstract nodes as recorded positives. Consider three *alternative* singleton-source hypotheses: only A, only B, or only C. These are not real wetland sites.

| Compatibility across the 64 graphs | Exact number |
| --- | ---: |
| Source A alone | **16** |
| Source B alone | **16** |
| Source C alone | **16** |
| **Every** source hypothesis compatible | **1** |
| **At least one** source hypothesis compatible | **37** |
| **Some but not all** hypotheses compatible | **36** |
| **No** declared hypothesis compatible | **27** |

The proof is independent of numeric first-passage computation. For source A to reach the other two nodes in one step, both outgoing edges A>B and A>C must exist, while the other four edges are arbitrary, giving 2^4=16 graphs. Source B and C are symmetric. Pairwise intersections of any two source hypotheses fix four different directed edges, leaving 2^2=4 graphs. The triple intersection fixes all six directed edges and has exactly one graph. Inclusion-exclusion gives **3*16 - 3*4 + 1 = 37** distinct source-possible graphs.

For positive nodes A/B only, the alternative single fixed sources A or B support 32 graphs each; 16 are shared, 48 are possible under either, 32 are source-dependent and 16 are unsupported under both.

**This is not self-excluded peer-source compatibility**. In the earlier exact three-node EOG study self-excluded diagnostics on all A/B/C positives supported **27** of the 64 graphs. That is NOT the same quantity as 37 graphs compatible under at least one alternative declared singleton source. The two source policies answer different questions.

## Existing EOG work not repeated

The archived EOG v6–v8 source/barrier/analyst world-growth experiments already showed that universe expansion can erode universal certificates, with v6 retention of **96.1%** robust reachability versus **64.8%** robust impossibility and v8 quantitative threat counts. Those results are frozen and are not regenerated or rescored here.

The new operation instead holds the *rule universe fixed* and tests how one alternative declared source assignment versus another changes the compatibility identities. It complements the older world-growth experiments, and it does not open any new empirical EOG-WF endpoint.

Likewise, Glanville's annual realized source states belong in the existing sequential_world_forecast API. Candidate-fixed-source comparisons in a single cross-section are NOT time-indexed predictions. Algar source qualification establishes response-independent data readiness, not historical ancestry; original Hungary wetland date/method source-positive records do not establish historical founders.

## Reproducibility and safeguards

- Implementation: src/eog/v2/fixed_source_hypothesis_sensitivity.py.
- Public route: eog.v2.traversability.audit_fixed_source_hypotheses, with historical eog.v2 lazy export.
- Unit tests: tests/test_fixed_source_hypothesis_sensitivity.py covering all 64 synthetic graph rules, two-node subset, multi-source alternative, deterministic fingerprints and invalid node/source hypotheses.
- Post-exposure fixed design: validation/fixed_source_hypothesis_sensitivity_v1/protocol.json.

The function fails closed if candidate operator node universes differ, source IDs are not contained in recorded positive nodes, one hypothesis has duplicate or empty source IDs, duplicate hypothetical source sets are given under different labels, or a hypothesis has no non-source target. Missing observations are UNKNOWN, not true biological absences.

These are synthetic finite candidate-rule compatibility calculations, not historical source inference, ecological occupancy, original unmarked refits, causal A/B/M identification, or restoration treatment effects. The locked EOG-WF three scored / 31 scientific STOP / three administrative exclusion accounting is unchanged. PR #698 remains Draft/unmerged; source-rich PR #697 is also unchanged and unmerged.
