# Independent core local bridge confirmation results

The frozen confirmation in issue #13 used seed `20260917`, 15 repeats per cell, sample sizes 60, 120, and 240, and dimensions 2, 4, and 8.

## Frozen gate result

The gate failed.

- minimum primary raw-gap AUC: `0.1942`;
- minimum primary core-local-bridge-score AUC: `0.5533`;
- minimum primary AUC improvement: `0.3591`;
- minimum 20:80 two-mode AUC: `0.9502`;
- connected-median reversal: `true`.

The score therefore must not enter the public API as a general fragmentation statistic and must not replace `gap_strength` in the frozen real-taxon pilot.

## What did confirm

The frozen score remained strong for mode separation in the independent two-dimensional analysis. Across unseen equal and unequal two-mode generators, AUCs ranged from about `0.919` to `1.000`, including 20:80 modes.

## What failed

Performance was inadequate for narrow support interruptions:

- narrow bridge AUC: about `0.553` at n=60, `0.714` at n=120, and `0.586` at n=240;
- medium bridge AUC: about `0.752`, `0.911`, and `0.765`;
- wide bridge AUC: about `0.921`, `0.873`, and `0.996`.

S-shaped and ring-like connected manifolds sometimes had higher median scores than narrow missing-bridge clouds. The developmental statistic therefore conflated strong manifold bottlenecks with subtle internal support loss.

## Interpretation

A single scalar should not be claimed to cover both multimodal separation and missing support along a connected manifold. Future work must separate these ecological questions:

1. **mode separation**: are occupied states divided into dense environmental modes?
2. **support interruption**: is an otherwise continuous occupied trajectory missing an internal segment?

The current score is retained as benchmark evidence for the first question only. A separate method and separate validation target are required for the second.
