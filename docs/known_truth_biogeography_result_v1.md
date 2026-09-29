# Known-truth virtual biogeography v1 — result interpretation

## Status

The first canonical benchmark and the preregistered 64-case witness-complexity factorial have both completed successfully in CI.

This is a separate simulation-validation line and does not change the frozen EOG-WF empirical denominator.

## Canonical benchmark

The hand-constructed canonical cases behaved as required:

- H1 truth retention: **SUPPORTED**
- H2 discriminating contraction: **SUPPORTED**
- H3 omitted-truth finite-universe falsification when complete positive witnesses exist: **SUPPORTED**
- H4 honest non-identification under observational equivalence: **SUPPORTED**
- H5 false-positive observation boundary: **CONFIRMED**

The canonical result fingerprint is:

`4b4ccf41052ccc09609ad81f33e10d34919199c4af45104bc4d901893b858f04`

This establishes that the implementation can do all four logical operations when the required positive witnesses exist.

## Preregistered factorial

The larger factorial used:

- 4 virtual landscape families;
- 16 candidate virtual processes per landscape;
- 64 eligible truth cases;
- positive-occurrence coverage of 0.1, 0.25, 0.5 and 1.0;
- 32 nested sampling replicates per truth case.

The full result fingerprint is:

`b1a2df3a6b1708b533f1f2c2d573eb9802f3a18d8bcada3e55e37124918d533b`

### Exact correctness checks

- truth-retention failures: **0**
- witness-criterion mismatches: **0**
- nested-sampling monotonicity violations: **0**
- observational-equivalence violations: **0**
- omitted-truth set-boundary mismatches: **0**

Therefore the finite positive-occurrence compatibility logic behaved exactly as declared.

### The important negative result

Despite those correctness results:

- unique truth identification at full occurrence coverage: **0/64**
- observational-equivalence cases: **64/64**
- minimum positive witness set: **unavailable in 64/64 cases**
- unique identification rate at 10%, 25%, 50%, 100% coverage: **0 at every level**
- omitted-truth universe falsification: **0/64**
- omitted-truth universe survival: **64/64**

Thus the stronger proposition

> enough positive occurrences should eventually recover the true virtual distribution-forming process

is **refuted for the frozen factorial universe**.

The reason is structural rather than statistical. Every true process had at least one false candidate whose reachable positive state was identical to, or a superset of, the truth. Positive occurrences cannot falsify a process that supports every observed positive state.

## Exact witness criterion

For truth reachable set (R_*), false-world reachable sets (R_w), and observed positive set (Osubseteq R_*):

a false world (w) is eliminated exactly when

[
O cap (R_* setminus R_w) 
eq arnothing.
]

Truth is uniquely identifiable only when the observed positives hit the exclusion set of **every** false world:

[
orall w
eq *,quad
O cap (R_* setminus R_w) 
eq arnothing.
]

If any false world satisfies

[
R_* subseteq R_w,
]

then no amount of positive-occurrence sampling can eliminate it.

This is the central result exposed by the factorial.

## Scientific consequence for EOG

The simulation does **not** support EOG as a general true-process recovery algorithm from positive occurrence data.

It supports a narrower and cleaner role:

> **EOG can falsify a declared process only when the observations contain a positive witness that the process cannot accommodate; otherwise the correct result is unresolved, even with complete occurrence coverage.**

This turns non-identification from a weakness into an explicit output.

The next scientific question should therefore not be “how can we force EOG to choose the true world?” It should be:

> **What additional evidence creates new witnesses between otherwise positive-equivalent process worlds?**

Candidate evidence types include independently surveyed negatives, temporal colonisation order, genetic relationships, or other process-specific observations. These should be separate future protocols rather than repairs to the present factorial.

## Language / performance result

The preregistered Python factorial required **75.865 s** for the target workload, exceeding the frozen 60 s threshold.

Therefore a C++ backend is now **permitted** for larger sweeps.

However the runtime is dominated by repeated recomputation of the same first-passage relations across thousands of occurrence subsets. The first optimisation should be algorithmic:

1. precompute per-world reachable-state bitsets;
2. use bitwise subset tests for repeated positive-occurrence compatibility;
3. retain Python production reconstruction on frozen audit fixtures;
4. only then benchmark whether a C++ bitset/graph backend is still necessary.

Recommended architecture:

```text
Python = scientific reference, contracts, fingerprints, audit, plots
C++    = optional repeated reachability / bitset backend after equivalence tests
```

Do not rewrite the scientific logic in C++ before the Python/C++ equivalence contract exists.
