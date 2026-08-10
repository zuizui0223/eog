# Tanzania current-flow cross-run fingerprint policy

## Why the original freeze failed

Two independent, outcome-free GitHub Actions executions generated the same
Tanzania source package, the same 512 resistance combinations per region, and
candidate arrays that passed every electrical-network invariant. The final
library check nevertheless failed because it hashed float64 arrays after
rounding to 12 decimal places.

Sparse LU factorization can differ by a few units in the last place across
otherwise equivalent runners. In the observed rerun comparison, the largest
absolute difference was approximately `4.5e-10` and the largest relative
difference was approximately `9.2e-13`. Those changes did not alter candidate
ordering, symmetry, diagonal values, positivity, uniqueness, or Rayleigh
monotonicity.

Treating that machine-level variation as scientific drift made the freeze less
reproducible rather than more rigorous.

## Frozen two-level integrity rule

The implementation now uses two distinct checks.

1. **Run-local shard integrity remains strict.** Each shard verifies the exact
   file it wrote using the existing 12-decimal fingerprint. This detects
   truncation, corruption, accidental file replacement, and within-run mixing.
2. **Cross-run library identity uses seven decimal places.** The complete
   library hashes and scalar manifest summaries are normalized to `1e-7`
   before hashing. This is more than two orders of magnitude coarser than the
   largest observed runner-level LU difference.

The raw candidate arrays are still stored as unmodified float64 values. The
normalization applies only to diagnostic hashes and human-readable scalar
summaries; it does not change current-flow values used by later models.

## Scientific guards retained

Every full 512-candidate library must still satisfy all of the following before
it can match the committed fingerprint:

- finite and non-negative pairwise effective resistances;
- finite and positive primary and sensitivity isolation values;
- symmetric 42 x 42 matrices with zero diagonals;
- 512 distinct pairwise matrices and 512 distinct primary isolation vectors;
- the all-one resistance surface as the elementwise minimum;
- zero Rayleigh-monotonicity violations across all adjacent resistance levels
  for eucalyptus, tea, and other agriculture.

A synthetic regression test additionally requires a `4.5e-10` perturbation to
retain the same cross-run fingerprint, while a `2e-6` change must produce a
different fingerprint.

## Claim boundary

This correction was selected from two candidate-generation runs before any
species-specific resistance choice, occurrence-model fit, log loss, AUC, or
EOG comparison. It changes only the reproducibility diagnostic and provides no
opportunity to improve a biological outcome.
