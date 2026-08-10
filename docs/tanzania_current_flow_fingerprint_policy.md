# Tanzania current-flow cross-run fingerprint policy

## Why exact and seven-decimal freezes failed

The current-flow candidate engine stores raw float64 arrays and verifies each
shard locally at 12 decimal places. Sparse LU factorization nevertheless differs
by a few last-place units across otherwise equivalent GitHub runners. Two early
outcome-free executions differed by at most about `4.5e-10` absolutely and
`9.2e-13` relatively, so the initial cross-run contract used seven decimals.

During independent verification after the first held-out result had already been
frozen, a third candidate-generation execution failed that seven-decimal hash.
A direct array audit showed no biological or algorithmic change:

- East arrays were identical under the seven-decimal contract;
- West pairwise values differed by at most `3.430500328249764e-11`;
- West primary isolation differed by at most `3.9540282159578055e-10`;
- the maximum relative difference was `8.360282256199145e-13`;
- all physical invariants and all 512 candidate distinctions were preserved.

The failure occurred because a few values lay almost exactly on a seven-decimal
rounding boundary. Tiny values on opposite sides of that boundary receive
different hashes even when their numerical difference is orders of magnitude
smaller than `1e-7`. Decimal rounding is therefore a quantization diagnostic,
not a mathematical tolerance comparison.

## Current two-level integrity rule

1. **Run-local shard integrity remains strict.** Each shard verifies the exact
   file it wrote using the 12-decimal fingerprint. This detects corruption,
   truncation, replacement, and within-run artifact mixing.
2. **Cross-run library identity uses six decimal places.** Complete-library
   diagnostic hashes and scalar summaries are normalized to `1e-6`. The two
   independently generated full West libraries that failed at seven decimals
   are identical at six decimals, as are the East libraries.
3. **Raw model inputs are never rounded.** Candidate selection and held-out
   prediction continue to use the unmodified float64 arrays.

Six-decimal normalization still leaves all 512 pairwise matrices and all 512
primary isolation vectors distinct in each region. Every library must also pass
finiteness, positivity, symmetry, zero-diagonal, all-one minimum, and Rayleigh
monotonicity checks.

## Regression guard

The synthetic test deliberately places values across a seven-decimal rounding
boundary and perturbs them by `4e-10`. It requires the seven-decimal hashes to
differ, the six-decimal hashes to agree, and a `2e-6` change to remain
detectable.

## Claim boundary and timing

The initial tolerance policy was selected before species-level outcomes. The
change from seven to six decimals was made after the first held-out result was
frozen but before independent result confirmation. It was triggered solely by
an upstream candidate-library gate and was based on direct array differences,
not on the sign, magnitude, or significance of the EOG comparison. It cannot
improve or reverse the biological result because it changes only diagnostic
hashes; raw current-flow arrays and all downstream formulas remain unchanged.
