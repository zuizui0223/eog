# EOG v2 occurrence-conditioned transition-rule compatibility contract

## Status

Prospective method-development contract for issue #141. This contract is frozen before any new empirical occurrence or genetic dataset is used to compare transition rules. It does not alter or rescue any frozen v0.1/v2 outcome.

## Question

Observed occurrences are treated as more than local viability labels: under a declared candidate transition rule, their configuration can constrain whether the current declared network is capable of supporting reachability to those observed states.

This is **constraint/falsification**, not historical reconstruction.

The primary question is:

> Given a frozen transition operator and an explicit source policy, which observed occurrence targets receive non-zero first-passage support, and how permissive is the operator that produced that compatibility?

## Source policies

Two estimands are deliberately separated.

### Fixed-source compatibility

Use when historical, training, or otherwise prospectively declared source occurrences are available.

- sources remain fixed;
- source occurrences are excluded from target scoring;
- all other declared occurrences are evaluated as targets;
- directional first-passage support is allowed.

This is the preferred compatibility estimand when a defensible source anchor exists.

### Self-excluded peer-source compatibility

Use only when no source ordering is declared.

For each occurrence in turn:

- remove that occurrence from the source set;
- treat all remaining occurrences as equal-weight peer sources;
- evaluate first-passage support to the held-out occurrence.

This is a source-uncertain mutual-compatibility envelope. It is **not a directional historical-colonisation test**. In a true one-way source -> descendant chain, the ancestral source may correctly be unreachable from descendants and therefore unsupported under this peer-source estimand.

## Outputs per candidate rule

Report separately:

- per-target first-passage support;
- first positive propagation step when supported;
- unsupported occurrence target IDs;
- occurrence coverage fraction;
- mean log support with a declared numerical floor;
- median support;
- operator mean outgoing transition mass;
- operator active-edge fraction;
- source policy;
- operator and result fingerprints.

## No winner score

Occurrence compatibility and operator permissiveness must not be collapsed into one tuned scalar.

A fully connected or otherwise highly permissive rule can support every observed occurrence simply because it supports nearly everything. Therefore:

> higher occurrence compatibility is not, by itself, evidence that a rule is a better historical explanation.

The comparison API returns candidate results side by side and intentionally has no `winner`, ranking, posterior probability, or universal acceptance threshold.

## Interpretation of unsupported occurrences

If a target has zero support under the frozen current network, the allowed statement is:

> the target is unsupported under this declared transition rule, source policy, node universe, and propagation depth.

Do not translate this automatically into:

- historically impossible;
- never colonised;
- causal environmental barrier;
- no gene flow;
- absence of extinct or unsurveyed intermediates.

Historical environments, extinct stepping stones, missing nodes, long-distance events and human transport remain alternative explanations unless independently constrained.

## Candidate-rule comparison

Candidate operators must use exactly the same node universe and node order. Rule IDs are sorted deterministically. Occurrence ID input order must not change results or fingerprints.

The comparison preserves:

1. occurrence compatibility;
2. transition permissiveness;
3. directional/source-policy dependence.

It does not select a winner.

## Synthetic falsification gate

Before empirical use, known-truth tests must show at least:

1. a fixed-source chain supports all downstream observed occurrences;
2. a broken rule leaves the disconnected observed target unsupported;
3. an over-permissive rule may also support all occurrences but is explicitly more permissive and is not auto-selected;
4. self-excluded peer-source compatibility can fail for the ancestral source of a true one-way chain, demonstrating that it must not be interpreted as directional history recovery;
5. occurrence order does not change fingerprints;
6. no empirical outcome is involved in rule construction or gate selection.

## Next-stage boundary

Passing this gate would establish only that occurrences can **falsify or constrain** some candidate transition rules under declared assumptions.

It would not establish that occurrence-only information uniquely identifies the generating transition rule. Distinguishing multiple occurrence-compatible rules requires additional information, such as independently surveyed non-detections, historical colonisation order, directional movement data, genetics used strictly as external validation, or other process-specific evidence.
