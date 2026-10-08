# Matched-information geometry result

Design `aee75d1` was committed before scoring. Eight new seeds, 120 independent
graphs per seed, four regimes: 32 cases. Full scores, decisions, provenance and
runtime are in `validation/layer_b_mechanism_v2/matched_information_offset_result_v1.json`.
No graph, ridge, signal scale, selector or feature definition was retuned.

## Mean calibration-selected excess natural-log loss

Negative improves over the baseline. These are small developmental synthetic
comparisons, not a statistical superiority test or an ecological validation.

| Truth regime | EOG offset, 2 | Best-path offset, 2 | RF + EOG, 2 | EOG offset, 10 |
| --- | ---: | ---: | ---: | ---: |
| Multiple-path diffusion | -0.017026 | -0.010314 | -0.018811 | -0.015351 |
| Best-path process | -0.000412 | -0.004896 | +0.001721 | -0.000135 |
| Environment only | +0.002625 | +0.002474 | +0.002039 | +0.003271 |
| Unseen diffusion reversal | +0.094244 | +0.049982 | +0.055710 | +0.140659 |

Paired selected EOG-two minus path-two differences:

- Diffusion: mean -0.006712, range [-0.036414,+0.021596], 5 wins/8, 1 tie.
- Best path: mean +0.004484, range [-0.008734,+0.016052], 1 win/8, 2 ties.
- Environment only: mean +0.000151, range [-0.014583,+0.013375], 1 win/8, 5 ties.
- Reversal: mean +0.044262, range [-0.005229,+0.169449], 1 win/8, 1 tie.

## Conclusion and development decision

The preceding comparison's true-radius/horizon advantage is removed: both
methods share transition matrices, loss, sources, candidate-world information and
horizon, and the primary offsets both use two features. Summing routes and
selecting the strongest route express different process assumptions. In these
controls the matching representation tends to work better, not universally.

The proposed residual-learning change does **not** demonstrate superiority to
simple concatenation: in the diffusion regime two-feature concatenation has
lower selected loss than two-feature offset. Ten features are no improvement
over two here. All informative approaches are vulnerable to the unobserved
reversal; calibration-only adoption does not solve future concept change.

Accordingly do not promote offset learning or ten-feature expansion to default.
Retain the minimal two-feature representation and concatenation as required
comparators. A future method must justify learning *when* multiple-route support
adds information beyond best-path support, while preserving null/reversal
outcomes and the independent safety policy. Do not claim that fitted coefficients
identify biological movement mechanisms.

## Limits

This deliberately contains one positive control for each process assumption.
Diffusion truth is a finite Monte Carlo simulation of the same declared
transition mechanism, not an unrelated ecological process; best-path truth
likewise intentionally favours the path assumption. Structural responses are
still synthetic, and both methods are given geometry/kernel parameters rather
than estimating them. The hidden world is sampled but never exposed as a
predictor. Monte Carlo error is retained. Eight seeds, one graph family and one
signal scale are not a basis for a general methods-paper or empirical claim.

Previous results remain frozen. All 32 rows, always-on losses and permuted-feature
controls are kept, including cases where random features appear favourable by
chance. No new biological response was accessed and no default pipeline changed.
