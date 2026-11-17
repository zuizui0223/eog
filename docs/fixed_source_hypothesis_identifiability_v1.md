# Conditional source uniqueness is not global source identification

## Main exact synthetic finding

In the already declared finite candidate universe of all 64 directed simple graphs on abstract nodes A, B, C, each of three alternative singleton fixed-source hypotheses has 16 compatible graph rules. But this is not enough to identify a founder if the **graph itself remains unknown**.

| Number of singleton-source hypotheses compatible in a given graph | Graph rules | Compatible (graph, source) pairs |
| --- | ---: | ---: |
| None | 27 | 0 |
| Exactly one | **27** | 27 |
| Exactly two | 9 | 18 |
| All three | 1 | 3 |
| **Total** | **64** | **48** |

Nine graphs uniquely support A, nine uniquely support B, and nine uniquely support C, conditional on each graph being selected. With the graph rule unknown, the projection of all **48** compatible graph-source pairs still includes **A, B and C**. Thus all three sources remain logically possible in the declared universe, even though 27 of its individual rules are source-specific.

The only graph compatible with all three source hypotheses is the complete six-edge directed graph, which is **maximally permissive**, not the automatically preferred ecological mechanism.

## Independent combinatorial derivation

Every singleton source must reach both other observed positives in one EOG propagation step. Its two outgoing directed edges must both exist. Each candidate source has one successful two-bit pattern and three unsuccessful patterns. The outgoing two-edge groups of A, B and C are disjoint in this simple graph universe.

The number of graphs supporting exactly k out of three sources is:

\[
\binom{3}{k}3^{3-k},\qquad k=0,1,2,3.
\]

This yields 27 / 27 / 9 / 1 graphs. The joint compatible pair count is 27×1 + 9×2 + 1×3 = **48**. Independently, each of the three sources is supported by 16 graphs, giving 3×16 = 48.

These are complete counts only in the **synthetic three-node, one-step, 64-rule universe**. They are not model probabilities, real dispersal rates or frequencies of ecological founders.

## Three epistemic states the API keeps apart

**Selected synthetic graph (conditional uniqueness).** For the abstract hub topology A↔C↔B with no direct A↔B, only a fixed singleton source at C can support all three positives in one step. The source is conditionally unique **given that graph topology**. This does not prove the graph is true or that C was a real historical founder.

**Unknown graph (marginal ambiguity).** With all 64 graphs still allowed, each source A/B/C survives in some compatible graph-source assignment. No global source hypothesis is selected by these positives.

**Only one candidate source declared.** A one-hypothesis analysis cannot identify its source relative to alternatives that were never tested. The API labels this a single-candidate declaration, not an identification test. If no graph/source pair is compatible, it labels the declared universe falsified, not identified.

## New optional EOG API

The native EOG v2 traversability facade exports:

    summarize_fixed_source_hypothesis_identifiability(audit)

It accepts the existing result from:

    audit_fixed_source_hypotheses(operators, positive_occurrences, source_hypotheses, max_steps=...)

No graph reconstruction, new data access, source estimation, extra model fitting or response inspection occurs in the new summarizer.

It validates frozen rule IDs, operator identity ledger, per-hypothesis compatible/incompatible partitions, per-rule source status and aggregated union/intersection before returning:

- Support-cardinality counts across frozen graph rules (0, 1, 2, ... compatible sources)
- Complete compatible graph/source pair identities and their count
- Candidate graph IDs with **exactly one** supported source
- Counts of conditional unique graph rules for each source hypothesis
- All source IDs still possible after considering every compatible graph
- Explicit status for multiple possible sources, unique only within declared rule/source universe, one candidate declared, or no compatible graph-source assignment
- A stable parent result fingerprint, and explicit false flags for historical-origin proof and true graph identification

This is a new optional result dataclass; the prior EOG v2 result types, existing score semantics and fingerprints are unchanged. Tampered or inconsistent source-rule audit ledgers fail closed.

Reproduction: implementation at src/eog/v2/fixed_source_hypothesis_sensitivity.py; tests at tests/test_fixed_source_hypothesis_identifiability.py; fixed post-exposure design at validation/fixed_source_hypothesis_identifiability_v1/protocol.json.

## Scope and scientific STOP

No historical founder is independently identified. The actual Hungary wetland records establish methods/dates of observed positive records, not historical dispersal origins. The original EOG v6–v8 world-universe expansions are frozen and not rescored. Annually changing realized source states belong to sequential_world_forecast. No fourth EOG-WF scored empirical endpoint is added, and the frozen 3 scored / 31 scientific STOP / 3 administrative exclusions remain intact. Both PR #697 and PR #698 remain Draft/unmerged.
