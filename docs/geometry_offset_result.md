# Geometry-derived offset development result

Design committed before scoring as `2913f7f`. Four seeds, 120 eight-node graphs
per seed, three regimes: 12 paired comparisons. All results are retained in
`validation/layer_b_mechanism_v2/geometry_offset_development_result_v1.json`.
The graph operators and innovation fingerprints are aggregated into per-seed
SHA-256 provenance digests; `build_design` regenerates their individual records.

## Mean selected excess natural-log loss relative to baseline

Negative is improvement. All candidates use the same fit responses and a separate
graph-level calibration partition; selection ties choose baseline.

| Regime | RF + absolute EOG | EOG offset, 10 | EOG offset, mean/std | Distance offset, 1 |
| --- | ---: | ---: | ---: | ---: |
| Route signal | -0.001626 | -0.005771 | -0.003142 | -0.017738 |
| Environment only | -0.000572 | 0.000000 | +0.000406 | -0.000804 |
| Unseen route reversal | +0.002407 | +0.012419 | +0.006740 | +0.045802 |

On the route-signal cases the ten-feature offset improves over concatenation,
but the simple distance correction improves more. In the neutral regime the
ten-feature correction is never promoted. Under reversal all informative
corrections can be harmful; distance correction is promoted in every replicate
and has the largest selected harm. No general winner or deployment promotion is
declared. Always-on scores, selections, and null-feature controls are in the JSON.

## Interpretation ceiling

This is the first test in this offset development line to derive supports through
EOG operators from synthetic coordinates, rather than stipulating support values.
The response generator instead uses shortest paths, including finite routes that
can be unreachable within EOG's four-step horizon. Graphs, not target rows, are
held apart in both OOF fitting and outer evaluation.

The distance comparator uses radius 0.55, matching the known generating process;
EOG uses the predeclared radii 0.45/0.65 and depth four. Thus representation,
parameter knowledge, and process assumptions are not fully matched. This is a
simple mechanism-matched comparator, not proof that distance generally dominates
EOG or that all ten features are useless. The experiment favours path information
by design; no biological utility or methods-paper superiority follows.

## Development consequence

Do not add more summary features or promote the offset as generally superior.
The next distinct comparison must independently fix equal parameter information
for all methods and include uncertainty in the generating graph, simple
distance/mean/std controls, matched and misspecified assumptions, and the existing
adverse-shift case. Current results must not be reused to tune and then labelled
independent confirmation. Empirical closed-lane results remain unchanged.
