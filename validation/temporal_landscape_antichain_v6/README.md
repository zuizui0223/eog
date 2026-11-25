# Exact, output-sensitive temporal landscape restoration/cut certificates (v6)

## Provenance

Frozen protocol: 8fc4add64eac971be8a8fd295ef6e74b249ec3eb. Base: PR #763 head 3abcb1914ae9d2612a1340ff5ec50cc2c65e1669 (both CI workflows passed). Executed locally with Python 3.13.5, then checked runner and receipt Git blobs against local git hash-object: 3bc7d253dcf135da8801c766195ed6cc4b4a574b and 04dc666e6f4a84a3a66aba22925d1239d14bc8fa. No empirical sources or new EOG-WF endpoint.

## Method

Represent a required set of restored persistent sites by a bit mask. For a time-ordered DAG, keep only inclusion-minimal requirement sets among all paths ending at each vertex. A path extension unions its endpoint requirements with the previous mask. If A is a subset of B at the same vertex, then A union Q is a subset of B union Q for any future continuation Q; discarding B cannot remove a minimal complete restoration. Induction in topological order proves completeness conditional on the fixed finite graph and action semantics. For a nonempty world universe, possible repair takes the inclusion-minimal union of all world families; robust repair takes inclusion-minimal pairwise unions of one requirement set from each world. Cut families follow from v5 blocker duality: iteratively intersect each repair set, extending currently unhit candidates by one member of that set and discarding supersets. Empty families and empty masks retain their v5 algebraic meaning.

This is established antichain propagation, set dominance and hypergraph transversal enumeration, not a new mathematical algorithm. The contribution under evaluation is the exact world-consistent ecological estimand and its computation. The implementation avoids enumerating every intervention subset but remains potentially exponential. Each live minimal-family insertion has a cap of 2,048 labels. Exceeding this cap raises LabelLimit, and the benchmark records an explicit STOP without returning an alleged complete or minimal frontier. This cap is per family, not a bound on total memory, time, or intermediate work. It may stop even when a later reduction would yield a small final family. There is no production API; the runner assumes a declared topological order, protected anchors, nonempty worlds and nonnegative valid masks.

## Frozen results

Small panel: 80 systems, three independent worlds each, eight candidate sites. Independent direct reachability enumerated 61,440 world/action masks, then extracted inclusion-minimal true and false masks. All 800 local and aggregate repair/cut family comparisons passed; maximum live family size 12. The number of enumerated baseline masks is not the number of independent algorithm output comparisons.

Structured scale panel: each world requires its own gateway and one of the shared alternatives; all action sites are initially disabled. Analytical ground truth verifies every local and aggregate repair/cut family.

| Candidate sites | All possible action subsets (not enumerated) | Possible repair sets | All-world repair sets | Possible-loss cuts | Robust-loss cuts | Peak live family |
|---:|---:|---:|---:|---:|---:|---:|
| 24 | 16,777,216 | 63 | 21 | 2 | 4 | 63 |
| 48 | 281,474,976,710,656 | 135 | 45 | 2 | 4 | 135 |
| 96 | 79,228,162,514,264,337,593,543,950,336 | 279 | 93 | 2 | 4 | 279 |

These are deliberately structured examples, not performance estimates for arbitrary 96-site ecological networks. Exhaustive enumeration at these sizes was not run, so no timing-speedup ratio is claimed.

Adversarial panel: serial layers with two alternative sites per layer; the complete repair family has 2^k incomparable choices. Eight layers: 256 repairs/8 cuts, complete. Ten layers: 1,024 repairs/10 cuts, complete. Twelve layers: would require 4,096 repair labels; the 2,048 cap was reached and the solver returned no certificate. Thus output-size explosion remains a binding limit even with 24 sites. The certificate is about the declared finite graph, not actual conservation outcomes.

## Next decision

Do not add more near-identical synthetic panels. A minimum-cost decision-only solver or a certified bound can avoid requiring every minimal family; unlike this full-frontier benchmark, it must state the different estimand and prove optimality or report a gap. Before independent empirical use, declare observed source/target/time anchors, coordinate and detection semantics, externally supported world/transition rules, action definitions and response firewall. The intervention graph must not be presented as estimated ecological efficacy. The closed EOG-WF fresh-endpoint funnel must not reopen. No McKee clock/CRS STOP override or 2h holdout access. Frozen 3 scored / 31 scientific STOP / 3 administrative exclusions unchanged.

Replay: python validation/temporal_landscape_antichain_v6/run.py
