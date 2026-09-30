# BAM stochastic assay-risk v1

## Why Phase VIII exists

Phase VII showed that repeating the same deterministic systematically biased assay does
not add robust information.

That result must not be generalized to independent random error.

Phase VIII therefore changes the observation process while freezing the ecological
universe, future transformations and Phase-VII assay-field selection.

## Stochastic assay worlds

Two global assay-quality worlds are admitted:

- moderate accuracy: (p_{correct}=0.7);
- high accuracy: (p_{correct}=0.9).

For a field with (K) coordinate levels, every incorrect code receives equal positive
probability.  Thus every assay kernel has full support.

Repeats are iid conditional on ecological world, field and assay-quality world.

## Exact robustness and probabilistic distinguishability are different

Because every code has positive probability under every true value, no finite number of
repeats can make same-quality target-discordant hypotheses support-disjoint.

So exact EOG-style robust separation remains unavailable.

But repeated independent assays can reduce distributional overlap.

For two joint hypotheses (h_1,h_2), use Bhattacharyya affinity

[
BC(P,Q)=\sum_y\sqrt{P(y)Q(y)}.
]

Under independent repeats and fields, affinities multiply.

The equal-prior binary pairwise Bayes error satisfies

[
P_e^*\le BC/2.
]

The frozen Phase-VIII criterion is therefore the **worst target-discordant pair**
satisfying

[
BC/2\le0.05.
]

This is a pairwise sufficient error bound, not a global posterior probability.

## Fixed design

For every one of the 67 Phase-VII target-unresolved fibers:

1. reproduce its frozen Phase-VII canonical robust minimum;
2. keep only the ecological assay fields from that design;
3. apply random assay error to exactly those fields;
4. repeat every selected field (n=1,\ldots,30) times;
5. compare designs with and without one idealized assay-quality calibration action.

No new assay field is selected after stochastic scoring.

## Cost boundary

Synthetic action count is:

- no calibration: (n\times\#fields);
- quality calibration: (n\times\#fields+1).

This is not monetary, temporal, logistical or ethical field cost.
